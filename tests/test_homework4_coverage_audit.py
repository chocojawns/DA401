import unittest
import Homework4CoverageAudit as audit
from test_healthcare_stats import fixture


class HomeworkAuditTests(unittest.TestCase):
    def test_year_end_basis_not_average_balances(self):
        facts, _, _ = fixture()
        result = audit.candidate_financials(facts, 'TEST', audit.homework_functions('2025-12-31'))
        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result.iloc[0].roe, 10/60)
        self.assertAlmostEqual(result.iloc[0].asset_turnover, 100/120)

    def test_negative_equity_retained_and_flagged_zero_rejected(self):
        facts, _, _ = fixture()
        rows = facts['facts']['us-gaap']['StockholdersEquity']['units']['USD']
        rows[-1]['val'] = -60
        result = audit.candidate_financials(facts, 'TEST', audit.homework_functions('2025-12-31'))
        self.assertEqual(len(result), 1)
        self.assertTrue(result.iloc[0].negative_equity)
        self.assertAlmostEqual(result.iloc[0].roe, -10/60)
        rows[-1]['val'] = 0
        self.assertTrue(audit.candidate_financials(facts, 'TEST', audit.homework_functions('2025-12-31')).empty)

    def test_does_not_mix_accessions_or_future_filings(self):
        facts, _, _ = fixture()
        facts['facts']['us-gaap']['Revenues']['units']['USD'][0]['accn'] = 'another-filing'
        self.assertTrue(audit.candidate_financials(facts, 'TEST', audit.homework_functions('2025-12-31')).empty)
        facts, _, _ = fixture()
        self.assertTrue(audit.candidate_financials(facts, 'TEST', audit.homework_functions('2024-12-31')).empty)
