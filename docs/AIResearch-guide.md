# AIResearch.py: purposeful SEC research

## Research goal

Default question: **Which disclosed risks are relevant to changes in profit margin, asset turnover, and leverage, and what does the evidence suggest about the sustainability of shareholder returns?**

This is a source-grounded research workbook, not an automated stock recommendation. The program computes financial changes in Python, gives the AI those values and original Item 1A excerpts, and asks for evidence, possible financial mechanisms, investor relevance, alternative hypotheses, limitations, and targeted follow-up questions. It does not claim that risk disclosure proves the cause of a financial outcome.

It accepts BOTH healthcare and industrials. Each `--run-dir` must contain `staged_10k_batch.jsonl` and `financials.csv` from the same HealthcareStats run. Sector/company/fiscal-year identify a join; accession and filing date must also agree. Filings without usable matching financials are explicitly excluded from combined analysis, not silently given invented values. Prefer complete, corrected runs. Identical repeated inputs are deduplicated; conflicting duplicates stop the run.

## Installation and dry run

From your repository root, using the selected Python environment:

```powershell
python -m pip install -r requirements-openai.txt
python AIResearch.py --run-dir "healthcare/results/research/HEALTHCARE_RUN" --run-dir "industrials/results/research/INDUSTRIALS_RUN"
```

Replace the two placeholder run folders with actual paths. You can start with only healthcare, then add industrials when your partner's data is available. Dry runs use only Python's standard library and do not need a key or the API packages. Play without arguments shows usage; this script needs explicit input directories to avoid choosing an old or incomplete run automatically.

Outputs default to `results/ai_research/`, which Git ignores. Share source code through GitHub; arrange separate sharing/backups for generated data. Use `--output` for a separate experiment.

- `plan.json`: research question, selected model, input paths, exclusions, remaining chunks, and maximum requests this run.
- `research_workbook.md`: completion counts by company-year; after execution, findings, numeric evidence, SEC links, quotations, investor relevance, rival hypotheses, and research questions.
- `analyses.jsonl`: validated structured results, question, prompt version, timestamps, model, and token usage.
- `responses.jsonl`: raw paid responses including unsuccessful local validations, for inspection before retrying.

## Live execution and cost control

Create a replacement key if one was previously exposed. Set `OPENAI_API_KEY` securely in your process environment or secret manager; never paste it into code, GitHub, or chat. The script does not automatically read `.env` files.

Run one request first:

```powershell
python AIResearch.py --run-dir "healthcare/results/research/HEALTHCARE_RUN" --max-requests 1 --execute
```

To continue both sectors:

```powershell
python AIResearch.py --run-dir "healthcare/results/research/HEALTHCARE_RUN" --run-dir "industrials/results/research/INDUSTRIALS_RUN" --max-requests 3 --execute
```

Successful work is reused when you keep the same output folder. Hashes include the question, model, prompt instructions, metadata, financial evidence, and excerpt. Changing any of them creates new work and potential charges. Changes to a prior-year financial row also invalidate affected tasks. Files are divided into 24,000-character excerpts with 800-character overlap; no end-of-filing truncation. This is a conservative context choice, not the minimum possible request count. The six-year Pfizer sample requires 23 requests to finish, not three. Increasing `--max-requests` changes only the allowed new requests per invocation.

The default model is `gpt-4.1-mini`; override with `--model`. Verify availability and current pricing on OpenAI's official pricing page. Character counts are NOT token counts or exact dollar estimates. Each response is capped at 4,000 output tokens; actual usage is saved after calls. There is no automatic dollar-budget enforcement or retry loop. Review usage after the first response before expanding. SDK retries are disabled. Failed API calls or local quote rejection may still cost money. Successful responses are appended and flushed immediately, but a crash between response receipt and persistence can still cause a repeated call.

The `.running.lock` file prevents concurrent writes to the same output folder. After a crash, confirm the old process is stopped before removing the lock manually. A malformed JSONL file stops execution for repair; the program does not silently discard it. A failed quote check requires reviewing `responses.jsonl` before rerunning; invalid responses are not counted as completed analyses.

## Sources and interpretation

This version uses **the supplied SEC filings only**. It does not browse the internet or retrieve external studies. Each finding must include an exact quotation from the supplied excerpt and precisely the supplied SEC URL; local validation rejects invented quotes and different links. It does not verify every generated sentence or establish causality. Human source checking remains necessary.

The workbook's follow-up questions identify evidence still needed, such as MD&A, revenue notes, segment disclosures, regulatory documents, or peer-reviewed research. Those questions are NOT claims that the AI has read those materials. External literature retrieval can be added as a separate, traceable research stage with saved documents and verified citations.

Chunk coverage is visible. A partly analyzed company is not ready for a complete company conclusion. Repeated quotes with the same component are suppressed in the displayed workbook, but semantically similar claims can remain. Chunk findings are not independent observations. Do not treat the number of generated findings as risk intensity, prevalence, severity, or a sample size. Sector synthesis is a later reviewed step; this script does not infer sector superiority from partial data.

The default question supports presentation case studies. You can choose a narrower question:

```powershell
python AIResearch.py --run-dir "healthcare/results/research/HEALTHCARE_RUN" --question "How could disclosed reimbursement and pricing pressures affect profit margins, and what additional evidence would distinguish these risks from realized causes?"
```

Keep the same question for both sectors when comparing coding. Company-year changes are retrospective; Item 1A is generally filed after the year it describes. Do not mistake this for an out-of-sample forecasting study. Follow the HealthcareStats methods guide for any subsequent panel modeling and multiple-testing decisions.

## Validation

Local tests cover text preservation across chunks, year-over-year calculations, provenance mismatch, cache identity, quote/source rejection, and partial coverage reporting. The existing HealthcareStats tests also pass. A dry run on six real Pfizer records generated a 23-chunk plan. Live OpenAI authentication, model access, output quality, and billing have NOT been tested, and no paid requests were made while implementing this feature.
