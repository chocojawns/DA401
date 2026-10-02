from pathlib import Path
import os
import json
import time
import html
import re

import pandas as pd
import requests
import matplotlib

# Save charts without Tk windows, avoiding the missing-icon error.
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


# ============================================================
# CONFIGURATION
# ============================================================

USER_AGENT_NAME = os.getenv(
    "SEC_USER_AGENT_NAME",
    "Analytics Class Project"
)

USER_AGENT_EMAIL = os.getenv(
    "SEC_USER_AGENT_EMAIL",
    "a.johnson3@andersonuniversity.edu"
).strip()

HEADERS = {
    "User-Agent": os.getenv(
        "SEC_USER_AGENT",
        f"{USER_AGENT_NAME} {USER_AGENT_EMAIL}"
    )
}

# Reproducible filing cutoff; financial years still end at 2025.
FILED_BY = "2026-09-23"

BASE_DIR = (
    Path(__file__).resolve().parent
    if "__file__" in globals()
    else Path.cwd()
)

OUTPUT_DIR = Path(
    os.getenv("DUPONT_OUTPUT_DIR", str(BASE_DIR / "results"))
)

CACHE_DIR = Path(
    os.getenv("SEC_CACHE", str(BASE_DIR / "sec_cache"))
)

DOWNLOAD_DIR = BASE_DIR / "sec_edgar_downloads"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Item 1A settings:
# True: retrieve risk factors after generating the graphs.
# False: run only the financial analysis and graphs.
RUN_ITEM_1A = os.getenv(
    "RUN_ITEM_1A", "1"
).strip().lower() not in {"0", "false", "no"}

# None means the latest 10-K filed on or before FILED_BY.
# Change to 2024, for example, to select filings submitted in 2024.
# This is FILING year, not necessarily fiscal year.
ITEM_1A_FILING_YEAR = None


# ============================================================
# LOAD COMPANY LISTS
# ============================================================

def load_companies(filename):
    companies = pd.read_csv(BASE_DIR / filename, dtype=str)
    companies.columns = companies.columns.str.strip().str.upper()

    needed = {"SYMBOL", "CIK_PADDED"}

    if not needed <= set(companies.columns):
        raise ValueError(
            f"{filename} needs Symbol and CIK_Padded columns; "
            f"found {list(companies.columns)}"
        )

    if companies[list(needed)].isna().any().any():
        raise ValueError(
            f"{filename} contains a missing ticker or CIK"
        )

    companies["CIK_PADDED"] = (
        companies["CIK_PADDED"].str.strip().str.zfill(10)
    )

    if not companies["CIK_PADDED"].str.fullmatch(r"[0-9]{10}").all():
        raise ValueError(f"{filename} has an invalid CIK")

    return dict(
        zip(
            companies["SYMBOL"].str.strip(),
            companies["CIK_PADDED"]
        )
    )


INDUSTRIAL = load_companies("industrials/industrials_ciks.csv")
HEALTHCARE = load_companies("healthcare/health_care_ciks.csv")

SECTOR_COMPANIES = {
    "Industrial": INDUSTRIAL,
    "Healthcare": HEALTHCARE
}

NET_INCOME_TAGS = ["NetIncomeLoss"]

REVENUE_TAGS = [
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "SalesRevenueNet",
    "Revenues",
    "RevenueFromContractWithCustomerIncludingAssessedTax"
]

ASSETS_TAGS = ["Assets"]
EQUITY_TAGS = ["StockholdersEquity"]

# URI's contract revenue excludes most rental revenue.
# Use its total revenue.
REVENUE_OVERRIDES = {
    "URI": ["Revenues"],
    "PFE": ["Revenues"] + REVENUE_TAGS,
    "LDOS": ["Revenues"] + REVENUE_TAGS,
    "SNA": ["Revenues"] + REVENUE_TAGS,
    "CNC": ["Revenues"] + REVENUE_TAGS,
    "PODD": ["Revenues"] + REVENUE_TAGS
}


# ============================================================
# FINANCIAL DATA RETRIEVAL AND PARSING
# ============================================================

def fetch_company_facts(cik):
    """Download once, then reuse the saved SEC data."""
    cache_file = CACHE_DIR / f"CIK{cik}.json"

    if cache_file.exists():
        try:
            facts = json.loads(
                cache_file.read_text(encoding="utf-8")
            )

            if (
                int(facts.get("cik", -1)) == int(cik)
                and "facts" in facts
            ):
                return facts

        except (ValueError, OSError):
            # Download again if a previous cache write was interrupted.
            pass

    time.sleep(0.2)

    url = (
        "https://data.sec.gov/api/xbrl/companyfacts/"
        f"CIK{cik}.json"
    )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=45
    )

    response.raise_for_status()
    facts = response.json()

    if (
        int(facts.get("cik", -1)) != int(cik)
        or "facts" not in facts
    ):
        raise ValueError(
            "SEC response does not match the requested company"
        )

    cache_file.write_text(
        json.dumps(facts),
        encoding="utf-8"
    )

    return facts


