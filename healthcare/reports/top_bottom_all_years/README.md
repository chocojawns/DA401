# Annual highest and lowest healthcare ROE, 2020–2025

Select the top 10 and bottom 10 separately in each fiscal year from the existing eligible 43-company cohort. No year is singled out. Ranking is by ROE descending, with ticker as a deterministic tie-breaker. These are ROE ranks, not investment quality ranks. Financial history uses year-end balances.

120 selected company-years represent 36 unique companies. 110 company-years across 33 companies have matched fiscal-year and period-end Item 1A text. Ten selected observations lack matched text: ZBH 2020/2021/2022/2023/2025, STE 2021/2022/2023/2024, CI 2021. All 120 remain in annual_rankings.csv; no lower-ranked company replaces a missing disclosure. risk_coverage.csv makes missingness explicit.

Run from repository root:

```powershell
git pull --ff-only origin main
python HealthcareTopBottomAI.py
python HealthcareTopBottomAI.py --execute
```

The dry run currently reports 549 chunks, 110 company-years, 33 unique companies and all six fiscal years. Execute prompts for a key if needed. The new output directory is healthcare/results/top_bottom_all_years_ai; existing 2025 output is preserved. Previous 2025 API responses are not reused because the question and payload changed. Do not run both versions simultaneously. Stop an old active run with Ctrl+C before updating.

This is retrospective disclosure interpretation. Repeated companies are dependent observations; groups change annually. Extreme selection does not establish sector-wide risk prevalence or causality. Comparative financials can come from later filings, whose provenance is retained separately. AI reads every available matched disclosure in chunks without truncation; chunk counts are not company counts. Exact quotes and source URLs are checked. API costs depend on actual token usage; no paid calls were made while preparing these inputs.
