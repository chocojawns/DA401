import os
import re
import glob
import time
import json
import requests
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from sec_edgar_downloader import Downloader

# Read the CSV. dtype=str keeps the leading zeros in the CIK (the API needs 10 digits)
companies = pd.read_csv('industrials_ciks.csv', dtype={'CIK_Padded': str})

# SEC EDGAR requires a User-Agent that identifies you
USER_AGENT_NAME = "Analytics Class Project"
USER_AGENT_EMAIL = "test@andersonuniversity.edu"
DOWNLOAD_DIR = "sec_edgar_downloads"
OUTPUT_FILE = "full_industrials_batch.jsonl"

# Fiscal years we want
FIRST_YEAR = 2020
LAST_YEAR = 2025

dl = Downloader(USER_AGENT_NAME, USER_AGENT_EMAIL, DOWNLOAD_DIR)
api_headers = {"User-Agent": USER_AGENT_NAME + " " + USER_AGENT_EMAIL}

# XBRL tag names for the DuPont inputs.
# Companies label revenue differently, so we try several names in order.
REVENUE_TAGS = [
    "Revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "SalesRevenueNet"
]
NET_INCOME_TAG = "NetIncomeLoss"
ASSETS_TAG = "Assets"
EQUITY_TAG = "StockholdersEquity"


# --------------------------------------------
# 1. ITEM 1A PARSING

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

    # findall returns every match (the table of contents entry AND the real section)
    all_matches = pattern.findall(normalized_text)

    # Keep the longest match; the table of contents entry is short
    longest_match = ""
    for match_text in all_matches:
        if len(match_text) > len(longest_match):
            longest_match = match_text

    if len(longest_match) > 500:
        return longest_match.strip()

    # Real Item 1A section was not found
    return ""


def find_main_html_file(filing_folder: str) -> str:
    """
    Returns the path of the biggest .html file in the filing folder
    (the main 10-K document is always the biggest one). Returns "" if none.
    """
    html_files = glob.glob(os.path.join(filing_folder, "*.html"))

    biggest_file = ""
    biggest_size = 0
    for html_file in html_files:
        file_size = os.path.getsize(html_file)
        if file_size > biggest_size:
            biggest_size = file_size
            biggest_file = html_file

    return biggest_file


def get_period_end_date(filing_folder: str) -> str:
    """
    Reads the SEC header at the top of full-submission.txt and returns the
    fiscal year end date like "2023-12-31". Returns "" if not found.
    """
    submission_path = os.path.join(filing_folder, "full-submission.txt")
    if not os.path.exists(submission_path):
        return ""

    with open(submission_path, "r", encoding="utf-8", errors="ignore") as inFile:
        header_text = inFile.read(5000)

    match = re.search(r"CONFORMED PERIOD OF REPORT:\s+(\d{8})", header_text)
    if not match:
        return ""

    period = match.group(1)
    end_date = period[0:4] + "-" + period[4:6] + "-" + period[6:8]
    return end_date


# --------------------------------------------
# 2. DUPONT DATA FROM SEC XBRL API

def get_annual_values(us_gaap, tag, is_duration):
    """
    Returns a dictionary like {"2023-12-31": 1234000000, ...} holding one
    full-year value per fiscal year end date for the given tag.
    is_duration is True for income statement items (cover a period of time)
    and False for balance sheet items (a single point in time).
    """
    annual_values = {}
    filed_dates = {}

    if tag not in us_gaap:
        return annual_values

    units = us_gaap[tag]["units"]
    if "USD" not in units:
        return annual_values

    for fact in units["USD"]:
        # Only keep numbers from a 10-K, for a full fiscal year
        if fact.get("form") != "10-K":
            continue
        if fact.get("fp") != "FY":
            continue

        # Income statement items: the period must be about a year long
        if is_duration:
            if "start" not in fact:
                continue
            start_date = datetime.strptime(fact["start"], "%Y-%m-%d")
            end_date_object = datetime.strptime(fact["end"], "%Y-%m-%d")
            number_of_days = (end_date_object - start_date).days
            if number_of_days < 300:
                continue

        end_date = fact["end"]
        filed_date = fact["filed"]

        # Same year can appear in several filings; keep the most recently filed value
        if end_date not in annual_values:
            annual_values[end_date] = fact["val"]
            filed_dates[end_date] = filed_date
        elif filed_date > filed_dates[end_date]:
            annual_values[end_date] = fact["val"]
            filed_dates[end_date] = filed_date

    return annual_values


def get_revenue_values(us_gaap):
    """
    Tries each revenue tag in order. A later tag only fills in
    years that the earlier tags did not have.
    """
    revenue_values = {}

    for tag in REVENUE_TAGS:
        tag_values = get_annual_values(us_gaap, tag, True)
        for end_date in tag_values:
            if end_date not in revenue_values:
                revenue_values[end_date] = tag_values[end_date]

    return revenue_values


