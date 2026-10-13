# NYC Rat Intelligence — Power BI Desktop build guide

## Release status
Verified backfill run: 38460233982 (2026-08-01 inclusive to 2026-09-01 exclusive).
Stored after run: 3,393 complaints and 25,344 inspections. Do not interpret as annual or total-city rat incidence.

## 1. Download and import
From GitHub, download these files from `data/`:
- `daily_metrics.csv` → **DailyMetrics** (aggregated table)
- `weekly_complaints_by_zip.csv` → **WeeklyComplaintsZIP** (optional for hotspot view)
- `refresh_status.json` → optional separate freshness page

In Power BI Desktop, choose Home > Get data > Text/CSV, import CSV, then Transform Data.
Cast:
- DailyMetrics[date] as Date
- DailyMetrics[zip_code] as Text (preserves leading zero)
- DailyMetrics[borough] as Text
- numeric metric columns as Whole Number

The daily mart's observation grain is **date × borough × ZIP**. It contains separate complaint and inspection counts, but inspection rows currently use borough = UNKNOWN. Do not assume each row refers to a single visit.

## 2. Calendar dimension
Modeling > New table:
```dax
Calendar = CALENDAR(MIN(DailyMetrics[date]), MAX(DailyMetrics[date]))
```
Change Calendar[Date] to Date type, mark Calendar as the date table, and create a one-to-many relationship to DailyMetrics[date] with single direction filter from Calendar to DailyMetrics.

Optional calculated columns:
```dax
Year = YEAR('Calendar'[Date])
Month Year = FORMAT('Calendar'[Date], "YYYY-MM")
Week Start = 'Calendar'[Date] - WEEKDAY('Calendar'[Date],2) + 1
```

## 3. Measures
Create the measures from `MEASURES.dax` one at a time (Power BI's New measure editor does not accept multiple definitions at once).

## 4. Pages and visuals
**Executive overview**
- 4 card visuals: Total Complaints, Total Inspections, Rat Activity Inspections, Rat Activity Rate.
- Line chart: Calendar[Week Start] → Total Complaints; avoid showing gaps as zero without explaining missing ingestion dates.
- Stacked column chart: date/month vs Rat Activity Inspections, Passed Inspections, Other Inspection Outcomes.
- Slicers: dates and ZIP. Do NOT apply borough slicers to both source types yet.

**Complaints geography**
- Table or horizontal bar: ZIP vs Total Complaints, filter Top N = 10.
- Borough vs Total Complaints (311-only).
- A geographic map can be added using complaint-level coordinates after validating location completeness.

**Inspections**
- Outcomes by week, rat-activity rate by date, top inspection ZIP codes.
- Do NOT use the UNKNOWN inspection borough for borough-level conclusions.

**Data reliability**
- Show latest observed date and data refresh metadata.
- Explicitly show known missing collection periods.

## 5. Known coverage caveats
- August backfill is verified, as is recent September/October ingestion, but the interval from September 1 to September 21 has not yet been backfilled.
- For that gap, run GitHub Actions mode=backfill with start_date=2026-09-01 and end_date=2026-09-22.
- Longer-term trend analysis needs additional monthly windows.
- Complaint rate is not rat population prevalence; inspection findings are conditional on where inspections occurred.
- Rat Activity Rate denominator is all stored inspections, not all properties or reports.
- This is a model recipe, **not a finished PBIX**.

## 6. Automating Power BI Service
A GitHub Actions CSV commit does not automatically refresh Power BI Service datasets. After a PBIX is published, configure the semantic model's supported cloud data source and credentials, then schedule refresh after the Monday collection. GitHub CSV private authentication must be handled appropriately; a local manual CSV import does not auto-refresh.