def fiscal_year_labels(facts, ends):
    """Map period ends to fiscal labels rather than filing FY."""
    balances = pd.DataFrame(
        facts["facts"]["us-gaap"]["Assets"]["units"]["USD"]
    )

    annual = balances[
        balances["form"].isin(["10-K", "10-K/A"])
        & (balances["fp"] == "FY")
        & (balances["filed"] <= FILED_BY)
    ].copy()

    annual = annual[
        annual["end"]
        == annual.groupby("accn")["end"].transform("max")
    ]

    # Correct three API fiscal labels against original annual filings.
    annual.loc[
        annual["accn"] == "0000773840-22-000018", "fy"
    ] = 2021

    annual.loc[
        annual["accn"] == "0000920148-23-000017", "fy"
    ] = 2022

    annual.loc[
        annual["accn"] == "0001393052-22-000017", "fy"
    ] = 2022

    mapping = (
        annual.sort_values("filed")
        .drop_duplicates("end", keep="last")
        .set_index("end")["fy"]
    )

    labels = ends.map(mapping)

    # Allow early-January endings for 52-week financial years.
    dates = pd.to_datetime(ends)

    fallback = dates.dt.year - (
        (dates.dt.month == 1)
        & (dates.dt.day <= 7)
    ).astype(int)

    return labels.fillna(fallback).astype(int)


def parse_income_metric(facts_json, tag_name):
    """Keep full-year values with their filing and period dates."""
    columns = [
        "fy", "start", "end", "accn", "filed", tag_name
    ]

    units = (
        facts_json.get("facts", {})
        .get("us-gaap", {})
        .get(tag_name, {})
        .get("units", {})
        .get("USD", [])
    )

    df = pd.DataFrame(units)

    required = {
        "fy", "start", "end", "accn",
        "filed", "val", "form", "fp"
    }

    if df.empty or not required <= set(df.columns):
        return pd.DataFrame(columns=columns)

    df = df[
        df["form"].isin(["10-K", "10-K/A"])
        & (df["fp"] == "FY")
        & (df["filed"] <= FILED_BY)
    ].copy()

    days = (
        pd.to_datetime(df["end"])
        - pd.to_datetime(df["start"])
    ).dt.days

    # Full 52/53-week reporting years.
    df = df[(days + 1).between(350, 380)].copy()

    df["fy"] = fiscal_year_labels(facts_json, df["end"])
    df = df[df["fy"].between(2020, 2025)]

    keys = ["fy", "start", "end", "accn"]

    df = df[
        df.groupby(keys)["val"].transform("nunique") == 1
    ]

    return (
        df.drop_duplicates(keys)
        .rename(columns={"val": tag_name})[columns]
    )


def parse_balance_sheet_metric(facts_json, tag_name):
    """Keep year-end balances matched to income-period endings."""
    columns = ["fy", "end", "accn", "filed", tag_name]

    units = (
        facts_json.get("facts", {})
        .get("us-gaap", {})
        .get(tag_name, {})
        .get("units", {})
        .get("USD", [])
    )

    df = pd.DataFrame(units)

    required = {
        "fy", "end", "accn", "filed",
        "val", "form", "fp"
    }

    if df.empty or not required <= set(df.columns):
        return pd.DataFrame(columns=columns)

    df = df[
        df["form"].isin(["10-K", "10-K/A"])
        & (df["fp"] == "FY")
        & (df["filed"] <= FILED_BY)
    ].copy()

    df["fy"] = fiscal_year_labels(facts_json, df["end"])
    df = df[df["fy"].between(2020, 2025)]

    keys = ["fy", "end", "accn"]

    df = df[
        df.groupby(keys)["val"].transform("nunique") == 1
    ]

    return (
        df.drop_duplicates(keys)
        .rename(columns={"val": tag_name})[columns]
    )


def get_combined_metric(facts, tag_list, is_balance_sheet=False):
    """Choose a tag within each filing, preserving source details."""
    parse_fn = (
        parse_balance_sheet_metric
        if is_balance_sheet
        else parse_income_metric
    )

    keys = (
        ["fy", "end", "accn"]
        if is_balance_sheet
        else ["fy", "start", "end", "accn"]
    )

    frames = []

    for tag in tag_list:
        metric = parse_fn(facts, tag).rename(
            columns={tag: "val"}
        )

        metric["tag"] = tag
        frames.append(metric)

    # Subtract noncontrolling interests when a fallback is needed.
    fallback = None

    if tag_list == NET_INCOME_TAGS:
        fallback = (
            "ProfitLoss",
            "NetIncomeLossAttributableToNoncontrollingInterest"
        )

    elif tag_list == EQUITY_TAGS:
        fallback = (
            "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
            "MinorityInterest"
        )

    if fallback:
        total_tag, minority_tag = fallback
        total = parse_fn(facts, total_tag)
        minority = parse_fn(facts, minority_tag)

        if not total.empty and not minority.empty:
            derived = total.merge(
                minority.drop(columns="filed"),
                on=keys
            )

            derived["val"] = (
                derived[total_tag] - derived[minority_tag]
            )

            derived["tag"] = (
                total_tag + " minus " + minority_tag
            )

            frames.append(
                derived[keys + ["filed", "val", "tag"]]
            )

    combined = pd.concat(frames, ignore_index=True)

    # Preserve complete source rows.
    return combined.drop_duplicates(keys)


# ============================================================
# BUILD THE SIX-YEAR FINANCIAL DATASET
# ============================================================

all_results = []
exclusions = []
revenue_checks = []

required_years = set(range(2020, 2026))

