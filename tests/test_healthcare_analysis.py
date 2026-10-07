import tempfile
from pathlib import Path
import unittest
import numpy as np
import pandas as pd
import HealthcareAnalysis as a

class AnalysisTests(unittest.TestCase):
    def test_multicompany_outputs(self):
        rows=[]
        for i in range(12):
            for year in range(2020,2024):
                margin=.03+i*.01+(year-2020)*.002
                turnover=.3+i*.03;leverage=1.5+(i%3)*.4
                rows.append(dict(ticker=f'T{i}',fiscal_year=year,profit_margin=margin,asset_turnover=turnover,
                    equity_multiplier=leverage,roe=margin*turnover*leverage,equity_warning=False,
                    source_url='https://example.com',analysis_exclusion='',subsector='Group A' if i<6 else 'Group B'))
        # An otherwise valid firm with only two years must not enter any
        # comparisons when the required minimum is three.
        rows += [dict(rows[j], ticker='SHORT') for j in range(2)]
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);a.analyze(pd.DataFrame(rows),out,2020,2023,3)
            self.assertTrue((out/'company_clusters.csv').exists())
            scores=pd.read_csv(out/'cluster_scores.csv')
            self.assertIn(2,scores.k.values)
            self.assertEqual(len(pd.read_csv(out/'annual_changes.csv')),36)
            self.assertTrue((out/'roe_subsectors.png').exists())
            eligibility=pd.read_csv(out/'company_eligibility.csv').set_index('ticker')
            self.assertFalse(eligibility.loc['SHORT','included'])
            self.assertNotIn('SHORT',pd.read_csv(out/'company_averages.csv').ticker.values)

    def test_duplicate_rows_rejected(self):
        row=dict(ticker='A',fiscal_year=2024,profit_margin=.1,asset_turnover=1,equity_multiplier=2,
                 roe=.2,equity_warning=False,source_url='https://example.com')
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'data.csv';pd.DataFrame([row,row]).to_csv(p,index=False)
            with self.assertRaisesRegex(ValueError,'Duplicate'):a.load_financials(p)

    def test_labels_need_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'labels.csv'
            pd.DataFrame([dict(ticker='A',subsector='Pharma',classification_source='')]).to_csv(p,index=False)
            with self.assertRaises(ValueError):a.add_subsectors(pd.DataFrame({'ticker':['A']}),p)
        result=a.add_subsectors(pd.DataFrame({'ticker':['A']}),None)
        self.assertEqual(result.subsector.iloc[0],'Unclassified')

    def test_small_sample_skips_clusters(self):
        with tempfile.TemporaryDirectory() as tmp:
            note=a.cluster_companies(pd.DataFrame({'profit_margin':[.1]}),Path(tmp))
            self.assertIn('at least six',note)
            self.assertFalse((Path(tmp)/'cluster_scores.csv').exists())

if __name__=='__main__':unittest.main()
