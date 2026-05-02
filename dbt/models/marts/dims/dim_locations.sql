{{
    config(
        materialized='table',
        engine='MergeTree()',
        order_by='location_key'
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
    if(
        isNotNull(location2) and location2 != '',
        concat(location1, ' at ', location2),
        location1
    )                               as location_display,
    ticket_count
from locations
