# Industrials workspace

Owner: Partner. Keep sector-specific research notes here. The company CSV in this directory is the authoritative input list.

From the repository root, preview Item 1A analysis:

```sh
python analyze_10k_risks.py --sector industrials --input industrials/results/staged_10k_batch.jsonl
```

After configuring your own API key, add `--execute --limit 1` for one paid request. Outputs default to `industrials/results/10k_risk_analysis.jsonl`; `results/` is ignored by Git. The input file must first be created by collecting filings and supplying verified metadata (see the root README). The script filters input records against this sector's company list.

Both sectors use the same root-level calculation and API scripts. Homework 4 and helper.py still run the combined two-sector analysis needed for comparative figures and clustering. Do not interpret a combined run as a sector-only run. Edit shared methods together through pull requests; create your own task branches for research notes.
