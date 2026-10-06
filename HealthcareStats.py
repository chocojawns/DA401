"""Auditable SEC DuPont and Item 1A pipeline. No AI calls are made here."""
import argparse
import hashlib
import json
import os
import re
import time
from datetime import date, timedelta, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
REVENUE = ['RevenueFromContractWithCustomerExcludingAssessedTax', 'Revenues',
           'SalesRevenueNet', 'RevenueFromContractWithCustomerIncludingAssessedTax']
METRICS = ['profit_margin', 'asset_turnover', 'equity_multiplier', 'roe']


class SEC:
    def __init__(self, cache, user_agent, offline=False):
        self.cache, self.user_agent, self.offline = Path(cache), user_agent, offline
        self.cache.mkdir(parents=True, exist_ok=True)
        self.last = 0.0

    def get(self, url):
        path = self.cache / (hashlib.sha256(url.encode()).hexdigest() + '.txt')
        if path.exists():
            return path.read_text(encoding='utf-8')
        if self.offline:
            raise ValueError('Not cached: ' + url)
        if '@' not in self.user_agent:
            raise ValueError('Set SEC_USER_AGENT to project name and contact email')
        time.sleep(max(0, .25 - (time.monotonic() - self.last)))
        self.last = time.monotonic()
        response = requests.get(url, headers={'User-Agent': self.user_agent}, timeout=60)
        response.raise_for_status()
        text = response.content.decode('utf-8', errors='replace')
        temp = path.with_suffix('.tmp')
        temp.write_text(text, encoding='utf-8')
        temp.replace(path)
        return text


def entries(facts, tag):
    return facts.get('facts', {}).get('us-gaap', {}).get(tag, {}).get('units', {}).get('USD', [])


def pick(facts, tags, accession, end, start=None):
    """Never mix periods, accessions, or conflicting values within a tag."""
    found = []
    for tag in tags:
        rows = [r for r in entries(facts, tag) if r.get('accn') == accession
                and r.get('end') == end and r.get('start') == start]
        values = {float(r['val']) for r in rows}
        if len(values) > 1:
            raise ValueError(f'Conflicting {tag} values in {accession}')
        if values:
            value = values.pop()
            if not np.isfinite(value):
                raise ValueError('Nonfinite financial value')
            found.append((value, tag))
    if not found:
        raise ValueError(f'Missing {tags} for {start or "instant"} to {end}')
    return found[0][0], found[0][1], found


def annual_filings(facts, cutoff):
    # Latest annual income period within each original 10-K, never a comparative
    # period from a later annual report. Exact fiscal label is checked in HTML.
    by_acc = {}
    for r in entries(facts, 'NetIncomeLoss'):
        if r.get('form') != '10-K' or r.get('fp') != 'FY' or r.get('filed', '') > cutoff:
            continue
        if not r.get('start'):
            continue
        days = (date.fromisoformat(r['end']) - date.fromisoformat(r['start'])).days + 1
        if not 350 <= days <= 380:
            continue
        acc = r['accn']
        if acc not in by_acc or r['end'] > by_acc[acc]['end']:
            by_acc[acc] = r
    # Prefer the earliest original filing for the period; no later restatements.
    result = {}
    for r in sorted(by_acc.values(), key=lambda r: (r['filed'], r['accn'])):
        result.setdefault(r['end'], r)
    return list(result.values())


def primary_document(submission):
    for doc in re.findall(r'<DOCUMENT>(.*?)</DOCUMENT>', submission, re.S | re.I):
        if re.search(r'<TYPE>\s*10-K\s*(?:\r?\n|<)', doc, re.I):
            match = re.search(r'<TEXT>(.*?)</TEXT>', doc, re.S | re.I)
            return match.group(1) if match else doc
    raise ValueError('No primary 10-K document found in submission')


def filing_metadata(html):
    soup = BeautifulSoup(html, 'html.parser')
    def field(name):
        values = {node.get_text('', strip=True) for node in soup.find_all(
            attrs={'name': re.compile(r'(?:^|:)' + name + '$', re.I)})}
        if len(values) != 1:
            raise ValueError(f'Missing/ambiguous inline XBRL {name}; manual review required')
        return values.pop()
    year = int(field('DocumentFiscalYearFocus'))
    period = field('DocumentPeriodEndDate')
    period = pd.to_datetime(period).date().isoformat()
    return year, period


