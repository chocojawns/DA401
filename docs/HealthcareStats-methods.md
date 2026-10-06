# HealthcareStats: stage 1 research protocol

## Scope and readiness

`HealthcareStats.py` is the new SEC collection, DuPont calculation, Item 1A extraction, and graphing program. It defaults to healthcare. It makes no OpenAI requests. A later, separate program will analyze the staged JSONL after source validation. Earlier API drafts remain preliminary examples, not part of this program.

Seven offline tests pass, including synthetic SEC data through graph and JSONL generation. Live SEC verification is blocked in the current cloud environment by network policy (proxy CONNECT 403). Do not present synthetic test results as company findings or claim this program has been validated on the actual healthcare universe yet.

## Run

Install the root `requirements.txt` in your virtual environment. Set `SEC_USER_AGENT` to your project name and real contact email. The email is local configuration, not committed project data.

PowerShell example (replace the email):

```powershell
$env:SEC_USER_AGENT = "DA401 research your-email@example.com"
python HealthcareStats.py --tickers PFE --start-year 2024 --end-year 2024 --cutoff 2026-10-05
```

macOS/Linux:

```sh
export SEC_USER_AGENT='DA401 research your-email@example.com'
python HealthcareStats.py --tickers PFE --start-year 2024 --end-year 2024 --cutoff 2026-10-05
```

After manually validating the small sample:

```sh
python HealthcareStats.py --start-year 2020 --end-year 2025 --cutoff 2026-10-05
```

Use `--offline` to reuse cached documents without network access. Uncached documents are reported as failures. `--sector industrials` uses the partner's company list. Each run creates a new timestamped folder under `healthcare/results/research/` (or industrials), preventing overwriting earlier evidence. The cache is shared in `sec_cache/research/`. Generated outputs and cached documents are ignored by Git; back them up separately.

The environment must permit HTTPS access to `data.sec.gov` and `www.sec.gov`. SEC requests are spaced at least 0.25 seconds apart, use timeouts, and are cached. HTTP errors are logged, not bypassed. Do not run parallel copies to increase request rate.

## Measurement decisions

- Profit margin = net income attributable to the parent / revenue.
- Asset turnover = revenue / average beginning and ending total assets.
- Equity multiplier = average assets / average beginning and ending parent stockholders' equity.
- ROE = net income / average equity = product of the three components.
- Ratios in CSVs are decimals; graph labels distinguish percentages from multiples.

Average balances align annual flows with the assets/equity employed over the year. This intentionally differs from the legacy homework scripts' ending-balance convention. Check course expectations and label the convention explicitly when comparing results. First-year calculations require the preceding year-end balance in the selected filing; the program does not substitute ending balances when the opening balance is missing.

Financial facts must share the exact annual period and accession. Original 10-K filings are selected; 10-K/A and later comparative restatements are not used to revise earlier observations. Annual periods must contain 350–380 days. Fiscal year and report period are checked against the primary filing's inline XBRL metadata; absent metadata requires manual review. This conservative draft does not yet support custom taxonomy tags, non-inline filings, transition years, or minority-interest reconstruction. It rejects conflicting revenue concepts for manual resolution instead of guessing which total is right.

Each available company-year is retained. Missing years do not automatically remove all other observations for the company. The current company CSV is a selected universe, not historical S&P membership: survivorship and selection bias remain. Current SEC Company Facts snapshots may contain later corrections even when original accessions are used; this is not a reconstructed historical investable database.

Negative/zero equity at either endpoint or average equity below 1% of average assets triggers a warning. Those rows stay in source tables but are omitted from the component comparison and operating-profile plots. All presentation charts exclude flagged observations, which remain available in the source tables. No silent winsorization is applied. The 1% rule is a transparent diagnostic choice, not a universal statistical standard; run sensitivity analyses before interpretation. Zero average equity has undefined ROE.

## Files and figures

