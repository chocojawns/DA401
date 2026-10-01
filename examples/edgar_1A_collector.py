import os
import re
import glob
import time
from bs4 import BeautifulSoup
from sec_edgar_downloader import Downloader
import json


# SEC EDGAR mandates a User-Agent header in the format: Sample Company Name AdminContact@<sample company domain>.com
USER_AGENT_NAME = "Analytics Class Project"
USER_AGENT_EMAIL = "test@andersonuniversity.edu"
DOWNLOAD_DIR = "sec_edgar_downloads"

dl = Downloader(USER_AGENT_NAME, USER_AGENT_EMAIL, DOWNLOAD_DIR)

# --------------------------------------------
# 1. PARSING ENGINE: EXTRACT ITEM 1A FROM HTML 

def extract_item_1a_from_html(html_path: str) -> str:

    with open(html_path, "r", encoding="utf-8", errors="ignore") as inFile:
        content = inFile.read()

    # Parse HTML and strip script/style tags
    soup = BeautifulSoup(content, "html.parser")
    for elem in soup(["script", "style"]):
        elem.extract()
    
    raw_text = soup.get_text(separator=" ")

    # Normalize whitespace (replace multiple spaces/newlines with a single space)
    normalized_text = re.sub(r"\s+", " ", raw_text)

    # Regex pattern to capture text starting at Item 1A up to Item 1B or Item 2
    pattern = re.compile(
        r"(ITEM\s+1A[\.\:\s\–\-]+RISK\s+FACTORS.*?)(?=ITEM\s+1B|ITEM\s+2|\Z)",
        re.IGNORECASE
    )

    match = pattern.search(normalized_text)

    if match:
        extracted = match.group(1).strip()
        # Ensure we didn't just match the Table of Contents anchor (must be > 500 chars)
        if len(extracted) > 500:
            return extracted

    # Fallback: If regex anchor misses due to non-standard formatting, return top portion of text
    return normalized_text[:30000]

# --------------------------------------------------
# 2. RETRIEVAL WRAPPER: FETCH & PARSE SINGLE TICKER 

def get_item_1a_text(ticker: str, year: int = 2024) -> str:
    try:
        dl.get("10-K", ticker, limit=1)
        
        # Locate the downloaded file
        search_pattern = os.path.join(
            DOWNLOAD_DIR, "sec-edgar-filings", ticker.upper(), "10-K", "*", "*.html"
        )
        files = glob.glob(search_pattern)

        # Not HTML
        if not files:
            search_pattern = os.path.join(
                DOWNLOAD_DIR, "sec-edgar-filings", ticker.upper(), "10-K", "*", "full-submission.txt"
            )
            files = glob.glob(search_pattern)

        if not files:
            print("No 10-K filing files found on disk for", ticker)
            return ""

        # Extract text from the retrieved document
        filepath = files[0]
        item_1a = extract_item_1a_from_html(filepath)
        return item_1a

    except Exception as e:
        print("Error retrieving 10-K for {ticker}:", e)
        return ""

# ---------------------------------------------------
# 3. DYNAMIC BATCH GENERATOR FOR THE GEMINI PIPELINE 

def build_sector_batch(sector_companies: list) -> list:
    filings_batch = []

    for row in sector_companies:
        ticker = row[0]
        company = row[1]
        text_1A = get_item_1a_text(ticker)
        
        if text_1A:
            filings_batch.append((ticker, company, text_1A))
            print(company, '1A text retrieved.')
        else:
            print(company, 'Unable to retrieve 1A text.')

        time.sleep(0.2)

    print('1A text retrieved')
    return filings_batch

def save_batch_to_jsonl(batch: list, output_filepath: str = "staged_10k_batch.jsonl"):
    """
    Saves the fetched 10-K batch to a JSON Lines (.jsonl) staging file.
    Works whether batch entries are tuples or dicts.
    """
    with open(output_filepath, "w", encoding="utf-8") as f:
        for item in batch:
            if isinstance(item, tuple):
                record = {
                    "ticker": item[0],
                    "company_name": item[1],
                    "item_1a_text": item[2]
                }
            else:
                record = item
            
            # Write row as a single line JSON string
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            
    print(f" Successfully staged {len(batch)} records to '{output_filepath}'")
# ------------------------------------------------------
# MAIN

sample_sector = [
    ("AAPL", "Apple Inc."),
    ("CAT", "Caterpillar Inc.")
]

batch = build_sector_batch(sample_sector)
save_batch_to_jsonl(batch)
# for ticker, name, text in batch:
#     print("\n" + "=" * 60)
#     print(f"TICKER: {ticker} | COMPANY: {name}")
#     print(f"TEXT PREVIEW (First 3000 chars):\n{text[:3000]}...")
#     print("=" * 60)