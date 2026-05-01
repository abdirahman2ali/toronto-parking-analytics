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
        extract(year from infraction_date)::integer                 as infraction_year,
        extract(month from infraction_date)::integer                as infraction_month,
        extract(day from infraction_date)::integer                  as infraction_day,
        extract(dow from infraction_date)::integer                  as day_of_week_num,
        trim(to_char(infraction_date, 'Day'))                       as day_of_week_name,
        extract(week from infraction_date)::integer                 as iso_week,
        extract(quarter from infraction_date)::integer              as infraction_quarter,

        -- time dimensions (time_of_infraction is a 4-char HHMM string)
        case
            when time_of_infraction ~ '^\d{4}$'
            then left(time_of_infraction, 2)::integer
            else null
        end                                                         as infraction_hour,

        case
            when time_of_infraction ~ '^\d{4}$'
                and left(time_of_infraction, 2)::integer between 6 and 11
            then 'Morning'
            when time_of_infraction ~ '^\d{4}$'
                and left(time_of_infraction, 2)::integer between 12 and 17
            then 'Afternoon'
            when time_of_infraction ~ '^\d{4}$'
                and left(time_of_infraction, 2)::integer between 18 and 22
            then 'Evening'
            when time_of_infraction ~ '^\d{4}$'
            then 'Night'
            else null
        end                                                         as time_of_day_bucket,

        -- weekend flag (0 = Sunday, 6 = Saturday in PostgreSQL)
        extract(dow from infraction_date) in (0, 6)                as is_weekend
    from source
)

select * from enriched