- `financials.csv`: raw values, selected tags, ratios, fiscal period, original filing date, source URL, and accession.
- `staged_10k_batch.jsonl`: one extracted Item 1A per company/filing with dates, source URL, accession, and text hash. It can contain filings whose financial calculation failed; join and check coverage before combined analysis.
- `retrieval_status.csv`: successes/failures separately for metadata, financial calculations, and Item 1A.
- `coverage.csv`: every requested company-year, with financial and Item 1A availability.
- `equity_warnings.csv`: potentially unstable equity denominators.
- `roe_trend.png`, `profit_margin_trend.png`, `asset_turnover_trend.png`, `equity_multiplier_trend.png`: four separate, labeled median line charts with company counts. Missing years leave gaps. The sample can change by year.
- `annual_summary.csv`: medians, quartiles, and sample counts underlying the trends. Quartiles describe dispersion, not confidence intervals.
- `company_roe_YEAR_PAGE.png`: sorted horizontal bars with company names, tickers, and ROE percentages for the latest financial year. Pages contain at most 20 companies; all eligible companies are included.
- `company_roe_comparison.csv`: values behind the company bar chart.
- `next_year_research_pairs.csv`: consecutive fiscal-year financial pairs and next-year margin changes in percentage points. It is a preparation table, not a fitted statistical model.
- `manifest.json`: requested universe, cutoff, source-list and program hashes, and row count.

Item 1A extraction rejects short table-of-contents matches and requires a bounded section. It does not fall back to arbitrary filing text. Still review extracted first/last paragraphs against the original filing; regex boundaries alone cannot establish perfect extraction.

## What correlations are worth testing?

Do not regress ROE on all three DuPont components and describe the association as a discovery: their relationship is an accounting identity. Ratios can also share denominators, creating mechanical association. Descriptive component plots explain ROE; they do not demonstrate causality.

Pre-specify a small research question before examining the AI results. A useful healthcare starting question is: "Is disclosure of reimbursement/pricing pressure associated with a subsequent decline in profit margin?"

Suggested outcome (dependent variable): the following year's change in profit margin, in percentage points. This is usually more interpretable than ROE for a healthcare operational-risk hypothesis because leverage and equity can distort ROE. Secondary outcomes: change in asset turnover for utilization risks, and change in equity multiplier for financing risks. Negative-equity firms require separate treatment.

Suggested exposure (independent variable): a manually validated binary indicator for a defined disclosure category (e.g. reimbursement/pricing pressure), or whether that category newly appeared since the previous filing. Do not treat an AI-generated severity number or raw count of risk paragraphs as a measured probability of loss. Long filings and model verbosity otherwise become confounders.

Timing matters: a 10-K is usually filed AFTER the fiscal year ends and after the following fiscal year begins. The output flags whether disclosure precedes the next outcome period's START. Adjacent-year results generally describe an association with partially overlapping time, not a clean prospective forecast. For strict predictive work, choose the first complete fiscal period beginning after publication, or use post-publication quarterly outcomes. Never label a retrospective relationship a trading signal.

For exploratory panels, consider company fixed effects, fiscal-year effects, and pre-specified controls (baseline margin, log assets, and leverage), with standard errors clustered by company. Company fixed effects require within-company changes in the exposure; stable categories may not be identifiable. Check sample size, category prevalence, missingness, extreme denominators, and power before estimating. With roughly 45 companies and six years, keep models small and treat uncertainty seriously. Company clustering may still need small-sample correction or a company-level bootstrap. Comparing many risk categories requires multiple-testing control (e.g. Benjamini–Hochberg) and explicit exploratory labeling.

Report effect sizes and uncertainty, not only p-values. Repeat key findings with a balanced panel and alternative equity thresholds to assess sensitivity. Compare healthcare subsectors (insurers, pharmaceuticals, equipment, providers) when reliable labels are added: healthcare is not one homogeneous business model. This first program deliberately does NOT output unvalidated correlations, significance claims, AI scores, or causal conclusions.

## Validation checklist before presentation

1. Hand-check a company's six financial values and period dates against the cited filing.
2. Verify fiscal-year identity, report-period alignment, and source accession.
3. Review Item 1A boundaries and retain supporting quotations.
4. Inspect failures and denominator warnings; explain selection rules.
5. Confirm cohort size and whether changing sample composition explains trends.
6. Only then design and validate the qualitative coding and statistical model.

Run offline tests with `python -m unittest discover -s tests -v` from the repository root.
