---
title: Toronto Parking Analytics
---

<style>
  .hero-header {
    background: linear-gradient(135deg, #0d0d1a 0%, #12091a 50%, #0a0f1a 100%);
    border-bottom: 1px solid #1e1e30;
    padding: 2.5rem 2rem 2rem;
    margin-bottom: 0;
  }
  .city-tag {
    display: inline-block;
    background: #e8353a;
    color: white;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    padding: 0.2rem 0.6rem;
    border-radius: 2px;
    margin-bottom: 0.75rem;
  }
  .hero-title {
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: #e8e8f0;
    margin: 0 0 0.3rem;
    line-height: 1.1;
  }
  .hero-subtitle {
    color: #6b6b88;
    font-size: 0.875rem;
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

<div class="hero-header">
  <div class="city-tag">Toronto Open Data</div>
  <h1 class="hero-title">Parking Enforcement<br/>Analytics</h1>
  <p class="hero-subtitle">2008 – 2024 &nbsp;·&nbsp; 34.7M tickets &nbsp;·&nbsp; City of Toronto</p>
</div>

```sql kpi
select
    total_tickets,
    total_revenue_cad,
    avg_fine_cad,
    unique_violation_types
from toronto_parking.kpi_summary
```

```sql years_list
select distinct year from toronto_parking.annual_trend order by year desc
```

<Dropdown data={years_list} name=selected_year value=year title="Filter by Year">
    <DropdownOption value=0 valueLabel="All Years (2008–2024)"/>
</Dropdown>

---

<div class="section-label">At a Glance</div>

<BigValue
    data={kpi}
    value=total_tickets
    title="Total Tickets Issued"
    fmt='#,##0'
/>

<BigValue
    data={kpi}
    value=total_revenue_cad
    title="Total Fines Collected"
    fmt='$#,##0'
/>

<BigValue
    data={kpi}
    value=avg_fine_cad
    title="Average Fine (CAD)"
    fmt='$#,##0.00'
/>

<BigValue
    data={kpi}
    value=unique_violation_types
    title="Distinct Violation Types"
    fmt='#,##0'
/>

---

```sql annual_filtered
select
    year,
    tickets,
    revenue_cad
from toronto_parking.annual_trend
where (year = ${inputs.selected_year.value} or ${inputs.selected_year.value} = 0)
order by year
```

<div class="section-label">Tickets Issued by Year</div>

<LineChart
    data={annual_filtered}
    x=year
    y=tickets
    title="Annual Ticket Volume"
    yAxisTitle="Tickets Issued"
    xAxisTitle="Year"
    lineColor="#e8353a"
    markers=true
/>

---

```sql time_split
select bucket, tickets from toronto_parking.time_of_day_split
```

```sql monthly_filtered
select
    year_month,
    ticket_count,
    total_fines_cad,
    avg_fine_cad,
    morning_ticket_count,
    afternoon_ticket_count,
    evening_ticket_count,
    night_ticket_count,
    weekend_ticket_count
from toronto_parking.monthly_trend
where (year = ${inputs.selected_year.value} or ${inputs.selected_year.value} = 0)
order by year_month
```

<div class="section-label">Revenue by Year</div>

<BarChart
    data={annual_filtered}
    x=year
    y=revenue_cad
    title="Annual Fines Collected (CAD)"
    yAxisTitle="Revenue (CAD)"
    xAxisTitle="Year"
    colorPalette={['#3b8fe8']}
/>

---

<div class="section-label">Enforcement by Time of Day</div>

<BarChart
    data={time_split}
    x=bucket
    y=tickets
    title="Tickets by Time of Day (All Years)"
    yAxisTitle="Tickets"
    colorPalette={['#e8353a', '#3b8fe8', '#f4b548', '#4ade80']}
    swapXY=true
/>

---

<div class="section-label">Monthly Trend</div>

<LineChart
    data={monthly_filtered}
    x=year_month
    y=ticket_count
    title="Monthly Ticket Volume"
    yAxisTitle="Tickets"
    lineColor="#e8353a"
/>
