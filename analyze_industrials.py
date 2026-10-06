import os
import json
import time
from openai import OpenAI
import os

os.environ["OPENAI_API_KEY"] = "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"

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    default_headers={"Accept-Encoding": "gzip, deflate"}
)

# ---------------------------------------------------------
# SETTINGS
INPUT_FILE = "full_industrials_batch.jsonl"
OUTPUT_FILE = "industrials_analysis.jsonl"
MODEL_NAME = "gpt-4o-mini"   # change this to whichever OpenAI model you want to use
MAX_1A_CHARACTERS = 150000        # cut very long Item 1A text so the request stays a safe size
SECONDS_BETWEEN_CALLS = 1         # small pause to avoid rate limit errors



# ---------------------------------------------------------
# 1. LOAD DATA

def load_records(file_name):
    """Reads the JSONL file (one JSON record per line) into a list of dictionaries."""
    records = []
    with open(file_name, "r", encoding="utf-8") as inFile:
        for line in inFile:
            line = line.strip()
            if line == "":
                continue
            records.append(json.loads(line))
    return records


def load_finished_accessions(file_name):
    """
    Returns the accession numbers already analyzed, so if the script stops
    halfway you can run it again and it picks up where it left off.
    """
    finished = []
    if not os.path.exists(file_name):
        return finished

    with open(file_name, "r", encoding="utf-8") as inFile:
        for line in inFile:
            line = line.strip()
            if line == "":
                continue
            result = json.loads(line)
            finished.append(result["accession"])
    return finished


# ---------------------------------------------------------
# 2. BUILD THE PROMPT

def format_number(value, decimals):
    """Turns a number into text. Returns 'not available' if the value is None."""
    if value is None:
        return "not available"
    return str(round(value, decimals))


def build_prompt(record):
    item_1a_text = record["item_1a_text"]
    if len(item_1a_text) > MAX_1A_CHARACTERS:
        item_1a_text = item_1a_text[0:MAX_1A_CHARACTERS]

    if item_1a_text == "":
        item_1a_text = "NOT AVAILABLE (the Item 1A section could not be extracted)"

    prompt = "You are a financial analyst reviewing one 10-K filing.\n\n"
    prompt = prompt + "Company: " + record["company_name"] + " (" + record["ticker"] + ")\n"
    prompt = prompt + "Fiscal year: " + str(record["fiscal_year"]) + " (ended " + record["fiscal_year_end"] + ")\n\n"

    prompt = prompt + "DuPont inputs from SEC XBRL data:\n"
    prompt = prompt + "Net income: " + format_number(record["net_income"], 0) + "\n"
    prompt = prompt + "Revenue: " + format_number(record["revenue"], 0) + "\n"
    prompt = prompt + "Total assets: " + format_number(record["total_assets"], 0) + "\n"
    prompt = prompt + "Equity: " + format_number(record["equity"], 0) + "\n"
    prompt = prompt + "Profit margin: " + format_number(record["profit_margin"], 4) + "\n"
    prompt = prompt + "Asset turnover: " + format_number(record["asset_turnover"], 4) + "\n"
    prompt = prompt + "Equity multiplier: " + format_number(record["equity_multiplier"], 4) + "\n"
    prompt = prompt + "ROE: " + format_number(record["roe"], 4) + "\n\n"

    prompt = prompt + "Item 1A Risk Factors text:\n" + item_1a_text + "\n\n"

    prompt = prompt + """Return ONLY a JSON object with exactly these keys:
{
  "dupont_analysis": "Which of the three DuPont drivers (margin, turnover, leverage) is driving ROE, and what stands out. If the numbers are not available, say so.",
  "supply_chain_operational_risk": "The main supply chain and operational risks named in Item 1A, and how severe they look.",
  "stakeholder_decision_framework": "How these risks affect customers, suppliers, employees, lenders and shareholders.",
  "recommended_action": "One or two concrete actions management or an investor should take.",
  "statistical_integrity_limitations": "Data problems that limit how much to trust this analysis (missing inputs, extraction problems, one-year snapshot, and so on).",
  "risk_score_1_to_10": 5
}
Use only the information given above. Do not invent numbers."""

    return prompt


# ---------------------------------------------------------
# 3. CALL GEMINI

def analyze_record(record):
    """Sends one record to OpenAI and returns a dictionary with the analysis."""
    prompt = build_prompt(record)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.2
    )

    # OpenAI puts the answer text here
    response_text = response.choices[0].message.content

    # Turn the text into a dictionary. If that fails, keep the raw text.
    try:
        analysis = json.loads(response_text)
    except Exception:
        analysis = {"raw_response": response_text}

    return analysis


# ---------------------------------------------------------
# MAIN

records = load_records(INPUT_FILE)
finished_accessions = load_finished_accessions(OUTPUT_FILE)
print("Loaded", len(records), "records.", len(finished_accessions), "already analyzed.")

# To test first, change this line to: for record in records[:3]:
for record in records:
    if record["accession"] in finished_accessions:
        continue

    try:
        analysis = analyze_record(record)
    except Exception as e:
        print(record["ticker"], record["fiscal_year"], "Gemini call failed:", e)
        continue

    result = {
        "ticker": record["ticker"],
        "company_name": record["company_name"],
        "fiscal_year": record["fiscal_year"],
        "accession": record["accession"],
        "roe": record["roe"],
        "analysis": analysis
    }

    # "a" appends, so each result is saved right away and nothing is lost if the script stops
    with open(OUTPUT_FILE, "a", encoding="utf-8") as outFile:
        outFile.write(json.dumps(result, ensure_ascii=False) + "\n")

    print(record["ticker"], record["fiscal_year"], "done")
    time.sleep(SECONDS_BETWEEN_CALLS)

print("Finished. Results are in", OUTPUT_FILE)