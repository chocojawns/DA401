from pathlib import Path
import os
import json
import time

import pandas as pd
import requests
import matplotlib
# Save charts without Tk windows; this also avoids missing Tk icon errors.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import html
import re

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score



HEADERS = {
    "User-Agent": os.getenv("SEC_USER_AGENT", "Andy Johnson DA401 academic research")
}
FILED_BY = "2026-09-23"  # Reproducible filing cutoff; years still end at 2025.

# CSVs and cache live beside this script. In notebook cells, use the current folder.
BASE_DIR = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
OUTPUT_DIR = Path(os.getenv("DUPONT_OUTPUT_DIR", str(BASE_DIR / "results")))
CACHE_DIR = Path(os.getenv("SEC_CACHE", str(BASE_DIR / "sec_cache")))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def load_companies(filename):
    companies = pd.read_csv(BASE_DIR / filename, dtype=str)
    companies.columns = companies.columns.str.strip().str.upper()
    needed = {"SYMBOL", "CIK_PADDED"}
    if not needed <= set(companies.columns):
        raise ValueError(f"{filename} needs Symbol and CIK_Padded columns; found {list(companies.columns)}")
    if companies[list(needed)].isna().any().any():
        raise ValueError(f"{filename} contains a missing ticker or CIK")
    companies["CIK_PADDED"] = companies["CIK_PADDED"].str.strip().str.zfill(10)
    if not companies["CIK_PADDED"].str.fullmatch(r"[0-9]{10}").all():
        raise ValueError(f"{filename} has an invalid CIK")
    return dict(zip(companies["SYMBOL"].str.strip(), companies["CIK_PADDED"]))

INDUSTRIAL = load_companies("industrials/industrials_ciks.csv")
HEALTHCARE = load_companies("healthcare/health_care_ciks.csv")
SECTOR_COMPANIES = {"Industrial": INDUSTRIAL, "Healthcare": HEALTHCARE}

NET_INCOME_TAGS = ["NetIncomeLoss"]
REVENUE_TAGS = ["RevenueFromContractWithCustomerExcludingAssessedTax",
                "SalesRevenueNet", "Revenues", "RevenueFromContractWithCustomerIncludingAssessedTax"]
ASSETS_TAGS = ["Assets"]
EQUITY_TAGS = ["StockholdersEquity"]
# URI's contract revenue excludes most rental revenue. Use its total revenue.
REVENUE_OVERRIDES = {
    "URI": ["Revenues"],
    "PFE": ["Revenues"] + REVENUE_TAGS,
    "LDOS": ["Revenues"] + REVENUE_TAGS,
    "SNA": ["Revenues"] + REVENUE_TAGS,
    "CNC": ["Revenues"] + REVENUE_TAGS,
    "PODD": ["Revenues"] + REVENUE_TAGS,
}


def fetch_company_facts(cik):
    """Download once, then reuse the saved SEC data."""
    cache_file = CACHE_DIR / f"CIK{cik}.json"
    if cache_file.exists():
        try:
            facts = json.loads(cache_file.read_text(encoding="utf-8"))
            if int(facts.get("cik", -1)) == int(cik) and "facts" in facts:
                return facts
        except (ValueError, OSError):
            pass  # Download again if a previous cache write was interrupted.
    time.sleep(0.2)
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    response = requests.get(url, headers=HEADERS, timeout=45)
    response.raise_for_status()
    facts = response.json()
    if int(facts.get("cik", -1)) != int(cik) or "facts" not in facts:
        raise ValueError("SEC response does not match the requested company")
    cache_file.write_text(json.dumps(facts), encoding="utf-8")
    return facts