for sector, companies in SECTOR_COMPANIES.items():
    for ticker, cik in companies.items():
        try:
            print(
                f"Checking {sector}: {ticker}",
                flush=True
            )

            facts = fetch_company_facts(cik)

            df_net_inc = get_combined_metric(
                facts,
                NET_INCOME_TAGS
            ).rename(
                columns={
                    "val": "Net_Income",
                    "tag": "Income_Tag"
                }
            )

            df_rev = (
                get_combined_metric(
                    facts,
                    REVENUE_OVERRIDES.get(ticker, REVENUE_TAGS)
                )
                .rename(
                    columns={
                        "val": "Revenue",
                        "tag": "Revenue_Tag"
                    }
                )
                .drop(columns="filed")
            )

            df_assets = get_combined_metric(
                facts,
                ASSETS_TAGS,
                is_balance_sheet=True
            ).rename(
                columns={
                    "val": "Total_Assets",
                    "tag": "Assets_Tag"
                }
            )

            df_equity = get_combined_metric(
                facts,
                EQUITY_TAGS,
                is_balance_sheet=True
            ).rename(
                columns={
                    "val": "Total_Equity",
                    "tag": "Equity_Tag"
                }
            )

            frames = [
                df_net_inc,
                df_rev,
                df_assets,
                df_equity
            ]

            if any(frame.empty for frame in frames):
                raise ValueError(
                    "Missing required primary financial concept"
                )

            df_comp = df_net_inc.merge(
                df_rev,
                on=["fy", "start", "end", "accn"],
                how="inner"
            )

            df_comp = df_comp.merge(
                df_assets.drop(columns="filed"),
                on=["fy", "end", "accn"],
                how="inner"
            )

            df_comp = df_comp.merge(
                df_equity.drop(columns="filed"),
                on=["fy", "end", "accn"],
                how="inner"
            )

            df_comp = (
                df_comp.sort_values(
                    ["fy", "end", "filed", "accn"]
                )
                .drop_duplicates("fy", keep="last")
            )

            # Consecutive financial years must not overlap or leave gaps.
            gaps = (
                pd.to_datetime(df_comp["start"])
                - pd.to_datetime(df_comp["end"].shift())
            ).dt.days.dropna()

            if len(df_comp) == 6 and not gaps.eq(1).all():
                raise ValueError(
                    "Annual periods overlap or have a gap; "
                    "review fiscal labels"
                )

            df_comp["Filing_URL"] = df_comp["accn"].map(
                lambda accn: (
                    "https://www.sec.gov/Archives/edgar/data/"
                    f"{int(cik)}/{accn.replace('-', '')}/"
                    f"{accn}-index.html"
                )
            )

            # Save alternative revenue values for review.
            for tag in REVENUE_TAGS:
                candidate = parse_income_metric(facts, tag)

                if candidate.empty:
                    continue

                check = df_comp[
                    [
                        "fy", "start", "end", "accn",
                        "Revenue", "Revenue_Tag"
                    ]
                ].merge(
                    candidate,
                    on=["fy", "start", "end", "accn"]
                )

                check = check[
                    (check[tag] - check["Revenue"]).abs()
                    > check["Revenue"].abs() * 0.000001
                ]

                for _, row in check.iterrows():
                    revenue_checks.append({
                        "Ticker": ticker,
                        "Year": row["fy"],
                        "Selected_Tag": row["Revenue_Tag"],
                        "Selected_Revenue": row["Revenue"],
                        "Other_Tag": tag,
                        "Other_Value": row[tag],
                        "Accession": row["accn"]
                    })

            df_comp["Ticker"] = ticker
            df_comp["Sector"] = sector

            # Three DuPont components.
            df_comp["Net Profit Margin (%)"] = (
                df_comp["Net_Income"] / df_comp["Revenue"]
            ) * 100

            df_comp["Asset Turnover (x)"] = (
                df_comp["Revenue"] / df_comp["Total_Assets"]
            )

            df_comp["Equity Multiplier (x)"] = (
                df_comp["Total_Assets"] / df_comp["Total_Equity"]
            )

            df_comp["ROE (%)"] = (
                (df_comp["Net Profit Margin (%)"] / 100)
                * df_comp["Asset Turnover (x)"]
                * df_comp["Equity Multiplier (x)"]
            ) * 100

            metric_columns = [
                "Net_Income",
                "Revenue",
                "Total_Assets",
                "Total_Equity",
                "Net Profit Margin (%)",
                "Asset Turnover (x)",
                "Equity Multiplier (x)",
                "ROE (%)"
            ]

            has_full_coverage = (
                len(df_comp) == 6
                and set(df_comp["fy"]) == required_years
                and df_comp["fy"].is_unique
            )

            clean_metrics = df_comp[metric_columns].replace(
                [float("inf"), -float("inf")],
                float("nan")
            )

            has_valid_values = (
                clean_metrics.notna().all().all()
            )

            has_valid_denominators = (
                (df_comp["Revenue"] > 0).all()
                and (df_comp["Total_Assets"] > 0).all()
                and (df_comp["Total_Equity"] != 0).all()
            )

            if (
                has_full_coverage
                and has_valid_values
                and has_valid_denominators
            ):
                df_comp["Equity_Warning"] = ""

                df_comp.loc[
                    df_comp["Total_Equity"]
                    / df_comp["Total_Assets"] < 0.01,
                    "Equity_Warning"
                ] = "Equity below 1% of assets"

                df_comp.loc[
                    df_comp["Total_Equity"] < 0,
                    "Equity_Warning"
                ] = "Negative equity"

                all_results.append(df_comp)

            else:
                exclusions.append({
                    "Sector": sector,
                    "Ticker": ticker,
                    "Reason": (
                        "Incomplete matched fiscal years "
                        "or invalid denominators"
                    ),
                    "Years_found": ", ".join(
                        str(int(year))
                        for year in sorted(df_comp["fy"])
                    )
                })

        except Exception as error:
            exclusions.append({
                "Sector": sector,
                "Ticker": ticker,
                "Reason": str(error),
                "Years_found": ""
            })


if not all_results:
    raise RuntimeError(
        "No companies had complete 2020-2025 data. "
        "Check SEC responses."
    )

df_master = pd.concat(all_results, ignore_index=True)

