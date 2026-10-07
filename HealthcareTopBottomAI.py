"""Compare annual 2020–2025 healthcare ROE extremes with supplied Item 1A; dry-run by default."""
import argparse,json,os,getpass
from pathlib import Path
from AIResearch import INSTRUCTIONS,chunks,digest,schema,normalize,append
ROOT=Path(__file__).resolve().parent
QUESTION='Compare the highest and lowest ROE healthcare firms separately for each fiscal year from 2020 through 2025. Focus this assessment on ranking_year and the matched fiscal-year disclosure. For this firm, explain the supplied DuPont profile and 2020–2025 history, identify disclosed risks relevant to margin, turnover or equity, and distinguish possible mechanisms from demonstrated causes. Do not treat highest ROE as best investment. Do not infer risk differences merely from the selected extreme groups.'
def filter_findings(result,evidence):
 """Keep exact-source findings; preserve rejected findings separately for review."""
 accepted=[];rejected=[]
 for finding in result['findings']:
  quote=normalize(finding['supporting_quote'])
  reason=None
  if not quote or quote not in normalize(evidence['item_1a_excerpt']):reason='Quote failed exact source validation'
  elif finding['source_url']!=evidence['filing']['source_url']:reason='Source URL mismatch'
  if reason:rejected.append(dict(reason=reason,finding=finding))
  else:accepted.append(finding)
 clean=dict(result,findings=accepted,limitations=list(result['limitations']))
 if rejected:clean['limitations'].append(f'{len(rejected)} finding(s) excluded for unsupported quotes or URLs; manual review required. This chunk is only partially validated, even if no findings remain.')
 return clean,rejected

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');p.add_argument('--model',default='gpt-4.1-mini');p.add_argument('--input',type=Path,default=ROOT/'healthcare/reports/top_bottom_all_years/comparison_inputs.jsonl');p.add_argument('--output',type=Path,default=ROOT/'healthcare/results/top_bottom_all_years_ai');a=p.parse_args()
 records=[json.loads(s) for s in a.input.read_text().splitlines() if s.strip()];tasks=[]
 for record in records:
  text=record['filing']['item_1a_text'];pieces=chunks(text)
  for i,part in enumerate(pieces,1):
   evidence=dict(record);evidence['filing']={k:v for k,v in record['filing'].items() if k!='item_1a_text'};evidence.update(research_question=QUESTION,item_1a_excerpt=part,chunk_number=i,total_chunks=len(pieces))
   tasks.append((digest(dict(model=a.model,instructions=INSTRUCTIONS,payload=evidence)),evidence))
 a.output.mkdir(parents=True,exist_ok=True);resultfile=a.output/'analyses.jsonl';done={}
 if resultfile.exists():done={r['task_id']:r for r in map(json.loads,resultfile.read_text().splitlines())}
 pending=[(k,v) for k,v in tasks if k not in done];plan=dict(unique_companies=len({r["ticker"] for r in records}),company_years=len(records),years=sorted({r["filing"]["fiscal_year"] for r in records}),total_chunks=len(tasks),pending_chunks=len(pending),model=a.model,question=QUESTION,missing='See risk_coverage.csv beside the input for unmatched selected company-years; no substitutes',execute=a.execute)
 (a.output/'plan.json').write_text(json.dumps(plan,indent=2));print(json.dumps(plan,indent=2))
 if not a.execute:print('Dry run: no API calls. Add --execute to run.');return
 api_key=os.getenv('OPENAI_API_KEY','').strip()
 if not api_key:
  try:
   api_key=getpass.getpass('Paste your OpenAI API key (hidden), then press Enter: ').strip()
  except (EOFError,KeyboardInterrupt):
   raise SystemExit('Key entry cancelled. No API requests made.')
 if not api_key:raise SystemExit('No API key entered. No API requests made.')
 if not api_key.isascii() or any(c.isspace() for c in api_key):raise SystemExit('The key contains invalid characters or spaces. Copy only the API key and try again; no API requests made.')
 from openai import OpenAI
 client=OpenAI(api_key=api_key,timeout=120,max_retries=0)
 lock=a.output/'.running.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd)
 try:
  for key,evidence in pending:
   print(f"Analyzing {evidence['ticker']} FY{evidence['filing']['fiscal_year']} chunk {evidence['chunk_number']}/{evidence['total_chunks']}",flush=True)
   response=client.responses.parse(model=a.model,instructions=INSTRUCTIONS,input=json.dumps(evidence),text_format=schema(),max_output_tokens=4000,store=False)
   append(a.output/'responses.jsonl',dict(task_id=key,response=response.model_dump(mode='json')))
   if response.output_parsed is None:raise ValueError('Incomplete structured response; inspect responses.jsonl')
   result=response.output_parsed.model_dump()
   result,rejected=filter_findings(result,evidence)
   if rejected:
    append(a.output/'validation_issues.jsonl',dict(task_id=key,ticker=evidence['ticker'],fiscal_year=evidence['filing']['fiscal_year'],rejected=rejected))
    print(f"Flagged {len(rejected)} unsupported finding(s); continuing with validated findings only.",flush=True)
   row=dict(task_id=key,ticker=evidence['ticker'],group=evidence['group'],fiscal_year=evidence['filing']['fiscal_year'],chunk=evidence['chunk_number'],validation_status="partial_needs_review" if rejected else "quotes_checked",analysis=result);append(resultfile,row);done[key]=row
   lines=['# Healthcare top/bottom ROE risk comparison','',QUESTION,'','Separate annual 2020–2025 rankings; historical financial context. AI interpretations require human review. See risk_coverage.csv for missing disclosures. Quotes/URLs checked against inputs; claims are not causally verified.','']
   for group in ['Top 10','Bottom 10']:
    lines += ['## '+group,'']
    for taskid,payload in tasks:
     if taskid not in done or payload['group']!=group:continue
     output=done[taskid]['analysis'];lines += ['### '+payload['ticker']+f" FY{payload['filing']['fiscal_year']} — chunk {payload['chunk_number']}",'']
     for v in output['findings']:lines += [f"**{v['category']} / {v['component']}**",v['evidence_interpretation'],f"> {v['supporting_quote']}",v['source_url'],'Possible mechanism: '+v['possible_mechanism'],'Alternative to investigate: '+v['alternative_hypothesis'],'']
     lines += ['Limitations: '+'; '.join(output['limitations']),'Follow-up: '+'; '.join(output['follow_up_questions']),'']
   (a.output/'comparison_report.md').write_text('\n'.join(lines),encoding='utf-8')
 finally:lock.unlink()
if __name__=='__main__':main()