def parse_income_metric(facts_json, tag_name):
    """Keep full-year values with their filing and period dates."""
    columns = ["fy", "start", "end", "accn", "filed", tag_name]
    units = facts_json.get("facts", {}).get("us-gaap", {}).get(
        tag_name, {}).get("units", {}).get("USD", [])
    df = pd.DataFrame(units)
    if df.empty or not {"fy", "start", "end", "accn", "filed", "val", "form", "fp"} <= set(df.columns):
        return pd.DataFrame(columns=columns)
    df = df[df["form"].isin(["10-K", "10-K/A"]) & (df["fp"] == "FY") & (df["filed"] <= FILED_BY)].copy()
    days = (pd.to_datetime(df["end"]) - pd.to_datetime(df["start"])).dt.days
    df = df[(days + 1).between(350, 380)].copy()  # Full 52/53-week reporting years.
    df["fy"] = fiscal_year_labels(facts_json, df["end"])
    df = df[df["fy"].between(2020, 2025)]
    keys = ["fy", "start", "end", "accn"]
    df = df[df.groupby(keys)["val"].transform("nunique") == 1]
    return df.drop_duplicates(keys).rename(columns={"val": tag_name})[columns]


def parse_balance_sheet_metric(facts_json, tag_name):
    """Keep year-end balances; the merge matches them to the income period."""
    columns = ["fy", "end", "accn", "filed", tag_name]
    units = facts_json.get("facts", {}).get("us-gaap", {}).get(
        tag_name, {}).get("units", {}).get("USD", [])
    df = pd.DataFrame(units)
    if df.empty or not {"fy", "end", "accn", "filed", "val", "form", "fp"} <= set(df.columns):
        return pd.DataFrame(columns=columns)
    df = df[df["form"].isin(["10-K", "10-K/A"]) & (df["fp"] == "FY") & (df["filed"] <= FILED_BY)].copy()
    df["fy"] = fiscal_year_labels(facts_json, df["end"])
    df = df[df["fy"].between(2020, 2025)]
    keys = ["fy", "end", "accn"]
    df = df[df.groupby(keys)["val"].transform("nunique") == 1]
    return df.drop_duplicates(keys).rename(columns={"val": tag_name})[columns]


def fiscal_year_labels(facts, ends):
    """Map period ends to fiscal labels, rather than a comparative filing's FY."""
    balances = pd.DataFrame(facts["facts"]["us-gaap"]["Assets"]["units"]["USD"])
    annual = balances[balances["form"].isin(["10-K", "10-K/A"]) & (balances["fp"] == "FY") & (balances["filed"] <= FILED_BY)].copy()
    annual = annual[annual["end"] == annual.groupby("accn")["end"].transform("max")]
    # Correct three API fiscal labels against the original annual filings.
    annual.loc[annual["accn"] == "0000773840-22-000018", "fy"] = 2021
    annual.loc[annual["accn"] == "0000920148-23-000017", "fy"] = 2022
    annual.loc[annual["accn"] == "0001393052-22-000017", "fy"] = 2022
    mapping = annual.sort_values("filed").drop_duplicates("end", keep="last").set_index("end")["fy"]
    labels = ends.map(mapping)
    # Missing original filing: use the period end, allowing early-January 52-week years.
    dates = pd.to_datetime(ends)
    fallback = dates.dt.year - ((dates.dt.month == 1) & (dates.dt.day <= 7)).astype(int)
    return labels.fillna(fallback).astype(int)


def get_combined_metric(facts, tag_list, is_balance_sheet=False):
    """Choose a tag within a filing, keeping enough detail to check it."""
    parse_fn = parse_balance_sheet_metric if is_balance_sheet else parse_income_metric
    frames = []
    keys = ["fy", "end", "accn"] if is_balance_sheet else ["fy", "start", "end", "accn"]
    for tag in tag_list:
        metric = parse_fn(facts, tag).rename(columns={tag: "val"})
        metric["tag"] = tag
        frames.append(metric)
    # If needed, subtract noncontrolling interests to keep the parent-company scope.
    fallback = None
    if tag_list == NET_INCOME_TAGS:
        fallback = ("ProfitLoss", "NetIncomeLossAttributableToNoncontrollingInterest")
    elif tag_list == EQUITY_TAGS:
        fallback = ("StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest", "MinorityInterest")
    if fallback:
        total_tag, minority_tag = fallback
        total = parse_fn(facts, total_tag)
        minority = parse_fn(facts, minority_tag)
        if not total.empty and not minority.empty:
            derived = total.merge(minority.drop(columns="filed"), on=keys)
            derived["val"] = derived[total_tag] - derived[minority_tag]
            derived["tag"] = total_tag + " minus " + minority_tag
            frames.append(derived[keys + ["filed", "val", "tag"]])
    combined = pd.concat(frames, ignore_index=True)
    # drop_duplicates keeps an entire source row; groupby.first can mix rows.
    return combined.drop_duplicates(keys)

