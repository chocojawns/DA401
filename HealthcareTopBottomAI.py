"""Compare 2025 healthcare ROE extremes with supplied Item 1A; dry-run by default."""
import argparse,json,os,getpass
from pathlib import Path
from AIResearch import INSTRUCTIONS,chunks,digest,schema,normalize,append
ROOT=Path(__file__).resolve().parent
QUESTION='Compare the highest and lowest 2025 ROE healthcare firms. For this firm, explain the supplied DuPont profile and 2020–2025 history, identify disclosed risks relevant to margin, turnover or equity, and distinguish possible mechanisms from demonstrated causes. Do not treat highest ROE as best investment. Do not infer risk differences merely from the selected extreme groups.'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');p.add_argument('--model',default='gpt-4.1-mini');p.add_argument('--input',type=Path,default=ROOT/'healthcare/reports/top_bottom_risk/comparison_inputs.jsonl');p.add_argument('--output',type=Path,default=ROOT/'healthcare/results/top_bottom_ai');a=p.parse_args()
 records=[json.loads(s) for s in a.input.read_text().splitlines() if s.strip()];tasks=[]
 for record in records:
  text=record['filing']['item_1a_text'];pieces=chunks(text)
  for i,part in enumerate(pieces,1):
   evidence=dict(record);evidence['filing']={k:v for k,v in record['filing'].items() if k!='item_1a_text'};evidence.update(research_question=QUESTION,item_1a_excerpt=part,chunk_number=i,total_chunks=len(pieces))
   tasks.append((digest(dict(model=a.model,instructions=INSTRUCTIONS,payload=evidence)),evidence))
 a.output.mkdir(parents=True,exist_ok=True);resultfile=a.output/'analyses.jsonl';done={}
 if resultfile.exists():done={r['task_id']:r for r in map(json.loads,resultfile.read_text().splitlines())}
 pending=[(k,v) for k,v in tasks if k not in done];plan=dict(companies=len(records),total_chunks=len(tasks),pending_chunks=len(pending),model=a.model,question=QUESTION,missing='ZBH: automatic Item 1A extraction failed; not silently substituted',execute=a.execute)
 (a.output/'plan.json').write_text(json.dumps(plan,indent=2));print(json.dumps(plan,indent=2))
 if not a.execute:print('Dry run: no API calls. Add --execute to run.');return
 api_key=os.getenv('OPENAI_API_KEY','').strip()
 if not api_key:
  try:
   api_key=getpass.getpass('Paste your OpenAI API key (hidden), then press Enter: ').strip()
  except (EOFError,KeyboardInterrupt):
   raise SystemExit('Key entry cancelled. No API requests made.')
 if not api_key:raise SystemExit('No API key entered. No API requests made.')
 from openai import OpenAI
 client=OpenAI(api_key=api_key,timeout=120,max_retries=0)
 lock=a.output/'.running.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd)
 try:
  for key,evidence in pending:
   print(f"Analyzing {evidence['ticker']} chunk {evidence['chunk_number']}/{evidence['total_chunks']}",flush=True)
   response=client.responses.parse(model=a.model,instructions=INSTRUCTIONS,input=json.dumps(evidence),text_format=schema(),max_output_tokens=4000,store=False)
   append(a.output/'responses.jsonl',dict(task_id=key,response=response.model_dump(mode='json')))
   if response.output_parsed is None:raise ValueError('Incomplete structured response; inspect responses.jsonl')
   result=response.output_parsed.model_dump()
   for finding in result['findings']:
    if not normalize(finding['supporting_quote']) or normalize(finding['supporting_quote']) not in normalize(evidence['item_1a_excerpt']):raise ValueError('Quote failed source validation')
    if finding['source_url']!=evidence['filing']['source_url']:raise ValueError('Source URL failed validation')
   row=dict(task_id=key,ticker=evidence['ticker'],group=evidence['group'],chunk=evidence['chunk_number'],analysis=result);append(resultfile,row);done[key]=row
   lines=['# Healthcare top/bottom ROE risk comparison','',QUESTION,'','2025 ranking; historical financial context. AI interpretations require human review. ZBH risk extraction unresolved. Quotes/URLs checked against inputs; claims are not causally verified.','']
   for group in ['Top 10','Bottom 10']:
    lines += ['## '+group,'']
    for taskid,payload in tasks:
     if taskid not in done or payload['group']!=group:continue
     output=done[taskid]['analysis'];lines += ['### '+payload['ticker']+f" — chunk {payload['chunk_number']}",'']
     for v in output['findings']:lines += [f"**{v['category']} / {v['component']}**",v['evidence_interpretation'],f"> {v['supporting_quote']}",v['source_url'],'Possible mechanism: '+v['possible_mechanism'],'Alternative to investigate: '+v['alternative_hypothesis'],'']
     lines += ['Limitations: '+'; '.join(output['limitations']),'Follow-up: '+'; '.join(output['follow_up_questions']),'']
   (a.output/'comparison_report.md').write_text('\n'.join(lines),encoding='utf-8')
 finally:lock.unlink()
if __name__=='__main__':main()