direct_roe = (
    df_master["Net_Income"]
    / df_master["Total_Equity"]
    * 100
)

assert (
    (df_master["ROE (%)"] - direct_roe).abs() < 0.000001
).all()

df_master.to_csv(
    OUTPUT_DIR / "financial_data_and_sources.csv",
    index=False
)

pd.DataFrame(
    exclusions,
    columns=["Sector", "Ticker", "Reason", "Years_found"]
).to_csv(
    OUTPUT_DIR / "excluded_companies.csv",
    index=False
)

pd.DataFrame(
    revenue_checks,
    columns=[
        "Ticker", "Year", "Selected_Tag", "Selected_Revenue",
        "Other_Tag", "Other_Value", "Accession"
    ]
).to_csv(
    OUTPUT_DIR / "revenue_tag_checks.csv",
    index=False
)


# ============================================================
# COMPANY COUNTS AND DISPLAY TABLES
# ============================================================

counts = (
    df_master.groupby("Sector")["Ticker"]
    .nunique()
    .rename("Kept")
    .to_frame()
)

counts["Input"] = pd.Series({
    sector: len(companies)
    for sector, companies in SECTOR_COMPANIES.items()
})

counts["Benchmark"] = pd.Series({
    "Industrial": 58,
    "Healthcare": 45
})

counts["Dropped"] = counts["Input"] - counts["Kept"]
counts["Difference"] = counts["Kept"] - counts["Benchmark"]

counts.to_csv(OUTPUT_DIR / "company_counts.csv")

print("\nCompany counts:\n", counts.to_string())

if counts["Difference"].ne(0).any():
    print(
        "Count note: this extraction differs "
        "from the professor's benchmark."
    )
    print(
        "Investigate and disclose the difference; "
        "do not arbitrarily remove complete companies."
    )

if len(counts) != 2 or (counts["Kept"] < 20).any():
    raise RuntimeError(
        "The assignment needs at least 20 usable "
        "companies in each sector."
    )

cols_to_display = [
    "Sector",
    "Ticker",
    "fy",
    "Net Profit Margin (%)",
    "Asset Turnover (x)",
    "Equity Multiplier (x)",
    "ROE (%)"
]

df_dupont = df_master[cols_to_display].copy()
df_dupont.rename(columns={"fy": "Year"}, inplace=True)

df_dupont = (
    df_dupont.sort_values(["Sector", "Ticker", "Year"])
    .reset_index(drop=True)
)

# Round only displayed results.
ratio_cols = cols_to_display[3:]
df_dupont[ratio_cols] = df_dupont[ratio_cols].round(2)

print("\n=== MULTI-SECTOR DUPONT DATAFRAME (2020-2025) ===")
print(df_dupont.to_string(index=False))

pivot_roe = df_dupont.pivot(
    index=["Sector", "Ticker"],
    columns="Year",
    values="ROE (%)"
)

print("\n=== ROE (%) BY YEAR & SECTOR ===")
print(pivot_roe.to_string())

df_dupont.to_csv(
    OUTPUT_DIR / "dupont_ratios.csv",
    index=False
)


# ============================================================
# GRAPH 1: SECTOR COMPARISON
# ============================================================

cols = [
    "Net Profit Margin (%)",
    "Asset Turnover (x)",
    "Equity Multiplier (x)",
    "ROE (%)"
]

colors = {
    "Industrial": "steelblue",
    "Healthcare": "darkorange"
}

df = df_master[["Sector", "Ticker", "fy"] + cols].copy()

df_sector = df.groupby(["Sector", "fy"])[cols].median()

# Medians describe a typical retained company.
# Multiplying separate sector medians does not reproduce median ROE.
# Add supporting macro sources and interpretation to your report.

plt.ioff()
plt.close("Sector comparison")

fig, axes = plt.subplots(
    2,
    2,
    num="Sector comparison",
    figsize=(12, 8),
    layout="constrained"
)

for col, ax in zip(cols, axes.flat):
    for sector in SECTOR_COMPANIES:
        if sector not in df_sector.index.get_level_values("Sector"):
            continue

        series = df_sector.loc[sector]

        ax.plot(
            series.index,
            series[col],
            marker="o",
            label=sector,
            color=colors[sector]
        )

    ax.set_title(col)
    ax.set_xlabel("Fiscal year label")
    ax.set_xticks(range(2020, 2026))
    ax.grid(alpha=0.25)
    ax.legend()

fig.suptitle(
    "DuPont sector comparison | annual company medians"
)

df_sector.to_csv(OUTPUT_DIR / "sector_medians.csv")


# ============================================================
# COMPANY-LEVEL OUTLIERS AND GRAPHS 2-5
# ============================================================

# One observation per company: its six-year mean.
df_avg = (
    df.groupby(["Sector", "Ticker"])[cols]
    .mean()
    .reset_index()
)

df_scores = df_avg.copy()

for col in cols:
    sector_mean = (
        df_avg.groupby("Sector")[col].transform("mean")
    )

    sector_std = (
        df_avg.groupby("Sector")[col].transform("std")
    )

    df_scores[col + " Z"] = (
        (df_avg[col] - sector_mean)
        / sector_std.replace(0, float("nan"))
    )

df_scores["Triggers"] = df_scores.apply(
    lambda row: "; ".join(
        col for col in cols
        if abs(row[col + " Z"]) > 2
    ),
    axis=1
)

df_outliers = df_scores[
    df_scores["Triggers"] != ""
].copy()

df_avg.to_csv(
    OUTPUT_DIR / "company_averages.csv",
    index=False
)

df_scores.to_csv(
    OUTPUT_DIR / "company_z_scores.csv",
    index=False
)

