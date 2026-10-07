# Use this package for the presentation

## Files and scope

- `Healthcare_ROE_presentation_draft.pptx`: editable 13-slide draft. The subsector slide is provisional; the sector comparison is a diagnostic appendix.
- `Healthcare_presentation_data.xlsx`: the actual dataframes, rankings, descriptive statistics and correlation tables.
- `graphs/`: eight standalone PNGs.
- `dataframes/`: machine-readable CSVs.

No industrial source or output files were modified. No paid AI calls were made.
All calculations use the recovered year-end-balance healthcare dataset, not the earlier average-balance data. There are 43 eligible companies over 2020–2025, 40 with all six years, and 41 with usable fiscal-2025 data. The year-end eligibility filter removes negative/small equity observations; it does not remove all economic outliers.

## The math to explain aloud

ROE = net income / equity.
Profit margin = net income / revenue.
Asset turnover = revenue / assets.
Equity multiplier = assets / equity.
Multiplying the last three cancels revenue and assets, leaving net income / equity. Here assets and equity are fiscal-year-end values. Average-balance ROE is another convention and produces different values.

Amgen 2025: net income $7.711bn / equity $8.658bn = 89.06%.
Equivalently: 0.209817 × 0.405703 × 10.462693 = 0.890621.
The 10.46× multiplier means equity is 9.56% of assets. It is an equity/asset relationship, not the debt-to-equity ratio: liabilities include more than interest-bearing debt. This supports an accounting explanation for high ROE, not proof of why equity became small. Inspect equity rollforwards and cash-flow/transaction notes for that.

HCA 2025: positive net income $6.784bn / negative equity −$6.027bn = −112.56%. The negative ROE does not mean HCA lost money. This is why hospitals with negative equity require a separate discussion rather than ordinary ROE rankings.

## 2025 ranking among the 41 eligible observations

|Company|ROE|Profit margin|Turnover|Equity multiplier|
|---|---:|---:|---:|---:|
|Amgen|89.06%|20.98%|0.406×|10.46×|
|Zoetis|80.25%|28.23%|0.612×|4.64×|
|Eli Lilly|77.78%|31.67%|0.579×|4.24×|
|IDEXX|65.99%|24.62%|1.284×|2.09×|
|Bristol Myers Squibb|38.19%|14.64%|0.535×|4.87×|

Amgen and IDEXX illustrate different combinations: Amgen has a much larger multiplier, while IDEXX has much higher asset turnover. This is more informative than calling both “high ROE.” Do not multiply cohort-average or median components and expect average/median ROE to reconcile; the annual identity applies within individual rows.

The lowest eligible 2025 observations are Centene −33.45%, Moderna −32.62%, Baxter −15.61%, Charles River −4.56%, and CVS +2.35%. The ratios identify cases, not their causes. Source URLs, exact quantities and filing dates are in the workbook.

## Standard deviations, bell curves and probabilities

For the 41 eligible 2025 observations: mean ROE 17.73%, median 12.81%, sample SD 24.86 percentage points, Q1 6.88%, Q3 21.18%. SD uses sqrt(sum((x−mean)^2)/(n−1)). It measures dispersion between observed companies, not uncertainty in a forecast or a causal estimate.

The histogram/normal-Q–Q plot uses one mean annual ROE per eligible company. Its skewness is about 2.37: a long right tail makes a bell-curve interpretation inappropriate. Do not automatically use the 68–95–99.7 rule, normal-tail probabilities or mean ±1.96 SD as a confidence interval. Annual 2025 statistics and the distribution of six/five-year company means are distinct summaries.

Four of 41 eligible companies had net losses in 2025: an observed proportion of 9.76%. This describes this selected sample. It is not a 9.76% forecast probability for a company, a stock-price-loss probability, or a representative estimate for all healthcare businesses. The denominator and exclusions matter. No inferential probability interval is asserted for this nonrandom selected cohort.

## Correlations: useful but not causal

Spearman correlations across 43 company-average profiles:
- ROE and profit margin: +0.604.
- ROE and asset turnover: +0.181.
- ROE and equity multiplier: +0.162.

Margin has the strongest monotonic association in this particular profile comparison. This does not prove margin improvements cause ROE improvements, nor that leverage is irrelevant (Amgen is a counterexample). Ratios share components and denominators, averages conceal changing conditions, and business models differ. No claim of statistical significance is made. One company contributes one profile, not six supposedly independent observations.

