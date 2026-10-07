# Healthcare presentation working files

Homework 5 allows a maximum of **10 slides for the entire team**, not 10 per sector.
The included 10-slide healthcare deck is a quantitative working draft. It must be
condensed and combined with industrial material; it is not a completed Homework 5
briefing. The earlier presentation guide describes a 13-slide draft; use the
10-slide working file here instead. All industrial files remain unchanged.

Still needed: stakeholder persona, validated sector-wide Item 1A risk frequency
and severity, evidence-supported risk/ratio links, mitigation assessment, and a
combined stakeholder recommendation. Provisional subgroup and industrial
correlation exhibits are not validated headline results.

Coverage: 318 financial company-years across 56 companies; 47 have all six
fiscal years, 49 have at least five. The main equity-screened analysis retains
43 companies. No claim of complete coverage of all 59 companies is made.

## Company-level outlier sensitivity

Each company contributes its mean annual ROE across its usable years (five or six).
These figures are NOT the 2025-only mean and are not pooled company-year means.

|Rule|Remaining firms|Mean company-average ROE|
|---|---:|---:|
|All eligible firms|43|20.74%|
|Exclude flags on any of the four metrics, original 1.5-IQR rule|30|14.21%|
|Exclude only ROE 1.5-IQR flags|38|13.50%|
|Exclude only ROE values beyond mean ±2 sample SD|39|14.50%|

The untrimmed median is 14.93%; sample SD of company-average ROEs is 21.90
percentage points. The two-SD rule is a sensitivity check, not the original
method and not proof of a normal distribution. Outliers are not automatically
errors; deleting them changes the study population. Retain the full-sample
result and present trimmed means alongside it.

ROE-only IQR flags: ABBV, AMGN, IDXX, LLY, ZTS. Two-SD flags: ABBV, AMGN, IDXX, LLY.
See dataframes/outlier_mean_sensitivity.csv for every company's flags. The Excel
workbook predates this extra CSV; the outlier sensitivity is supplied separately.
