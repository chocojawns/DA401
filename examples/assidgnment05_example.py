import pandas as pd
import numpy as np

# 1. LOAD SECTOR DATASET
df = pd.read_csv("merged_risk_data.csv")

# Ensure required fields
df['Risk Category'] = df['Risk Category'].replace({'Competition': 'Market'})

# Deduplicate financial records per company/year
financials = df[['Ticker', 'Company Name', 'Filing Year', 'Profit_Margin', 'Asset_Turnover', 'Equity_Multiplier', 'ROE']].drop_duplicates()

print("             SECTOR BENCHMARKING & STAKEHOLDER ANALYTICS             \n")

# 2. SECTOR BENCHMARKING (MEDIANS & DISPERSION)
print("--- 1. SECTOR ANNUAL RATIO MEDIANS (2020-2025) ---")
sector_medians = financials.groupby('Filing Year')[['Profit_Margin', 'Asset_Turnover', 'Equity_Multiplier', 'ROE']].median()
print(sector_medians.round(4))

print("\n--- 2. COMPANY DUPONT AVERAGES VS. SECTOR MEDIAN ---")
company_averages = financials.groupby(['Ticker', 'Company Name']).agg({
    'Profit_Margin': 'mean',
    'Asset_Turnover': 'mean',
    'Equity_Multiplier': 'mean',
    'ROE': 'mean'
}).reset_index()

# Calculate relative performance to sector median
sec_margin_med = financials['Profit_Margin'].median()
sec_roe_med = financials['ROE'].median()

company_averages['Margin_vs_Sector'] = company_averages['Profit_Margin'] - sec_margin_med
company_averages['ROE_vs_Sector'] = company_averages['ROE'] - sec_roe_med

print(company_averages.to_string(index=False, formatters={
    'Profit_Margin': '{:.2%}'.format,
    'Asset_Turnover': '{:.2f}x'.format,
    'Equity_Multiplier': '{:.2f}x'.format,
    'ROE': '{:.2%}'.format,
    'Margin_vs_Sector': '{:+.2%}'.format,
    'ROE_vs_Sector': '{:+.2%}'.format
}))


# 3. QUALITATIVE SECTOR RISK CONCENTRATION
print("\n--- 3. SECTOR RISK CATEGORY DISTRIBUTION BY COMPANY ---")
sector_risk_matrix = pd.crosstab(df['Ticker'], [df['Risk Category'], df['Severity']], margins=True)
print(sector_risk_matrix)

# 4. STAKEHOLDER DECISION MATRIX
print("\n--- 4. STAKEHOLDER SUMMARY: QUALITY OF ROE DECONSTRUCTION ---")
company_averages['Operational_ROA'] = company_averages['Profit_Margin'] * company_averages['Asset_Turnover']
company_averages['Financial_Leverage_Boost'] = company_averages['ROE'] / company_averages['Operational_ROA']

print(company_averages[['Ticker', 'Profit_Margin', 'Asset_Turnover', 'Operational_ROA', 'Equity_Multiplier', 'ROE', 'Financial_Leverage_Boost']].to_string(index=False, formatters={
    'Profit_Margin': '{:.2%}'.format,
    'Asset_Turnover': '{:.2f}x'.format,
    'Operational_ROA': '{:.2%}'.format,
    'Equity_Multiplier': '{:.2f}x'.format,
    'ROE': '{:.2%}'.format,
    'Financial_Leverage_Boost': '{:.2f}x'.format
}))