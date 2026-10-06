import json
from pathlib import Path
import tempfile
import unittest
import AIResearch as ai


class ResearchTests(unittest.TestCase):
    def fixtures(self):
        f=dict(ticker='PFE',sector='healthcare',fiscal_year=2024,company_name='Example',
               filing_date='2025-02-20',accession_number='example',source_url='https://www.sec.gov/Archives/example',
               item_1a_text='Pricing pressure could reduce margins. '*1000)
        row=dict(f,profit_margin='.1',asset_turnover='1',equity_multiplier='2',roe='.2',equity_warning='False')
        return {('healthcare','PFE',2024):f},{('healthcare','PFE',2024):row}

    def test_chunks_preserve_all_text(self):
        text=''.join(chr(65+i%26) for i in range(90000))
        pieces=ai.chunks(text)
        self.assertEqual(pieces[0]+''.join(x[800:] for x in pieces[1:]),text)

    def test_changes_and_missing_data(self):
        f,r=self.fixtures();previous=dict(next(iter(r.values())),profit_margin='.08',roe='.16')
        r[('healthcare','PFE',2023)]=previous
        tasks,excluded=ai.tasks_for(f,r,'model','question')
        self.assertAlmostEqual(tasks[0]['payload']['financial_evidence']['changes']['profit_margin_change_pp'],2)
        self.assertFalse(excluded)
        self.assertEqual(ai.tasks_for(f,{},'model','question')[0],[])

    def test_provenance_mismatch(self):
        f,r=self.fixtures();next(iter(r.values()))['accession_number']='other'
        with self.assertRaises(ValueError):ai.tasks_for(f,r,'m','q')

    def test_cache_changes_with_question_and_model(self):
        f,r=self.fixtures()
        a=ai.tasks_for(f,r,'m','q')[0][0]['task_id']
        self.assertNotEqual(a,ai.tasks_for(f,r,'m','new question')[0][0]['task_id'])
        self.assertNotEqual(a,ai.tasks_for(f,r,'new model','q')[0][0]['task_id'])

    def test_citations_and_quotes(self):
        f,r=self.fixtures();task=ai.tasks_for(f,r,'m','q')[0][0]
        finding={'supporting_quote':'Pricing pressure could reduce margins.', 'source_url':next(iter(f.values()))['source_url']}
        ai.validate_result({'findings':[finding]},task)
        finding['supporting_quote']='Invented quotation'
        with self.assertRaises(ValueError):ai.validate_result({'findings':[finding]},task)
        finding['supporting_quote']='Pricing pressure could reduce margins.'
        finding['source_url']='https://example.com'
        with self.assertRaises(ValueError):ai.validate_result({'findings':[finding]},task)

    def test_both_sector_directories(self):
        import csv
        with tempfile.TemporaryDirectory() as tmp:
            dirs=[]
            for sector,ticker in [('healthcare','PFE'),('industrials','CAT')]:
                folder=Path(tmp)/sector;folder.mkdir();dirs.append(folder)
                f,r=self.fixtures();filing=next(iter(f.values()));row=next(iter(r.values()))
                filing.update(sector=sector,ticker=ticker);row.update(sector=sector,ticker=ticker)
                (folder/'staged_10k_batch.jsonl').write_text(json.dumps(filing)+'\n',encoding='utf-8')
                with (folder/'financials.csv').open('w',newline='',encoding='utf-8') as stream:
                    writer=csv.DictWriter(stream,fieldnames=list(row));writer.writeheader();writer.writerow(row)
            filings,finances=ai.load_runs(dirs)
            tasks,excluded=ai.tasks_for(filings,finances,'m','q')
            self.assertEqual({t['payload']['filing']['sector'] for t in tasks},{'healthcare','industrials'})
            self.assertFalse(excluded)

    def test_partial_workbook_and_unicode(self):
        f,r=self.fixtures();tasks,exclusions=ai.tasks_for(f,r,'m','q')
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);ai.report(tasks,{},out,'Why “pricing” matters?',exclusions)
            text=(out/'research_workbook.md').read_text(encoding='utf-8')
            self.assertIn('0/2',text)
            self.assertIn('“pricing”',text)


if __name__=='__main__':unittest.main()