# Keep only companies with complete annual data for all six years.
all_results = []
exclusions = []
revenue_checks = []
required_years = set(range(2020, 2026))

for sector, companies in SECTOR_COMPANIES.items():
    for ticker, cik in companies.items():
        try:
            print(f"Checking {sector}: {ticker}", flush=True)
            facts = fetch_company_facts(cik)

            df_net_inc = get_combined_metric(facts, NET_INCOME_TAGS).rename(
                columns={"val": "Net_Income", "tag": "Income_Tag"}
            )
            df_rev = get_combined_metric(facts, REVENUE_OVERRIDES.get(ticker, REVENUE_TAGS)).rename(
                columns={"val": "Revenue", "tag": "Revenue_Tag"}
            ).drop(columns="filed")
            df_assets = get_combined_metric(
                facts, ASSETS_TAGS, is_balance_sheet=True
            ).rename(columns={"val": "Total_Assets", "tag": "Assets_Tag"})
            df_equity = get_combined_metric(
                facts, EQUITY_TAGS, is_balance_sheet=True
            ).rename(columns={"val": "Total_Equity", "tag": "Equity_Tag"})

            if any(frame.empty for frame in [df_net_inc, df_rev, df_assets, df_equity]):
                raise ValueError("Missing required primary financial concept")
            df_comp = df_net_inc.merge(df_rev, on=["fy", "start", "end", "accn"], how="inner")
            df_comp = df_comp.merge(df_assets.drop(columns="filed"), on=["fy", "end", "accn"], how="inner")
            df_comp = df_comp.merge(df_equity.drop(columns="filed"), on=["fy", "end", "accn"], how="inner")
            df_comp = df_comp.sort_values(["fy", "end", "filed", "accn"]).drop_duplicates("fy", keep="last")
            # Use the latest matched comparative values available by FILED_BY.
            # Consecutive financial years must not overlap or leave a gap.
            gaps = (pd.to_datetime(df_comp["start"]) - pd.to_datetime(df_comp["end"].shift())).dt.days.dropna()
            if len(df_comp) == 6 and not gaps.eq(1).all():
                raise ValueError("Annual periods overlap or have a gap; review fiscal labels")
            df_comp["Filing_URL"] = df_comp["accn"].map(
                lambda accn: f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accn.replace('-', '')}/{accn}-index.html")

            # Save alternative revenue values for review, without changing the ratios.
            for tag in REVENUE_TAGS:
                candidate = parse_income_metric(facts, tag)
                if candidate.empty:
                    continue
                check = df_comp[["fy", "start", "end", "accn", "Revenue", "Revenue_Tag"]].merge(
                    candidate, on=["fy", "start", "end", "accn"])
                check = check[(check[tag] - check["Revenue"]).abs() > check["Revenue"].abs() * 0.000001]
                for _, row in check.iterrows():
                    revenue_checks.append({"Ticker": ticker, "Year": row["fy"],
                        "Selected_Tag": row["Revenue_Tag"], "Selected_Revenue": row["Revenue"],
                        "Other_Tag": tag, "Other_Value": row[tag], "Accession": row["accn"]})

            # Calculate the three DuPont components and ROE.
            df_comp["Ticker"] = ticker
            df_comp["Sector"] = sector
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
                "Net_Income", "Revenue", "Total_Assets", "Total_Equity",
                "Net Profit Margin (%)", "Asset Turnover (x)",
                "Equity Multiplier (x)", "ROE (%)",
            ]

            # Skip incomplete years, missing/infinite values, or zero denominators.
            has_full_coverage = (
                len(df_comp) == 6
                and set(df_comp["fy"]) == required_years
                and df_comp["fy"].is_unique
            )
            clean_metrics = df_comp[metric_columns].replace(
                [float("inf"), -float("inf")], float("nan")
            )
            has_valid_values = clean_metrics.notna().all().all()
            has_valid_denominators = (
                (df_comp["Revenue"] > 0).all()
                and (df_comp["Total_Assets"] > 0).all()
                and (df_comp["Total_Equity"] != 0).all()
            )

            if has_full_coverage and has_valid_values and has_valid_denominators:
                df_comp["Equity_Warning"] = ""
                df_comp.loc[df_comp["Total_Equity"] / df_comp["Total_Assets"] < 0.01,
                            "Equity_Warning"] = "Equity below 1% of assets"
                df_comp.loc[df_comp["Total_Equity"] < 0, "Equity_Warning"] = "Negative equity"
                all_results.append(df_comp)
            else:
                exclusions.append({"Sector": sector, "Ticker": ticker,
                    "Reason": "Incomplete matched fiscal years or invalid denominators",
                    "Years_found": ", ".join(str(int(y)) for y in sorted(df_comp["fy"]))})

        except Exception as e:
            exclusions.append({"Sector": sector, "Ticker": ticker, "Reason": str(e), "Years_found": ""})

