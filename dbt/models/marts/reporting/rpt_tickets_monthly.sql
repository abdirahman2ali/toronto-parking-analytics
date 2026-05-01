{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['year', 'month'], 'unique': True},
            {'columns': ['year_month']},
        ]
    )
}}

with facts as (
    select * from {{ ref('fct_parking_tickets') }}
),

monthly as (
    select
        infraction_year                                             as year,
        infraction_month                                            as month,
        to_char(
            make_date(infraction_year, infraction_month, 1),
            'YYYY-MM'
        )                                                           as year_month,

        count(*)                                                    as ticket_count,
        sum(set_fine_amount)                                        as total_fines_cad,
        round(avg(set_fine_amount), 2)                              as avg_fine_cad,
        count(distinct infraction_code)                             as unique_infraction_codes,
        count(distinct location1)                                   as unique_streets,
        count(*) filter (where is_weekend)                          as weekend_ticket_count,
        count(*) filter (where time_of_day_bucket = 'Morning')      as morning_ticket_count,
        count(*) filter (where time_of_day_bucket = 'Afternoon')    as afternoon_ticket_count,
        count(*) filter (where time_of_day_bucket = 'Evening')      as evening_ticket_count,
        count(*) filter (where time_of_day_bucket = 'Night')        as night_ticket_count,
        mode() within group (order by infraction_code)              as top_infraction_code
    from facts
    group by infraction_year, infraction_month
)

select * from monthly
order by year, month
