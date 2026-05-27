{{
    config(
        materialized='table',
        engine='MergeTree()',
        order_by='(year, month)',
        partition_by='year'
    )
}}

with facts as (
    select * from {{ ref('fct_parking_tickets') }}
),

monthly as (
    select
        infraction_year                                                     as year,
        infraction_month                                                    as month,
        concat(
            toString(infraction_year), '-',
            leftPad(toString(infraction_month), 2, '0')
        )                                                                   as year_month,

        count(*)                                                            as ticket_count,
        sum(set_fine_amount)                                                as total_fines_cad,
        round(avg(set_fine_amount), 2)                                      as avg_fine_cad,
        count(distinct infraction_code)                                     as unique_infraction_codes,
        count(distinct location1)                                           as unique_streets,
        countIf(is_weekend)                                                 as weekend_ticket_count,
        countIf(time_of_day_bucket = 'Morning')                             as morning_ticket_count,
        countIf(time_of_day_bucket = 'Afternoon')                           as afternoon_ticket_count,
        countIf(time_of_day_bucket = 'Evening')                             as evening_ticket_count,
        countIf(time_of_day_bucket = 'Night')                               as night_ticket_count,
        any(infraction_code)                                                as top_infraction_code
    from facts
    group by infraction_year, infraction_month
)

select * from monthly
order by year, month