if not all_results:
    raise RuntimeError("No companies had complete 2020–2025 data. Check SEC responses.")

df_master = pd.concat(all_results, ignore_index=True)
direct_roe = df_master["Net_Income"] / df_master["Total_Equity"] * 100
assert ((df_master["ROE (%)"] - direct_roe).abs() < 0.000001).all()
df_master.to_csv(OUTPUT_DIR / "financial_data_and_sources.csv", index=False)
pd.DataFrame(exclusions).to_csv(OUTPUT_DIR / "excluded_companies.csv", index=False)
pd.DataFrame(revenue_checks).to_csv(OUTPUT_DIR / "revenue_tag_checks.csv", index=False)
counts = df_master.groupby("Sector")["Ticker"].nunique().rename("Kept").to_frame()
counts["Input"] = pd.Series({s: len(c) for s, c in SECTOR_COMPANIES.items()})
counts["Benchmark"] = pd.Series({"Industrial": 58, "Healthcare": 45})
counts["Dropped"] = counts["Input"] - counts["Kept"]
counts["Difference"] = counts["Kept"] - counts["Benchmark"]
counts.to_csv(OUTPUT_DIR / "company_counts.csv")
print("\nCompany counts:\n", counts.to_string())
if counts["Difference"].ne(0).any():
    print("Count note: this extraction differs from the professor's benchmark.")
    print("Keep all complete companies; disclose the difference in the presentation.")
if len(counts) != 2 or (counts["Kept"] < 20).any():
    raise RuntimeError("The assignment needs at least 20 usable companies in each sector.")

cols_to_display = [
    "Sector", "Ticker", "fy", "Net Profit Margin (%)",
    "Asset Turnover (x)", "Equity Multiplier (x)", "ROE (%)",
]

df_dupont = df_master[cols_to_display].copy()
df_dupont.rename(columns={"fy": "Year"}, inplace=True)
df_dupont = df_dupont.sort_values(["Sector", "Ticker", "Year"]).reset_index(drop=True)

# Round only the displayed results. Graphs use the unrounded df_master.
ratio_cols = cols_to_display[3:]
df_dupont[ratio_cols] = df_dupont[ratio_cols].round(2)

print("\n=== MULTI-SECTOR DUPONT DATAFRAME (2020-2025) ===")
print(df_dupont.to_string(index=False))

pivot_roe = df_dupont.pivot(
    index=["Sector", "Ticker"], columns="Year", values="ROE (%)"
)
print("\n=== ROE (%) BY YEAR & SECTOR ===")
print(pivot_roe.to_string())



df_dupont.to_csv(OUTPUT_DIR / "dupont_ratios.csv", index=False)
# %% GRAPHS: Run after the original calculations create df_master.
# This section does NOT make another SEC request.
cols = ["Net Profit Margin (%)", "Asset Turnover (x)",
        "Equity Multiplier (x)", "ROE (%)"]
colors = {"Industrial": "steelblue", "Healthcare": "darkorange"}

df = df_master[["Sector", "Ticker", "fy"] + cols].copy()
df_sector = df.groupby(["Sector", "fy"])[cols].median()
# Medians describe a typical retained company, not a sector's aggregate ratio.
# Margin x turnover x multiplier works per row, not across separate medians.
# Finding: industrial turnover and equity multiplier are higher in each year.
# Healthcare margin peaks in 2021; industrial margins exceed it in 2024/2025.
# Pandemic demand shifted differently for airlines and COVID-product makers.
# Inflation/rate increases are context, not a proven cause of these median trends.
# Filing links are in financial_data_and_sources.csv.
# Add supporting macro sources and interpretation to the accompanying report.

