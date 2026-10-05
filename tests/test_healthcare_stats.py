import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import HealthcareStats as h


def fixture():
    filing = dict(accn='0000000001-25-000001', start='2024-01-01', end='2024-12-31',
                  filed='2025-02-20', fy=2024, fp='FY', form='10-K')
    facts = {'cik':78003, 'entityName':'SYNTHETIC Pfizer fixture', 'facts':{'us-gaap':{}}}
    for tag, items in {'NetIncomeLoss':[(10,'2024-12-31','2024-01-01')],
                       'Revenues':[(100,'2024-12-31','2024-01-01')],
                       'Assets':[(80,'2023-12-31',None),(120,'2024-12-31',None)],
                       'StockholdersEquity':[(40,'2023-12-31',None),(60,'2024-12-31',None)]}.items():
        rows=[]
        for val,end,start in items:
            row=dict(filing,val=val,end=end)
            row.pop('start')
            if start: row['start']=start
            rows.append(row)
        facts['facts']['us-gaap'][tag]={'units':{'USD':rows}}
    html='<html><ix:nonNumeric name="dei:DocumentFiscalYearFocus">2024</ix:nonNumeric><ix:nonNumeric name="dei:DocumentPeriodEndDate">2024-12-31</ix:nonNumeric><p>Item 1A. Risk Factors</p><p>Item 1B. Unresolved Staff Comments</p><h2>Item 1A. Risk Factors</h2><p>'+('Synthetic reimbursement and competition disclosure. '*30)+'</p><h2>Item 1B. Unresolved Staff Comments</h2></html>'
    submission='<DOCUMENT>\n<TYPE>10-K\n<TEXT>'+html+'</TEXT></DOCUMENT>'
    return facts,filing,submission


class Tests(unittest.TestCase):
    def test_averages_identity(self):
        facts,filing,_=fixture(); r=h.calculate(facts,filing)
        self.assertAlmostEqual(r['roe'],.2)
        self.assertAlmostEqual(r['profit_margin'],.1)
        self.assertAlmostEqual(r['asset_turnover'],1)
        self.assertAlmostEqual(r['equity_multiplier'],2)
        self.assertFalse(r['equity_warning'])

    def test_missing_opening_not_replaced_with_closing(self):
        facts,filing,_=fixture(); facts['facts']['us-gaap']['Assets']['units']['USD'].pop(0)
        with self.assertRaises(ValueError): h.calculate(facts,filing)

    def test_conflicting_revenue_rejected(self):
        facts,filing,_=fixture()
        facts['facts']['us-gaap']['SalesRevenueNet']={'units':{'USD':[dict(filing,val=90)]}}
        with self.assertRaisesRegex(ValueError,'Conflicting revenue'): h.calculate(facts,filing)

    def test_negative_equity_flagged(self):
        facts,filing,_=fixture()
        for r in facts['facts']['us-gaap']['StockholdersEquity']['units']['USD']: r['val']=-10
        self.assertTrue(h.calculate(facts,filing)['equity_warning'])

    def test_extraction_and_metadata(self):
        _,_,sub=fixture(); html=h.primary_document(sub)
        self.assertEqual(h.filing_metadata(html),(2024,'2024-12-31'))
        text=h.extract_item1a(html)
        self.assertIn('reimbursement',text)
        self.assertNotIn('Unresolved',text)
        with self.assertRaises(ValueError): h.extract_item1a('<p>no risk section</p>')

    def test_original_filing_and_cutoff(self):
        facts,filing,_=fixture()
        newer=dict(filing,accn='new',filed='2026-02-20',fy=2025,val=12)
        facts['facts']['us-gaap']['NetIncomeLoss']['units']['USD'].append(newer)
        self.assertEqual(h.annual_filings(facts,'2025-12-31'),[dict(filing,val=10)])

    def test_end_to_end_offline(self):
        facts,filing,sub=fixture()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); cache=root/'cache'; cache.mkdir()
            urls={'https://data.sec.gov/api/xbrl/companyfacts/CIK0000078003.json':json.dumps(facts),
                  'https://www.sec.gov/Archives/edgar/data/78003/000000000125000001/0000000001-25-000001.txt':sub}
            for url,text in urls.items():
                (cache/(h.hashlib.sha256(url.encode()).hexdigest()+'.txt')).write_text(text)
            result=subprocess.run([sys.executable,str(h.ROOT/'HealthcareStats.py'),'--offline','--tickers','PFE',
                                   '--start-year','2024','--end-year','2024','--cutoff','2025-12-31',
                                   '--cache',str(cache),'--output',str(root/'results')],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            run=next((root/'results').iterdir())
            for name in ['financials.csv','coverage.csv','retrieval_status.csv','annual_components.png','roe_heatmap.png','operating_profiles.png']:
                self.assertGreater((run/name).stat().st_size,0)
            record=json.loads((run/'staged_10k_batch.jsonl').read_text())
            self.assertEqual(record['fiscal_year'],2024)
            self.assertEqual(record['filing_date'],'2025-02-20')
            self.assertEqual(len(h.pd.read_csv(run/'financials.csv')),1)


if __name__=='__main__': unittest.main()
