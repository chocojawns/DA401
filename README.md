# DA401

DuPont ROE analysis of healthcare and industrial companies, with an Item 1A risk-factor research extension.

## Project files

- `homeWork4AndyJohnson.py`: financial analysis for 2020–2025, tables, graphs, outliers, and clustering.
- `helper.py`: extended financial analysis and Item 1A collection. This is an executable script, not a safe-to-import utility module.
- `healthcare/health_care_ciks.csv`, `industrials/industrials_ciks.csv`: sector company lists.
- `docs/Homework #4 Document.pdf`: assignment reference.
- `examples/`: supplied Item 1A, Gemini, and merged-analysis examples; not a connected, validated pipeline.

OpenAI is selected for the new draft risk-analysis workflow. The old Gemini files remain reference examples. No AI requests are needed to collaborate on this repository.

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

## New collaborator: start here

Repository: https://github.com/chocojawns/DA401

You can use any editor. Git handles version history and synchronization; GitHub hosts the shared repository. The `main` branch holds the team's merged work. Each person makes changes on a separate task branch, then opens a pull request for review.

**Pull and pull request mean different things:** `git pull` downloads and incorporates updates into your local branch. A **pull request (PR)** asks the team to review and merge your branch into `main`. You do not need a pull request to download the latest code.

### 1. One-time setup on your computer

