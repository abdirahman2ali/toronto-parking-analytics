---
title: Locations — Toronto Parking Analytics
---

<style>
  .page-header {
    padding: 2rem 0 1.5rem;
    border-bottom: 1px solid #1e1e30;
    margin-bottom: 1.5rem;
  }
  .page-tag {
    display: inline-block;
    background: #4ade80;
    color: #08080f;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    padding: 0.2rem 0.6rem;
    border-radius: 2px;
    margin-bottom: 0.5rem;
  }
  .page-title {
    font-size: 1.6rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #e8e8f0;
    margin: 0 0 0.25rem;
  }
  .page-desc {
    color: #6b6b88;
    font-size: 0.85rem;
    margin: 0;
  }
  .section-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #6b6b88;
    margin-bottom: 0.75rem;
    padding-left: 2px;
  }
</style>

<div class="page-header">
  <div class="page-tag">Locations</div>
  <h1 class="page-title">Toronto's Highest-Enforcement Streets</h1>
  <p class="page-desc">Ranked by total tickets issued across 2008–2024</p>
</div>

```sql locations_data
select
    location_display,
    location1,
    ticket_count
from toronto_parking.locations
order by ticket_count desc
```

```sql top25
select
    location_display,
    ticket_count
from toronto_parking.locations
order by ticket_count desc
limit 25
```

<div class="section-label">Top 25 Locations by Ticket Volume</div>

<BarChart
    data={top25}
    x=location_display
    y=ticket_count
    title="Highest-Ticket Locations in Toronto"
    yAxisTitle="Total Tickets"
    xAxisTitle="Location"
    swapXY=true
    colorPalette={['#4ade80']}
/>

---

<div class="section-label">All Locations — Searchable</div>

<DataTable
    data={locations_data}
    search=true
    rows=25
>
    <Column id=location_display title="Location" />
    <Column id=location1 title="Street" />
    <Column id=ticket_count title="Total Tickets" fmt='#,##0' contentType=colorscale colorScale={['#06180c', '#4ade80']} />
</DataTable>
