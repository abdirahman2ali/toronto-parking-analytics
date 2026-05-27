---
title: Time Patterns — Toronto Parking Analytics
---

<style>
  .page-header {
    padding: 2rem 0 1.5rem;
    border-bottom: 1px solid #1e1e30;
    margin-bottom: 1.5rem;
  }
  .page-tag {
    display: inline-block;
    background: #f4b548;
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
  <div class="page-tag">Time Patterns</div>
  <h1 class="page-title">When Does Toronto Get Ticketed?</h1>
  <p class="page-desc">Enforcement intensity by hour, day of week, and month — 2008 to 2024</p>
</div>

```sql heatmap_data
select
    day_of_week_num,
    day_of_week_name,
    infraction_hour,
    tickets
from toronto_parking.hour_day_heatmap
order by day_of_week_num, infraction_hour
```

```sql dow_data
select
    day_of_week_num,
    day_of_week_name,
    tickets,
    avg_fine
from toronto_parking.day_of_week
order by day_of_week_num
```

```sql seasonality_data
select
    month,
    avg_monthly_tickets,
    total_tickets
from toronto_parking.monthly_seasonality
order by month
```

<div class="section-label">Enforcement Intensity — Hour × Day of Week</div>

<p style="color: #6b6b88; font-size: 0.8rem; margin: 0 0 1rem;">Each cell shows the total number of tickets issued at that hour on that day of the week, across all 17 years. Darker red = higher enforcement.</p>

<Heatmap
    data={heatmap_data}
    x=infraction_hour
    y=day_of_week_name
    value=tickets
    title="Ticket Intensity by Hour and Day"
    xAxisTitle="Hour of Day (0 = Midnight)"
    yAxisTitle="Day of Week"
    colorScale={['#0d0507', '#e8353a']}
/>

---

<div class="section-label">Tickets by Day of Week</div>

<BarChart
    data={dow_data}
    x=day_of_week_name
    y=tickets
    title="Total Tickets by Day of Week"
    yAxisTitle="Tickets Issued"
    xAxisTitle="Day"
    colorPalette={['#e8353a']}
/>

---

<div class="section-label">Average Fine by Day of Week</div>

<BarChart
    data={dow_data}
    x=day_of_week_name
    y=avg_fine
    title="Average Fine by Day of Week (CAD)"
    yAxisTitle="Average Fine (CAD)"
    xAxisTitle="Day"
    colorPalette={['#3b8fe8']}
/>

---

<div class="section-label">Seasonal Patterns — Average Monthly Tickets</div>

<p style="color: #6b6b88; font-size: 0.8rem; margin: 0 0 1rem;">Average number of tickets issued per calendar month, across all years in the dataset.</p>

<BarChart
    data={seasonality_data}
    x=month
    y=avg_monthly_tickets
    title="Average Tickets per Calendar Month"
    yAxisTitle="Avg Monthly Tickets"
    xAxisTitle="Month"
    colorPalette={['#f4b548']}
/>
