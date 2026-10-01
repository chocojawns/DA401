import os
import time
import csv
from typing import List
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from google.genai import errors
import json
import gemini_api_key


# PYDANTIC SCHEMA DEFINITION CLASSES
class RiskFactor(BaseModel):
    category: str = Field(
        description="Broad category of the risk (e.g., Operational, Regulatory, Market, Financial, Cybersecurity)"
    )
    summary: str = Field(
        description="A concise 1-2 sentence summary of the specific risk factor and its material impact"
    )
    severity: str = Field(
        description="Estimated severity level: High, Medium, or Low"
    )

class SECRiskAnalysis(BaseModel):
    ticker: str = Field(description="Stock ticker symbol")
    company_name: str = Field(description="Official company name")
    filing_year: str = Field(description="Fiscal year")
    primary_risks: List[RiskFactor] = Field(
        description="List of key extracted risk factors from Item 1A"
    )


# AVALIABLE LLM MODELS
MODEL_CASCADE = [
    'gemini-3.5-flash',
    'gemini-3.5-flash-lite',
    'gemini-3.6-flash'
]

# Initialize LLM Client 
client = genai.Client(api_key=gemini_api_key.get_api_key())

# EXTRACT RISK PROFILE USING LLM
def extract_risk_profile(ticker: str, company_name: str, filing_year: str, item_1a_text: str, max_retries: int = 3) -> SECRiskAnalysis:
    truncated_text = item_1a_text[:15000]

    prompt = f"""
    Analyze the following Item 1A Risk Factors excerpt from the 10-K filing for {company_name} ({ticker} {filing_year}).
    Extract the key business, financial, operational, and regulatory risks into the required structured schema.

    Item 1A Excerpt:
    {truncated_text}
    """

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=SECRiskAnalysis,
        temperature=0.0,
    )

    for attempt in range(max_retries):
        for model_name in MODEL_CASCADE:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config
                )
                return response.parsed
            except errors.APIError as e:
                if e.code in [503, 429]:
                    print(f"   {e.code} on {model_name}. Failing over to next cascade model...")
                    continue
                else:
                    raise e
            except Exception as err:
                print(f"   Unexpected error on {model_name}: {err}")
                continue

        # If all models in the cascade fail, back off exponentially
        sleep_time = 8 * (attempt + 1)
        print(f"   All cascade endpoints busy. Backing off for {sleep_time}s (Attempt {attempt + 1}/{max_retries})...")
        time.sleep(sleep_time)

    raise RuntimeError(f"Extraction failed for {ticker}: All model endpoints saturated after {max_retries} attempts.")


# WRITE THE CSV OUTPUT FILE
def append_to_csv(analysis: SECRiskAnalysis, output_csv: str):
    """
    Appends extracted risk records directly to disk after each API success.
    Ensures zero data loss if processing is interrupted.
    """
    file_exists = os.path.exists(output_csv)
    
    with open(output_csv, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        if not file_exists:
            writer.writerow(['Ticker', 'Company Name', 'Filing Year', 'Risk Category', 'Risk Summary', 'Severity'])
            
        for risk in analysis.primary_risks:
            writer.writerow([
                analysis.ticker,
                analysis.company_name,
                analysis.filing_year,
                risk.category,
                risk.summary,
                risk.severity
            ])


# READ JSON TUPLES LIST AND SEND DATA TO LLM
def run_sector_pipeline(filings_batch: list, output_csv: str = "sector_risk_analysis.csv"):
    """
    Processes a list of tuples
    """
    print(f"Starting risk extraction pipeline for {len(filings_batch)} companies...")
    
    successful = 0
    failed = 0
    idx = 1
    for row in filings_batch:
        ticker = row['ticker']
        company_name = row['company_name']
        filing_year = row['filing_year']
        raw_text = row['item_1a_text']
        print(f"[{idx}/{len(filings_batch)}] Processing: {ticker} ({company_name}, {filing_year})...")
        
        try:
            result = extract_risk_profile(ticker, company_name, filing_year, raw_text)
            append_to_csv(result, output_csv)
            successful += 1
            print(f"   Extracted {len(result.primary_risks)} risks -> Saved to CSV.")
        except Exception as err:
            failed += 1
            print(f"   FAILED {ticker}: {err}")
            
        time.sleep(6)
        idx = idx + 1

    print("\n" + "=" * 50)
    print(f"PIPELINE COMPLETE: {successful} Successful | {failed} Failed")
    print("=" * 50)

# READ JSON FILE AND CREATE TUPLE LIST
def load_staged_batch(input_filepath: str = "staged_10k_batch.jsonl") -> list:
    staged_data = []
    with open(input_filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                staged_data.append(json.loads(line))
                
    print(f" Loaded {len(staged_data)} companies from staging file. Ready for LLM processing.")
    return staged_data

sector_batch = load_staged_batch('staged_10k_multiyear_batch.jsonl')
run_sector_pipeline(sector_batch, output_csv="test_sector_risks.csv")