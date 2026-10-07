# Homework 5 team briefing: speaker notes

## Slide 1: Healthcare + industrials: what should an ERM team monitor?

Introduce both team members. Explain that the briefing distinguishes observed ratios, management disclosures and proposed actions. It is not a buy/sell recommendation. The industrial numerical panel has not passed the same checks as healthcare; do not imply a fully validated cross-sector test.

## Slide 2: Healthcare trends persist when membership is held constant

Use the year-end-balance dataset only. 318 matched company-years exist across 56 firms; 49 have five matched years, 47 have six, and 43 have five unflagged equity years. The main 2025 cross-section has 41 observations. Source: recovered homework_basis/financials.csv. Industry-wide four-component comparison remains incomplete without the industrial raw input table. Changes in medians are not medians of within-firm changes.

## Slide 3: Look across every year before selecting individual examples

255 eligible company-years; 43 distinct firms. Missing or flagged years are not imputed. Scatter x = net income / year-end assets; y = net income / year-end equity. Their ratio is the equity multiplier. This is a mechanical relationship, not an independent causal test. A company appears in multiple panels: observations are dependent. Full ticker-by-year values are in roe_all_years_percent.csv and all_company_years.png. The previous Amgen/IDEXX pair was illustrative, not the entire analyzed sample.

## Slide 4: Across the same 40 firms, margin contributes most to the 2025 rebound

For each firm and consecutive year, replace margin, turnover and multiplier in all six possible orders; average each factor’s incremental contribution. Then average firm contributions equally across the same 40 companies. Contributions sum exactly to the change in mean ROE. This is NOT a decomposition of median ROE. The 2021 increase is predominantly margin; all three components contribute negatively in 2023. Firm-level contributions and aggregate means are supplied as CSV. To investigate causes, use company disclosures: Pfizer 2023 discusses lower COVID demand, inventory write-offs and Seagen acquisition, but this does not establish the sector-wide causal effect. Source: https://www.sec.gov/Archives/edgar/data/78003/000007800324000039/0000078003-24-000039.txt

## Slide 5: 3M: persistent exposure is not the same as current disruption

Industrial source independently read: 3M 2024 10-K, https://www.sec.gov/Archives/edgar/data/66740/000006674025000006/0000066740-25-000006.txt
Exact excerpts: “some of our suppliers are limited- or sole-source suppliers”; “In 2024, global supply chains stabilized, with disruptions driven from more isolated factors”; “Market price risks were partially mitigated via negotiated supply contracts and leveraging scale across supply base.” This juxtaposition is useful: risk factors are exposures, while business/MD&A discusses realized conditions. Do not attribute 3M ROE movements to supplier risks without reconciling settlement, tax, spin-off and earnings effects. The filing reports PFAS liabilities retained in connection with the Solventum separation.

## Slide 6: The AI severity scores fail a basic usefulness check

Computed from the partner-provided industrials_analysis.jsonl: all 472 records have risk_score_1_to_10 equal to 5. This is a frequency of model outputs, not a frequency or severity of economic risks. Constant values have zero variance, so correlation with ROE is undefined. The supplied industrial prompt contains an example risk score of 5; this may warrant investigating anchoring, but we have not established why all outputs match it. Required sector-wide market/operational/regulatory/financial risk frequency and severity analysis remains incomplete. Do not present these scores as validated measurements.

## Slide 7: Tie supply-chain monitoring to a measurable financial pathway

These arrows describe plausible mechanisms and proposed monitoring, not causal coefficients estimated in our study. Inventory days, delivery performance and forecast errors are not measured in the current financial dataset. Distinguish a write-off effect on earnings/assets from a sales-volume effect on turnover. Healthcare evidence: Pfizer 2023. Industrial evidence: 3M 2024. Risk-category labels: market demand and operational inventory for Pfizer; operational sourcing and market input prices for 3M.

## Slide 8: Evaluate management actions using outcomes, not promises

Pfizer source: https://www.sec.gov/Archives/edgar/data/78003/000007800324000039/0000078003-24-000039.txt
Exact wording includes “This program is expected to deliver net cost savings of at least $4 billion, to be achieved primarily from 2023 through 2024.” This was a forward-looking statement in that filing; we have not verified realized savings.
3M source: https://www.sec.gov/Archives/edgar/data/66740/000006674025000006/0000066740-25-000006.txt
Reported partial mitigation is management’s account, not our independent causal estimate. Suggested monitoring is the team recommendation, separate from reported actions.

## Slide 9: A few extreme profiles materially change the average

43 eligible company-average ROEs: mean 20.74%, sample SD 21.90 percentage points. IQR-only ROE outliers: ABBV, AMGN, IDXX, LLY and ZTS. Removing them leaves 38 firms and mean 13.50%. Two-SD ROE flags exclude four firms, leaving 39 and mean 14.50%. These are not 2025-only statistics. Repeated firm-years are dependent; ratios share components; the selected sample is not random. No normality assumption or causal significance claim. Source spreadsheet: outlier_mean_sensitivity.csv.

## Slide 10: ERM recommendation: prioritize evidence-backed monitoring

Suggested owners: CFO/finance for the accounting bridge; supply-chain leaders for operational indicators; analytics/risk team for disclosure coding. This is an ERM monitoring recommendation, not a tested claim of cost savings or a security valuation. Important assignment limitations: validated sector-wide risk frequency/severity and comparable industrial four-component annual medians are not yet complete. The 10-slide cap includes this slide; do not append a second full deck. Both presenters should acknowledge scope openly in Q&A.
