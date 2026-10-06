"""Analyze saved DuPont data. No downloads, AI calls, or automatic causal claims."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, adjusted_rand_score
from sklearn.preprocessing import StandardScaler

FEATURES = ['profit_margin', 'asset_turnover', 'equity_multiplier']
METRICS = FEATURES + ['roe']
LABELS = {'profit_margin':'Profit margin (%)','asset_turnover':'Asset turnover (x)',
          'equity_multiplier':'Equity multiplier (x)','roe':'Return on equity (%)'}


def load_financials(path):
    df=pd.read_csv(path)
    required=['ticker','fiscal_year','equity_warning','source_url']+METRICS
    missing=set(required)-set(df.columns)
    if missing:raise ValueError(f'Missing columns: {sorted(missing)}')
    if df.empty:raise ValueError('No financial rows')
    df['ticker']=df.ticker.astype(str).str.strip().str.upper()
    df['fiscal_year']=pd.to_numeric(df.fiscal_year,errors='raise')
    if not np.isfinite(df.fiscal_year).all() or not (df.fiscal_year%1==0).all():
        raise ValueError('Fiscal years must be finite integers')
    df['fiscal_year']=df.fiscal_year.astype(int)
    if df.duplicated(['ticker','fiscal_year']).any():raise ValueError('Duplicate company-year rows')
    flags=df.equity_warning.astype(str).str.lower()
    if not flags.isin(['true','false']).all():raise ValueError('Unknown equity_warning value')
    df['equity_warning']=flags.eq('true')
    for col in METRICS:df[col]=pd.to_numeric(df[col],errors='raise')
    valid=np.isfinite(df[METRICS]).all(axis=1)
    if not np.allclose((df.profit_margin*df.asset_turnover*df.equity_multiplier)[valid],df.roe[valid],rtol=1e-6,atol=1e-9):
        raise ValueError('DuPont identity does not reconcile')
    df['analysis_exclusion']=np.where(~valid,'Nonfinite ratios',np.where(df.equity_warning,'Flagged equity',''))
    return df


def add_subsectors(df,path):
    if path is None:
        return df.assign(subsector='Unclassified')
    labels=pd.read_csv(path,dtype=str).fillna('')
    if not {'ticker','subsector','classification_source'} <= set(labels):
        raise ValueError('Classification file requires ticker, subsector, classification_source')
    labels['ticker']=labels.ticker.str.strip().str.upper()
    if labels.ticker.duplicated().any():raise ValueError('Duplicate classification tickers')
    labels['subsector']=labels.subsector.str.strip()
    if ((labels.subsector!='') & labels.classification_source.str.strip().eq('')).any():
        raise ValueError('Every assigned subsector needs a classification source')
    labels['subsector']=labels.subsector.replace('','Unclassified')
    return df.merge(labels[['ticker','subsector','classification_source']],on='ticker',how='left',validate='many_to_one').fillna({'subsector':'Unclassified','classification_source':''})


def outliers(company):
    rows=[]
    for metric in METRICS:
        s=company[metric];q1,q3=s.quantile([.25,.75]);iqr=q3-q1
        if len(s)<8 or iqr==0:continue
        for ticker,value in s.items():
            if value < q1-1.5*iqr or value > q3+1.5*iqr:
                rows.append(dict(ticker=ticker,metric=metric,value=value,lower=q1-1.5*iqr,upper=q3+1.5*iqr))
    return pd.DataFrame(rows,columns=['ticker','metric','value','lower','upper'])


def cluster_companies(company,out):
    note='Clustering requires at least six companies and three distinct feature profiles.'
    if len(company)<6:return note
    x=StandardScaler().fit_transform(company[FEATURES])
    unique=len(np.unique(x,axis=0))
    if unique<3:return note
    scores=[];models={}
    for k in range(2,min(6,len(x)-1,unique-1)+1):
        model=KMeans(n_clusters=k,random_state=42,n_init=20).fit(x)
        models[k]=model
        stability=[]
        for seed in [7,19,101]:
            other=KMeans(n_clusters=k,random_state=seed,n_init=10).fit_predict(x)
            stability.append(adjusted_rand_score(model.labels_,other))
        scores.append(dict(k=k,silhouette=silhouette_score(x,model.labels_),inertia=model.inertia_,
                           mean_seed_agreement=np.mean(stability)))
    table=pd.DataFrame(scores);table.to_csv(out/'cluster_scores.csv',index=False)
    best=int(table.sort_values(['silhouette','k'],ascending=[False,True]).iloc[0].k)
    result=company.copy();result['cluster_k2']=models[2].labels_+1;result['cluster_selected']=models[best].labels_+1
    result.to_csv(out/'company_clusters.csv')
    result.groupby('cluster_selected')[METRICS].median().to_csv(out/'cluster_profiles.csv')
    pd.crosstab(result.cluster_selected,result.subsector).to_csv(out/'clusters_by_subsector.csv')
    pd.crosstab(result.cluster_k2,result.subsector).to_csv(out/'k2_by_subsector.csv')
    fig,ax=plt.subplots(figsize=(8,5));ax.plot(table.k,table.silhouette,marker='o')
    ax.set(xlabel='Number of clusters',ylabel='Silhouette score',title='Exploratory cluster separation')
    ax.set_xticks(table.k);fig.tight_layout();fig.savefig(out/'cluster_selection.png',dpi=160);plt.close(fig)
    return f'Selected K={best} by highest silhouette among tested K values. Seed agreement is not sampling stability. Results are exploratory and sensitive to scaling/outliers.'


def analyze(df,out,start,end,min_years):
    clean=df[df.analysis_exclusion.eq('')].copy()
    if clean.empty:raise ValueError('No usable rows after quality exclusions')
    counts=clean.groupby('ticker').fiscal_year.nunique()
    eligible=counts[counts>=min_years].index
    company=clean[clean.ticker.isin(eligible)].groupby('ticker')[METRICS].mean()
    company=company.join(counts.rename('years_available')).join(clean.groupby('ticker').subsector.first())
    company.to_csv(out/'company_averages.csv')
    outliers(company).to_csv(out/'company_outliers.csv',index=False)
    summary=clean.groupby(['subsector','fiscal_year'])[METRICS].agg(['median','count','std',lambda x:x.quantile(.25),lambda x:x.quantile(.75)])
    summary.to_csv(out/'subsector_summary.csv')
    balanced=counts[counts==end-start+1].index
    clean[clean.ticker.isin(balanced)].groupby('fiscal_year')[METRICS].median().to_csv(out/'balanced_panel_medians.csv')
    fig,ax=plt.subplots(figsize=(10,6))
    for subset,label in [(clean,'All available companies'),(clean[clean.ticker.isin(balanced)],'Complete-year companies')]:
        med=subset.groupby('fiscal_year').roe.median().reindex(range(start,end+1))
        ax.plot(med.index,med*100,marker='o',label=label)
    ax.set(title='Does changing company coverage affect median ROE?',xlabel='Fiscal year',ylabel='Median ROE (%)')
    ax.set_xticks(range(start,end+1));ax.legend();fig.tight_layout();fig.savefig(out/'coverage_sensitivity.png',dpi=160);plt.close(fig)
    latest=clean[clean.fiscal_year==end]
    for metric in METRICS:
        groups=latest[latest.subsector!='Unclassified'].groupby('subsector')[metric].agg(['median','count'])
        groups.to_csv(out/f'{metric}_subsector_comparison.csv')
        if groups.empty:continue
        groups=groups.sort_values('median');factor=100 if metric in ['roe','profit_margin'] else 1
        fig,ax=plt.subplots(figsize=(10,max(4,len(groups)*.5)))
        ax.barh([f'{i} (n={int(r["count"])})' for i,r in groups.iterrows()],groups['median']*factor,color='#2465a4')
        ax.set(title=f'Subsector comparison — {end}',xlabel=LABELS[metric]);ax.axvline(0,color='gray',linewidth=.8)
        fig.tight_layout();fig.savefig(out/f'{metric}_subsectors.png',dpi=160);plt.close(fig)
    pairs=clean.merge(clean.assign(fiscal_year=clean.fiscal_year+1),on=['ticker','fiscal_year'],suffixes=('','_prior'))
    pairs['margin_change_pp']=100*(pairs.profit_margin-pairs.profit_margin_prior)
    pairs['roe_change_pp']=100*(pairs.roe-pairs.roe_prior)
    pairs.sort_values('margin_change_pp').to_csv(out/'annual_changes.csv',index=False)
    # Descriptive between-company association only. No p-values or causal labels.
    if len(company)>=8:
        company[METRICS].corr(method='spearman').to_csv(out/'descriptive_company_correlations.csv')
    questions=[]
    for r in pairs.assign(abs_change=pairs.margin_change_pp.abs()).sort_values('abs_change',ascending=False).head(10).itertuples():
        questions.append(dict(ticker=r.ticker,fiscal_year=int(r.fiscal_year),subsector=r.subsector,
            question=f'What disclosed risks might relate to the {r.margin_change_pp:+.2f} percentage-point profit-margin change at {r.ticker} in {r.fiscal_year}, and what evidence is needed to establish actual causes?',
            evidence=dict(profit_margin=r.profit_margin,prior_profit_margin=r.profit_margin_prior,roe=r.roe,prior_roe=r.roe_prior),
            source_url=r.source_url,prior_source_url=r.source_url_prior,
            interpretation='Exploratory retrospective question, not evidence of causation or prediction.'))
    (out/'research_questions.json').write_text(json.dumps(questions,indent=2,allow_nan=False),encoding='utf-8')
    note=cluster_companies(company,out)
    report=f'''# Healthcare statistical review

Usable rows: {len(clean)} / {len(df)}. Companies: {clean.ticker.nunique()}.
Company-level analyses require at least {min_years} years: {len(company)} eligible companies.
Complete {start}–{end} panel: {len(balanced)} companies.
Unclassified companies: {clean.loc[clean.subsector.eq('Unclassified'),'ticker'].nunique()}.

{note}

- Financial quality exclusions remain in quality_review.csv; missing data is not imputed.
- Subsector medians represent available companies; groups with few companies are descriptive only.
- Outliers use 1.5-IQR fences on company averages (minimum eight companies); they are review candidates, not errors or significance tests. Mixed subsectors can explain outliers.
- Company averages can cover different years. Compare balanced_panel_medians.csv before attributing changes to economics.
- Clustering standardizes margin, turnover and multiplier; ROE is excluded as a redundant product. K=2 and selected K are both saved. The healthcare-only run cannot reproduce the assignment's two-sector comparison; that requires both sectors later.
- Spearman correlations, when produced, use one average per company. Correlations involving ROE/components are mechanically linked, not discoveries. There are no p-values or causal claims.
- No qualitative–quantitative correlations are computed yet: they require validated risk-category measurements, publication timing, a prespecified outcome, and company/year-aware inference.
- Research questions rank absolute margin changes and are hypothesis-generating. Item 1A describes potential risks; MD&A and financial notes are needed to investigate realized causes.
- research_questions.json is a saved question list. Automatic integration into AIResearch.py is not implemented; select a question and pass it with --question for now.
'''
    (out/'analysis_report.md').write_text(report,encoding='utf-8')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-dir',type=Path,required=True)
    p.add_argument('--subsectors',type=Path)
    p.add_argument('--output',type=Path)
    p.add_argument('--min-years',type=int,default=3)
    args=p.parse_args()
    if args.min_years<1:p.error('min-years must be positive')
    source=args.run_dir/'financials.csv';df=load_financials(source)
    manifest_path=args.run_dir/'manifest.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
    start,end=manifest.get('years',[int(df.fiscal_year.min()),int(df.fiscal_year.max())])
    if start>end or not df.fiscal_year.between(start,end).all():raise ValueError('Invalid or conflicting year range')
    df=add_subsectors(df,args.subsectors)
    base=args.output or args.run_dir/'analysis'
    out=base/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True)
    df.to_csv(out/'quality_review.csv',index=False)
    template=pd.DataFrame({'ticker':sorted(df.ticker.unique())});template['subsector']='';template['classification_source']=''
    template.to_csv(out/'subsector_template.csv',index=False)
    universe=manifest.get('companies',sorted(df.ticker.unique()))
    coverage=pd.MultiIndex.from_product([universe,range(start,end+1)],names=['ticker','fiscal_year']).to_frame(index=False)
    coverage.merge(df[['ticker','fiscal_year','analysis_exclusion']].assign(financial_available=True),how='left').to_csv(out/'analysis_coverage.csv',index=False)
    analyze(df,out,start,end,args.min_years)
    (out/'analysis_manifest.json').write_text(json.dumps(dict(financials_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        program_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),min_years=args.min_years,
        subsectors_sha256=hashlib.sha256(args.subsectors.read_bytes()).hexdigest() if args.subsectors else None),indent=2),encoding='utf-8')
    print(f'Analysis saved to {out}')


if __name__=='__main__':main()
