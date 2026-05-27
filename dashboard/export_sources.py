"""
Export pre-aggregated datasets from ClickHouse to CSV for Evidence.dev.

Usage:
    python export_sources.py

Reads CLICKHOUSE_* credentials from .env (project-local) or .claude/.env (shared).
Writes CSV files to sources/toronto_parking/.
"""

import os
import csv
import logging
from pathlib import Path

import clickhouse_connect
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

SHARED_ENV = Path(__file__).resolve().parents[4] / ".claude" / ".env"
LOCAL_ENV = Path(__file__).resolve().parent / ".env"

load_dotenv(SHARED_ENV)
load_dotenv(LOCAL_ENV, override=True)

OUT_DIR = Path(__file__).resolve().parent / "sources" / "toronto_parking"

QUERIES: dict[str, str] = {
    "kpi_summary": """
        SELECT
            sum(ticket_count)                                       AS total_tickets,
            round(sum(total_fines_cad), 0)                         AS total_revenue_cad,
            round(sum(total_fines_cad) / sum(ticket_count), 2)     AS avg_fine_cad,
            (SELECT count() FROM toronto_marts.dim_infraction_codes)      AS unique_violation_types
        FROM toronto_marts.rpt_tickets_monthly
    """,
    "annual_trend": """
        SELECT
            year,
            sum(ticket_count)           AS tickets,
            round(sum(total_fines_cad), 0) AS revenue_cad
        FROM toronto_marts.rpt_tickets_monthly
        GROUP BY year
        ORDER BY year
    """,
    "monthly_trend": """
        SELECT
            year,
            month,
            year_month,
            ticket_count,
            round(total_fines_cad, 0)   AS total_fines_cad,
            round(avg_fine_cad, 2)       AS avg_fine_cad,
            morning_ticket_count,
            afternoon_ticket_count,
            evening_ticket_count,
            night_ticket_count,
            weekend_ticket_count
        FROM toronto_marts.rpt_tickets_monthly
        ORDER BY year, month
    """,
    "monthly_seasonality": """
        SELECT
            month,
            round(avg(ticket_count), 0) AS avg_monthly_tickets,
            sum(ticket_count)           AS total_tickets
        FROM toronto_marts.rpt_tickets_monthly
        GROUP BY month
        ORDER BY month
    """,
    "time_of_day_split": """
        SELECT 'Morning'   AS bucket, sum(morning_ticket_count)   AS tickets FROM toronto_marts.rpt_tickets_monthly
        UNION ALL
        SELECT 'Afternoon' AS bucket, sum(afternoon_ticket_count) AS tickets FROM toronto_marts.rpt_tickets_monthly
        UNION ALL
        SELECT 'Evening'   AS bucket, sum(evening_ticket_count)   AS tickets FROM toronto_marts.rpt_tickets_monthly
        UNION ALL
        SELECT 'Night'     AS bucket, sum(night_ticket_count)     AS tickets FROM toronto_marts.rpt_tickets_monthly
    """,
    "violations": """
        SELECT
            infraction_description,
            standard_fine_amount,
            total_tickets,
            first_seen_date,
            last_seen_date
        FROM toronto_marts.dim_infraction_codes
        ORDER BY total_tickets DESC
        LIMIT 100
    """,
    "fine_distribution": """
        SELECT
            set_fine_amount,
            count() AS ticket_count
        FROM toronto_marts.fct_parking_tickets
        WHERE set_fine_amount > 0
        GROUP BY set_fine_amount
        ORDER BY set_fine_amount
    """,
    "hour_day_heatmap": """
        SELECT
            day_of_week_num,
            day_of_week_name,
            infraction_hour,
            count() AS tickets
        FROM toronto_marts.fct_parking_tickets
        WHERE infraction_hour IS NOT NULL
          AND infraction_hour >= 0
          AND day_of_week_name != ''
        GROUP BY day_of_week_num, day_of_week_name, infraction_hour
        ORDER BY day_of_week_num, infraction_hour
    """,
    "day_of_week": """
        SELECT
            day_of_week_num,
            day_of_week_name,
            count()                       AS tickets,
            round(avg(set_fine_amount), 2) AS avg_fine
        FROM toronto_marts.fct_parking_tickets
        WHERE day_of_week_name != ''
        GROUP BY day_of_week_num, day_of_week_name
        ORDER BY day_of_week_num
    """,
    "locations": """
        SELECT
            location_display,
            location1,
            ticket_count
        FROM toronto_marts.dim_locations
        WHERE location1 IS NOT NULL
          AND location1 != ''
        ORDER BY ticket_count DESC
        LIMIT 100
    """,
}


def _get_client() -> clickhouse_connect.driver.Client:
    host = os.getenv("CLICKHOUSE_HOST", "localhost")
    port = int(os.getenv("CLICKHOUSE_PORT", "8123"))
    user = os.getenv("CLICKHOUSE_USER", "default")
    password = os.getenv("CLICKHOUSE_PASSWORD", "")
    return clickhouse_connect.get_client(
        host=host,
        port=port,
        username=user,
        password=password,
    )


def _export(client: clickhouse_connect.driver.Client, name: str, query: str) -> None:
    log.info("Exporting %s ...", name)
    result = client.query(query.strip())
    out_path = OUT_DIR / f"{name}.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(result.column_names)
        writer.writerows(result.result_rows)
    log.info("  → %s (%d rows)", out_path.name, len(result.result_rows))


def main() -> None:
    client = _get_client()
    log.info("Connected to ClickHouse at %s", os.getenv("CLICKHOUSE_HOST", "localhost"))
    for name, query in QUERIES.items():
        _export(client, name, query)
    log.info("Export complete. Run `npm run dev` inside dashboard/ to preview.")


if __name__ == "__main__":
    main()
