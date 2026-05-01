# Toronto Parking Analytics

Monthly data pipeline ingesting Toronto parking ticket data from the [Toronto Open Data](https://open.toronto.ca/dataset/parking-tickets/) CKAN API into a Neon PostgreSQL warehouse, transformed with dbt into analytics-ready fact, dimension, and reporting tables.

**Stack:** Python · PostgreSQL (Neon) · dbt · GitHub Actions

---

## What it does

- Downloads ~2.8M+ parking ticket records per year from Toronto Open Data
- Loads them into a range-partitioned PostgreSQL table (one partition per year)
- Transforms the raw data through three dbt layers into a dimensional model
- Runs monthly via GitHub Actions; incremental after the first full load

## Setup

Requires Python 3.11+.

```bash
git clone <repo-url>
cd toronto-parking-analytics

# Install ingestion dependencies
pip install -r ingestion/requirements.txt

# Install dbt
pip install dbt-postgres>=1.8.0

# Install dbt packages
cd dbt && dbt deps
```

Copy `.env.example` to a local `.env` file (or add vars to `.claude/.env`) and fill in your Neon connection strings:

```bash
cp ingestion/.env.example ingestion/.env
```

## Environment variables

| Variable | Description | Example |
|----------|-------------|---------|
| `TORONTO_DATABASE_URL` | Neon pooled connection string | `postgresql://user:pass@ep-xxx.pooler.region.neon.tech/toronto_parking` |
| `TORONTO_DATABASE_URL_DIRECT` | Neon direct connection string (DDL only) | `postgresql://user:pass@ep-xxx.region.neon.tech/toronto_parking` |
| `TORONTO_PGHOST` | Postgres host (for dbt) | `ep-xxx.pooler.region.neon.tech` |
| `TORONTO_PGPORT` | Postgres port | `5432` |
| `TORONTO_PGDATABASE` | Database name | `toronto_parking` |
| `TORONTO_PGUSER` | Postgres user | `user` |
| `TORONTO_PGPASSWORD` | Postgres password | — |

## How to run

**Initial full load:**

```bash
# 1. Run ingestion (downloads all available years from CKAN)
python ingestion/main.py

# 2. Build all dbt models from scratch
cd dbt && dbt run --full-refresh && dbt test
```

**Incremental (subsequent months):**

```bash
python ingestion/main.py        # upserts current year's new tickets
cd dbt && dbt run && dbt test   # incremental run on fct_parking_tickets
```

## Data model

```
toronto.parking_tickets_raw          ← partitioned raw table (yearly range partitions)
    │
    ▼
toronto_staging.stg_parking_tickets  ← column renaming, type casting
    │
    ▼
toronto_intermediate.int_tickets_enriched  ← date/time dimensions added
    │
    ▼
toronto_marts.fct_parking_tickets    ← fact table, incremental
toronto_marts.dim_infraction_codes   ← one row per violation type
toronto_marts.dim_locations          ← one row per street/cross-street
toronto_marts.rpt_tickets_monthly    ← monthly rollup for dashboards
```

## How to test

```bash
# Lint Python
ruff check ingestion/

# dbt compile (syntax check)
cd dbt && dbt compile

# dbt tests
cd dbt && dbt test
```

## GitHub Actions

The pipeline runs automatically on the 1st of every month. A `workflow_dispatch` trigger allows manual runs with an optional `full_refresh` boolean input (set to `true` for the initial load).

Secrets required in the GitHub repo:
- `TORONTO_DATABASE_URL`
- `TORONTO_DATABASE_URL_DIRECT`
