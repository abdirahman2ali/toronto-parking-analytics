#!/usr/bin/env python3
"""
Generates dashboard/index.html from pre-aggregated CSVs in sources/toronto_parking/.
Run from the dashboard/ directory: python3 build_dashboard.py
"""
import csv
import json
from pathlib import Path

SOURCES = Path(__file__).parent / "sources" / "toronto_parking"
OUTPUT = Path(__file__).parent / "index.html"


def _read(name: str) -> list[dict]:
    with open(SOURCES / f"{name}.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_data() -> dict:
    kpi = _read("kpi_summary")[0]
    return {
        "kpi": {
            "total_tickets": int(kpi["total_tickets"]),
            "total_revenue": float(kpi["total_revenue_cad"]),
            "avg_fine": float(kpi["avg_fine_cad"]),
            "violation_types": int(kpi["unique_violation_types"]),
        },
        "annual": [
            {"year": int(r["year"]), "tickets": int(r["tickets"])}
            for r in _read("annual_trend")
        ],
        "monthly_trend": [
            {
                "year": int(r["year"]),
                "month": int(r["month"]),
                "tickets": int(r["ticket_count"]),
                "revenue": float(r["total_fines_cad"]),
                "morning": int(r["morning_ticket_count"]),
                "afternoon": int(r["afternoon_ticket_count"]),
                "evening": int(r["evening_ticket_count"]),
                "night": int(r["night_ticket_count"]),
            }
            for r in _read("monthly_trend")
        ],
        "violations": [
            {
                "desc": r["infraction_description"],
                "fine": float(r["standard_fine_amount"]),
                "tickets": int(r["total_tickets"]),
                "first": r["first_seen_date"][:4],
                "last": r["last_seen_date"][:4],
            }
            for r in _read("violations")
        ],
        "fine_dist": [
            {"fine": float(r["set_fine_amount"]), "tickets": int(r["ticket_count"])}
            for r in _read("fine_distribution")
        ],
        "dow": [
            {
                "day": r["day_of_week_name"][:3],
                "tickets": int(r["tickets"]),
                "avg_fine": float(r["avg_fine"]),
            }
            for r in _read("day_of_week")
        ],
        "heatmap": [
            {
                "day": int(r["day_of_week_num"]),
                "hour": int(r["infraction_hour"]),
                "tickets": int(r["tickets"]),
            }
            for r in _read("hour_day_heatmap")
        ],
        "seasonality": [
            {"month": int(r["month"]), "avg": float(r["avg_monthly_tickets"])}
            for r in _read("monthly_seasonality")
        ],
        "time_of_day": [
            {"bucket": r["bucket"], "tickets": int(r["tickets"])}
            for r in _read("time_of_day_split")
        ],
    }


TEMPLATE = """<!DOCTYPE html>
<html class="light" lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>Toronto Parking Analytics</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" rel="stylesheet"/>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script id="tailwind-config">
tailwind.config = {
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "primary":                  "#00294d",
        "on-primary":               "#ffffff",
        "primary-container":        "#003f72",
        "on-primary-container":     "#80abe5",
        "primary-fixed":            "#d3e4ff",
        "primary-fixed-dim":        "#a2c9ff",
        "on-primary-fixed":         "#001c38",
        "inverse-primary":          "#a2c9ff",
        "secondary":                "#476176",
        "on-secondary":             "#ffffff",
        "secondary-container":      "#c8e3fb",
        "on-secondary-container":   "#4c667a",
        "on-secondary-fixed":       "#001e2f",
        "surface":                  "#f9f9ff",
        "background":               "#f9f9ff",
        "surface-container-lowest": "#ffffff",
        "surface-container-low":    "#f0f3ff",
        "surface-container":        "#e7eeff",
        "surface-container-high":   "#dee8ff",
        "surface-container-highest":"#d8e3fb",
        "surface-variant":          "#d8e3fb",
        "surface-dim":              "#cfdaf2",
        "surface-tint":             "#326095",
        "on-surface":               "#111c2d",
        "on-surface-variant":       "#42474f",
        "outline":                  "#737780",
        "outline-variant":          "#c2c6d1",
        "error":                    "#ba1a1a",
        "error-container":          "#ffdad6",
        "on-error":                 "#ffffff",
        "on-error-container":       "#93000a",
        "tertiary-container":       "#ffdbc8",
        "on-tertiary-container":    "#3a1800",
        "inverse-surface":          "#263143",
        "inverse-on-surface":       "#ecf1ff",
      },
      borderRadius: {
        "DEFAULT": "0.125rem",
        "lg":   "0.25rem",
        "xl":   "0.5rem",
        "2xl":  "0.75rem",
        "full": "9999px",
      },
      spacing: {
        "container-margin-mobile":  "16px",
        "container-margin-desktop": "32px",
        "stack-sm": "4px",
        "stack-md": "12px",
        "stack-lg": "24px",
        "base":     "8px",
        "gutter":   "16px",
      },
      fontFamily: {
        "body-lg":   ["Inter"],
        "body-sm":   ["Inter"],
        "headline-lg": ["Inter"],
        "headline-md": ["Inter"],
        "label-caps":  ["Inter"],
        "data-display":["Inter"],
      },
      fontSize: {
        "body-lg":           ["16px", {"lineHeight":"24px","fontWeight":"400"}],
        "headline-lg":       ["32px", {"lineHeight":"40px","letterSpacing":"-0.02em","fontWeight":"700"}],
        "headline-lg-mobile":["24px", {"lineHeight":"32px","letterSpacing":"-0.01em","fontWeight":"700"}],
        "headline-md":       ["20px", {"lineHeight":"28px","fontWeight":"600"}],
        "label-caps":        ["12px", {"lineHeight":"16px","letterSpacing":"0.05em","fontWeight":"700"}],
        "body-sm":           ["14px", {"lineHeight":"20px","fontWeight":"400"}],
        "data-display":      ["28px", {"lineHeight":"32px","letterSpacing":"-0.02em","fontWeight":"700"}],
      },
    },
  },
}
</script>
<style>
  .material-symbols-outlined {
    font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
    user-select: none;
  }
  .pulse-dot { animation: pulse-anim 2s infinite; }
  @keyframes pulse-anim {
    0%   { transform: scale(0.95); opacity: 0.8; }
    50%  { transform: scale(1.1);  opacity: 1;   }
    100% { transform: scale(0.95); opacity: 0.8; }
  }
  .bento-grid {
    display: grid;
    grid-template-columns: repeat(12, 1fr);
    gap: 16px;
  }
  .glass-card {
    background: rgba(255,255,255,0.85);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(194,198,209,0.5);
  }
  /* Heatmap */
  .hm-grid {
    display: grid;
    grid-template-columns: 44px repeat(24, minmax(26px, 1fr));
    gap: 3px;
    min-width: 720px;
  }
  .hm-cell {
    height: 28px;
    border-radius: 3px;
    background: #326095;
    cursor: default;
    transition: transform 0.1s;
  }
  .hm-cell:hover { transform: scale(1.1); position: relative; z-index: 1; }
  /* Scrollbars */
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: #c2c6d1; border-radius: 10px; }
  /* Table row selected */
  tr.row-selected td { background-color: rgba(211,228,255,0.5) !important; }
  /* Animate KPI numbers */
  .kpi-animate { transition: all 0.3s ease; }
</style>
</head>
<body class="bg-background font-body-lg text-on-background selection:bg-primary-fixed overflow-x-hidden">

<!-- ── TOP APP BAR ─────────────────────────────────────────────── -->
<header class="flex justify-between items-center px-container-margin-mobile h-14 w-full z-50 sticky top-0 bg-surface border-b border-outline-variant shadow-sm">
  <div class="flex items-center gap-stack-md">
    <h1 class="text-headline-md font-headline-md text-primary tracking-tight">Toronto Parking</h1>
  </div>
  <div class="flex items-center gap-stack-md">
    <span id="year-badge" class="hidden text-label-caps text-primary bg-primary-fixed px-3 py-1 rounded-full"></span>
    <select id="year-filter" class="text-body-sm text-on-surface bg-surface-container-low border border-outline-variant rounded-xl px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary/30 cursor-pointer">
      <option value="">All Years</option>
    </select>
  </div>
</header>

<!-- ── MAIN CONTENT ────────────────────────────────────────────── -->
<main class="max-w-7xl mx-auto px-container-margin-mobile md:px-container-margin-desktop py-stack-lg pb-32 space-y-stack-lg">

  <!-- ═══════════════════════════════ OVERVIEW ═══════════════════ -->
  <section id="section-overview">

    <!-- Hero Bento -->
    <div class="bento-grid mb-stack-lg">

      <!-- Main hero card -->
      <div class="col-span-12 lg:col-span-7 bg-surface-container-lowest rounded-2xl p-stack-lg shadow-[0_4px_12px_rgba(0,0,0,0.05)] border border-outline-variant flex flex-col md:flex-row gap-stack-lg items-center relative overflow-hidden">
        <div class="flex-1 z-10">
          <div class="flex items-center gap-base mb-stack-sm">
            <div class="w-2 h-2 rounded-full bg-surface-tint pulse-dot"></div>
            <span class="font-label-caps text-label-caps text-on-surface-variant uppercase">Historical Dataset</span>
          </div>
          <h2 class="font-headline-lg-mobile md:font-headline-lg text-headline-lg-mobile md:text-headline-lg text-primary mb-base leading-tight">Toronto Central Enforcement</h2>
          <p class="font-body-sm text-body-sm text-on-surface-variant max-w-md">16 years of parking enforcement data from the City of Toronto Open Data portal. Covers all ticketed violations across the city from 2008 to 2024.</p>
        </div>
        <!-- Donut showing peak-hours share -->
        <div class="w-full md:w-48 h-48 relative flex items-center justify-center flex-shrink-0">
          <svg class="w-40 h-40 -rotate-90" viewBox="0 0 192 192">
            <circle cx="96" cy="96" r="80" fill="transparent" stroke="#dee8ff" stroke-width="18"/>
            <circle cx="96" cy="96" r="80" fill="transparent" stroke="#326095"
              stroke-dasharray="502.65" stroke-dashoffset="190" stroke-width="18"
              style="transition: stroke-dashoffset 1.5s cubic-bezier(0.4,0,0.2,1)" id="donut-arc"/>
          </svg>
          <div class="absolute flex flex-col items-center">
            <span class="material-symbols-outlined text-4xl text-primary">local_parking</span>
            <span class="text-headline-md font-headline-md text-primary">62%</span>
            <span class="text-[10px] font-label-caps text-on-surface-variant uppercase">Peak Hours</span>
          </div>
        </div>
      </div>

      <!-- 2×2 KPI cards -->
      <div class="col-span-12 lg:col-span-5 grid grid-cols-2 gap-gutter">
        <div class="bg-primary-container rounded-2xl p-stack-md shadow-[0_4px_12px_rgba(0,0,0,0.05)] border border-outline-variant flex flex-col justify-between group hover:scale-[1.02] transition-transform cursor-default">
          <span class="font-label-caps text-label-caps text-on-primary-container uppercase">Tickets Issued</span>
          <div class="flex items-end justify-between mt-base">
            <span class="text-2xl font-bold text-on-primary-container kpi-animate leading-none" id="kpi-tickets">—</span>
            <span class="material-symbols-outlined text-2xl text-on-primary-container opacity-60">confirmation_number</span>
          </div>
        </div>
        <div class="bg-surface-container-low rounded-2xl p-stack-md shadow-[0_4px_12px_rgba(0,0,0,0.05)] border border-outline-variant flex flex-col justify-between group hover:scale-[1.02] transition-transform cursor-default">
          <span class="font-label-caps text-label-caps text-on-surface-variant uppercase">Revenue</span>
          <div class="flex items-end justify-between mt-base">
            <span class="text-2xl font-bold text-on-surface kpi-animate leading-none" id="kpi-revenue">—</span>
            <span class="material-symbols-outlined text-2xl text-on-surface-variant opacity-60">payments</span>
          </div>
        </div>
        <div class="bg-secondary-container rounded-2xl p-stack-md shadow-[0_4px_12px_rgba(0,0,0,0.05)] border border-outline-variant flex flex-col justify-between group hover:scale-[1.02] transition-transform cursor-default">
          <span class="font-label-caps text-label-caps text-on-secondary-container uppercase">Avg Fine</span>
          <div class="flex items-end justify-between mt-base">
            <span class="text-2xl font-bold text-on-secondary-fixed kpi-animate leading-none" id="kpi-fine">—</span>
            <span class="material-symbols-outlined text-2xl text-secondary opacity-60">price_check</span>
          </div>
        </div>
        <div class="bg-error-container rounded-2xl p-stack-md shadow-[0_4px_12px_rgba(0,0,0,0.05)] border border-outline-variant flex flex-col justify-between group hover:scale-[1.02] transition-transform cursor-default">
          <span class="font-label-caps text-label-caps text-on-error-container uppercase">Violation Types</span>
          <div class="flex items-end justify-between mt-base">
            <span class="text-2xl font-bold text-on-error-container leading-none" id="kpi-types">—</span>
            <span class="material-symbols-outlined text-2xl text-error opacity-60">gavel</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Annual trend chart -->
    <div class="bg-surface-container-lowest rounded-2xl p-stack-lg shadow-[0_4px_12px_rgba(0,0,0,0.05)] border border-outline-variant">
      <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-stack-sm mb-stack-md">
        <div>
          <h3 class="text-headline-md font-headline-md text-on-surface">Annual Ticket Volume</h3>
          <p class="text-body-sm text-on-surface-variant mt-stack-sm max-w-xl">Tickets issued per year across Toronto. 2020&ndash;2021 reflects reduced enforcement during COVID-19.</p>
        </div>
        <span id="annual-badge" class="font-label-caps text-label-caps bg-surface-container-low border border-outline-variant text-on-surface-variant px-3 py-1 rounded-full self-start whitespace-nowrap flex-shrink-0">All Years</span>
      </div>
      <div class="relative h-64">
        <canvas id="chart-annual"></canvas>
      </div>
      <p class="text-[11px] text-on-surface-variant mt-stack-sm">* 2023&ndash;2024 bars are dimmed &mdash; incomplete records in the source dataset.</p>
    </div>
  </section>

  <!-- ═══════════════════════════════ WHEN ══════════════════════ -->
  <section id="section-when" class="hidden space-y-stack-lg">

    <div class="bento-grid">
      <!-- Day of week -->
      <div class="col-span-12 lg:col-span-7 bg-surface-container-lowest rounded-2xl p-stack-lg shadow-[0_4px_12px_rgba(0,0,0,0.05)] border border-outline-variant">
        <div class="flex justify-between items-start mb-stack-sm">
          <div>
            <h3 class="text-headline-md font-headline-md text-on-surface">Day of Week</h3>
            <p class="text-body-sm text-on-surface-variant mt-stack-sm">Mid-week (Tue&ndash;Thu) is peak enforcement. Weekends are ~15% quieter.</p>
          </div>
          <span class="font-label-caps text-label-caps bg-surface-container-low border border-outline-variant text-on-surface-variant px-3 py-1 rounded-full text-[10px] flex-shrink-0">All years</span>
        </div>
        <div class="relative h-52">
          <canvas id="chart-dow"></canvas>
        </div>
      </div>
      <!-- Time of day doughnut -->
      <div class="col-span-12 lg:col-span-5 bg-surface-container-lowest rounded-2xl p-stack-lg shadow-[0_4px_12px_rgba(0,0,0,0.05)] border border-outline-variant">
        <div class="flex justify-between items-start mb-stack-sm">
          <div>
            <h3 class="text-headline-md font-headline-md text-on-surface">Time of Day</h3>
            <p class="text-body-sm text-on-surface-variant mt-stack-sm">Afternoon accounts for 35% of all daily ticket activity.</p>
          </div>
          <span id="tod-badge" class="font-label-caps text-label-caps bg-surface-container-low border border-outline-variant text-on-surface-variant px-3 py-1 rounded-full text-[10px] flex-shrink-0">All years</span>
        </div>
        <div class="relative h-52">
          <canvas id="chart-tod"></canvas>
        </div>
      </div>
    </div>

    <!-- Monthly chart -->
    <div class="bg-surface-container-lowest rounded-2xl p-stack-lg shadow-[0_4px_12px_rgba(0,0,0,0.05)] border border-outline-variant">
      <div class="flex justify-between items-start mb-stack-sm">
        <div>
          <h3 class="text-headline-md font-headline-md text-on-surface" id="monthly-title">Monthly Seasonality</h3>
          <p class="text-body-sm text-on-surface-variant mt-stack-sm" id="monthly-caption">Average monthly ticket volume across all years. October peaks; February dips.</p>
        </div>
        <span id="monthly-badge" class="font-label-caps text-label-caps bg-surface-container-low border border-outline-variant text-on-surface-variant px-3 py-1 rounded-full text-[10px] flex-shrink-0">All years</span>
      </div>
      <div class="relative h-52">
        <canvas id="chart-monthly"></canvas>
      </div>
    </div>

    <!-- Enforcement heatmap -->
    <div class="bg-surface-container-lowest rounded-2xl p-stack-lg shadow-[0_4px_12px_rgba(0,0,0,0.05)] border border-outline-variant">
      <div class="flex justify-between items-start mb-stack-sm">
        <div>
          <h3 class="text-headline-md font-headline-md text-on-surface">Enforcement Heatmap</h3>
          <p class="text-body-sm text-on-surface-variant mt-stack-sm">Weekday business hours (Mon&ndash;Fri, 8&nbsp;AM&ndash;6&nbsp;PM) form the peak enforcement window. Hover any cell for exact count. All-time data.</p>
        </div>
        <span class="font-label-caps text-label-caps bg-surface-container-low border border-outline-variant text-on-surface-variant px-3 py-1 rounded-full text-[10px] flex-shrink-0">All years</span>
      </div>
      <div class="overflow-x-auto mt-stack-md">
        <div class="hm-grid" id="heatmap-grid"></div>
      </div>
    </div>
  </section>

  <!-- ═══════════════════════════════ VIOLATIONS ════════════════ -->
  <section id="section-violations" class="hidden space-y-stack-lg">

    <div class="bento-grid">
      <!-- Top 15 violations chart -->
      <div class="col-span-12 lg:col-span-8 bg-surface-container-lowest rounded-2xl p-stack-lg shadow-[0_4px_12px_rgba(0,0,0,0.05)] border border-outline-variant">
        <div class="flex justify-between items-start mb-stack-sm">
          <div>
            <h3 class="text-headline-md font-headline-md text-on-surface">Top 15 Infractions</h3>
            <p class="text-body-sm text-on-surface-variant mt-stack-sm">Click any bar to select. Signed highway prohibitions dominate. All-time data.</p>
          </div>
          <span class="font-label-caps text-label-caps bg-surface-container-low border border-outline-variant text-on-surface-variant px-3 py-1 rounded-full text-[10px] flex-shrink-0">All years</span>
        </div>
        <div class="relative" style="height:400px;">
          <canvas id="chart-violations"></canvas>
        </div>
      </div>
      <!-- Fine distribution -->
      <div class="col-span-12 lg:col-span-4 bg-surface-container-lowest rounded-2xl p-stack-lg shadow-[0_4px_12px_rgba(0,0,0,0.05)] border border-outline-variant">
        <h3 class="text-headline-md font-headline-md text-on-surface mb-stack-sm">Fine Distribution</h3>
        <p class="text-body-sm text-on-surface-variant mb-stack-md">$30 fines dominate. Accessible parking violations carry $450.</p>
        <div class="relative" style="height:400px;">
          <canvas id="chart-fine-dist"></canvas>
        </div>
      </div>
    </div>

    <!-- Violations table card -->
    <div class="bg-surface-container-lowest rounded-2xl p-stack-lg shadow-[0_4px_12px_rgba(0,0,0,0.05)] border border-outline-variant">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-stack-md mb-stack-sm">
        <div>
          <h3 class="text-headline-md font-headline-md text-on-surface">All Infractions</h3>
          <p class="text-body-sm text-on-surface-variant mt-stack-sm">100 infraction types &middot; Click a row or chart bar to select &middot; Click column headers to sort</p>
        </div>
        <div class="relative flex-shrink-0">
          <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[18px]">search</span>
          <input id="v-search" type="text" placeholder="Search infractions&hellip;"
            class="pl-9 pr-4 py-2 text-body-sm bg-surface-container-low border border-outline-variant rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/20 w-64"/>
        </div>
      </div>
      <!-- Selection banner -->
      <div id="v-banner" class="hidden mb-stack-md bg-primary-fixed/60 border border-primary/20 rounded-xl p-stack-md flex items-center gap-stack-md flex-wrap">
        <span class="font-label-caps text-label-caps text-primary uppercase">Selected</span>
        <span class="font-body-sm font-semibold text-on-surface flex-1 min-w-[180px]" id="vb-title"></span>
        <span class="text-body-sm text-on-surface-variant">Fine: <strong class="text-on-surface" id="vb-fine"></strong></span>
        <span class="text-body-sm text-on-surface-variant">Tickets: <strong class="text-on-surface" id="vb-tickets"></strong></span>
        <span class="text-body-sm text-on-surface-variant">Active: <strong class="text-on-surface" id="vb-dates"></strong></span>
        <button onclick="clearVSel()" class="ml-auto p-1 hover:bg-primary/10 rounded-full transition-colors">
          <span class="material-symbols-outlined text-on-surface-variant text-[18px]">close</span>
        </button>
      </div>
      <div class="overflow-auto max-h-96 rounded-xl border border-outline-variant">
        <table class="w-full text-body-sm border-collapse">
          <thead class="sticky top-0 bg-surface-container-low z-10">
            <tr>
              <th data-col="desc" onclick="sortV('desc')" class="v-th text-left py-2.5 px-3 font-label-caps text-label-caps text-on-surface-variant border-b border-outline-variant cursor-pointer hover:text-primary select-none">Infraction</th>
              <th data-col="fine" onclick="sortV('fine')" class="v-th text-right py-2.5 px-3 font-label-caps text-label-caps text-on-surface-variant border-b border-outline-variant cursor-pointer hover:text-primary select-none whitespace-nowrap">Fine</th>
              <th data-col="tickets" onclick="sortV('tickets')" class="v-th text-right py-2.5 px-3 font-label-caps text-label-caps text-on-surface-variant border-b border-outline-variant cursor-pointer hover:text-primary select-none whitespace-nowrap sort-active sort-desc">Tickets ▼</th>
              <th data-col="pct" onclick="sortV('pct')" class="v-th text-right py-2.5 px-3 font-label-caps text-label-caps text-on-surface-variant border-b border-outline-variant cursor-pointer hover:text-primary select-none whitespace-nowrap">% of Total</th>
            </tr>
          </thead>
          <tbody id="v-tbody" class="divide-y divide-outline-variant/40"></tbody>
        </table>
      </div>
    </div>
  </section>


</main>

<!-- ── BOTTOM NAVIGATION ──────────────────────────────────────── -->
<nav class="fixed bottom-0 left-0 w-full z-50 flex justify-around items-center px-4 py-2 bg-surface border-t border-outline-variant shadow-[0_-4px_12px_rgba(0,0,0,0.05)] rounded-t-2xl">
  <button id="nav-overview" onclick="switchSection('overview')" class="nav-btn flex flex-col items-center justify-center bg-secondary-container text-on-secondary-container rounded-full px-5 py-1 transition-all duration-200 scale-90 active:scale-100">
    <span class="material-symbols-outlined" style="font-variation-settings:'FILL' 1,'wght' 400,'GRAD' 0,'opsz' 24">dashboard</span>
    <span class="font-label-caps text-label-caps">Overview</span>
  </button>
  <button id="nav-when" onclick="switchSection('when')" class="nav-btn flex flex-col items-center justify-center text-on-surface-variant hover:text-primary transition-all duration-200 scale-90 active:scale-100 px-5 py-1">
    <span class="material-symbols-outlined">schedule</span>
    <span class="font-label-caps text-label-caps">When</span>
  </button>
  <button id="nav-violations" onclick="switchSection('violations')" class="nav-btn flex flex-col items-center justify-center text-on-surface-variant hover:text-primary transition-all duration-200 scale-90 active:scale-100 px-5 py-1">
    <span class="material-symbols-outlined">receipt_long</span>
    <span class="font-label-caps text-label-caps">Violations</span>
  </button>
</nav>

<!-- ── SCRIPTS ────────────────────────────────────────────────── -->
<script>
const DATA = %%DATA%%;

// ── Palette (M3 tokens) ──────────────────────────────────────────
const C_PRIMARY   = '#326095'; // surface-tint — more visible on charts than #00294d
const C_SECONDARY = '#476176';
const C_AMBER     = '#c77000'; // readable amber
const C_SLATE     = '#42474f'; // on-surface-variant
const C_GRID      = '#e7eeff'; // surface-container
const MONTHS      = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

// ── State ────────────────────────────────────────────────────────
let activeSection = 'overview';
let activeYear    = null;
const CH          = {};           // chart instances

// Table state
let vRows = [], vSortCol = 'tickets', vSortDir = 'desc';
let vTopReversed = [];

// ── Chart.js defaults ────────────────────────────────────────────
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.font.size   = 11;
Chart.defaults.color       = '#42474f';

const scaleBase = {
  grid:   { color: C_GRID },
  border: { display: false },
  ticks:  { font: { family: "'Inter', sans-serif", size: 11 }, color: '#42474f' },
};
const scaleNoGrid = { ...scaleBase, grid: { display: false } };
const ttBase = {
  backgroundColor: '#263143',
  titleFont:  { family: "'Inter', sans-serif", size: 12, weight: '600' },
  bodyFont:   { family: "'Inter', sans-serif", size: 11 },
  padding: 10, cornerRadius: 6,
};

// ── Formatters ───────────────────────────────────────────────────
function fmtNum(n) {
  if (n >= 1e9) return '$' + (n / 1e9).toFixed(2) + 'B';
  if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M';
  if (n >= 1e3) return (n / 1e3).toFixed(0) + 'K';
  return n.toLocaleString();
}

// ── Section navigation ───────────────────────────────────────────
function switchSection(name) {
  document.querySelectorAll('section[id^="section-"]').forEach(s => s.classList.add('hidden'));
  document.getElementById('section-' + name).classList.remove('hidden');

  document.querySelectorAll('.nav-btn').forEach(b => {
    b.className = b.className
      .replace('bg-secondary-container text-on-secondary-container rounded-full', '')
      .trim();
    b.classList.add('text-on-surface-variant', 'hover:text-primary');
  });
  const active = document.getElementById('nav-' + name);
  active.classList.remove('text-on-surface-variant', 'hover:text-primary');
  active.classList.add('bg-secondary-container', 'text-on-secondary-container', 'rounded-full');

  activeSection = name;
  // Resize charts in newly visible section so they fill their containers
  setTimeout(() => Object.values(CH).forEach(c => c.resize && c.resize()), 50);
}

// ── Year filter ──────────────────────────────────────────────────
function setupYearFilter() {
  const sel = document.getElementById('year-filter');
  const years = [...new Set(DATA.monthly_trend.map(r => r.year))].sort();
  years.forEach(y => {
    const o = document.createElement('option');
    o.value = y;
    o.textContent = y >= 2023 ? y + ' (partial)' : y;
    sel.appendChild(o);
  });
  sel.addEventListener('change', () => {
    activeYear = sel.value ? parseInt(sel.value) : null;
    onYearChange();
  });
}

function computeStats() {
  if (!activeYear) {
    return {
      tickets: DATA.kpi.total_tickets,
      revenue: DATA.kpi.total_revenue,
      avg_fine: DATA.kpi.avg_fine,
      tod: DATA.time_of_day,
      monthly: DATA.seasonality.map(d => d.avg),
      monthlyLabels: MONTHS,
    };
  }
  const rows = DATA.monthly_trend.filter(r => r.year === activeYear).sort((a,b) => a.month - b.month);
  const tickets = rows.reduce((s,r) => s + r.tickets, 0);
  const revenue = rows.reduce((s,r) => s + r.revenue, 0);
  const tod = [
    { bucket: 'Morning',   tickets: rows.reduce((s,r) => s + r.morning,   0) },
    { bucket: 'Afternoon', tickets: rows.reduce((s,r) => s + r.afternoon, 0) },
    { bucket: 'Evening',   tickets: rows.reduce((s,r) => s + r.evening,   0) },
    { bucket: 'Night',     tickets: rows.reduce((s,r) => s + r.night,     0) },
  ];
  return {
    tickets, revenue,
    avg_fine: tickets > 0 ? revenue / tickets : 0,
    tod,
    monthly: rows.map(r => r.tickets),
    monthlyLabels: rows.map(r => MONTHS[r.month - 1]),
  };
}

function onYearChange() {
  const stats = computeStats();
  updateKPIs(stats);
  updateAnnualColors();
  if (CH.tod)     { CH.tod.data.datasets[0].data = stats.tod.map(d => d.tickets); CH.tod.update('none'); }
  if (CH.monthly) {
    CH.monthly.data.labels = stats.monthlyLabels;
    CH.monthly.data.datasets[0].data = stats.monthly;
    CH.monthly.update('none');
    document.getElementById('monthly-title').textContent =
      activeYear ? 'Monthly Tickets — ' + activeYear : 'Monthly Seasonality';
    document.getElementById('monthly-caption').textContent = activeYear
      ? 'Month-by-month ticket volume for ' + activeYear + '.'
      : 'Average monthly ticket volume across all years. October peaks; February dips.';
  }
  updateBadges();
}

function updateKPIs(stats) {
  document.getElementById('kpi-tickets').textContent = fmtNum(stats.tickets);
  document.getElementById('kpi-revenue').textContent = fmtNum(stats.revenue);
  document.getElementById('kpi-fine').textContent    = '$' + stats.avg_fine.toFixed(2);
}

function updateAnnualColors() {
  if (!CH.annual) return;
  CH.annual.data.datasets[0].backgroundColor = DATA.annual.map(d => {
    const partial = d.year >= 2023;
    if (activeYear) {
      return d.year === activeYear
        ? '#ba1a1a'
        : partial ? 'rgba(50,96,149,0.15)' : 'rgba(50,96,149,0.22)';
    }
    return partial ? 'rgba(50,96,149,0.35)' : 'rgba(50,96,149,0.80)';
  });
  CH.annual.update('none');
}

function updateBadges() {
  const label = activeYear ? String(activeYear) : 'All years';
  const isY   = !!activeYear;
  ['annual-badge','tod-badge','monthly-badge'].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = label;
    if (isY) {
      el.className = el.className.replace('bg-surface-container-low border border-outline-variant text-on-surface-variant','').trim();
      el.classList.add('bg-primary-fixed','border','border-primary/20','text-primary');
    } else {
      el.className = el.className.replace('bg-primary-fixed border border-primary/20 text-primary','').trim();
      el.classList.add('bg-surface-container-low','border','border-outline-variant','text-on-surface-variant');
    }
  });
  const badge = document.getElementById('year-badge');
  if (isY) {
    badge.textContent = activeYear;
    badge.classList.remove('hidden');
  } else {
    badge.classList.add('hidden');
  }
}

// ── Charts ───────────────────────────────────────────────────────
function initAnnual() {
  CH.annual = new Chart(document.getElementById('chart-annual'), {
    type: 'bar',
    data: {
      labels: DATA.annual.map(d => d.year),
      datasets: [{ data: DATA.annual.map(d => d.tickets), backgroundColor: DATA.annual.map(d => d.year >= 2023 ? 'rgba(50,96,149,0.35)' : 'rgba(50,96,149,0.80)'), borderWidth: 0, borderRadius: 3 }],
    },
    options: {
      animation: false, responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { ...ttBase, callbacks: { label: c => ' ' + c.parsed.y.toLocaleString() + ' tickets' } } },
      scales: {
        x: { ...scaleNoGrid },
        y: { ...scaleBase, ticks: { ...scaleBase.ticks, callback: v => (v/1e6).toFixed(1)+'M' } },
      },
    },
  });
}

function initDow() {
  const WEEKEND = new Set(['Sun','Sat']);
  CH.dow = new Chart(document.getElementById('chart-dow'), {
    type: 'bar',
    data: {
      labels: DATA.dow.map(d => d.day),
      datasets: [{ data: DATA.dow.map(d => d.tickets), backgroundColor: DATA.dow.map(d => WEEKEND.has(d.day) ? 'rgba(50,96,149,0.42)' : 'rgba(50,96,149,0.80)'), borderWidth: 0, borderRadius: 3 }],
    },
    options: {
      animation: false, responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { ...ttBase, callbacks: { label: c => ' ' + c.parsed.y.toLocaleString() + ' tickets' } } },
      scales: {
        x: { ...scaleNoGrid },
        y: { ...scaleBase, ticks: { ...scaleBase.ticks, callback: v => (v/1e6).toFixed(1)+'M' } },
      },
    },
  });
}

function initTod() {
  const total = DATA.time_of_day.reduce((s,d) => s + d.tickets, 0);
  CH.tod = new Chart(document.getElementById('chart-tod'), {
    type: 'doughnut',
    data: {
      labels: DATA.time_of_day.map(d => d.bucket),
      datasets: [{ data: DATA.time_of_day.map(d => d.tickets), backgroundColor: [C_PRIMARY, C_SECONDARY, C_AMBER, C_SLATE], borderWidth: 0, hoverOffset: 8 }],
    },
    options: {
      animation: false, responsive: true, maintainAspectRatio: false, cutout: '60%',
      plugins: {
        legend: { display: true, position: 'bottom', labels: { font: { family: "'Inter'", size: 11 }, color: '#42474f', boxWidth: 11, padding: 12 } },
        tooltip: { ...ttBase, callbacks: { label: c => ' ' + c.parsed.toLocaleString() + ' (' + (c.parsed/total*100).toFixed(1) + '%)' } },
      },
    },
  });
}

function initMonthly() {
  CH.monthly = new Chart(document.getElementById('chart-monthly'), {
    type: 'line',
    data: {
      labels: MONTHS,
      datasets: [{ data: DATA.seasonality.map(d => d.avg), borderColor: C_PRIMARY, backgroundColor: 'rgba(50,96,149,0.08)', borderWidth: 2, pointRadius: 3, pointBackgroundColor: C_PRIMARY, fill: true, tension: 0.3 }],
    },
    options: {
      animation: false, responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { ...ttBase, callbacks: { label: c => ' ' + Math.round(c.parsed.y).toLocaleString() } } },
      scales: {
        x: { ...scaleNoGrid },
        y: { ...scaleBase, ticks: { ...scaleBase.ticks, callback: v => (v/1e3).toFixed(0)+'K' } },
      },
    },
  });
}

function initViolationsChart() {
  const top15 = DATA.violations.slice(0, 15);
  vTopReversed = [...top15].reverse();
  CH.violations = new Chart(document.getElementById('chart-violations'), {
    type: 'bar',
    data: {
      labels: vTopReversed.map(d => d.desc),
      datasets: [{ data: vTopReversed.map(d => d.tickets), backgroundColor: 'rgba(50,96,149,0.75)', borderWidth: 0, borderRadius: 3 }],
    },
    options: {
      animation: false, responsive: true, maintainAspectRatio: false, indexAxis: 'y',
      plugins: {
        legend: { display: false },
        tooltip: { ...ttBase, callbacks: { label: c => ' ' + c.parsed.x.toLocaleString() + ' tickets' } },
      },
      onClick: (evt, elements) => {
        if (!elements.length) return;
        const v = vTopReversed[elements[0].index];
        const idx = vRows.findIndex(r => r.desc === v.desc);
        if (idx !== -1) {
          selectV(idx);
          if (activeSection !== 'violations') switchSection('violations');
          setTimeout(() => document.getElementById('v-tbody').closest('.overflow-auto').scrollTo({ top: 0 }), 50);
        }
      },
      scales: {
        x: { ...scaleBase, ticks: { ...scaleBase.ticks, callback: v => (v/1e6).toFixed(1)+'M' } },
        y: { ...scaleNoGrid, ticks: { ...scaleBase.ticks, font: { family: "'Inter'", size: 10 } }, afterFit: axis => { axis.width = 230; } },
      },
    },
  });
}

function initFineDist() {
  const maxT = Math.max(...DATA.fine_dist.map(d => d.tickets));
  CH.fineDist = new Chart(document.getElementById('chart-fine-dist'), {
    type: 'bar',
    data: {
      labels: DATA.fine_dist.map(d => '$' + d.fine.toFixed(0)),
      datasets: [{ data: DATA.fine_dist.map(d => d.tickets), backgroundColor: DATA.fine_dist.map(d => d.tickets === maxT ? '#ba1a1a' : 'rgba(50,96,149,0.65)'), borderWidth: 0, borderRadius: 3 }],
    },
    options: {
      animation: false, responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { ...ttBase, callbacks: { label: c => ' ' + c.parsed.y.toLocaleString() + ' tickets' } } },
      scales: {
        x: { ...scaleNoGrid },
        y: { ...scaleBase, ticks: { ...scaleBase.ticks, callback: v => (v/1e6).toFixed(1)+'M' } },
      },
    },
  });
}

// ── Heatmap ──────────────────────────────────────────────────────
function initHeatmap() {
  const grid = document.getElementById('heatmap-grid');
  const lookup = {};
  DATA.heatmap.forEach(d => { if (!lookup[d.day]) lookup[d.day] = {}; lookup[d.day][d.hour] = d.tickets; });
  const maxT  = Math.max(...DATA.heatmap.map(d => d.tickets));
  const days  = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  const hLbl  = h => h===0?'12a':h<12?h+'a':h===12?'12p':(h-12)+'p';
  const frag  = document.createDocumentFragment();
  // Header row
  frag.appendChild(Object.assign(document.createElement('div'), {}));
  for (let h = 0; h < 24; h++) {
    frag.appendChild(Object.assign(document.createElement('div'), {
      className: 'text-[10px] text-on-surface-variant text-center pb-1',
      textContent: hLbl(h),
    }));
  }
  // Day rows
  for (let d = 0; d < 7; d++) {
    frag.appendChild(Object.assign(document.createElement('div'), {
      className: 'text-[11px] font-semibold text-on-surface flex items-center',
      textContent: days[d],
    }));
    for (let h = 0; h < 24; h++) {
      const t = (lookup[d] && lookup[d][h]) || 0;
      const op = (0.06 + (t/maxT)*0.88).toFixed(3);
      const cell = document.createElement('div');
      cell.className = 'hm-cell';
      cell.style.opacity = op;
      cell.title = days[d] + ' ' + hLbl(h) + ': ' + t.toLocaleString() + ' tickets';
      frag.appendChild(cell);
    }
  }
  grid.appendChild(frag);
}

// ── Tables ───────────────────────────────────────────────────────
function renderVTable(filter) {
  const q = (filter || document.getElementById('v-search').value).toLowerCase();
  const total = DATA.kpi.total_tickets;
  let rows = DATA.violations;
  if (q) rows = rows.filter(v => v.desc.toLowerCase().includes(q));
  const d = vSortDir === 'asc' ? 1 : -1;
  vRows = [...rows].sort((a,b) => {
    if (vSortCol === 'desc') return d * a.desc.localeCompare(b.desc);
    if (vSortCol === 'fine') return d * (a.fine - b.fine);
    return d * (a.tickets - b.tickets);
  });
  document.getElementById('v-tbody').innerHTML = vRows.map((v,i) =>
    '<tr data-idx="'+i+'" onclick="selectV('+i+')" class="cursor-pointer hover:bg-surface-container-low transition-colors">' +
    '<td class="py-2 px-3 text-on-surface">' + v.desc + '</td>' +
    '<td class="py-2 px-3 text-right text-on-surface-variant tabular-nums">$' + v.fine.toFixed(0) + '</td>' +
    '<td class="py-2 px-3 text-right text-on-surface tabular-nums font-semibold">' + v.tickets.toLocaleString() + '</td>' +
    '<td class="py-2 px-3 text-right text-on-surface-variant tabular-nums">' + (v.tickets/total*100).toFixed(2) + '%</td>' +
    '</tr>'
  ).join('');
}

function sortV(col) {
  if (vSortCol === col) { vSortDir = vSortDir === 'asc' ? 'desc' : 'asc'; } else { vSortCol = col; vSortDir = col==='desc'?'asc':'desc'; }
  document.querySelectorAll('.v-th').forEach(th => {
    th.textContent = th.textContent.replace(/ [▲▼]$/, '');
    if (th.dataset.col === vSortCol) th.textContent += vSortDir === 'asc' ? ' ▲' : ' ▼';
  });
  renderVTable();
}

function selectV(idx) {
  const v = vRows[idx];
  document.getElementById('vb-title').textContent   = v.desc;
  document.getElementById('vb-fine').textContent    = '$' + v.fine.toFixed(0);
  document.getElementById('vb-tickets').textContent = v.tickets.toLocaleString();
  document.getElementById('vb-dates').textContent   = v.first + '–' + v.last;
  document.getElementById('v-banner').classList.remove('hidden');
  document.querySelectorAll('#v-tbody tr').forEach(tr => tr.classList.remove('row-selected'));
  const row = document.querySelector('#v-tbody tr[data-idx="' + idx + '"]');
  row?.classList.add('row-selected');
  row?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function clearVSel() {
  document.getElementById('v-banner').classList.add('hidden');
  document.querySelectorAll('#v-tbody tr').forEach(tr => tr.classList.remove('row-selected'));
}

// ── Initialise ───────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // KPIs
  updateKPIs({ tickets: DATA.kpi.total_tickets, revenue: DATA.kpi.total_revenue, avg_fine: DATA.kpi.avg_fine });
  document.getElementById('kpi-types').textContent = DATA.kpi.violation_types;

  // Animate donut arc
  setTimeout(() => {
    const arc = document.getElementById('donut-arc');
    if (arc) arc.style.strokeDashoffset = '190';
  }, 200);

  setupYearFilter();
  initAnnual();
  initDow();
  initTod();
  initMonthly();
  initViolationsChart();
  initFineDist();
  initHeatmap();
  renderVTable();

  // Search bindings
  document.getElementById('v-search').addEventListener('input', () => renderVTable());
});
</script>

</body>
</html>"""


def main() -> None:
    data = load_data()
    html = TEMPLATE.replace("%%DATA%%", json.dumps(data, separators=(",", ":")))
    OUTPUT.write_text(html, encoding="utf-8")
    size_kb = OUTPUT.stat().st_size // 1024
    print(f"Generated {OUTPUT} ({size_kb} KB)")


if __name__ == "__main__":
    main()
