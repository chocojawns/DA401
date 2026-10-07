# Healthcare: one clear workflow

Use **HealthcareWorkflow.py** as your starting point. Its numbered sections are
settings, input checks, financial analysis, AI review, and the main command.
It calls the existing tested programs so there is one implementation of the
accounting calculations. Industrial files are not involved.

## Start here: understand the data already collected

From your DA401 terminal with your Python environment active:

```powershell
python HealthcareWorkflow.py analyze
```

This defaults to the recovered **year-end balance** dataset in
`healthcare/reports/homework4_recovered/homework_basis`. It applies the five-year
rule, creates graphs and research questions, and writes a consolidated
`healthcare_study.json`. No internet connection or API key is needed.

The terminal prints the path to `START_HERE.md` in the new analysis folder.
Read it, then `analysis_report.md`. In the saved snapshot, 43 companies qualify.
The consolidated JSON contains method details, source hashes, eligibility,
company averages, outliers, cluster results and research questions. Table cells
copied from CSV are strings; margin/ROE values remain decimal ratios.

No-argument runs (including VS Code's Play button) show instructions only. They
do not silently start a download or incur API charges.

## Classify business models when verified

```powershell
python HealthcareWorkflow.py analyze --subsectors ".\healthcare\my_verified_subsectors.csv"
```

Use the generated `subsector_template.csv` columns: ticker, subsector,
classification_source. Verify labels against Item 1 and segment descriptions;
a source URL alone is not evidence that a label is correct. Until then the
analysis explicitly shows Unclassified.

## Collect only when you need fresh SEC data

```powershell
$env:SEC_USER_AGENT = "DA401 research YOUR_CONTACT_EMAIL"
python HealthcareWorkflow.py collect
```

This uses HealthcareStats.py for healthcare fiscal years 2020–2025. It reuses the
SEC cache and produces original-filing **average-balance** calculations plus
Item 1A JSONL. This is a different method from the recovered year-end study.
Keep the panels separate; do not silently combine their ratios.

## Ask focused AI questions after the quantitative review

```powershell
python HealthcareWorkflow.py ai --run-dir ".\healthcare\results\research\YOUR_COLLECTION_FOLDER"
```

This previews tasks, without paid calls. Review exclusions and request counts.
To execute a small batch, set OPENAI_API_KEY locally using your normal secure
configuration, then add `--execute --max-requests 3`. API requests may split long
filings into multiple chunks; three requests does not necessarily mean three
companies. The underlying AIResearch cache tracks input/prompt/model hashes.
Do not place a key in the source code or commit it to GitHub.

Use `--question "YOUR SPECIFIC RESEARCH QUESTION"` to focus the analysis.
Require quotations, sources, limitations, and alternative explanations. Item 1A
contains potential risks; MD&A/financial notes are needed for realized causes.

The AI stage requires the matching original financial and Item 1A collection.
It deliberately rejects the recovered comparative-only financial dataset:
matching it to an older risk filing without explicit timing would misrepresent
what information was available. `healthcare_study.json` is a quantitative
summary, not a complete Item 1A evidence bundle. No automatic paid handoff occurs.

## Programs underneath the workflow

|Purpose|Program|
|---|---|
|Collect original financials and Item 1A|HealthcareStats.py|
|Reconcile Homework 4 coverage offline|Homework4CoverageAudit.py|
|Quality checks, company comparisons and graphs|HealthcareAnalysis.py|
|Source-checked AI task preparation and responses|AIResearch.py (called for healthcare only)|

The industrial programs and their output files remain unchanged.