def build_dupont_by_year(us_gaap):
    """
    Returns a dictionary: fiscal year end date -> dictionary of DuPont numbers.
    """
    dupont_by_end = {}

    net_income_values = get_annual_values(us_gaap, NET_INCOME_TAG, True)
    revenue_values = get_revenue_values(us_gaap)
    assets_values = get_annual_values(us_gaap, ASSETS_TAG, False)
    equity_values = get_annual_values(us_gaap, EQUITY_TAG, False)

    for end_date in net_income_values:
        if end_date not in revenue_values:
            continue
        if end_date not in assets_values:
            continue
        if end_date not in equity_values:
            continue

        net_income = net_income_values[end_date]
        revenue = revenue_values[end_date]
        total_assets = assets_values[end_date]
        equity = equity_values[end_date]

        # Skip years that would divide by zero or have negative equity
        if revenue == 0 or total_assets == 0 or equity <= 0:
            continue

        # DuPont: ROE = Profit Margin x Asset Turnover x Equity Multiplier
        profit_margin = net_income / revenue
        asset_turnover = revenue / total_assets
        equity_multiplier = total_assets / equity

        dupont_by_end[end_date] = {
            "net_income": net_income,
            "revenue": revenue,
            "total_assets": total_assets,
            "equity": equity,
            "profit_margin": profit_margin,
            "asset_turnover": asset_turnover,
            "equity_multiplier": equity_multiplier,
            "roe": profit_margin * asset_turnover * equity_multiplier
        }

    return dupont_by_end


# --------------------------------------------
# 3. BUILD ONE RECORD PER TICKER PER FISCAL YEAR

def build_records_for_ticker(ticker: str, cik_padded: str) -> list:
    records = []

    # ---- DuPont data and company name from the XBRL API ----
    company_name = ticker
    dupont_by_end = {}

    url = "https://data.sec.gov/api/xbrl/companyfacts/CIK" + cik_padded + ".json"
    response = requests.get(url, headers=api_headers)

    if response.status_code == 200:
        company_data = response.json()
        company_name = company_data.get("entityName", ticker)
        if "us-gaap" in company_data["facts"]:
            dupont_by_end = build_dupont_by_year(company_data["facts"]["us-gaap"])
    else:
        print(ticker, "XBRL request failed with status", response.status_code)

    # ---- Download every 10-K filed since 2020 ----
    try:
        dl.get("10-K", ticker, after="2020-01-01", before="2026-12-31", download_details=True)
    except Exception as e:
        print("Error downloading 10-Ks for", ticker, ":", e)
        return records

    filing_folders = glob.glob(os.path.join(DOWNLOAD_DIR, "sec-edgar-filings", ticker.upper(), "10-K", "*"))
    filing_folders = sorted(filing_folders)

    for filing_folder in filing_folders:
        accession = os.path.basename(filing_folder)

        # Which fiscal year is this filing for?
        end_date = get_period_end_date(filing_folder)
        if end_date == "":
            print(ticker, accession, "could not read fiscal year end")
            continue

        fiscal_year = int(end_date[0:4])
        if fiscal_year < FIRST_YEAR or fiscal_year > LAST_YEAR:
            continue

        # Item 1A text
        html_path = find_main_html_file(filing_folder)
        item_1a_text = ""
        if html_path == "":
            print(ticker, fiscal_year, "no html file found")
        else:
            item_1a_text = extract_item_1a_from_html(html_path)
            if item_1a_text == "":
                print(ticker, fiscal_year, "Item 1A section not found")

        # Start the record, then add DuPont numbers if we have them for this year
        record = {
            "ticker": ticker,
            "company_name": company_name,
            "fiscal_year": fiscal_year,
            "fiscal_year_end": end_date,
            "accession": accession,
            "item_1a_text": item_1a_text,
            "net_income": None,
            "revenue": None,
            "total_assets": None,
            "equity": None,
            "profit_margin": None,
            "asset_turnover": None,
            "equity_multiplier": None,
            "roe": None
        }

        if end_date in dupont_by_end:
            dupont_numbers = dupont_by_end[end_date]
            for key in dupont_numbers:
                record[key] = dupont_numbers[key]
        else:
            print(ticker, fiscal_year, "no DuPont data for", end_date)

        records.append(record)
        print(ticker, fiscal_year, "1A characters:", len(item_1a_text))

    return records


# --------------------------------------------
# MAIN

all_records = []

# To test first, change this line to: for index in companies.index[:3]:
for index in companies.index:
    ticker = companies.loc[index, "Symbol"]
    cik_padded = companies.loc[index, "CIK_Padded"]

    ticker_records = build_records_for_ticker(ticker, cik_padded)
    for record in ticker_records:
        all_records.append(record)

    time.sleep(0.2)

with open(OUTPUT_FILE, "w", encoding="utf-8") as outFile:
    for record in all_records:
        outFile.write(json.dumps(record, ensure_ascii=False) + "\n")

print("Saved", len(all_records), "records to", OUTPUT_FILE)