def extract_item1a(html):
    soup = BeautifulSoup(html, 'html.parser')
    for node in soup(['script', 'style', 'ix:header']):
        node.decompose()
    # Match standalone HTML headings, not in-paragraph cross-references.
    start_pattern = re.compile(r'ITEM\s*1\s*A[\s.:–—-]*RISK\s+FACTORS[\s.:–—-]*', re.I)
    end_pattern = re.compile(r'ITEM\s*(?:1\s*B[\s.:–—-]*UNRESOLVED\s+STAFF\s+COMMENTS|1\s*C[\s.:–—-]*CYBERSECURITY|2[\s.:–—-]*PROPERTIES)[\s.:–—-]*', re.I)
    markers = []
    for node in soup.find_all(['div', 'p', 'h1', 'h2', 'h3', 'h4', 'td']):
        text = ' '.join(node.get_text(' ').split())
        kind = 'start' if start_pattern.fullmatch(text) else 'end' if end_pattern.fullmatch(text) else None
        if kind:
            markers.append((node, kind))
    # Nested containers may repeat the same heading; use the innermost match.
    marked_ids = {id(node) for node, _ in markers}
    for node, kind in markers:
        if any(id(child) in marked_ids for child in node.find_all(True)):
            continue
        node.insert_before(' DA401_SECTION_' + kind.upper() + ' ')
    text = ' '.join(soup.get_text(' ').split())
    candidates = []
    for match in re.finditer(r'DA401_SECTION_START (.*?)(?=DA401_SECTION_END|DA401_SECTION_START|$)', text):
        section = match.group(1).strip()
        # A real ending heading is mandatory; no whole-document fallback.
        if text[match.end():].startswith('DA401_SECTION_END') and len(section) > 500:
            candidates.append(section)
    if not candidates:
        raise ValueError('No bounded standalone Item 1A heading; manual review required')
    return max(candidates, key=len)


def calculate(facts, filing):
    acc, start, end = filing['accn'], filing['start'], filing['end']
    opening = (date.fromisoformat(start) - timedelta(days=1)).isoformat()
    specs = {'net_income': (['NetIncomeLoss'], end, start),
             'revenue': (REVENUE, end, start),
             'assets_begin': (['Assets'], opening, None),
             'assets_end': (['Assets'], end, None),
             'equity_begin': (['StockholdersEquity'], opening, None),
             'equity_end': (['StockholdersEquity'], end, None)}
    row = {}
    for name, (tags, stop, begin) in specs.items():
        value, tag, candidates = pick(facts, tags, acc, stop, begin)
        row[name] = value
        row[name + '_tag'] = tag
        if name == 'revenue':
            row['revenue_candidates'] = json.dumps(candidates)
            if any(not np.isclose(v, value, rtol=1e-6) for v, _ in candidates):
                raise ValueError('Conflicting revenue concepts: ' + json.dumps(candidates))
    row['average_assets'] = (row['assets_begin'] + row['assets_end']) / 2
    row['average_equity'] = (row['equity_begin'] + row['equity_end']) / 2
    if row['revenue'] <= 0 or min(row['assets_begin'], row['assets_end']) <= 0:
        raise ValueError('Nonpositive revenue/assets')
    row['profit_margin'] = row['net_income'] / row['revenue']
    row['asset_turnover'] = row['revenue'] / row['average_assets']
    eq = row['average_equity']
    row['equity_multiplier'] = row['average_assets'] / eq if eq else np.nan
    row['roe'] = row['net_income'] / eq if eq else np.nan
    row['equity_warning'] = (min(row['equity_begin'], row['equity_end']) <= 0
                             or eq / row['average_assets'] < .01)
    if eq and not np.isclose(row['profit_margin'] * row['asset_turnover'] * row['equity_multiplier'], row['roe']):
        raise ValueError('DuPont identity failed')
    return row


