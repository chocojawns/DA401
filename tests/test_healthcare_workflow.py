import argparse
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import HealthcareWorkflow as w


class HealthcareWorkflowTests(unittest.TestCase):
    def test_rejects_industrial_input(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)
            (p/'manifest.json').write_text(json.dumps({'sector':'industrials'}))
            with self.assertRaisesRegex(ValueError,'healthcare'):
                w.read_manifest(p)

    def test_ai_rejects_comparative_financials_before_call(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)
            (p/'manifest.json').write_text(json.dumps({'sector':'healthcare','original_filings_only':False}))
            with patch.object(w,'run_program') as run:
                with self.assertRaisesRegex(ValueError,'different filing dates'):
                    w.ai(argparse.Namespace(run_dir=p))
                run.assert_not_called()

    def test_ai_preview_does_not_execute(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)
            (p/'manifest.json').write_text(json.dumps({'sector':'healthcare','original_filings_only':True}))
            (p/'staged_10k_batch.jsonl').write_text('')
            args=argparse.Namespace(run_dir=p,question='Question',model='test',max_requests=3,execute=False)
            with patch.object(w,'run_program') as run:
                w.ai(args)
                self.assertNotIn('--execute',run.call_args.args[1])

if __name__=='__main__':unittest.main()
