{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['location_key'], 'unique': True},
            {'columns': ['location1']},
        ]
    )
}}

with tickets as (
    select * from {{ ref('stg_parking_tickets') }}
),

locations as (
    select
        location1,
        location2,
        count(*)            as ticket_count
    from tickets
    where location1 is not null
    group by location1, location2
)

select
    {{ dbt_utils.generate_surrogate_key(['location1', "coalesce(location2, '')"]) }}
                                    as location_key,
    location1,
    location2,
    location1
        || case
            when location2 is not null and location2 != ''
            then ' at ' || location2
            else ''
        end                         as location_display,
    ticket_count
from locations
