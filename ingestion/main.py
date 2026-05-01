import datetime
import logging
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

# Load shared credentials before importing modules that read env vars at import time
load_dotenv(Path.home() / ".claude" / ".env")
load_dotenv()

from toronto_parking.fetcher import fetch_available_years, fetch_year  # noqa: E402
from toronto_parking.loader import ensure_schema, ensure_table, get_engine, upsert_dataframe  # noqa: E402
from toronto_parking.transformer import prepare_for_db  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 30


def _loaded_years(engine) -> list[int]:
    from sqlalchemy import text

    try:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT DISTINCT extract(year from date_of_infraction)::integer AS yr
                FROM toronto.parking_tickets_raw
                ORDER BY yr
            """))
            return [r[0] for r in rows]
    except Exception:
        return []


def _run_year(year: int, engine) -> dict:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"[{year}] Attempt {attempt}/{MAX_RETRIES}: fetching")
            df_raw = fetch_year(year)
            if df_raw is None or df_raw.empty:
                logger.warning(f"[{year}] No data returned — skipping")
                return {"year": year, "status": "skipped", "rows": 0}

            logger.info(f"[{year}] Fetched {len(df_raw):,} rows — transforming")
            df = prepare_for_db(df_raw)

            logger.info(f"[{year}] Upserting {len(df):,} rows")
            inserted = upsert_dataframe(df, engine)
            logger.info(f"[{year}] Done: {inserted:,} new rows inserted")
            return {"year": year, "status": "ok", "rows": inserted}

        except Exception as exc:
            if attempt < MAX_RETRIES:
                logger.warning(f"[{year}] Attempt {attempt} failed: {exc} — retrying in {RETRY_DELAY}s")
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"[{year}] Failed after {MAX_RETRIES} attempts: {exc}")
                return {"year": year, "status": "error", "rows": 0, "error": str(exc)}


def main() -> None:
    engine_direct = get_engine(direct=True)
    engine = get_engine(direct=False)

    available_years = fetch_available_years()
    if not available_years:
        logger.error("No years found in CKAN package — aborting")
        sys.exit(1)
    logger.info(f"Available years in CKAN: {available_years}")

    ensure_schema(engine_direct)
    ensure_table(engine_direct, available_years)

    loaded_years = _loaded_years(engine)
    logger.info(f"Already loaded years: {loaded_years or 'none'}")

    current_year = datetime.date.today().year
    if not loaded_years:
        years_to_process = available_years
        logger.info(f"First run: loading all {len(years_to_process)} available years")
    else:
        # Incremental: re-process current year to pick up new tickets
        years_to_process = [current_year] if current_year in available_years else [max(available_years)]
        logger.info(f"Incremental run: processing year(s) {years_to_process}")

    results = [_run_year(yr, engine) for yr in years_to_process]

    total_inserted = sum(r.get("rows", 0) for r in results)
    failed = [r["year"] for r in results if r["status"] == "error"]

    logger.info(f"Pipeline complete — {total_inserted:,} total rows inserted")
    if failed:
        logger.error(f"Failed years: {failed}")
        sys.exit(1)


if __name__ == "__main__":
    main()
