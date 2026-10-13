# Step 2 — Verified data ingestion and Power BI plan

## Current verified status (2026-10-13)
GitHub workflow run 38453297579 succeeded.
Archive totals: 1,254 distinct 311 complaints; 9,670 stored inspection rows; 1,920 daily aggregate rows.
This is a short-period archive and not a year-over-year report. Inspect `data/refresh_status.json` after each refresh.

## Historical backfill
1. GitHub → Actions → NYC Rodent Weekly Refresh → Run workflow.
2. Set mode **backfill**.
3. Set start_date `2026-08-01` and end_date `2026-09-01` (exclusive).
4. Check completion, then use `2026-07-01` to `2026-08-01`.
5. Repeat in windows of up to 45 days, progressing backward as far as desired.
6. Leave mode **weekly** for ordinary 21-day incremental refreshes; the Monday cron does this automatically.

GitHub workflows can take some time, and API pagination can be interrupted. A successful run is required for each backfill window. Backfills should not overlap with another active run.

## Model and dashboard
Import `data/daily_metrics.csv` into Power BI Desktop as DailyMetrics.
- `date` → Date type; measures → Whole number.
- Calendar dimension → DATEADD-aware trends.
- KPI cards: Total Complaints, Total Inspections, Rat Activity Inspections, Rat Activity Rate.
- Line chart: calendar date vs complaints; a week-start grouping is better for annual trend.
- Bar chart: ZIP vs complaints, Top N 10.
- Filters: Calendar Date and ZIP.
- Display latest refresh time from `refresh_status.json` separately if needed.

## Caveats and next improvements
- Current daily mart has inspection borough as UNKNOWN; a borough-based comparison across the two sources would be misleading.
- Inspection identity uses job ID, inspection date, type, BBL, and result; validate against source unique-event semantics before relying on its deduplication for research-grade reporting.
- Geospatial complaint-to-inspection matching and an inspection coverage denominator have not been built.
- One calendar day may include multiple groups, so don't treat daily mart row count as number of days.
- The `Rat Activity Rate` is rat-activity outcomes / all stored inspections, not a citywide rat prevalence estimate.
- GitHub's Monday scheduled refresh updates CSVs in the repository; Power BI Service needs its own supported refresh mechanism and credentials. A local PBIX does not live-refresh automatically.
- No native PBIX file has been deployed.

## Release checklist
- [x] Official NYC API extraction confirmed in GitHub
- [x] Weekly GitHub scheduled workflow
- [x] Incremental deduplication
- [x] CSV mart and initial DAX measures
- [x] Date-scoped manual historical backfill workflow uploaded
- [ ] Confirm backfill run completes
- [ ] Validate historical data completeness
- [ ] Validate inspection data schema, uniqueness and dimensions
- [ ] Create and publish native Power BI report
- [ ] Configure Power BI Service refresh
