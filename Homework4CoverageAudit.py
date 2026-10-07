"""Replay the repository's Homework 4 financial-selection rules from cached SEC facts.

This is a method-reconciliation audit, not a replacement for the original-filing
research panel. No network or AI requests are made. Negative equity remains
flagged; candidate completeness is not evidence of investment comparability.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
REVENUE_TAGS = ['RevenueFromContractWithCustomerExcludingAssessedTax',
                'SalesRevenueNet', 'Revenues', 'RevenueFromContractWithCustomerIncludingAssessedTax']


def homework_functions(cutoff):
    # Load only the four existing pure selection functions, not the legacy
    # program's top-level download loops, plotting or filesystem mutations.
    source = ROOT/'homeWork4AndyJohnson.py'
    wanted = {'parse_income_metric', 'parse_balance_sheet_metric',
              'fiscal_year_labels', 'get_combined_metric'}
    nodes = [n for n in ast.parse(source.read_text(encoding='utf-8')).body
             if isinstance(n, ast.FunctionDef) and n.name in wanted]
    if {n.name for n in nodes} != wanted:
        raise ValueError('Homework selection functions changed; review the audit adapter')
    namespace = dict(pd=pd, FILED_BY=cutoff, NET_INCOME_TAGS=['NetIncomeLoss'],
                     EQUITY_TAGS=['StockholdersEquity'])
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec'), namespace)
    return namespace


def candidate_financials(facts, ticker, functions):
    """Same-accession annual quantities; year-end denominators, latest comparatives."""
    tables = []
    for name, tags, balance in [
        ('net_income', ['NetIncomeLoss'], False),
        ('revenue', ['Revenues']+REVENUE_TAGS if ticker in ['PFE', 'CNC', 'PODD'] else REVENUE_TAGS, False),
        ('assets', ['Assets'], True), ('equity', ['StockholdersEquity'], True)]:
        tables.append(functions['get_combined_metric'](facts, tags, balance).rename(
            columns={'val': name, 'tag': name+'_tag'}))
    frame = tables[0]
    for i in range(1, 4):
        keys = ['fy', 'start', 'end', 'accn'] if i == 1 else ['fy', 'end', 'accn']
        frame = frame.merge(tables[i].drop(columns='filed'), on=keys, validate='one_to_one')
    frame = frame.sort_values(['fy', 'end', 'filed', 'accn']).drop_duplicates('fy', keep='last')
    for column in ['net_income', 'revenue', 'assets', 'equity']:
        frame[column] = pd.to_numeric(frame[column], errors='coerce')
    valid = (np.isfinite(frame[['net_income', 'revenue', 'assets', 'equity']]).all(axis=1)
             & frame.revenue.gt(0) & frame.assets.gt(0) & frame.equity.ne(0))
    frame = frame[valid].copy()
    frame['roe'] = frame.net_income / frame.equity
    frame['profit_margin'] = frame.net_income / frame.revenue
    frame['asset_turnover'] = frame.revenue / frame.assets
    frame['equity_multiplier'] = frame.assets / frame.equity
    frame['equity_warning'] = frame.equity/frame.assets < .01
    frame['negative_equity'] = frame.equity < 0
    if not np.allclose(frame.roe, frame.profit_margin*frame.asset_turnover*frame.equity_multiplier):
        raise ValueError('DuPont identity failed')
    return frame


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-dir', type=Path, required=True, help='Existing HealthcareStats results')
    p.add_argument('--cache', type=Path, default=ROOT/'sec_cache/research')
    p.add_argument('--cutoff', default='2026-09-23', help='Legacy Homework 4 program cutoff, not fiscal year')
    p.add_argument('--output', type=Path, required=True, help='New audit folder; existing results stay untouched')
    args = p.parse_args()
    from datetime import date
    date.fromisoformat(args.cutoff)
    functions = homework_functions(args.cutoff)
    companies = pd.read_csv(ROOT/'healthcare/health_care_ciks.csv', dtype=str)
    original = pd.read_csv(args.run_dir/'financials.csv')
    status = pd.read_csv(args.run_dir/'retrieval_status.csv').fillna('')
    original['equity_warning'] = original.equity_warning.astype(str).str.lower().eq('true')
    args.output.mkdir(parents=True, exist_ok=False)
    rows, records, conflicts, cache_hashes = [], [], [], {}
    for company in companies.itertuples():
        ticker, cik = company.Symbol, company.CIK_Padded.zfill(10)
        old = original[original.ticker.eq(ticker)]
        audit = dict(ticker=ticker, collector_years=old.fiscal_year.nunique(),
                     research_usable_years=old[~old.equity_warning].fiscal_year.nunique())
        audit['recorded_errors'] = ' | '.join(sorted(set(status[status.ticker.eq(ticker) & status.error.ne('')].error)))
        try:
            url = f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json'
            cache = args.cache/(hashlib.sha256(url.encode()).hexdigest()+'.txt')
            data = cache.read_bytes(); facts = json.loads(data)
            if int(facts['cik']) != int(cik):
                raise ValueError('Cached CIK does not match company')
            cache_hashes[ticker] = hashlib.sha256(data).hexdigest()
            frame = candidate_financials(facts, ticker, functions)
            frame['ticker'], frame['cik'] = ticker, cik
            frame['source_url'] = frame.accn.map(lambda acc:
                f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace("-", "")}/{acc}.txt')
            gaps = (pd.to_datetime(frame.start)-pd.to_datetime(frame.end.shift())).dt.days.dropna()
            audit.update(hw4_years=len(frame), hw4_five_years=len(frame)>=5,
                         hw4_six_years=set(frame.fy)==set(range(2020, 2026)) and gaps.eq(1).all(),
                         hw4_unflagged_years=int((~frame.equity_warning).sum()), hw4_error='')
            # Preserve material competing revenue tags for manual review. A tag
            # priority is the legacy method, not proof the selected value is total revenue.
            for tag in REVENUE_TAGS:
                alternatives = functions['parse_income_metric'](facts, tag)
                matched = frame.merge(alternatives, on=['fy','start','end','accn'])
                for _, r in matched.iterrows():
                    if not np.isclose(r.revenue, r[tag], rtol=1e-6):
                        conflicts.append(dict(ticker=ticker, fiscal_year=int(r.fy), accession=r.accn,
                                              selected_tag=r.revenue_tag, selected_value=r.revenue,
                                              alternative_tag=tag, alternative_value=r[tag], source_url=r.source_url))
            records.extend(frame.to_dict('records'))
        except (OSError, ValueError, KeyError) as exc:
            audit.update(hw4_years=0, hw4_five_years=False, hw4_six_years=False,
                         hw4_unflagged_years=0, hw4_error=str(exc))
        rows.append(audit)
    comparison = pd.DataFrame(rows)
    comparison.to_csv(args.output/'company_method_comparison.csv', index=False)
    pd.DataFrame(records).to_csv(args.output/'homework_method_candidate_financials.csv', index=False)
    pd.DataFrame(conflicts, columns=['ticker','fiscal_year','accession','selected_tag','selected_value',
                                   'alternative_tag','alternative_value','source_url']).to_csv(args.output/'revenue_review.csv', index=False)
    manifest = dict(cutoff=args.cutoff, years=[2020,2025], mode='Legacy method reconciliation; candidates require accounting review',
                    denominator='Year-end assets and parent equity; not averages',
                    filing_selection='Latest same-accession comparative quantities before cutoff; not information available at period end',
                    cache_sha256=cache_hashes, program_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    legacy_program_sha256=hashlib.sha256((ROOT/'homeWork4AndyJohnson.py').read_bytes()).hexdigest(),
                    five_year_candidates=int(comparison.hw4_five_years.sum()), six_year_candidates=int(comparison.hw4_six_years.sum()),
                    five_unflagged_year_candidates=int((comparison.hw4_unflagged_years>=5).sum()))
    (args.output/'audit_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    # Separate compatible input for descriptive analysis. Never merge these
    # year-end ratios into the average-balance research panel.
    basis = args.output/'homework_basis'
    basis.mkdir()
    pd.DataFrame(records).rename(columns={'fy':'fiscal_year', 'filed':'filing_date',
        'accn':'accession_number', 'start':'period_start', 'end':'period_end'}).to_csv(basis/'financials.csv', index=False)
    basis_manifest = dict(manifest, companies=companies.Symbol.tolist(), sector='healthcare',
                          original_filings_only=False,
                          note='Homework year-end basis; later comparative data. Not suitable for a point-in-time predictive study.')
    (basis/'manifest.json').write_text(json.dumps(basis_manifest, indent=2), encoding='utf-8')
    print(f"Five-year candidates: {manifest['five_year_candidates']}; all-six-year candidates: {manifest['six_year_candidates']}; at least five unflagged years: {manifest['five_unflagged_year_candidates']}")
    print(f'Revenue conflicts needing review: {len(conflicts)}. Audit saved to {args.output}')


if __name__ == '__main__':
    main()