df_outliers.to_csv(
    OUTPUT_DIR / "company_outliers.csv",
    index=False
)

print(
    "\nCompany outliers:\n",
    df_outliers[
        ["Sector", "Ticker", "Triggers"]
    ].to_string(index=False)
)

for col in cols:
    plt.close(f"All companies - {col}")

    fig, axes = plt.subplots(
        1,
        2,
        num=f"All companies - {col}",
        figsize=(15, 18),
        layout="constrained"
    )

    for ax, sector in zip(axes, SECTOR_COMPANIES):
        companies = df_scores[
            df_scores["Sector"] == sector
        ].sort_values(col)

        y = range(len(companies))
        outlier = companies[col + " Z"].abs() > 2

        dot_colors = [
            "crimson" if flag else colors[sector]
            for flag in outlier
        ]

        ax.scatter(
            companies[col],
            y,
            c=dot_colors,
            s=24
        )

        ax.scatter(
            [],
            [],
            color="crimson",
            label="|Z| > 2 for this metric"
        )

        ax.set_yticks(
            list(y),
            companies["Ticker"],
            fontsize=8
        )

        mean = companies[col].mean()
        sd = companies[col].std()

        ax.axvline(
            mean,
            color="gray",
            linestyle="--",
            label="Sector mean"
        )

        ax.axvline(
            mean - 2 * sd,
            color="gray",
            linestyle=":",
            label="Mean +/- 2 SD"
        )

        ax.axvline(
            mean + 2 * sd,
            color="gray",
            linestyle=":"
        )

        ax.set_title(sector)
        ax.set_xlabel(
            col + " | 2020-2025 company average"
        )
        ax.grid(axis="x", alpha=0.25)
        ax.legend(loc="lower right")

    fig.suptitle(f"All retained companies | {col}")


# ============================================================
# SINGLE-YEAR ANOMALY SCREENING
# ============================================================

df_annual = df_master.copy()
annual_z = []

for col in cols:
    mean = (
        df_annual.groupby("Ticker")[col].transform("mean")
    )

    sd = (
        df_annual.groupby("Ticker")[col].transform("std")
    )

    name = col + " Annual Z"

    df_annual[name] = (
        (df_annual[col] - mean)
        / sd.replace(0, float("nan"))
    )

    annual_z.append(name)

df_annual["Max_Annual_Z"] = (
    df_annual[annual_z].abs().max(axis=1)
)

df_annual["Triggers"] = df_annual.apply(
    lambda row: "; ".join(
        col
        for col, name in zip(cols, annual_z)
        if abs(row[name]) > 1.5
    ),
    axis=1
)

df_anomalies = df_annual[
    df_annual["Max_Annual_Z"] > 1.5
].sort_values(
    "Max_Annual_Z",
    ascending=False
)

df_anomalies.to_csv(
    OUTPUT_DIR / "annual_anomaly_candidates.csv",
    index=False
)

# Six observations provide a short baseline.
# These are research candidates, not proof of abnormal events.
# Company outliers above use 2 SD; this within-company screen uses 1.5 SD.


# ============================================================
# GRAPH 6: COMPANY-YEAR EVENTS
# ============================================================

# These examples need supporting disclosures in the report.
# PFE 2023: lower COVID sales, inventory charges, Paxlovid reversal.
# MRNA 2023: lower COVID demand and resizing/tax charges.
# DAL 2020: pandemic travel disruption and related charges.
# EMR 2023: gain on the Copeland sale.
# MCK FY2021: opioid accrual and negative equity distort ROE.
# VRSK 2023: divestiture and accelerated share repurchases.

events = [
    ("PFE", 2023, cols[0]),
    ("MRNA", 2023, cols[0]),
    ("DAL", 2020, cols[0]),
    ("EMR", 2023, cols[0]),
    ("MCK", 2021, cols[3]),
    ("VRSK", 2023, cols[2])
]

fig, axes = plt.subplots(
    3,
    2,
    num="Company-year events",
    figsize=(13, 10),
    layout="constrained"
)

for ax, (ticker, year, col) in zip(axes.flat, events):
    data = df_master[
        df_master["Ticker"] == ticker
    ].sort_values("fy")

    ax.plot(
        data["fy"],
        data[col],
        marker="o"
    )

    point = data[data["fy"] == year]

    ax.scatter(
        point["fy"],
        point[col],
        color="crimson",
        s=60
    )

    ax.set_title(f"{ticker}: FY{year} | {col}")
    ax.set_xticks(range(2020, 2026))
    ax.grid(alpha=0.25)


# ============================================================
# K = 2 CLUSTERING AND GRAPH 7
# ============================================================

# ROE is the product of the three components.
features = cols[:3]

scaled = StandardScaler().fit_transform(
    df_avg[features]
)

df_clusters = df_avg.copy()

model2 = KMeans(
    n_clusters=2,
    random_state=42,
    n_init=20
)

df_clusters["Cluster_K2"] = model2.fit_predict(scaled)

sector_table = pd.crosstab(
    df_clusters["Cluster_K2"],
    df_clusters["Sector"]
)

sector_table.to_csv(
    OUTPUT_DIR / "k2_sector_comparison.csv"
)

print(
    "\nK = 2 versus sectors:\n",
    sector_table.to_string()
)

fig, axes = plt.subplots(
    1,
    2,
    num="Official sectors versus K=2",
    figsize=(13, 5),
    layout="constrained"
)

for sector in SECTOR_COMPANIES:
    data = df_clusters[
        df_clusters["Sector"] == sector
    ]

    axes[0].scatter(
        data[cols[1]],
        data[cols[0]],
        label=sector,
        color=colors[sector]
    )

