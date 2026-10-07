# Question-led briefing: speaker notes

## Slide 1: What is behind healthcare ROE—and how sustainable is it?

Road map: what happened; accounting explanations; business evidence; monitoring implications. The quantitative findings concern the eligible healthcare sample. The industrial portion is a verified 3M disclosure case, not a validated sector-wide statistical comparison. Sustainability is a question to investigate, not an estimated probability.

## Slide 2: ROE measures profit per dollar of book equity

Margin = net income/revenue; turnover = revenue/assets; multiplier = assets/equity. Dollars cancel; ROE and margin are dimensionless ratios expressed as percentages. Example .20 × .50 × 2 = .20 = 20%. Book equity is assets minus liabilities, not market capitalization. Year-end denominators are used consistently here; do not mix with older average-balance graphs. Agilent lacks matched 2020, Bio-Techne lacks matched 2025, AbbVie has negative 2025 equity of $3.27bn. Missing matched data does not prove missing SEC filing. Professor benchmark is 45; verified eligible count here is 43. Inclusion requires five usable years, fixed panel six. 2026 filing dates can describe fiscal 2025.

## Slide 3: What happened? Median ROE peaked in 2021, then fell

These are separately calculated annual medians for a balanced 40-company sample. Their product does not equal median ROE. Fixing membership removes changing-composition effects within this panel, not survivorship or selection bias. Median ROE changes describe distributions, not a typical company causal effect. Data: balanced_component_medians.csv. Companies have different fiscal year-end dates.

## Slide 4: Why do returns differ? The equity base can amplify ROE

Each dot represents a firm in the indicated year; repeated dots across years are not independent observations. x = net income/assets, y = net income/equity; y = x × equity multiplier. Amgen margin .209817 × turnover .405703 × multiplier 10.462693 = ROE .890621. IDEXX .246175 × 1.284396 × 2.087202 = .659945. Asset returns are about 8.51% and 31.62%, respectively. This demonstrates the accounting denominator effect, not the historical cause of equity levels. Buybacks, losses, distributions and acquisitions require separate evidence. Names of annual top-ten firms are supplied in top10_each_year.csv; the full eligible table has 255 rows.

## Slide 5: What changed? Margin contributes most to the 2025 rebound

For each of 40 firms, decompose each adjacent-year ROE change by averaging contributions over all six orders of replacing margin, turnover and multiplier. Average each contribution across firms. The three contributions sum to the change in mean ROE, not median ROE. 200 firm-level bridges. A one-percentage-point change means, for example, 10% to 11%. 2021 mean increase is 6.098 pp, of which margin contributes 6.235 pp. In 2023 all three average contributions are negative. Accounting allocations do not estimate counterfactual event effects.

## Slide 6: How robust is the average? Extreme firms change it substantially

Company averages use each eligible firm’s five or six unflagged years, then equal company weights. Sample SD is 21.90 percentage points. IQR = Q3−Q1; flag values below Q1−1.5IQR or above Q3+1.5IQR. ROE-only flags: ABBV, AMGN, IDXX, LLY, ZTS. Removing five leaves 38 firms with mean 13.50%. Alternative mean ±2 sample SD removes four, leaving 39 and mean 14.50%. Neither rule proves an accounting error. No normal bell-curve assumption, random sample inference or causal significance claim. Extreme group selection and repeated observations also constrain the risk comparison.

## Slide 7: What might explain the pattern? Pfizer documents demand pressure

Pfizer year-end ROE fell from 32.795% in 2022 to 2.381% in 2023. Symmetric contributions: margin −24.350 pp, turnover −9.585 pp, multiplier +3.520 pp. Source: https://www.sec.gov/Archives/edgar/data/78003/000007800324000039/0000078003-24-000039.txt. The filing discusses reduced COVID-product demand, excess inventory and significant Paxlovid/Comirnaty write-offs. Seagen is an additional asset-base issue. This is one verified case, not a sector explanation. Management expected at least $4bn cost realignment net savings primarily in 2023–2024; we have not verified realized savings. Proposed follow-up: revenue mix, inventory charges, acquisition effects and realized savings.

## Slide 8: Industrial comparison: disclosed exposure need not mean disruption

Source: 3M 2024 10-K https://www.sec.gov/Archives/edgar/data/66740/000006674025000006/0000066740-25-000006.txt. Exact excerpts include “some of our suppliers are limited- or sole-source suppliers”; “In 2024, global supply chains stabilized, with disruptions driven from more isolated factors”; “Market price risks were partially mitigated via negotiated supply contracts and leveraging scale across supply base.” This illustrates how Item 1A exposures differ from realized conditions discussed elsewhere. The filing does not support attributing all ROE changes to sourcing. Comparable industrial four-component quantitative panel remains unverified. Industrial files have not been edited.

## Slide 9: Do risk disclosures distinguish high and low ROE? Still under review

Do not present a high-versus-low risk difference as a finding yet. Ten selected disclosure matches are missing: ZBH 2020/2021/2022/2023/2025, STE 2021/2022/2023/2024, CI 2021. Financial rankings retain all 120 entries. The 110 matched filings represent 33 companies and 549 chunks, not 549 independent observations. Rank groups change annually. Later financial history is retrospective context. Exact quote and URL validation does not validate causal interpretations. Partner industrial scores are all 5 across 472 records, with no anchored rubric; constant scores cannot support correlation. Required sector-wide risk-frequency/severity measurement remains incomplete.

## Slide 10: Why care? High ROE is a signal to investigate its source

Close by answering the research question directly. Recommended monitoring owners: finance for recurring earnings, transaction charges and equity rollforwards; operations for inventory aging, write-offs, delivery and supplier concentration; risk analytics for reviewed disclosure coding. These operating KPIs are recommendations, not measurements already present in our dataset. The evidence supports accounting explanations and selected documented cases, not a causal model or sustainability forecast. Remaining Homework 5 gaps: completed reviewed all-years AI comparison, validated sector-wide risk frequency/severity, and comparable industrial four-component annual statistics. This ten-slide deck remains an evidence-limited team briefing.