def charts(frame, out, label):
    if frame.empty:
        return
    # Flagged equity stays in source tables but is excluded from ratio comparison plots.
    clean = frame[~frame.equity_warning].copy()
    if clean.empty:
        return
    names = {'roe': 'Return on equity', 'profit_margin': 'Profit margin',
             'asset_turnover': 'Asset turnover', 'equity_multiplier': 'Equity multiplier'}
    summary = []
    years = range(int(frame.fiscal_year.min()), int(frame.fiscal_year.max()) + 1)
    for metric in METRICS:
        grouped = clean.groupby('fiscal_year')[metric]
        med = grouped.median().reindex(years)
        scale = 100 if metric in ['profit_margin', 'roe'] else 1
        unit = '%' if scale == 100 else 'x'
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(med.index, med * scale, color='#2465a4', marker='o', linewidth=2)
        ax.set(title=f'{clean.iloc[0].company_name if clean.ticker.nunique() == 1 else label.title() + " sample median"}: {names[metric].lower()}',
               xlabel='Fiscal year', ylabel=f'{names[metric]} ({unit})')
        ax.set_xticks(list(years))
        ax.axhline(0, color='gray', linewidth=.7)
        ax.grid(axis='y', alpha=.2)
        ax.margins(y=.25)
        for year, value in med.dropna().items():
            n = int(grouped.count().loc[year])
            ax.annotate(f'{value * scale:.2f}{unit}\n{n} ' + ('company' if n == 1 else 'companies'),
                        (year, value * scale), xytext=(0, 10),
                        textcoords='offset points', ha='center', fontsize=9)
            summary.append(dict(fiscal_year=year, metric=metric, median=value,
                                q25=grouped.quantile(.25).loc[year],
                                q75=grouped.quantile(.75).loc[year], n=n))
        fig.text(.5, .02, 'Available companies; sample may change by year. Flagged equity excluded.',
                 ha='center', fontsize=9)
        fig.tight_layout(rect=(0, .05, 1, 1))
        fig.savefig(out/f'{metric}_trend.png', dpi=160)
        plt.close(fig)
    pd.DataFrame(summary).to_csv(out/'annual_summary.csv', index=False)
    year = int(frame.fiscal_year.max())
    latest = clean[clean.fiscal_year == year].sort_values('roe')
    latest[['ticker', 'company_name', 'fiscal_year', 'roe']].to_csv(out/'company_roe_comparison.csv', index=False)
    if latest.empty:
        return
    # Paginate to keep all company labels readable, without selecting only winners.
    for page, start in enumerate(range(0, len(latest), 20), 1):
        subset = latest.iloc[start:start+20]
        fig, ax = plt.subplots(figsize=(12, max(5, len(subset)*.4+2)))
        bars = ax.barh([f'{r.company_name} ({r.ticker})' for r in subset.itertuples()],
                       subset.roe*100, color='#2465a4')
        ax.bar_label(bars, labels=[f'{x:.1f}%' for x in subset.roe*100], padding=4)
        ax.axvline(0, color='gray', linewidth=.8)
        ax.margins(x=.2)
        ax.set(title=f'{label.title()}: company ROE in {year} — page {page}', xlabel='Return on equity (%)')
        fig.text(.5, .02, 'Flagged equity excluded. Higher ROE alone does not mean a better investment.',
                 ha='center', fontsize=9)
        fig.tight_layout(rect=(0,.05,1,1))
        fig.savefig(out/f'company_roe_{year}_{page}.png', dpi=160)
        plt.close(fig)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sector', choices=['healthcare','industrials'], default='healthcare')
    p.add_argument('--tickers', nargs='+', help='Optional small validation sample')
    p.add_argument('--start-year', type=int, default=2020)
    p.add_argument('--end-year', type=int, default=2025)
    p.add_argument('--cutoff', default=date.today().isoformat())
    p.add_argument('--output', type=Path)
    p.add_argument('--cache', type=Path, default=ROOT/'sec_cache/research')
    p.add_argument('--offline', action='store_true')
    args = p.parse_args()
    date.fromisoformat(args.cutoff)
    if args.end_year < args.start_year:
        p.error('end-year must not precede start-year')
    if not args.offline and '@' not in os.getenv('SEC_USER_AGENT',''):
        p.error('Set SEC_USER_AGENT to project name and contact email')
    base = args.output or ROOT/args.sector/'results/research'
    out = base/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out.mkdir(parents=True, exist_ok=False)
    company_file = ROOT/args.sector/('health_care_ciks.csv' if args.sector=='healthcare' else 'industrials_ciks.csv')
    companies = pd.read_csv(company_file, dtype=str)
    if args.tickers:
        wanted = {x.upper() for x in args.tickers}
        if wanted - set(companies.Symbol):
            p.error('Requested ticker is not in the selected sector CSV')
        companies = companies[companies.Symbol.isin(wanted)]
    sec = SEC(args.cache, os.getenv('SEC_USER_AGENT',''), args.offline)
    financials, status = [], []
    with (out/'staged_10k_batch.jsonl').open('w', encoding='utf-8') as batch:
        for company in companies.itertuples(index=False):
            ticker, cik = company.Symbol, str(company.CIK_Padded).zfill(10)
            try:
                facts_url = f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json'
                facts = json.loads(sec.get(facts_url))
                if int(facts['cik']) != int(cik):
                    raise ValueError('Company Facts CIK mismatch')
                candidates = annual_filings(facts, args.cutoff)
                if not candidates:
                    raise ValueError('No annual NetIncomeLoss filings found')
            except Exception as e:
                status.append(dict(ticker=ticker, stage='companyfacts', error=str(e)))
                continue
            for filing in candidates:
                # Generous date prefilter; exact fiscal label comes from original 10-K.
                if not args.start_year-1 <= int(filing['end'][:4]) <= args.end_year+1:
                    continue
                acc = filing['accn']; stem = f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace("-", "")}'
                url = f'{stem}/{acc}.txt'
                record = dict(ticker=ticker, cik=cik, company_name=facts.get('entityName',ticker),
                              filing_date=filing['filed'], accession_number=acc,
                              source_url=url, sector=args.sector)
                try:
                    submission = sec.get(url)
                    html = primary_document(submission)
                    year, period = filing_metadata(html)
                    if period != filing['end']:
                        raise ValueError('Filing report period disagrees with selected financial period')
                    if not args.start_year <= year <= args.end_year:
                        continue
                    record.update(fiscal_year=year, period_end=period)
                except Exception as e:
                    status.append(dict(**record, stage='filing_metadata', error=str(e)))
                    continue
                try:
                    ratios = calculate(facts, filing)
                    financials.append(dict(**record, period_start=filing['start'], facts_url=facts_url, **ratios))
                    status.append(dict(**record, stage='financials', error=''))
                except Exception as e:
                    status.append(dict(**record, stage='financials', error=str(e)))
                try:
                    text = extract_item1a(html)
                    batch.write(json.dumps(dict(**record, item_1a_text=text,
                        text_sha256=hashlib.sha256(text.encode()).hexdigest()), ensure_ascii=False)+'\n')
                    batch.flush()
                    status.append(dict(**record, stage='item1a', error='', characters=len(text)))
                except Exception as e:
                    status.append(dict(**record, stage='item1a', error=str(e)))
    frame = pd.DataFrame(financials)
    if not frame.empty and frame.duplicated(['ticker','fiscal_year']).any():
        # Transition fiscal years need explicit human mapping; never average them silently.
        frame.to_csv(out/'ambiguous_financials.csv', index=False)
        raise ValueError('Duplicate company/fiscal-year records: inspect ambiguous_financials.csv')
    frame.to_csv(out/'financials.csv', index=False)
    pd.DataFrame(status).to_csv(out/'retrieval_status.csv', index=False)
    coverage = pd.MultiIndex.from_product([companies.Symbol, range(args.start_year,args.end_year+1)], names=['ticker','fiscal_year']).to_frame(index=False)
    if frame.empty:
        coverage['financial_available'] = False
    else:
        coverage = coverage.merge(frame[['ticker','fiscal_year']].assign(financial_available=True), how='left').fillna({'financial_available':False})
        frame[frame.equity_warning].to_csv(out/'equity_warnings.csv', index=False)
        # Explicit consecutive-year pairs; no automatic significance tests.
        ordered = frame.sort_values(['ticker','fiscal_year']).copy()
        following = ordered[['ticker','fiscal_year','profit_margin','period_start']].copy()
        following['fiscal_year'] -= 1
        following = following.rename(columns={'profit_margin':'next_profit_margin','period_start':'next_period_start'})
        pairs = ordered.merge(following, on=['ticker','fiscal_year'])
        pairs['next_margin_change_pp'] = 100*(pairs.next_profit_margin-pairs.profit_margin)
        pairs['strictly_preperiod_disclosure'] = pairs.filing_date < pairs.next_period_start
        pairs.to_csv(out/'next_year_research_pairs.csv', index=False)
        charts(frame, out, args.sector)
    extracted = [json.loads(line) for line in (out/'staged_10k_batch.jsonl').read_text().splitlines() if line.strip()]
    if extracted:
        item_keys = pd.DataFrame(extracted)[['ticker','fiscal_year']].drop_duplicates()
        coverage = coverage.merge(item_keys.assign(item1a_available=True), how='left').fillna({'item1a_available':False})
    else:
        coverage['item1a_available'] = False
    coverage.to_csv(out/'coverage.csv', index=False)
    (out/'manifest.json').write_text(json.dumps(dict(sector=args.sector, cutoff=args.cutoff,
        years=[args.start_year,args.end_year], companies=companies.Symbol.tolist(),
        csv_sha256=hashlib.sha256(company_file.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        financial_rows=len(frame), original_filings_only=True,
        note='Unbalanced descriptive panel; no causal inference. Review coverage and extraction manually.'), indent=2))
    print(f'Saved {len(frame)} financial company-years to {out}')
    if frame.empty:
        raise SystemExit('No usable financial rows; inspect retrieval_status.csv. Run is not validated.')


if __name__ == '__main__':
    main()
