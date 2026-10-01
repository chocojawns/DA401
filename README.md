# DA401

DuPont ROE analysis of healthcare and industrial companies, with an Item 1A risk-factor research extension.

## Project files

- `homeWork4AndyJohnson.py`: financial analysis for 2020–2025, tables, graphs, outliers, and clustering.
- `helper.py`: extended financial analysis and Item 1A collection. This is an executable script, not a safe-to-import utility module.
- `health_care_ciks.csv`, `industrials_ciks.csv`: company lists; keep beside the main scripts.
- `docs/Homework #4 Document.pdf`: assignment reference.
- `examples/`: supplied Item 1A, Gemini, and merged-analysis examples; not a connected, validated pipeline.

The AI provider has not been selected. No AI requests are needed to collaborate on this repository.

## Python setup

Use Python 3.11 or 3.12. From the repository folder:

```sh
python -m venv .venv
```

Activate on Windows PowerShell: `.venv\Scripts\Activate.ps1`

Activate on macOS/Linux: `source .venv/bin/activate`

```sh
python -m pip install -r requirements.txt
```

Dependencies are an initial unpinned list inferred from imports, not a tested lockfile.

To run the financial workflow, set `SEC_USER_AGENT` to your project name and real contact email in your terminal, then run:

```sh
python homeWork4AndyJohnson.py
```

This downloads SEC data and may take time. Outputs go to `results/`, with cached responses in `sec_cache/`. These generated folders are excluded from Git. Running `helper.py` also enables Item 1A retrieval by default; set `RUN_ITEM_1A=0` to disable that step. Its downloader uses `SEC_USER_AGENT_NAME` and `SEC_USER_AGENT_EMAIL`.

## Collaborating with any editor

The repository owner must invite the partner under GitHub Settings → Collaborators. After accepting, either person can use GitHub Desktop (Windows/macOS) or Git CLI with their preferred editor.

### GitHub Desktop

1. Clone `chocojawns/DA401` once.
2. Before a new task, switch to `main`, click Fetch origin, then Pull origin if offered.
3. Create a descriptive task branch, such as `andy/financial-charts`.
4. Open the cloned folder in your editor and save changes.
5. Review changes in Desktop, commit, and publish/push the branch.
6. Open a pull request on GitHub, review it together, and merge.
7. Both return to `main` and pull before the next task.

Commit or stash unfinished changes before switching branches. Pulling does not download a partner's unmerged branch. Avoid editing the same file simultaneously where possible; resolve conflicts together and do not force-push shared work.

### Git CLI

```sh
git clone https://github.com/chocojawns/DA401.git
cd DA401
git switch main
git pull --ff-only origin main
git switch -c your-name/task-name
# Edit and review your changes.
git add path/to/changed-file.py
git commit -m "Describe the change"
git push -u origin your-name/task-name
```

Open and merge a pull request on GitHub, then switch to `main` and pull again. Clone only once per computer.

## Research and validation status

Uploaded Python files included here passed syntax parsing. Financial results, SEC retrieval, dependency installation, and live AI requests have not been validated for this initial upload.

Before using the examples for research:

- Match financial years to actual filing metadata; the standalone collector currently ignores its year argument.
- Reject failed Item 1A extraction instead of treating the beginning of a filing as risk factors.
- Align staging filenames and include the year field required by the AI example.
- Address the AI example's 15,000-character truncation and define evidence-based classification criteria.
- Verify model availability and replace the example's local `gemini_api_key` dependency with secure configuration if Gemini is selected.
- Include sector in combined sector benchmarks and review financial metric definitions.

The examples execute work at module level. Do not import or run them casually: the collector downloads filings and the Gemini example can make billable requests once configured. The merged-analysis example expects a `merged_risk_data.csv` file that is not supplied.

Never commit API keys, `.env` files, or credential modules. Keep reproducible source evidence and distinguish AI judgments from established financial facts.
