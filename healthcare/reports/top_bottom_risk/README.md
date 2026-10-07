# Top and bottom healthcare ROE comparison

Rankings use 2025 year-end-balance ROE among 41 usable 2025 observations in the 43-company cohort. Top/bottom does not mean best/worst investments. selected_company_history.csv retains their available 2020–2025 quantities, ratios and SEC sources. top10_each_year.csv names the ten highest ROE observations separately for each year. named_high_roe_companies.png labels the six highest each year; this is a rank rule, not a statistical outlier rule.

The 40-company balanced panel excludes Agilent (A: no matched 2020 row), AbbVie (ABBV: 2025 equity −$3.270bn flagged), and Bio-Techne (TECH: no matched 2025 row). Missing matched rows do not prove missing SEC filings. These three still contribute their usable years to the 43-company panel.

ROE = net income / year-end equity. 20% means $0.20 annual net income per $1 book equity. Equity is assets minus liabilities, not market capitalization. ROE is dimensionless, conventionally expressed as a percentage. Changes are percentage points. DuPont: net income/revenue × revenue/assets × assets/equity. These are accounting relationships, not independent predictors proving causality.

API preparation: 20 ranked companies, 19 matched 2025 Item 1A texts; ZBH (Zimmer Biomet) extraction fails bounded-heading validation and needs manual review. No substitute filing is used. Financials can be comparative values from later filings: source accession and filing date stay separate from the original-year Item 1A provenance. This is retrospective, not a predictive test. All text is chunked without truncation (100 requests currently). Each completed validated response is saved for resumption. Costs depend on model token usage; dry run makes no paid requests.

Run from repository root:

```powershell
git pull --ff-only origin main
python -m pip install -r requirements-openai.txt
python HealthcareTopBottomAI.py
```

Configure your own replacement OPENAI_API_KEY securely in the terminal environment, then:

```powershell
python HealthcareTopBottomAI.py --execute
```

Outputs: healthcare/results/top_bottom_ai/comparison_report.md, analyses.jsonl, responses.jsonl and plan.json. Do not commit keys. Quote checks establish textual support, not validity of every AI interpretation. No numeric severity scores or causal estimates are requested. Results require human review and will not by themselves complete the missing industrial assignment components.

If OPENAI_API_KEY is not set, --execute now prompts for a hidden key directly. Paste it and press Enter; no characters appearing is normal. The key stays in process memory and is not written to a file.
