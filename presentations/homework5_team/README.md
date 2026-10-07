# Homework 5 team briefing: use this draft

Open `Homework5_Team_10_Slides.pptx`. It has exactly 10 slides including title
and conclusions, with explanations and source links in PowerPoint speaker notes.
`SPEAKER_NOTES.md` is the same defense guidance in a readable document.

The new exhibits answer questions instead of presenting a long ratio ranking:
- Net income/assets versus ROE reverses the Amgen/IDEXX ranking.
- A Pfizer ROE bridge allocates its 2022–2023 change across DuPont components.
- Outlier sensitivity explains why a few companies lift the mean.
- A check of industrial AI scores shows all 472 equal 5; it is not valid severity measurement.

Use the recovered year-end-balance panel consistently. Do not insert the older
average-balance charts (e.g., Amgen 106.1%) beside the new 89.1% year-end figure
without explicitly explaining the accounting change.

## Assignment readiness — honest limitations

This is an evidence-limited team draft, NOT a claim that all Homework 5 analysis
is complete. Completed elements include an ERM stakeholder perspective,
healthcare macro/dispersion analysis, sourced Pfizer and 3M disclosure cases,
supply-chain mechanisms, reported management responses, recommended monitoring,
and statistical limitations.

Two important gaps remain:
1. Comparable industrial annual medians for all four DuPont measures require the
   raw financial inputs and consistent screening. The supplied AI output has ROE
   but not authoritative structured inputs for all components. The draft does
   not fabricate these medians.
2. Validated sector-wide Item 1A category frequency/severity is incomplete. All
   472 industrial AI scores are 5. Counting those scores is an output-quality
   check, not risk prevalence. Human validation and an explicit coding rubric
   are required before treating LLM scores as measurements.

Risk-to-ratio links are evidence-supported mechanisms and accounting
relationships, not causal estimates. No full-year 2026 outcomes are analyzed.

## Sources

Healthcare quantities: `healthcare/reports/homework4_recovered/homework_basis/financials.csv`
in the repository. `pfizer_case_data.csv` and `pfizer_bridge_values.json` contain
values underlying the Pfizer exhibit.

Pfizer 2023 10-K:
https://www.sec.gov/Archives/edgar/data/78003/000007800324000039/0000078003-24-000039.txt

3M 2024 10-K (independently read for this briefing):
https://www.sec.gov/Archives/edgar/data/66740/000006674025000006/0000066740-25-000006.txt

3M distinguishes supply chains stabilizing in 2024 from persistent sole-source
exposure and price inflation. Its reported mitigation is negotiated contracts
and purchasing scale. Do not claim a measured causal effect on ROE.

Pfizer describes demand/inventory pressures and a cost program targeting at
least $4bn savings; the quoted savings are expectations in that filing, not
verified realized savings.

## Before presenting

- Open the PPTX and check layout on your PowerPoint installation.
- Assign presenters and read the notes for each slide.
- Stay within 10 slides for the entire team. Do not append another full deck.
- Do not call provisional evidence a validated sector-wide statistical finding.
- Original industrial scripts and files were not modified.

## Expanded healthcare coverage

The deck now shows all four components over 2020–2025 for the same 40 companies, six annual scatter plots covering all 43 eligible companies (255 observations), and all five annual DuPont bridges. The 43-company heatmap is a separate detailed handout. The professor's 45 is a target, not the verified eligible count here.

Each firm-level bridge averages the incremental contribution of each factor across all six replacement orders. Sector contributions are equal-weight means of the 40 firm contributions. They sum to the change in mean ROE, not median ROE. Values are in percentage points. 2025 contributions: margin +4.340, turnover +0.647, multiplier −1.141; net +3.847 pp (rounding applies). This allocates accounting changes; it does not estimate event causality.

The industrial risk score 5 is an AI output, not a financial calculation. The supplied prompt has an example value 5 without an anchored severity rubric. All 472 saved outputs equal 5; the reason is unverified. Zero variance prevents a severity–ROE correlation. Treat this as a measurement limitation, not evidence of moderate risk.

New dataframes retain source URLs and accession numbers. Eligibility requires at least five unflagged observed years. No missing year is imputed. The 40-company balanced panel additionally requires all six years. The retained population excludes some equity cases and is not the full healthcare sector. Source differences from older average-balance charts must not be combined.
