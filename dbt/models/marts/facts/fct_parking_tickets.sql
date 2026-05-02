{{
    config(
        materialized='incremental',
        engine='MergeTree()',
        unique_key='ticket_id',
        incremental_strategy='delete+insert',
        order_by='(infraction_date, ticket_id)',
        partition_by='toYear(infraction_date)'
    )
}}

with source as (
    select * from {{ ref('int_tickets_enriched') }}
    {% if is_incremental() %}
        -- Re-process from the most recent date already in the table to catch late arrivals
        where infraction_date >= (select max(infraction_date) from {{ this }})
    {% endif %}
),

-- Deduplicate genuine source duplicates (identical rows in Toronto Open Data)
deduped as (
    select
        *,
        row_number() over (
            partition by tag_number_masked, infraction_date, time_of_infraction,
                         infraction_code, location2
            order by tag_number_masked
        ) as rn
    from source
)

select
    {{ dbt_utils.generate_surrogate_key(['tag_number_masked', 'infraction_date', 'time_of_infraction', "toString(coalesce(infraction_code, 0))", 'location2']) }}
                                                    as ticket_id,
    tag_number_masked,
    infraction_date,
    infraction_code,
    infraction_description,
    set_fine_amount,
    time_of_infraction,
    location1,
    location2,
    officer_tag_number,
    province,
    infraction_year,
    infraction_month,
    infraction_day,
    day_of_week_num,
    day_of_week_name,
    iso_week,
    infraction_quarter,
    infraction_hour,
    time_of_day_bucket,
    is_weekend
from deduped
where rn = 1
