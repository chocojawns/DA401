# HealthcareAnalysis.py

Stage 2 reads an existing HealthcareStats run. It never downloads data or calls an AI API. Run it after the collector finishes so the input files are complete. Source files remain untouched; each analysis gets a separate timestamped subfolder.

## Start

From the repository root, using the environment containing requirements.txt:

```powershell
python HealthcareAnalysis.py --run-dir "healthcare/results/research/YOUR_COMPLETED_RUN"
```

Replace YOUR_COMPLETED_RUN with your actual directory. You must supply the directory explicitly; the Play button without arguments displays help rather than guessing which results to use.

The collector can keep running while you install or read this code, but wait until it finishes before analyzing that run. No OpenAI key or SEC contact setting is required.

## Subsector labels

The first run writes `subsector_template.csv` with ticker, subsector, and classification_source. Copy it to `healthcare/subsectors.csv`, fill the classifications using a consistent cited taxonomy, and run:

```powershell
python HealthcareAnalysis.py --run-dir "healthcare/results/research/YOUR_COMPLETED_RUN" --subsectors healthcare/subsectors.csv
```

Use a documented classification source for every assigned label. Pharmaceuticals, biotechnology, equipment, providers, distributors, and insurers are possible groups, but agree on a consistent taxonomy and definition before coding. Broad diversified companies need an explicit assignment policy. Labels are treated as fixed across the study: business changes and classification date should be addressed in your methods. The software requires a source field but cannot certify the source's accuracy. Unclassified companies remain in overall analysis and are excluded from subsector bar charts. Labels are not guessed from company names or AI.

## Outputs

- `analysis_report.md`: sample size, eligibility, limitations, clustering status.
- `quality_review.csv`: all input rows with numerical/equity exclusions.
- `analysis_coverage.csv`: requested company-years from the collection manifest, including unavailable rows.
- `company_averages.csv`: one row per company with at least three usable years by default (`--min-years` overrides this).
- `subsector_summary.csv`: annual subsector medians, counts, standard deviations and quartiles.
- `*_subsectors.png`: four simple horizontal bar charts, latest requested year, with group counts.
- `coverage_sensitivity.png`: overall annual median ROE versus medians for companies observed in every requested year.
- `balanced_panel_medians.csv`: complete-period cohort medians for all components.
- `company_outliers.csv`: 1.5-IQR flags on company averages; requires eight companies and nonzero IQR. These are review candidates, not proven errors.
- `annual_changes.csv`: consecutive-year company pairs with margin and ROE changes in percentage points; missing years are not bridged.
- `descriptive_company_correlations.csv`: Spearman correlations on company averages if at least eight companies are eligible. No p-values; ROE/component relationships contain mathematical dependence.
- `cluster_scores.csv`, `company_clusters.csv`, `cluster_profiles.csv`: standardized three-component K-means, K=2 and highest-silhouette tested K. Requires six companies/three distinct profiles. ROE is excluded from clustering because it is the product of the inputs.
- `k2_by_subsector.csv`, `clusters_by_subsector.csv`: financial clusters versus supplied business classifications.
- `cluster_selection.png`: a simple silhouette-score line chart.
- `research_questions.json`: up to ten questions about the largest absolute margin changes, with calculated evidence and SEC URLs.
- `analysis_manifest.json`: input/program/classification hashes and configuration.

Conditional outputs are absent when sample size or labels are insufficient. Read the report before interpreting absence as an error.

## What the results mean

These are descriptive and exploratory analyses. Year coverage can differ across company averages. Balanced-panel comparisons help identify changing-sample effects but may introduce their own selection bias. Equity-flagged observations remain in quality_review.csv and are excluded from comparisons; thresholds come from the collection program. Review that policy before presentation.

Outlier fences across the entire healthcare sample can flag valid business-model differences. Check subsector context before calling any company anomalous. Clustering examines standardized mean margin, turnover, and equity multiplier, is sensitive to extremes, and evaluates initialization agreement across seeds—not bootstrap sampling stability. Highest silhouette among tested K is not a universally optimal number of economic groups. One-sector clustering does not satisfy the assignment's two-sector industry-separation question on its own.

No inferential panel models, causal claims, or automatic qualitative/quantitative correlations are included. Those require validated risk-category measurements, filing-date alignment, a prespecified outcome, controls, and company-aware uncertainty estimation. Do not use chunk-level AI finding counts as independent observations or risk intensity.

Questions are hypothesis-generating, not discovered causes. To ask AIResearch one of them, copy the question into its `--question` option with the same underlying run directory. Automatic ingestion of the whole question list is not yet implemented. AI cannot establish causes from Item 1A alone; investigate MD&A and financial notes too.

## Validation

Tests cover duplicate rejection, sourced classification requirements, minimum sample size, and a synthetic 12-company run through graphs and clustering. The saved six-year Pfizer sample also runs successfully; it correctly skips clustering for one company. The full healthcare dataset has not yet been analyzed or validated here.
