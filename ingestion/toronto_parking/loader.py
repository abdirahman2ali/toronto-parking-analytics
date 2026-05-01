import io
import logging
import os
from pathlib import Path
from typing import Optional

import pandas as pd
from dotenv import load_dotenv
from psycopg2.extras import execute_values
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

load_dotenv(Path(__file__).resolve().parents[4] / ".claude" / ".env")
load_dotenv()

logger = logging.getLogger(__name__)

SCHEMA = "toronto"
RAW_TABLE = "parking_tickets_raw"
CHUNK_SIZE = 10_000


def get_engine(direct: bool = False):
    key = "TORONTO_DATABASE_URL_DIRECT" if direct else "TORONTO_DATABASE_URL"
    url = os.getenv(key)
    if not url:
        raise RuntimeError(f"Environment variable {key} is not set")
    return create_engine(url, poolclass=NullPool)


def ensure_schema(engine) -> None:
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"))
    logger.info(f"Schema '{SCHEMA}' ensured")


def ensure_table(engine, years: list[int]) -> None:
    """Create the partitioned raw table and one child partition per year."""
    with engine.begin() as conn:
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {SCHEMA}.{RAW_TABLE} (
                tag_number_masked      text,
                date_of_infraction     date NOT NULL,
                infraction_code        integer,
                infraction_description text,
                set_fine_amount        numeric(10, 2),
                time_of_infraction     text,
                location1              text,
                location2              text,
                officer_tag_number     text,
                province               text,
                loaded_at              timestamptz DEFAULT now()
            ) PARTITION BY RANGE (date_of_infraction)
        """))

        # Unique constraint on (tag_number_masked, date_of_infraction) enables ON CONFLICT.
        # Must include the partition key (date_of_infraction) per PostgreSQL requirements.
        conn.execute(text(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'uq_{RAW_TABLE}'
                      AND conrelid = '{SCHEMA}.{RAW_TABLE}'::regclass
                ) THEN
                    ALTER TABLE {SCHEMA}.{RAW_TABLE}
                    ADD CONSTRAINT uq_{RAW_TABLE}
                    UNIQUE (tag_number_masked, date_of_infraction);
                END IF;
            EXCEPTION WHEN others THEN
                NULL;  -- partition already has data; index creation happens per partition
            END $$;
        """))

        for year in years:
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {SCHEMA}.{RAW_TABLE}_{year}
                PARTITION OF {SCHEMA}.{RAW_TABLE}
                FOR VALUES FROM ('{year}-01-01') TO ('{year + 1}-01-01')
            """))

        # Catch-all partition for any future years not yet explicitly created
        future_start = max(years) + 1 if years else 2026
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {SCHEMA}.{RAW_TABLE}_future
            PARTITION OF {SCHEMA}.{RAW_TABLE}
            FOR VALUES FROM ('{future_start}-01-01') TO ('9999-12-31')
        """))

    logger.info(f"Partitioned table ensured for years: {years}")


def _partition_is_empty(engine, year: int) -> bool:
    table = f"{SCHEMA}.{RAW_TABLE}_{year}"
    with engine.connect() as conn:
        row = conn.execute(text(f"SELECT 1 FROM {table} LIMIT 1")).fetchone()
        return row is None


def _copy_dataframe(df: pd.DataFrame, engine, columns: list[str]) -> int:
    """Bulk-load via COPY — minimal WAL, fastest path for empty partitions."""
    buf = io.StringIO()
    df[columns].to_csv(buf, index=False, header=False, na_rep="\\N")
    buf.seek(0)
    col_list = ", ".join(columns)
    with engine.begin() as conn:
        raw = conn.connection
        cursor = raw.cursor()
        cursor.copy_expert(
            f"COPY {SCHEMA}.{RAW_TABLE} ({col_list}) FROM STDIN WITH (FORMAT CSV, NULL '\\N')",
            buf,
        )
        return cursor.rowcount


def upsert_dataframe(df: pd.DataFrame, engine, year: Optional[int] = None) -> int:
    """Insert rows into the raw table, ignoring duplicates. Returns rows inserted.

    Uses COPY for empty partitions (WAL-minimal initial load) and INSERT ON CONFLICT
    for incremental runs where duplicates may exist.
    """
    if df.empty:
        return 0

    columns = list(df.columns)

    if year is not None and _partition_is_empty(engine, year):
        logger.info(f"[{year}] Partition empty — using COPY (WAL-minimal)")
        return _copy_dataframe(df, engine, columns)

    # Incremental path: partition has existing data, use ON CONFLICT to skip dupes.
    col_list = ", ".join(columns)
    sql = (
        f"INSERT INTO {SCHEMA}.{RAW_TABLE} ({col_list}) VALUES %s "
        f"ON CONFLICT (tag_number_masked, date_of_infraction) DO NOTHING"
    )
    tuples = list(df[columns].itertuples(index=False, name=None))
    total_inserted = 0
    for i in range(0, len(tuples), CHUNK_SIZE):
        chunk = tuples[i : i + CHUNK_SIZE]
        with engine.begin() as conn:
            raw = conn.connection
            cursor = raw.cursor()
            execute_values(cursor, sql, chunk, page_size=CHUNK_SIZE)
            total_inserted += cursor.rowcount
    return total_inserted
