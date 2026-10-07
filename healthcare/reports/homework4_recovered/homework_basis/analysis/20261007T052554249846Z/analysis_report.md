# Healthcare statistical review

Usable rows: 255 / 318. Companies: 43.
Company-level analyses require at least 5 years: 43 eligible companies.
Complete 2020–2025 panel: 40 companies.
Unclassified companies: 43.

Selected K=3 by highest silhouette among tested K values. Seed agreement is not sampling stability. Results are exploratory and sensitive to scaling/outliers.

- Financial quality exclusions remain in quality_review.csv; missing data is not imputed.
- Subsector medians represent available companies; groups with few companies are descriptive only.
- Outliers use 1.5-IQR fences on company averages (minimum eight companies); they are review candidates, not errors or significance tests. Mixed subsectors can explain outliers.
- Company averages can cover different years. Compare balanced_panel_medians.csv before attributing changes to economics.
- Clustering standardizes margin, turnover and multiplier; ROE is excluded as a redundant product. K=2 and selected K are both saved. The healthcare-only run cannot reproduce the assignment's two-sector comparison; that requires both sectors later.
- Spearman correlations, when produced, use one average per company. Correlations involving ROE/components are mechanically linked, not discoveries. There are no p-values or causal claims.
- No qualitative–quantitative correlations are computed yet: they require validated risk-category measurements, publication timing, a prespecified outcome, and company/year-aware inference.
- Research questions rank absolute margin changes and are hypothesis-generating. Item 1A describes potential risks; MD&A and financial notes are needed to investigate realized causes.
- research_questions.json is a saved question list. Automatic integration into AIResearch.py is not implemented; select a question and pass it with --question for now.
