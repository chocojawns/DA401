# Homework 4 coverage reconciliation

The professor's worksheet lists 45 kept healthcare companies out of 59.
That is a comparison benchmark, not a reason to alter values or force exclusions.
The current repository's legacy Homework 4 code is not known to be identical to
the professor's implementation.

`Homework4CoverageAudit.py` reuses four financial-selection functions from
`homeWork4AndyJohnson.py`, without running its top-level download loops. It reads
cached SEC Company Facts and performs no network or AI requests. It reproduces
legacy selection using year-end assets/equity, same-accession quantities and
latest available comparative annual figures by the supplied cutoff (default
2026-09-23, as in the legacy program). It retains negative equity with warnings.
That differs from `HealthcareStats.py`'s original-filing and average-balance
method. Keep the two datasets separate; do not splice newly recovered rows into
the older panel. Comparative data are not necessarily information available to
investors at the end of the measured year.

From the repository folder, using the active Python environment:

```powershell
python .\Homework4CoverageAudit.py --run-dir ".\healthcare\results\research\20261007T035423369138Z" --output ".\healthcare\results\homework4_audit"
python .\HealthcareAnalysis.py --run-dir ".\healthcare\results\homework4_audit\homework_basis" --min-years 5
```

The output folder must be new. Reuse of cached files requires the same `sec_cache/research`
folder or `--cache PATH`. There is no automatic download fallback. Missing cache
files are explicitly reported as audit errors, not counted as missing SEC data.

Outputs:
- `company_method_comparison.csv`: all 59 companies, before/after coverage and original errors.
- `homework_method_candidate_financials.csv`: annual quantities, tags, accessions, period dates, ratios and equity warnings.
- `revenue_review.csv`: materially competing revenue tags for review against filing statements.
- `audit_manifest.json`: cutoff, source/cache hashes and counts.
- `homework_basis/`: compatible input for HealthcareAnalysis, explicitly marked as year-end comparative data.

In the reviewed cache, this replay found 49 companies with five usable years,
47 with all six consecutive years, and 43 with at least five unflagged equity
years. The 14 revenue conflicts for CNC, HUM, PODD and PFE were checked against
cached original statements; total revenue selections matched their period-specific
inline amounts. Other/new caches may produce different outcomes and need review.

Six companies qualify by data completeness but do not have five unflagged years:
CAH, COR, DVA, HCA, MCK and MTD. Keep their raw quantities and discuss equity
separately rather than interpreting their ROE as comparable profitability.
The 45-company benchmark is not exactly replicated. Full professor code,
cutoff/snapshot and kept-ticker list would be needed to explain the remaining
difference exactly. No numerical values are fabricated to match that count.