# Graph 1: compare the two sector medians over 2020–2025.
plt.ioff()  # Render charts to files without opening GUI windows.
plt.close("Sector comparison")
fig, axes = plt.subplots(2, 2, num="Sector comparison", figsize=(12, 8), layout="constrained")
for col, ax in zip(cols, axes.flat):
    for sector in SECTOR_COMPANIES:
        if sector not in df_sector.index.get_level_values("Sector"):
            continue
        series = df_sector.loc[sector]
        ax.plot(series.index, series[col], marker="o",
                label=sector, color=colors[sector])
    ax.set_title(col)
    ax.set_xlabel("Fiscal year label")
    ax.set_xticks(range(2020, 2026))
    ax.grid(alpha=0.25)
    ax.legend()
fig.suptitle("DuPont sector comparison | annual company medians")
df_sector.to_csv(OUTPUT_DIR / "sector_medians.csv")

# Graphs 2–5: every retained company, for each DuPont measure.
# Each dot is that company's average across the six fiscal years.
df_avg = df.groupby(["Sector", "Ticker"])[cols].mean().reset_index()
df_scores = df_avg.copy()
for col in cols:
    sector_mean = df_avg.groupby("Sector")[col].transform("mean")
    sector_std = df_avg.groupby("Sector")[col].transform("std")
    df_scores[col + " Z"] = (df_avg[col] - sector_mean) / sector_std.replace(0, float("nan"))
z_cols = [col + " Z" for col in cols]
df_scores["Triggers"] = df_scores.apply(
    lambda row: "; ".join(col for col in cols if abs(row[col + " Z"]) > 2), axis=1)
df_outliers = df_scores[df_scores["Triggers"] != ""].copy()
# Each observation is one company's six-year mean; |Z| > 2 is our chosen rule.
# Negative equity can reverse ROE's sign; MCK also widens the sector SD.
df_avg.to_csv(OUTPUT_DIR / "company_averages.csv", index=False)
df_scores.to_csv(OUTPUT_DIR / "company_z_scores.csv", index=False)
df_outliers.to_csv(OUTPUT_DIR / "company_outliers.csv", index=False)
print("\nCompany outliers:\n", df_outliers[["Sector", "Ticker", "Triggers"]].to_string(index=False))
for number, col in enumerate(cols, start=2):
    plt.close(f"All companies - {col}")
    fig, axes = plt.subplots(1, 2, num=f"All companies - {col}",
                            figsize=(15, 18), layout="constrained")
    for ax, sector in zip(axes, SECTOR_COMPANIES):
        companies = df_scores[df_scores["Sector"] == sector].sort_values(col)
        y = range(len(companies))
        outlier = companies[col + " Z"].abs() > 2
        dot_colors = ["crimson" if flag else colors[sector] for flag in outlier]
        ax.scatter(companies[col], y, c=dot_colors, s=24)
        ax.scatter([], [], color="crimson", label="|Z| > 2 for this metric")
        ax.set_yticks(list(y), companies["Ticker"], fontsize=8)
        mean, sd = companies[col].mean(), companies[col].std()
        ax.axvline(mean, color="gray", linestyle="--", label="Sector mean")
        ax.axvline(mean - 2 * sd, color="gray", linestyle=":", label="Mean +/- 2 SD")
        ax.axvline(mean + 2 * sd, color="gray", linestyle=":")
        ax.set_title(sector)
        ax.set_xlabel(col + " | 2020–2025 company average")
        ax.grid(axis="x", alpha=0.25)
        ax.legend(loc="lower right")
    fig.suptitle(f"All retained companies | {col}")
    filename = ["profit_margin", "asset_turnover", "equity_multiplier", "roe"][number - 2]

# %% Single-year anomalies: compare a company with its own six-year history.
df_annual = df_master.copy()
annual_z = []
for col in cols:
    mean = df_annual.groupby("Ticker")[col].transform("mean")
    sd = df_annual.groupby("Ticker")[col].transform("std")
    name = col + " Annual Z"
    df_annual[name] = (df_annual[col] - mean) / sd.replace(0, float("nan"))
    annual_z.append(name)
    
