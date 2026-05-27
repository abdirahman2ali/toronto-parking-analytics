---
title: Violations — Toronto Parking Analytics
---

<style>
  .page-header {
    padding: 2rem 0 1.5rem;
    border-bottom: 1px solid #1e1e30;
    margin-bottom: 1.5rem;
  }
  .page-tag {
    display: inline-block;
    background: #3b8fe8;
    color: white;
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
  <div class="page-tag">Violations</div>
  <h1 class="page-title">What Are Drivers Getting Ticketed For?</h1>
  <p class="page-desc">Breakdown of the 100 most common infraction types across 2008–2024</p>
</div>

```sql violations_data
select
    infraction_description,
    standard_fine_amount,
    total_tickets,
    first_seen_date,
    last_seen_date
from toronto_parking.violations
order by total_tickets desc
```

```sql top20
select
    infraction_description,
    total_tickets,
    standard_fine_amount
from toronto_parking.violations
order by total_tickets desc
limit 20
```

```sql fine_dist
select
    set_fine_amount,
    ticket_count
from toronto_parking.fine_distribution
order by set_fine_amount
```

<div class="section-label">Top 20 Violations by Volume</div>

<BarChart
    data={top20}
    x=infraction_description
    y=total_tickets
    title="Most Common Parking Infractions"
    yAxisTitle="Total Tickets"
    xAxisTitle="Infraction Type"
    swapXY=true
    colorPalette={['#e8353a']}
/>

---

<div class="section-label">Fine Amount Distribution</div>

<BarChart
    data={fine_dist}
    x=set_fine_amount
    y=ticket_count
    title="How Are Fines Distributed?"
    yAxisTitle="Tickets Issued"
    xAxisTitle="Fine Amount (CAD)"
    colorPalette={['#f4b548']}
/>

---

<div class="section-label">All Violations — Searchable</div>

<DataTable
    data={violations_data}
    search=true
    rows=20
>
    <Column id=infraction_description title="Infraction" />
    <Column id=standard_fine_amount title="Fine (CAD)" fmt='$#,##0' />
    <Column id=total_tickets title="Total Tickets" fmt='#,##0' contentType=colorscale colorScale={['#1a0608', '#e8353a']} />
    <Column id=first_seen_date title="First Seen" />
    <Column id=last_seen_date title="Last Seen" />
</DataTable>
