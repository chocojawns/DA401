# Homework 5 team briefing: speaker notes

## Slide 1: Healthcare + industrials: what should an ERM team monitor?

Introduce both team members. Explain that the briefing distinguishes observed ratios, management disclosures and proposed actions. It is not a buy/sell recommendation. The industrial numerical panel has not passed the same checks as healthcare; do not imply a fully validated cross-sector test.

## Slide 2: Healthcare trends persist when membership is held constant

Use the year-end-balance dataset only. 318 matched company-years exist across 56 firms; 49 have five matched years, 47 have six, and 43 have five unflagged equity years. The main 2025 cross-section has 41 observations. Source: recovered homework_basis/financials.csv. Industry-wide four-component comparison remains incomplete without the industrial raw input table. Changes in medians are not medians of within-firm changes.

## Slide 3: A higher ROE can reverse the ranking of asset returns

2025 Amgen ROE: $7.711bn / $8.658bn = 89.06%. Its net income/assets is about 8.51%, versus IDEXX about 31.62%. The comparison is accounting ROA, not operating income/assets. ROE = margin × turnover × multiplier. Equity multipliers are not debt-to-equity ratios. Do not infer why equity became small without a rollforward. HCA provides a warning case: positive income $6.784bn / negative equity $6.027bn = negative 112.56% ROE, which does not indicate a net loss.

## Slide 4: Pfizer: investigate the margin and turnover decline together

Source: Pfizer 2023 10-K, https://www.sec.gov/Archives/edgar/data/78003/000007800324000039/0000078003-24-000039.txt
The filing states reduced COVID-product demand has led to reduced revenues/excess inventory and significant Paxlovid/Comirnaty write-offs in 2023. The chart uses current recovered year-end values, not older average-balance ratios. Contributions average all six orders of replacing the three DuPont factors and sum exactly to the observed ROE change. The acquisition of Seagen is an additional asset-base issue. The graph does not estimate how many ROE points were caused by a particular disclosed event.

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