df_annual["Max_Annual_Z"] = df_annual[annual_z].abs().max(axis=1)
df_annual["Triggers"] = df_annual.apply(
    lambda row: "; ".join(col for col, name in zip(cols, annual_z) if abs(row[name]) > 1.5), axis=1)
df_anomalies = df_annual[df_annual["Max_Annual_Z"] > 1.5].sort_values("Max_Annual_Z", ascending=False)
df_anomalies.to_csv(OUTPUT_DIR / "annual_anomaly_candidates.csv", index=False)
# Six observations give a short baseline. These are research candidates, not proof.
# 1.5 SD screens years within a company. Section 4 still uses 2 SD across companies.

# %% SECTION 5: RESEARCHED EVENTS. These examples need disclosure evidence.
# PFE 2023: COVID sales fell; inventory charges and a Paxlovid reversal hurt profit.
# MRNA 2023: lower COVID demand and resizing/tax charges drove a net loss.
# DAL 2020: pandemic travel disruption and impairment/restructuring charges.
# EMR 2023: an $8.4bn after-tax Copeland sale gain boosted total net income.
# MCK FY2021: an $8.1bn pre-tax opioid accrual contributed to the loss.
# MCK's -$4.539bn income / -$21m equity creates +21,614% ROE, not strong profit.
# VRSK 2023: divestiture and accelerated buybacks changed assets and equity.
# These are contributors, not complete causal decompositions.
events = [("PFE", 2023, cols[0]), ("MRNA", 2023, cols[0]),
        ("DAL", 2020, cols[0]), ("EMR", 2023, cols[0]),
        ("MCK", 2021, cols[3]), ("VRSK", 2023, cols[2])]
fig, axes = plt.subplots(3, 2, num="Company-year events", figsize=(13, 10), layout="constrained")
for ax, (ticker, year, col) in zip(axes.flat, events):
    data = df_master[df_master["Ticker"] == ticker].sort_values("fy")
    ax.plot(data["fy"], data[col], marker="o")
    point = data[data["fy"] == year]
    ax.scatter(point["fy"], point[col], color="crimson", s=60)
    ax.set_title(f"{ticker}: FY{year} | {col}")
    ax.set_xticks(range(2020, 2026))
    ax.grid(alpha=.25)

# %% Clustering: one row per company, using the three DuPont components.
features = cols[:3]  # ROE is the product of these components.
scaled = StandardScaler().fit_transform(df_avg[features])
df_clusters = df_avg.copy()
model2 = KMeans(n_clusters=2, random_state=42, n_init=20)
df_clusters["Cluster_K2"] = model2.fit_predict(scaled)
sector_table = pd.crosstab(df_clusters["Cluster_K2"], df_clusters["Sector"])
sector_table.to_csv(OUTPUT_DIR / "k2_sector_comparison.csv")
print("\nK = 2 versus sectors:\n", sector_table.to_string())
# Financial similarity need not reproduce sectors. MCK's equity ratio dominates
# this run: one mixed-sector group and one extreme negative-equity distributor.
fig, axes = plt.subplots(1, 2, num="Official sectors versus K=2", figsize=(13, 5), layout="constrained")
for sector in SECTOR_COMPANIES:
    data = df_clusters[df_clusters["Sector"] == sector]
    axes[0].scatter(data[cols[1]], data[cols[0]], label=sector, color=colors[sector])
for group in sorted(df_clusters["Cluster_K2"].unique()):
    data = df_clusters[df_clusters["Cluster_K2"] == group]
    axes[1].scatter(data[cols[1]], data[cols[0]], label=f"Cluster {group}: {len(data)} companies")
for ax in axes:
    ax.set_xlabel(cols[1]); ax.set_ylabel(cols[0]); ax.legend(); ax.grid(alpha=.25)
axes[0].set_title("Official sector labels")
axes[1].set_title("K=2: two-dimensional view of a three-feature model")

scores = []
for k in range(2, min(10, len(df_avg) - 1) + 1):
    model = KMeans(n_clusters=k, random_state=42, n_init=20)
    labels = model.fit_predict(scaled)
    scores.append({"K": k, "Silhouette": silhouette_score(scaled, labels),
                "Inertia": model.inertia_, "Smallest_cluster": pd.Series(labels).value_counts().min()})
