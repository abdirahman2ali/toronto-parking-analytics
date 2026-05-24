# Toronto Parking Analytics

End-to-end data pipeline processing 34.7M+ Toronto parking ticket records (2006–present) from the [Toronto Open Data](https://open.toronto.ca/dataset/parking-tickets/) CKAN API into an analytics-ready dimensional model.

The pipeline answers questions like: which infractions are most common, which streets generate the most tickets, how enforcement patterns shift by month and year, and what the fine revenue composition looks like across violation types.

**Stack:** Python · ClickHouse · dbt · GitHub Actions

---

## Architecture

```
Toronto Open Data (CKAN API)
    │  ~2.8M records/year, CSV per year (2006–present)
    ▼
Python ingestion
    │  Fetches, decodes (UTF-8/UTF-16/Latin-1), deduplicates, bulk-loads
    ▼
Neon PostgreSQL — toronto.parking_tickets_raw
    │  Range-partitioned by year; 34.7M+ rows total
    ▼
dbt transformation
    │  Staging → Intermediate → Marts
    ▼
BI layer (in-progress)
```

## Data model

Raw tickets flow through three dbt layers before landing in queryable marts:

```
toronto.parking_tickets_raw
    │  Partitioned raw table — one partition per year, append-only
    ▼
toronto_staging.stg_parking_tickets
    │  Column renaming, type casting, null normalization
    ▼
toronto_intermediate.int_tickets_enriched
    │  Date and time dimensions extracted (year, month, hour, day of week)
    ▼
toronto_marts.fct_parking_tickets    — fact table, incremental by ticket date
toronto_marts.dim_infraction_codes   — one row per violation type with fine amounts
toronto_marts.dim_locations          — one row per street / cross-street combination
toronto_marts.rpt_tickets_monthly    — monthly rollup aggregated for dashboard consumption
```

## BI layer (in-progress)

A dashboard layer connecting to the marts schema is planned. `rpt_tickets_monthly` is the primary reporting surface — pre-aggregated by month, infraction type, and location for fast dashboard queries. Tool selection (Grafana, Metabase, or Looker) is not yet decided.

## Automation

The pipeline runs on the 1st of every month via GitHub Actions. A `workflow_dispatch` trigger allows on-demand runs with a `full_refresh` boolean input for rebuilding all dbt models from scratch.

Secrets required in the GitHub repo: `TORONTO_DATABASE_URL`, `TORONTO_DATABASE_URL_DIRECT`.