for group in sorted(df_clusters["Cluster_K2"].unique()):
    data = df_clusters[
        df_clusters["Cluster_K2"] == group
    ]

    axes[1].scatter(
        data[cols[1]],
        data[cols[0]],
        label=f"Cluster {group}: {len(data)} companies"
    )

for ax in axes:
    ax.set_xlabel(cols[1])
    ax.set_ylabel(cols[0])
    ax.legend()
    ax.grid(alpha=0.25)

axes[0].set_title("Official sector labels")

axes[1].set_title(
    "K=2: two-dimensional view of a three-feature model"
)


# ============================================================
# OPTIMAL K AND CLUSTER PROFILES
# ============================================================

scores = []

for k in range(2, min(10, len(df_avg) - 1) + 1):
    model = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=20
    )

    labels = model.fit_predict(scaled)

    scores.append({
        "K": k,
        "Silhouette": silhouette_score(scaled, labels),
        "Inertia": model.inertia_,
        "Smallest_cluster": (
            pd.Series(labels).value_counts().min()
        )
    })

df_k_scores = pd.DataFrame(scores)

best_k = int(
    df_k_scores.loc[
        df_k_scores["Silhouette"].idxmax(),
        "K"
    ]
)

best_model = KMeans(
    n_clusters=best_k,
    random_state=42,
    n_init=20
)

df_clusters["Cluster_Best"] = (
    best_model.fit_predict(scaled)
)

df_profiles = (
    df_clusters.groupby("Cluster_Best")[cols]
    .agg(["mean", "median"])
)

df_clusters.to_csv(
    OUTPUT_DIR / "cluster_assignments.csv",
    index=False
)

df_profiles.to_csv(
    OUTPUT_DIR / "cluster_profiles.csv"
)

pd.crosstab(
    df_clusters["Cluster_Best"],
    df_clusters["Sector"]
).to_csv(
    OUTPUT_DIR / "best_k_sector_comparison.csv"
)

df_k_scores.to_csv(
    OUTPUT_DIR / "k_scores.csv",
    index=False
)

print("\nK scores:\n", df_k_scores.to_string(index=False))
print(f"\nBest K among the tested values: {best_k}")
print(df_profiles.round(2).to_string())

# A high silhouette can reflect an isolated extreme value.
# Standardization does not remove outliers or negative equity.


# ============================================================
# GRAPH 8: BEST-K FINANCIAL PROFILES
# ============================================================

fig, axes = plt.subplots(
    1,
    3,
    num="Best K financial profiles",
    figsize=(14, 5),
    layout="constrained"
)

for ax, col in zip(axes, features):
    (
        df_clusters.groupby("Cluster_Best")[col]
        .mean()
        .plot.bar(ax=ax)
    )

    ax.set_title(col)
    ax.set_xlabel("Cluster")
    ax.grid(axis="y", alpha=0.25)

fig.suptitle(
    f"K={best_k}: mean financial profile of each cluster"
)


# ============================================================
# GRAPH 9: CHOOSING K
# ============================================================

fig, axes = plt.subplots(
    1,
    2,
    num="Choosing K",
    figsize=(11, 4),
    layout="constrained"
)

axes[0].plot(
    df_k_scores["K"],
    df_k_scores["Silhouette"],
    marker="o"
)
axes[0].set_ylabel("Silhouette score")

axes[1].plot(
    df_k_scores["K"],
    df_k_scores["Inertia"],
    marker="o"
)
axes[1].set_ylabel("Inertia")

for ax in axes:
    ax.set_xlabel("K")
    ax.set_xticks(df_k_scores["K"])
    ax.grid(alpha=0.25)


# ============================================================
# SAVE ALL GRAPHS AND CREATE A BROWSER GALLERY
# ============================================================

GRAPH_DIR = OUTPUT_DIR / "graphs"
GRAPH_DIR.mkdir(parents=True, exist_ok=True)

gallery_cards = []

for number, figure_number in enumerate(
    plt.get_fignums(),
    start=1
):
    chart = plt.figure(figure_number)
    title = chart.get_label() or f"Chart {number}"

    slug = re.sub(
        r"[^a-z0-9]+",
        "_",
        title.lower()
    ).strip("_")

    image_name = f"{number:02d}_{slug}.png"

    chart.savefig(
        GRAPH_DIR / image_name,
        dpi=160,
        bbox_inches="tight",
        facecolor="white"
    )

    gallery_cards.append(
        f"<section><h2>{html.escape(title)}</h2>"
        f'<a href="{image_name}">'
        f'<img src="{image_name}" '
        f'alt="{html.escape(title, quote=True)}" '
        'loading="lazy"></a></section>'
    )

    plt.close(chart)

gallery = GRAPH_DIR / "index.html"

gallery.write_text(
    '<!doctype html><html lang="en"><head>'
    '<meta charset="utf-8">'
    '<meta name="viewport" '
    'content="width=device-width, initial-scale=1">'
    "<title>Homework 4 - DuPont Graphs</title>"
    "<style>"
    "body{font-family:Arial,sans-serif;"
    "margin:32px auto;padding:0 20px;"
    "max-width:1400px;background:#f3f5f8;color:#172334}"
    "section{background:white;padding:20px;"
    "margin:24px 0;border-radius:10px}"
    "img{display:block;width:100%;height:auto}"
    "h2{font-size:22px}"
    "</style></head><body>"
    "<h1>Homework 4: DuPont Analysis, 2020-2025</h1>"
    "<p>Click any graph to open its full-resolution image. "
    "Company comparison plots use six-year averages; "
    "sector trends use annual medians.</p>"
    + "".join(gallery_cards)
    + "</body></html>",
    encoding="utf-8"
)