df_k_scores = pd.DataFrame(scores)
best_k = int(df_k_scores.loc[df_k_scores["Silhouette"].idxmax(), "K"])
best_model = KMeans(n_clusters=best_k, random_state=42, n_init=20)
df_clusters["Cluster_Best"] = best_model.fit_predict(scaled)
df_profiles = df_clusters.groupby("Cluster_Best")[cols].agg(["mean", "median"])
df_clusters.to_csv(OUTPUT_DIR / "cluster_assignments.csv", index=False)
df_profiles.to_csv(OUTPUT_DIR / "cluster_profiles.csv")
pd.crosstab(df_clusters["Cluster_Best"], df_clusters["Sector"]).to_csv(OUTPUT_DIR / "best_k_sector_comparison.csv")
df_k_scores.to_csv(OUTPUT_DIR / "k_scores.csv", index=False)
print("\nK scores:\n", df_k_scores.to_string(index=False))
print(f"\nBest K among the tested values: {best_k}")
print(df_profiles.round(2).to_string())
# A high silhouette can reflect an isolated extreme value, not useful sectors.
# Standardization balances units; it does not remove outliers or negative equity.
# Describe clusters with original-unit means/medians, not standardized scores.
fig, axes = plt.subplots(1, 3, num="Best K financial profiles", figsize=(14, 5), layout="constrained")
for ax, col in zip(axes, features):
    df_clusters.groupby("Cluster_Best")[col].mean().plot.bar(ax=ax)
    ax.set_title(col); ax.set_xlabel("Cluster"); ax.grid(axis="y", alpha=.25)
fig.suptitle(f"K={best_k}: mean financial profile of each cluster")

fig, axes = plt.subplots(1, 2, num="Choosing K", figsize=(11, 4), layout="constrained")
axes[0].plot(df_k_scores["K"], df_k_scores["Silhouette"], marker="o")
axes[0].set_ylabel("Silhouette score")
axes[1].plot(df_k_scores["K"], df_k_scores["Inertia"], marker="o")
axes[1].set_ylabel("Inertia")
for ax in axes:
    ax.set_xlabel("K")
    ax.set_xticks(df_k_scores["K"])
    ax.grid(alpha=0.25)

# Save every chart and create a browser gallery for convenient viewing.
GRAPH_DIR = OUTPUT_DIR / "graphs"
GRAPH_DIR.mkdir(parents=True, exist_ok=True)
gallery_cards = []
for number, figure_number in enumerate(plt.get_fignums(), start=1):
    chart = plt.figure(figure_number)
    title = chart.get_label() or f"Chart {number}"
    slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    image_name = f"{number:02d}_{slug}.png"
    chart.savefig(GRAPH_DIR / image_name, dpi=160, bbox_inches="tight", facecolor="white")
    gallery_cards.append(
        f'<section><h2>{html.escape(title)}</h2>'
        f'<a href="{image_name}"><img src="{image_name}" '
        f'alt="{html.escape(title, quote=True)}" loading="lazy"></a></section>'
    )
    plt.close(chart)
gallery = GRAPH_DIR / "index.html"
gallery.write_text(
    '<!doctype html><html lang="en"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width, initial-scale=1">'
    '<title>Homework 4 - DuPont Graphs</title>'
    '<style>body{font-family:Arial,sans-serif;margin:32px auto;padding:0 20px;'
    'max-width:1400px;background:#f3f5f8;color:#172334}'
    'section{background:white;padding:20px;margin:24px 0;border-radius:10px}'
    'img{display:block;width:100%;height:auto}h2{font-size:22px}</style></head><body>'
    '<h1>Homework 4: DuPont Analysis, 2020-2025</h1>'
    '<p>Click any graph to open its full-resolution image. '
    'Company comparison plots use six-year averages; sector trends use annual medians.</p>'
    + ''.join(gallery_cards) + '</body></html>', encoding="utf-8"
)
print(f"\nSaved {len(gallery_cards)} graphs to: {GRAPH_DIR}")
print(f"Open the graph gallery: {gallery}")
