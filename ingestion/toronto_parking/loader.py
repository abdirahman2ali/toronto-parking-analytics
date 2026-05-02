import logging
import os
from pathlib import Path
from typing import Optional

import clickhouse_connect
import pandas as pd
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[4] / ".claude" / ".env")
load_dotenv()

logger = logging.getLogger(__name__)

DATABASE = "toronto"
RAW_TABLE = "parking_tickets_raw"
CHUNK_SIZE = 100_000


def get_client() -> clickhouse_connect.driver.Client:
    host = os.getenv("TORONTO_CLICKHOUSE_HOST", "localhost")
    port = int(os.getenv("TORONTO_CLICKHOUSE_PORT", "8123"))
    username = os.getenv("TORONTO_CLICKHOUSE_USER")
    password = os.getenv("TORONTO_CLICKHOUSE_PASSWORD")
    if not username:
        raise ValueError("TORONTO_CLICKHOUSE_USER env var is required")
    if password is None:
        raise ValueError("TORONTO_CLICKHOUSE_PASSWORD env var is required")
    return clickhouse_connect.get_client(
        host=host,
        port=port,
        username=username,
        password=password,
    )


def ensure_database(client: clickhouse_connect.driver.Client) -> None:
    client.command(f"CREATE DATABASE IF NOT EXISTS {DATABASE}")
    logger.info(f"Database '{DATABASE}' ensured")


def ensure_table(client: clickhouse_connect.driver.Client) -> None:
    client.command(f"""
        CREATE TABLE IF NOT EXISTS {DATABASE}.{RAW_TABLE} (
            tag_number_masked      Nullable(String),
            date_of_infraction     Date,
            infraction_code        Nullable(Int32),
            infraction_description Nullable(String),
            set_fine_amount        Nullable(Decimal(10, 2)),
            time_of_infraction     String,
            location1              Nullable(String),
            location2              Nullable(String),
            officer_tag_number     Nullable(String),
            province               Nullable(String),
            loaded_at              DateTime DEFAULT now()
        )
        ENGINE = MergeTree()
        PARTITION BY toYear(date_of_infraction)
        ORDER BY date_of_infraction
    """)
    logger.info(f"Table '{DATABASE}.{RAW_TABLE}' ensured")


def _year_row_count(client: clickhouse_connect.driver.Client, year: int) -> int:
    result = client.query(
        f"SELECT count() FROM {DATABASE}.{RAW_TABLE} "
        f"WHERE toYear(date_of_infraction) = {year}"
    )
    return result.first_row[0]


def upsert_dataframe(
    df: pd.DataFrame,
    client: clickhouse_connect.driver.Client,
    year: Optional[int] = None,
) -> int:
    """Insert rows into the raw table for a given year.

    If the partition already has data, it is dropped and reloaded (delete+insert).
    Returns the number of rows inserted.
    """
    if df.empty:
        return 0

    if year is not None and _year_row_count(client, year) > 0:
        logger.info(f"[{year}] Partition has existing data — dropping and reloading")
        client.command(
            f"ALTER TABLE {DATABASE}.{RAW_TABLE} DROP PARTITION '{year}'"
        )

    rows = len(df)
    for i in range(0, rows, CHUNK_SIZE):
        chunk = df.iloc[i : i + CHUNK_SIZE]
        client.insert_df(f"{DATABASE}.{RAW_TABLE}", chunk)
        logger.debug(f"[{year}] Inserted chunk {i // CHUNK_SIZE + 1}: {len(chunk):,} rows")

    logger.info(f"[{year}] Inserted {rows:,} rows total")
    return rows
