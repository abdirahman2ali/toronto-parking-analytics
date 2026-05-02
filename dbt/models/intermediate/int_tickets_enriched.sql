with source as (
    select * from {{ ref('stg_parking_tickets') }}
),

enriched as (
    select
        -- identifiers
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

        -- date dimensions
        toYear(infraction_date)                                         as infraction_year,
        toMonth(infraction_date)                                        as infraction_month,
        toDayOfMonth(infraction_date)                                   as infraction_day,
        -- toDayOfWeek: 1=Mon...7=Sun; % 7 converts to Postgres-style 0=Sun...6=Sat
        toDayOfWeek(infraction_date) % 7                                as day_of_week_num,
        -- ClickHouse toDayOfWeek: 1=Mon...7=Sun; array is 1-indexed
        ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][toDayOfWeek(infraction_date)]
                                                                        as day_of_week_name,
        toISOWeek(infraction_date)                                      as iso_week,
        toQuarter(infraction_date)                                      as infraction_quarter,

        -- time dimensions (time_of_infraction is a 4-char HHMM string)
        case
            when match(time_of_infraction, '^\\d{4}$')
            then toInt32(left(time_of_infraction, 2))
            else null
        end                                                             as infraction_hour,

        case
            when match(time_of_infraction, '^\\d{4}$')
                and toInt32(left(time_of_infraction, 2)) between 6 and 11
            then 'Morning'
            when match(time_of_infraction, '^\\d{4}$')
                and toInt32(left(time_of_infraction, 2)) between 12 and 17
            then 'Afternoon'
            when match(time_of_infraction, '^\\d{4}$')
                and toInt32(left(time_of_infraction, 2)) between 18 and 22
            then 'Evening'
            when match(time_of_infraction, '^\\d{4}$')
            then 'Night'
            else null
        end                                                             as time_of_day_bucket,

        -- weekend flag: toDayOfWeek 6=Sat, 7=Sun
        toDayOfWeek(infraction_date) in (6, 7)                         as is_weekend
    from source
)

select * from enriched