print(
    f"\nSaved {len(gallery_cards)} graphs to: {GRAPH_DIR}"
)
print(f"Open the graph gallery: {gallery}")


# ============================================================
# ITEM 1A: EXTRACT RISK FACTORS FROM A 10-K
# ============================================================

def extract_item_1a_from_html(html_path: str) -> str:
    """Extract a bounded Risk Factors section."""
    from bs4 import BeautifulSoup

    content = Path(html_path).read_text(
        encoding="utf-8",
        errors="ignore"
    )

    # A full submission may contain exhibits.
    # Parse only its primary 10-K document.
    documents = re.findall(
        r"<DOCUMENT>(.*?)</DOCUMENT>",
        content,
        re.IGNORECASE | re.DOTALL
    )

    if documents:
        primary = next(
            (
                document
                for document in documents
                if re.search(
                    r"<TYPE>\s*10-K\s*(?:\r?\n|<)",
                    document,
                    re.IGNORECASE
                )
            ),
            None
        )

        if primary is None:
            raise ValueError(
                "Submission has no primary 10-K document"
            )

        text_block = re.search(
            r"<TEXT>(.*?)</TEXT>",
            primary,
            re.IGNORECASE | re.DOTALL
        )

        content = (
            text_block.group(1)
            if text_block
            else primary
        )

    soup = BeautifulSoup(content, "html.parser")

    for element in soup(["script", "style", "ix:header"]):
        element.decompose()

    normalized_text = re.sub(
        r"\s+",
        " ",
        soup.get_text(separator=" ")
    ).strip()

    heading_pattern = re.compile(
        r"\bITEM\s*1\s*A\b"
        r"[\s.:\-\u2013\u2014]*"
        r"RISK\s+FACTORS\b",
        re.IGNORECASE
    )

    ending_pattern = re.compile(
        r"\bITEM\s*(?:"
        r"1\s*B\b[\s.:\-\u2013\u2014]*"
        r"UNRESOLVED\s+STAFF\s+COMMENTS"
        r"|1\s*C\b[\s.:\-\u2013\u2014]*CYBERSECURITY"
        r"|2\b[\s.:\-\u2013\u2014]*PROPERTIES"
        r")",
        re.IGNORECASE
    )

    candidates = []
    starts = list(
        heading_pattern.finditer(normalized_text)
    )

    for index, start in enumerate(starts):
        stop = ending_pattern.search(
            normalized_text,
            start.end()
        )

        if stop is None:
            continue

        # Reject TOC matches that span another Item 1A heading.
        if (
            index + 1 < len(starts)
            and starts[index + 1].start() < stop.start()
        ):
            continue

        candidate = normalized_text[
            start.start():stop.start()
        ].strip()

        if len(candidate) > 500:
            candidates.append(candidate)

    if not candidates:
        raise ValueError(
            "No bounded Item 1A section over 500 characters; "
            "manual review needed"
        )

    return max(candidates, key=len)


# ============================================================
# ITEM 1A: SELECT THE FILING DATE WINDOW
# ============================================================

def item_1a_date_window(year=None):
    """Year means filing calendar year, not fiscal year."""
    if year is None:
        return "1994-01-01", FILED_BY

    year = int(year)

    if not 1994 <= year <= int(FILED_BY[:4]):
        raise ValueError(
            f"Filing year must be between 1994 "
            f"and {FILED_BY[:4]}"
        )

    return (
        f"{year}-01-01",
        min(f"{year}-12-31", FILED_BY)
    )


# ============================================================
# ITEM 1A: RETRIEVE ONE COMPANY'S 10-K
# ============================================================

def get_item_1a_text(
    ticker: str,
    year=None,
    *,
    cik=None,
    downloader=None,
    download_dir=None,
    return_record=False
):
    """Download one 10-K and verify its filing date."""
    from sec_edgar_downloader import Downloader

    after, before = item_1a_date_window(year)

    root = (
        Path(download_dir)
        if download_dir is not None
        else DOWNLOAD_DIR / f"{after}_{before}"
    )

    if downloader is None:
        if not USER_AGENT_EMAIL:
            raise ValueError(
                "Set SEC_USER_AGENT_EMAIL to your contact email"
            )

        downloader = Downloader(
            USER_AGENT_NAME,
            USER_AGENT_EMAIL,
            root
        )

    identifier = (
        str(cik).zfill(10)
        if cik is not None
        else ticker.upper()
    )

    downloader.get(
        "10-K",
        identifier,
        limit=1,
        after=after,
        before=before,
        download_details=True,
        include_amends=False
    )

    filing_directory = (
        root
        / "sec-edgar-filings"
        / identifier
        / "10-K"
    )

    candidates = []

    # Read filing dates instead of picking an arbitrary cached file.
    for submission in filing_directory.glob(
        "*/full-submission.txt"
    ):
        header = submission.read_text(
            encoding="utf-8",
            errors="ignore"
        )[:50000]

        filed_match = re.search(
            r"FILED AS OF DATE:\s*(\d{8})",
            header
        )

        if not filed_match:
            continue

        value = filed_match.group(1)

        filed_date = (
            f"{value[:4]}-{value[4:6]}-{value[6:]}"
        )

        if after <= filed_date <= before:
            candidates.append(
                (
                    filed_date,
                    submission.parent.name,
                    submission
                )
            )

    if not candidates:
        raise ValueError(
            f"No verified 10-K for {ticker} filed "
            f"between {after} and {before}"
        )

    filed_date, accession, submission = max(candidates)

    details = submission.parent / "primary-document.html"
    source = details if details.exists() else submission

    try:
        text_1a = extract_item_1a_from_html(str(source))

    except ValueError:
        if source == submission:
            raise

        source = submission
        text_1a = extract_item_1a_from_html(str(source))

    record = {
        "ticker": ticker,
        "item_1a_text": text_1a,
        "filing_date": filed_date,
        "accession": accession,
        "source_file": str(source.resolve())
    }

    if cik is not None:
        record["cik"] = str(cik).zfill(10)

        record["filing_url"] = (
            "https://www.sec.gov/Archives/edgar/data/"
            f"{int(cik)}/{accession.replace('-', '')}/"
            f"{accession}-index.html"
        )

    return record if return_record else text_1a