1. Create/sign into your [GitHub account](https://github.com/).
2. Ask the repository owner to invite your username through **Settings → Collaborators → Add people**, then accept the invitation. Invitations are required for collaborator push access even if the repository is publicly readable.
3. Install [Git](https://git-scm.com/downloads), or use [GitHub Desktop](https://desktop.github.com/) on Windows/macOS (see below).
4. Open a terminal: PowerShell/Git Bash on Windows or Terminal on macOS/Linux. Check installation:

```sh
git --version
```

Set your commit identity once, replacing these sample values with your own. Use your GitHub email or the private noreply address from GitHub **Settings → Emails**:

```sh
git config --global user.name "Your Name"
git config --global user.email "YOUR_GITHUB_EMAIL"
```

These commands label your commits; they do not sign you into GitHub. `--global` applies to all repositories for your computer account. Complete Git's supported browser/credential-manager sign-in when prompted; GitHub account passwords do not work as HTTPS Git passwords. Never put credentials into a repository URL or project file.

In the folder where you want to store the project, run:

```sh
git clone https://github.com/chocojawns/DA401.git
cd DA401
```

- `git clone` downloads the repository and history into a new `DA401` folder, and names the GitHub connection `origin`.
- `cd DA401` moves your terminal into that folder.
- Clone only once per computer. On later visits, open a terminal in the existing folder.

Open the cloned folder in your preferred editor. Follow **Python setup** above when you want to run the analysis.

### 2. “I'm starting a new task and need the latest code”

Run all commands below from inside your local `DA401` folder:

```sh
git status
git switch main
git pull --ff-only origin main
git switch -c your-name/task-name
```

Replace `your-name/task-name` with a new, descriptive name, such as `andy/update-graphs` or `sam/risk-extraction`. Do not use spaces.

| Command | What it means |
| --- | --- |
| `git status` | Shows your current branch and any uncommitted changes. |
| `git switch main` | Changes to the shared main branch on your computer. |
| `git pull --ff-only origin main` | Fetches GitHub's main and updates your local main when it can do so without creating a merge commit. If histories diverge, it stops so you can investigate. |
| `git switch -c your-name/task-name` | Creates and switches to your own branch based on the updated main. |

**Before switching branches, commit unfinished work on its task branch or stash it.** Do not delete changes to get past an error. If continuing an existing task, use `git switch your-name/task-name` without `-c`; that resumes the branch rather than creating another one. Updating `main` does not automatically update an existing task branch; see the troubleshooting section.

### 3. “I've edited and saved my files”

Save files in your editor, then inspect what you changed:

```sh
git status
git diff
```

`git diff` shows changes in tracked files that are not yet staged. New untracked files appear in `git status`; open and inspect them separately. Press `q` to leave the diff viewer if needed.

Stage the files you want included, using their actual paths:

```sh
git add homeWork4AndyJohnson.py README.md
git diff --staged
git commit -m "Explain what changed and why"
```

- `git add` selects the current contents of named files for your next commit. The filenames above are examples; select your own changed files.
- `git diff --staged` lets you review exactly what will be committed.
- `git commit -m` saves a local version-history checkpoint with your description. It does not upload anything.

You can use `git add .` to stage all non-ignored changes in the current folder, including deletions, but review them first. Never commit API keys, credentials, or private local files. Run the relevant analysis/checks for your change and describe the results in the pull request. The project's full workflow is still being validated; do not claim an unrun check passed.

### 4. “Upload my revisions to GitHub”

From your task branch:

```sh
git push -u origin HEAD
```

`git push` uploads your commits. `origin` is this GitHub repository, `HEAD` means your current branch, and `-u` remembers its remote tracking branch. Check `git status` first to make sure you are on your task branch.

For more changes on the same branch, save, stage, commit, and then run:

```sh
git push
```

### 5. Review and merge the changes

1. Open [DA401 on GitHub](https://github.com/chocojawns/DA401).
2. Click **Compare & pull request** for your branch. If the banner is absent, use **Pull requests → New pull request**.
3. Choose **base: main** and **compare: your task branch**.
4. Describe what changed, why, and what you tested. Review the **Files changed** tab.
5. Create the pull request and ask your partner to review it. Additional commits pushed to the same branch update that PR automatically.
6. Resolve any comments/conflicts. When agreed and GitHub permits it, click **Merge pull request** and confirm.

A push makes your branch available on GitHub. The changes become part of shared `main` after the pull request is merged. Pulling `main` before the merge will not include them.

### 6. “The PR is merged; get both computers up to date”

Each collaborator, with their own unfinished work saved, runs:

```sh
git switch main
git pull --ff-only origin main
```

For the next task, create a fresh branch from this updated `main`. Keep old branches until you know all their work was merged.

### Common situations

- **“Not a git repository”**: your terminal is outside the cloned folder. Navigate to your actual `DA401` folder with `cd`.
- **“Branch already exists”**: use `git switch branch-name` to resume it, or choose a different name for a new task.
- **Push rejected / permission denied**: check the account you signed into and that you accepted the collaborator invitation. Do not force-push to bypass the error.
- **Main changed while you worked**: commit your task changes, then run `git fetch origin` followed by `git merge origin/main` while on your task branch. Fetch updates your knowledge of GitHub without changing your working files; merge brings the latest main into your task branch. Review, test, and push the result.
- **Merge conflicts**: run `git status`, open the listed files, and work with your partner to choose the correct combined content. Remove conflict markers, `git add` the resolved files, and `git commit`. If unsure, `git merge --abort` cancels an in-progress merge; ask your partner before trying again. Do not blindly choose one side or use `git reset --hard`.
- **Need to switch with unfinished edits**: prefer a commit on your task branch. Alternatively, `git stash push -u -m "Work in progress"` temporarily stores tracked and untracked changes locally (not ignored files). Return to the original branch and use `git stash pop` to restore them; restoration can require conflict resolution. A stash is not a GitHub backup.

Coordinate who is editing which files. Separate branches protect the review process but cannot prevent conflicts when both people edit the same lines.

### GitHub Desktop alternative (any editor)

1. Sign into GitHub Desktop and accept the repository invitation on GitHub.
2. Use **File → Clone repository** and select `chocojawns/DA401`.
3. Before a new task, select **main**, click **Fetch origin**, then **Pull origin** if offered.
4. Create a new task branch using **Current Branch → New Branch**.
5. Open the cloned folder in your preferred editor and save your changes.
6. Review the changed files in Desktop, select what to include, enter a summary, and click **Commit to [your branch]**.
7. Click **Publish branch** the first time or **Push origin** afterward.
8. Open a pull request on GitHub and follow the review/merge steps above.
9. After merging, return to **main**, fetch, and pull on both computers.

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

## Sector responsibilities and OpenAI draft

- **Andy:** [healthcare workspace](healthcare/README.md).
- **Partner:** [industrials workspace](industrials/README.md).
- **Shared methods:** root-level `homeWork4AndyJohnson.py`, `helper.py`, and `analyze_10k_risks.py`. Company CSV paths have been updated in both financial scripts. The financial scripts continue to analyze both sectors together for cross-sector comparisons; the new API script processes one sector per run.

### Input metadata

`analyze_10k_risks.py` reads UTF-8 JSONL (one object per line). Each record requires `ticker`, `company_name`, `fiscal_year`, `filing_date` (YYYY-MM-DD), `source_url`, and full `item_1a_text`. Include `accession_number` when available. Filing date and fiscal year must come from the actual SEC filing metadata; never infer fiscal year from filing date. Older collectors need their metadata adapted before this script can consume their output. This script does not download filings or calculate financial ratios.

### Run the draft

```sh
python -m pip install -r requirements-openai.txt
python analyze_10k_risks.py --sector healthcare --input healthcare/results/staged_10k_batch.jsonl
```

The first run is a preview and makes no API requests. Replace `healthcare` with `industrials` for the other sector. Both dry runs and live runs validate record dates and length, filter tickers against the sector CSV, and skip completed identical inputs. The default is one new filing; `--limit 5` selects at most five. Records outside the chosen sector are reported and skipped.

Set a newly generated key in `OPENAI_API_KEY` using your local environment or secret manager. Do not paste keys into scripts, GitHub, or chat. `.env` files are ignored, but this script does not automatically load them. No key is included in this repository.

```sh
python analyze_10k_risks.py --sector healthcare --input healthcare/results/staged_10k_batch.jsonl --limit 1 --execute
```

`--execute` authorizes billable API requests. `--model` overrides the draft default `gpt-4.1-mini`; verify model availability and current pricing first. Results are appended after each success to the sector's `results/10k_risk_analysis.jsonl`, including source dates/URL, model, prompt version, UTC analysis timestamp, structured risks, exact supporting quotations, and token usage. The analysis ID hashes the entire input, model, and prompt version. Changing any of these triggers new work.

The script has no automatic retries and stops on errors. A request that fails validation may still cost money. Do not run two processes writing the same output file. A crash after an API response but before saving can cause a repeated request on rerun. Review saved results before restarting. Keep local output backups: ignored results are not uploaded by Git.

Texts outside 500–100,000 characters are rejected rather than truncated. Character length is only a guard, not a token estimate or proof of correct Item 1A extraction. Exact-quote checks do not prove the interpretation is valid; manually review results. Severity probabilities and buy/sell recommendations are deliberately absent. This is a starting draft, not a validated investment model.

Validation for this update: offline dry-run filtering, metadata rejection, and resume behavior checked. No paid API calls or full SEC/financial runs performed.

## New stage 1 program: HealthcareStats.py

Start with [HealthcareStats.py](HealthcareStats.py) for the new healthcare-only-by-default SEC/DuPont/Item 1A workflow. It creates auditable financial tables, dated Item 1A JSONL, coverage reports, and simple line/bar charts. It uses average balance-sheet denominators, unlike the legacy ending-balance scripts. It makes no OpenAI calls; that stage is deferred until these outputs are verified.

Read the [methods, commands, limitations, and statistical research plan](docs/HealthcareStats-methods.md) before running or interpreting results. Offline synthetic tests pass; live SEC validation is pending network access. Do not describe this draft as validated on real company data yet.

### Windows: Beautiful Soup import or pip access-denied errors

If `from bs4 import BeautifulSoup` fails and pip reports `WinError 5` in the old environment's `beautifulsoup4-*.dist-info`, use a fresh virtual environment outside OneDrive. The traceback establishes a local package-access problem, not its exact cause. Leave the existing environment and project files intact. The package to install is `beautifulsoup4`; its Python import name is `bs4`.

In PowerShell from your DA401 checkout (stop if any command fails):

```powershell
py -3 -m venv "$env:LOCALAPPDATA\DA401\healthcare-venv"
& "$env:LOCALAPPDATA\DA401\healthcare-venv\Scripts\python.exe" -m pip install --upgrade pip
& "$env:LOCALAPPDATA\DA401\healthcare-venv\Scripts\python.exe" -m pip install -r requirements.txt
& "$env:LOCALAPPDATA\DA401\healthcare-venv\Scripts\python.exe" -c "from bs4 import BeautifulSoup; print('Beautiful Soup works')"
```

If `py` is unavailable, use your installed base Python executable to create the environment. In VS Code, use **Python: Select Interpreter → Enter interpreter path** and select the new environment's `Scripts\python.exe` under the directory printed by `$env:LOCALAPPDATA`. Open a new terminal afterward. You do not need to run VS Code as administrator or change file permissions.
