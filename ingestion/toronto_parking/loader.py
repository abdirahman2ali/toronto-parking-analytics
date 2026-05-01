import logging
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

load_dotenv(Path.home() / ".claude" / ".env")
load_dotenv()

logger = logging.getLogger(__name__)

SCHEMA = "toronto"
RAW_TABLE = "parking_tickets_raw"
CHUNK_SIZE = 5_000


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
            for idx_suffix, cols in [
                ("date", "date_of_infraction"),
                ("code", "infraction_code"),
                ("date_code", "date_of_infraction, infraction_code"),
            ]:
                conn.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS idx_{RAW_TABLE}_{year}_{idx_suffix}
                    ON {SCHEMA}.{RAW_TABLE}_{year} ({cols})
                """))

        # Catch-all partition for any future years not yet explicitly created
        future_start = max(years) + 1 if years else 2026
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {SCHEMA}.{RAW_TABLE}_future
            PARTITION OF {SCHEMA}.{RAW_TABLE}
            FOR VALUES FROM ('{future_start}-01-01') TO ('9999-12-31')
        """))

    logger.info(f"Partitioned table ensured for years: {years}")


def upsert_dataframe(df: pd.DataFrame, engine) -> int:
    """Insert rows into the raw table, ignoring duplicates. Returns rows inserted."""
    if df.empty:
        return 0

    columns = list(df.columns)
    col_list = ", ".join(columns)
    placeholders = ", ".join(f":{c}" for c in columns)

    sql = text(f"""
        INSERT INTO {SCHEMA}.{RAW_TABLE} ({col_list})
        VALUES ({placeholders})
        ON CONFLICT (tag_number_masked, date_of_infraction) DO NOTHING
    """)

    records = df.to_dict(orient="records")
    total_inserted = 0

    with engine.begin() as conn:
        for i in range(0, len(records), CHUNK_SIZE):
            chunk = records[i : i + CHUNK_SIZE]
            result = conn.execute(sql, chunk)
            total_inserted += result.rowcount

    return total_inserted