# ============================================================
# ITEM 1A: BUILD THE SECTOR BATCH
# ============================================================

def build_sector_batch(sector_companies: list, year=None) -> list:
    """Accept metadata dictionaries or (ticker, company) tuples."""
    from sec_edgar_downloader import Downloader

    if not USER_AGENT_EMAIL:
        raise ValueError(
            "Set SEC_USER_AGENT_EMAIL to your contact email"
        )

    after, before = item_1a_date_window(year)
    root = DOWNLOAD_DIR / f"{after}_{before}"

    downloader = Downloader(
        USER_AGENT_NAME,
        USER_AGENT_EMAIL,
        root
    )

    filings_batch = []
    statuses = []

    for row in sector_companies:
        if isinstance(row, dict):
            company = dict(row)
        else:
            company = {
                "ticker": row[0],
                "company_name": row[1]
            }

        ticker = company["ticker"]

        try:
            record = get_item_1a_text(
                ticker,
                year,
                cik=company.get("cik"),
                downloader=downloader,
                download_dir=root,
                return_record=True
            )

            record.update(company)
            filings_batch.append(record)

            statuses.append({
                "ticker": ticker,
                "status": "retrieved",
                "error": ""
            })

            print(
                f"{company['company_name']}: Item 1A retrieved "
                f"({len(record['item_1a_text']):,} characters).",
                flush=True
            )

        except Exception as error:
            statuses.append({
                "ticker": ticker,
                "status": "failed",
                "error": str(error)
            })

            print(
                f"Error retrieving 10-K for {ticker}: {error}",
                flush=True
            )

        time.sleep(0.2)

    pd.DataFrame(
        statuses,
        columns=["ticker", "status", "error"]
    ).to_csv(
        OUTPUT_DIR / "item_1a_retrieval_status.csv",
        index=False
    )

    return filings_batch


# ============================================================
# ITEM 1A: SAVE THE JSONL BATCH
# ============================================================

def save_batch_to_jsonl(batch: list, output_filepath=None):
    """Write one UTF-8 JSON object per company."""
    destination = (
        Path(output_filepath)
        if output_filepath is not None
        else OUTPUT_DIR / "staged_10k_batch.jsonl"
    )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temporary = destination.with_suffix(
        destination.suffix + ".tmp"
    )

    with temporary.open("w", encoding="utf-8") as outfile:
        for item in batch:
            if isinstance(item, tuple):
                record = {
                    "ticker": item[0],
                    "company_name": item[1],
                    "item_1a_text": item[2]
                }
            else:
                record = item

            outfile.write(
                json.dumps(record, ensure_ascii=False) + "\n"
            )

    temporary.replace(destination)

    print(
        f"Successfully staged {len(batch)} records "
        f"to '{destination}'"
    )


# ============================================================
# ITEM 1A: CONNECT TO THE RETAINED DUPONT COMPANIES
# ============================================================

def run_item_1a_pipeline():
    if not RUN_ITEM_1A:
        print("\nItem 1A retrieval is disabled.")
        return

    if not USER_AGENT_EMAIL:
        print(
            "\nItem 1A downloads skipped: "
            "set SEC_USER_AGENT_EMAIL to your contact email."
        )
        return

    try:
        import bs4
        import sec_edgar_downloader

    except ImportError:
        print(
            "\nItem 1A downloads require these packages:\n"
            "python -m pip install "
            "beautifulsoup4 sec-edgar-downloader"
        )
        return

    # An environment setting overrides the configuration at the top.
    year_setting = os.getenv(
        "ITEM_1A_FILING_YEAR",
        ""
    ).strip()

    year = (
        int(year_setting)
        if year_setting
        else ITEM_1A_FILING_YEAR
    )

    # Validate before starting the batch.
    after, before = item_1a_date_window(year)

    print(
        f"\n=== ITEM 1A RETRIEVAL: "
        f"FILINGS FROM {after} THROUGH {before} ==="
    )

    retained_companies = (
        df_master[["Sector", "Ticker"]]
        .drop_duplicates()
    )

    sector_companies = []

    for sector, ticker in retained_companies.itertuples(
        index=False,
        name=None
    ):
        cik = SECTOR_COMPANIES[sector][ticker]

        # The financial-data section already cached company names.
        cache_file = CACHE_DIR / f"CIK{cik}.json"

        cached_facts = json.loads(
            cache_file.read_text(encoding="utf-8")
        )

        sector_companies.append({
            "ticker": ticker,
            "company_name": (
                cached_facts.get("entityName") or ticker
            ),
            "sector": sector,
            "cik": cik
        })

    batch = build_sector_batch(
        sector_companies,
        year=year
    )

    save_batch_to_jsonl(batch)

    print(
        f"\nItem 1A coverage: "
        f"{len(batch)}/{len(sector_companies)} "
        "retained companies."
    )

    print(
        "Review results/item_1a_retrieval_status.csv "
        "for failed extractions."
    )


if __name__ == "__main__":
    run_item_1a_pipeline()