We do not yet have a consistently coded merger, buyback, patent, reimbursement or policy exposure dataset. Therefore we cannot validly claim those events are “highly correlated” with ROE from this dataset alone. To test that, define the exposure before selecting interesting outcomes, record timing and amounts, specify controls and outcomes, and address dependence/confounding. An AI risk score is not a validated measurement of economic risk by itself.

## Business models: preliminary comparisons, not proven subsector effects

Draft 2025 groups include pharma/biotech n=10 (median ROE 29.80%), devices/supplies n=12 (9.92%), and insurance/integrated health services n=6 (9.77%). Pharma/biotech median margin is 26.55%, versus 1.54% for insurance/integrated services; median turnover is 0.47× versus 1.69×. These suggest different combinations of margin and volume, but the labels are analyst-defined and have not all been independently verified against segment reports.

Hospitals are not a reliable group comparison here: UHS is the sole eligible hospital operator; the “care providers and diagnostics” label also contains Labcorp and Quest, which are not hospital operators. HCA's negative-equity case illustrates how exclusion can distort business-model coverage. Do not call the grouped chart a validated pharma-versus-hospitals statistical test. There is no adequate within-hospital sample to support one.

## Events and sources

[Pfizer 2023 10-K](https://www.sec.gov/Archives/edgar/data/78003/000007800324000039/0000078003-24-000039.txt): reduced COVID-product demand and significant inventory write-offs are disclosed. The filing also discusses the December 2023 Seagen acquisition. Reconcile revenue, margins, acquired assets and charges before attributing the entire ROE movement to any one event.

[Bristol Myers Squibb 2024 10-K](https://www.sec.gov/Archives/edgar/data/14272/000001427225000039/0000014272-25-000039.txt): acquired IPRD expense of $13.4bn, including $12.1bn related to Karuna, versus $913m of acquired IPRD in 2023. This is a documented acquisition-accounting mechanism affecting earnings. The pretax charge is not a one-for-one after-tax net-income adjustment.

Possible broader context to investigate across 2020–2025 includes pandemic demand and procedure disruptions, COVID-product expansion and subsequent decline, financing costs, acquisitions, and changes in utilization/reimbursement. These are research topics, not effects estimated by our model. Item 1A discusses potential risks; use MD&A and notes for realized changes. Full fiscal 2026 is not in this study: filing in 2026 often reports fiscal 2025. Do not label those figures as 2026 operating performance.

## Healthcare–industrials correlation: not yet presentation-grade

The industrial AI output contains 472 rows, 96 without numeric ROE, and five duplicate company-year keys (10 affected rows). This review excludes all duplicate keys rather than choosing a record arbitrarily. Fifty-three industrial firms then have six finite ROEs; their equity denominators and fiscal labels remain unverified. We have not established that their sampling rules match healthcare's.

Comparing those industrial annual medians with the fixed 40-company healthcare panel gives Pearson r≈−0.651 and Spearman r≈−0.771 across **six annual pairs**. These are provisional diagnostics only. Six time points share macro shocks and may be serially dependent; equity/fiscal-label screening differs. Do not describe this as a statistically established negative relationship, an investment hedge, or causation. It measures accounting ROE co-movement, not stock-return correlation.

For a defensible comparison obtain the industrial raw financial CSV or full_industrials_batch.jsonl, reconcile labels/duplicates, apply comparable denominator and equity rules, then regenerate the comparison. No industrial files were changed during this read-only diagnostic.

## How accurate is the data?

The arithmetic has been checked, inputs have accession/period provenance, missingness is explicit, and the 14 competing revenue selections in the coverage recovery were checked against total-revenue statement rows. These are concrete checks—not a basis for claiming “95% accurate.” Not every input has been manually re-audited against the primary statements. Later comparative figures can reflect restatements or discontinued operations; transaction accounting and business mix limit comparability. Source credibility, extraction correctness, measurement choices and representativeness are separate questions.

For the presentation, prioritize: formula with Amgen; negative-equity HCA; a fixed-company trend; distribution and dispersion; then one documented transaction/event case. Treat the draft subsector chart and provisional sector correlation as limitations/research directions unless their remaining evidence is supplied.
