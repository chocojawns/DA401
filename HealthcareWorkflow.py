"""Healthcare-only workflow: collect, analyze saved data, then review Item 1A.

Run without arguments for instructions. No downloads or paid AI calls happen
unless their specific stage is requested. Industrial files are never modified.
"""
import argparse
import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# 1. SETTINGS: paths are relative to this program, not the terminal folder.
ROOT = Path(__file__).resolve().parent
SAVED_DATA = ROOT/'healthcare/reports/homework4_recovered/homework_basis'
RESULTS = ROOT/'healthcare/results'
QUESTION = ('Which disclosed healthcare risks could affect profit margin, asset turnover, '
            'or equity, and which supplied evidence supports each connection? Separate '
            'potential risks from realized events and identify missing evidence. '
            'Do not infer causation or investment attractiveness from ROE alone.')


# 2. LOAD AND CHECK THE STUDY

def read_manifest(directory):
    manifest = json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('sector') != 'healthcare':
        raise ValueError('This workflow accepts healthcare studies only.')
    return manifest


def read_table(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def run_program(name, arguments):
    # Argument lists preserve spaces in Windows paths; no shell interpolation.
    subprocess.run([sys.executable, str(ROOT/name), *map(str, arguments)],
                   cwd=ROOT, check=True)


# 3. ANALYZE SAVED FINANCIAL DATA AND SAVE ONE STUDY SUMMARY

def summarize(source, analysis, manifest):
    eligibility = read_table(analysis/'company_eligibility.csv')
    included = [row['ticker'] for row in eligibility if row['included'].lower() == 'true']
    with (source/'financials.csv').open(encoding='utf-8-sig', newline='') as stream:
        observed = {row['ticker'] for row in csv.DictReader(stream)}
    summary = {
        'sector': 'healthcare', 'status': 'Quantitative analysis; no AI interpretation',
        'source_directory': str(source.resolve()),
        'financials_sha256': hashlib.sha256((source/'financials.csv').read_bytes()).hexdigest(),
        'method': manifest, 'included_company_count': len(included),
        'included_companies': included,
        'requested_companies_without_financial_rows': sorted(set(manifest.get('companies', []))-observed),
        'eligibility': eligibility,
        'company_averages': read_table(analysis/'company_averages.csv'),
        'company_outliers': read_table(analysis/'company_outliers.csv'),
        'balanced_panel_medians': read_table(analysis/'balanced_panel_medians.csv'),
        'research_questions': json.loads((analysis/'research_questions.json').read_text(encoding='utf-8')),
        'limitations': ['CSV-derived table cells are strings; ratios are decimals, not percentages.',
            'Repeated company-years are dependent observations.',
            'DuPont component correlations are mechanically related.',
            'Cluster membership and risk disclosures do not establish causation.',
            'Subsector conclusions require verified business classifications.'],
    }
    for filename in ['cluster_profiles.csv', 'cluster_scores.csv', 'company_clusters.csv']:
        if (analysis/filename).exists():
            summary[filename.removesuffix('.csv')] = read_table(analysis/filename)
    (analysis/'healthcare_study.json').write_text(json.dumps(summary, indent=2, allow_nan=False), encoding='utf-8')
    (analysis/'START_HERE.md').write_text(
        '# Healthcare study\n\n'
        f'{len(included)} companies meet the analysis eligibility rules.\n\n'
        '1. Read [the analysis report](analysis_report.md).\n'
        '2. Check [company eligibility](company_eligibility.csv) and [coverage](analysis_coverage.csv).\n'
        '3. Review [company averages](company_averages.csv) and [outliers](company_outliers.csv).\n'
        '4. Investigate [research questions](research_questions.json) against filings.\n'
        '5. Use [healthcare_study.json](healthcare_study.json) as the consolidated quantitative summary.\n\n'
        'No AI calls were made. The financial method and source hashes are in the JSON summary. '
        'Keep year-end comparative data separate from original-filing average-balance data.\n', encoding='utf-8')
    return summary


def analyze(args):
    source = args.run_dir or SAVED_DATA
    manifest = read_manifest(source)
    batch = RESULTS/'organized_analysis'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    command = ['--run-dir', source, '--output', batch, '--min-years', args.min_years]
    if args.subsectors:
        command += ['--subsectors', args.subsectors]
    print('STEP 1: Read saved healthcare financials (no SEC downloads).', flush=True)
    print('STEP 2: Apply quality checks, compare companies and create graphs.', flush=True)
    run_program('HealthcareAnalysis.py', command)
    reports = list(batch.glob('*/analysis_report.md'))
    if len(reports) != 1:
        raise ValueError('Expected exactly one analysis report in this new run')
    analysis = reports[0].parent
    summary = summarize(source, analysis, manifest)
    print(f"STEP 3: Saved {summary['included_company_count']}-company summary.\nOpen: {analysis/'START_HERE.md'}")


# 4. AI REVIEW: require matching original filing provenance; preview first.

def ai(args):
    if args.run_dir is None:
        raise ValueError('AI review needs --run-dir pointing to a HealthcareStats collection with Item 1A JSONL.')
    manifest = read_manifest(args.run_dir)
    if manifest.get('original_filings_only') is not True:
        raise ValueError('Use the original-filing collection for AI review. The recovered comparative dataset has different filing dates/accessions.')
    if not (args.run_dir/'staged_10k_batch.jsonl').exists():
        raise ValueError('The selected collection has no staged_10k_batch.jsonl')
    command = ['--run-dir', args.run_dir, '--output', RESULTS/'ai_review',
               '--question', args.question, '--model', args.model, '--max-requests', args.max_requests]
    if args.execute:
        command += ['--execute']
    run_program('AIResearch.py', command)


# 5. CHOOSE A STAGE

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', nargs='?', choices=['collect', 'analyze', 'ai'])
    parser.add_argument('--run-dir', type=Path)
    parser.add_argument('--min-years', type=int, default=5)
    parser.add_argument('--subsectors', type=Path)
    parser.add_argument('--question', default=QUESTION)
    parser.add_argument('--model', default='gpt-4.1-mini')
    parser.add_argument('--max-requests', type=int, default=3)
    parser.add_argument('--execute', action='store_true', help='Explicitly enable paid AI calls for the ai stage')
    args = parser.parse_args()
    if args.min_years < 1 or args.max_requests < 1:
        parser.error('Year and request limits must be positive')
    if args.execute and args.stage != 'ai':
        parser.error('--execute applies only to the ai stage')
    try:
        if args.stage == 'collect':
            run_program('HealthcareStats.py', ['--sector', 'healthcare', '--start-year', 2020, '--end-year', 2025])
        elif args.stage == 'analyze':
            analyze(args)
        elif args.stage == 'ai':
            ai(args)
        else:
            print('HEALTHCARE WORKFLOW\n'
                  '  python HealthcareWorkflow.py analyze   Analyze the saved recovered data.\n'
                  '  python HealthcareWorkflow.py collect   Download/check SEC data when needed.\n'
                  '  python HealthcareWorkflow.py ai --run-dir PATH   Preview original-filing AI tasks.\n'
                  'Start with analyze. AI preview makes no paid calls; --execute enables them.\n'
                  'Instructions: healthcare/WORKFLOW.md')
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'Healthcare workflow stopped: {exc}\n')


if __name__ == '__main__':
    main()
