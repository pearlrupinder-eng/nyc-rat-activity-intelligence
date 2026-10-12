# Power BI setup

Import `data/daily_metrics.csv` as `DailyMetrics` and optionally the two detail files for drill-through. Cast `date` as Date and counts as Whole Number.

Create Calendar table:
```dax
Calendar = CALENDAR(MIN(DailyMetrics[date]), MAX(DailyMetrics[date]))
```
Mark as date table and relate `Calendar[Date]` to `DailyMetrics[date]`. Add measures from `MEASURES.dax`.

## Report pages
1. Executive overview: complaints, inspections, rat activity rate, weekly change, trends and freshness.
2. Geography: ranked ZIP codes and maps when valid coordinates exist.
3. Inspection outcomes: result mix over time, inspection types and job drill-through.
4. Data quality: missing geography, last update, rows loaded.

**Interpretation:** A complaint does not prove rat presence, and a shared ZIP does not establish a visit caused by that complaint. Inspections have UNKNOWN borough in the daily mart until authoritative geography enrichment. Do not compare borough inspection rates from this file.

GitHub refresh is NOT Power BI Service refresh. Set up a separate supported cloud data source and semantic model scheduled refresh after deployment.
