#!/usr/bin/env python3
"""AR-CBT V8: reproducible arithmetic audit of supplied automated-score columns.
No LLM/API call; no human validation; no generation or reconstruction of sessions.
Input column names are retained verbatim for traceability, not interpreted as people.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, platform, sys
from pathlib import Path
import numpy as np
import scipy
from scipy.stats import pearsonr, spearmanr, rankdata

COLS=['Session','Rater1','Rater2','ModelScore']

def load_scores(path: str|Path) -> tuple[list[str], np.ndarray]:
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames != COLS: raise ValueError(f'Expected exact headers {COLS}; got {reader.fieldnames}')
        rows=list(reader)
    ids=[r['Session'].strip() for r in rows]
    if not ids or any(not s for s in ids) or len(ids)!=len(set(ids)):
        raise ValueError('Session labels must be non-empty and unique. No rows are silently dropped.')
    try: x=np.asarray([[float(r[c]) for c in COLS[1:]] for r in rows],dtype=float)
    except (ValueError,TypeError) as exc: raise ValueError('All three score columns must be numeric.') from exc
    if not np.isfinite(x).all(): raise ValueError('Missing/nonfinite score detected. No imputation is performed.')
    return ids,x

def _kappa(a: np.ndarray,b: np.ndarray) -> dict:
    labels=np.union1d(a,b)
    pa=np.asarray([(a==v).mean() for v in labels]); pb=np.asarray([(b==v).mean() for v in labels])
    po=float(np.mean(a==b)); pe=float(pa@pb)
    return {'kappa':float((po-pe)/(1-pe)) if pe<1 else None,'observed_agreement':po,'chance_agreement':pe}

def categorical_audit(a: np.ndarray,b: np.ndarray) -> dict:
    return {'nearest_even':_kappa(np.rint(a),np.rint(b)),
            'cutoff_4':_kappa((a>=4).astype(int),(b>=4).astype(int)),
            'scope':'Post-hoc numerical audit only. Nearest-even rounding is not a recovered historical protocol. The cutoff 4 is not a validated adequacy threshold. No human raters are represented.'}

def summarize(ids:list[str],x:np.ndarray,n_boot:int=10000,seed:int=42)->dict:
    if x.shape!=(len(ids),3) or len(ids)<3 or not np.isfinite(x).all(): raise ValueError('Expected at least 3 complete records and 3 score columns.')
    if np.any(np.ptp(x,axis=0)==0): raise ValueError('Correlation cannot be computed for a constant series.')
    a,b,m=x.T; ref=(a+b)/2; diff=m-ref
    series=[]
    for i,c in enumerate(COLS[1:]):
        s=x[:,i]
        series.append({'column':c,'n':len(s),'mean':float(s.mean()),'sd':float(s.std(ddof=1)),
                       'median':float(np.median(s)),'iqr':float(np.quantile(s,.75)-np.quantile(s,.25)),
                       'min':float(s.min()),'max':float(s.max())})
    pairs=[]
    for i,j in [(0,1),(0,2),(1,2)]:
        pairs.append({'series_1':COLS[i+1],'series_2':COLS[j+1],
                      'pearson_r':float(pearsonr(x[:,i],x[:,j]).statistic),
                      'spearman_rho':float(spearmanr(x[:,i],x[:,j]).statistic)})
    if n_boot<1: raise ValueError('n_boot must be positive.')
    # Resample complete rows. This assumes exchangeable rows; it does not address
    # unknown scenario clusters or shared-model dependence.
    rng=np.random.default_rng(seed)
    ix=rng.integers(0,len(ids),size=(n_boot,len(ids)))
    ra=rankdata(ref[ix],axis=1); rb=rankdata(m[ix],axis=1)
    ra-=ra.mean(axis=1,keepdims=True); rb-=rb.mean(axis=1,keepdims=True)
    den=np.sqrt(np.sum(ra*ra,axis=1)*np.sum(rb*rb,axis=1))
    ok=den>0; boot=(np.sum(ra*rb,axis=1)[ok]/den[ok])
    comp={'reference':'Arithmetic mean (Rater1 + Rater2)/2; not a human reference, consensus, or ground truth.',
          'pearson_r':float(pearsonr(ref,m).statistic),'spearman_rho':float(spearmanr(ref,m).statistic),
          'mean_difference':float(diff.mean()),'mae':float(np.abs(diff).mean()),'rmse':float(np.sqrt(np.mean(diff**2))),
          'min_difference':float(diff.min()),'max_difference':float(diff.max()),
          'row_bootstrap_ci':[float(v) for v in np.quantile(boot,[.025,.975])],
          'bootstrap_resamples':n_boot,'bootstrap_valid':int(ok.sum()),'bootstrap_seed':seed,
          'bootstrap_scope':'Exploratory row-wise percentile interval, not cluster-adjusted or evidence of clinical/evaluator validity.'}
    return {'n_records':len(ids),'n_numeric_scores':int(x.size),'series':series,'pairwise':pairs,
            'reference_comparison':comp,'categorical_audit':categorical_audit(a,b),
            'scope':'Author reports dialogue-level LLM scoring and no human raters. Source records do not identify the systems behind columns. Arithmetic reproducibility is not execution provenance.'}

def write_csv(path:Path,rows:list[dict]):
    if not rows: return
    with path.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    default=Path(__file__).resolve().parents[1]
    ap.add_argument('--data',type=Path,default=default/'data'/'scores_80_original_columns.csv')
    ap.add_argument('--summary',type=Path,default=default/'data'/'legacy_summary_original_labels.csv')
    ap.add_argument('--out',type=Path,default=default/'results')
    ap.add_argument('--bootstrap',type=int,default=10000); ap.add_argument('--seed',type=int,default=42)
    args=ap.parse_args(); ids,x=load_scores(args.data); result=summarize(ids,x,args.bootstrap,args.seed)
    args.out.mkdir(parents=True,exist_ok=True)
    result['input_sha256']=hashlib.sha256(args.data.read_bytes()).hexdigest()
    result['environment']={'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__}
    (args.out/'analysis_results.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf8')
    write_csv(args.out/'series_descriptives.csv',result['series']); write_csv(args.out/'pairwise_correlations.csv',result['pairwise'])
    write_csv(args.out/'record_level_audit.csv',[{'Session':sid,'Rater1':float(row[0]),'Rater2':float(row[1]),'ModelScore':float(row[2]),
              'ArithmeticReference':float((row[0]+row[1])/2),'Difference':float(row[2]-(row[0]+row[1])/2)} for sid,row in zip(ids,x)])
    if args.summary.exists():
        with args.summary.open(newline='',encoding='utf8') as f: old=list(csv.DictReader(f))
        if len(old)!=1: raise ValueError('Legacy summary must contain exactly one data row.')
        computed={'Cohen_Kappa':result['categorical_audit']['nearest_even']['kappa'],
                  'Raters_Pearson':result['pairwise'][0]['pearson_r'],
                  'Rater1_Mean':result['series'][0]['mean'],'Rater2_Mean':result['series'][1]['mean'],
                  'Rater1_SD':result['series'][0]['sd'],'Rater2_SD':result['series'][1]['sd'],
                  'Human_Model_Correlation':result['reference_comparison']['pearson_r']}
        ver=[{'legacy_label':k,'source_value':float(old[0][k]),'recomputed_value':v,
              'absolute_difference':abs(float(old[0][k])-v),'matches_at_1e_minus_12':abs(float(old[0][k])-v)<=1e-12} for k,v in computed.items()]
        write_csv(args.out/'legacy_summary_verification.csv',ver)
        if not all(r['matches_at_1e_minus_12'] for r in ver): raise ValueError('Legacy summary check failed; inspect outputs.')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    ref=x[:,:2].mean(axis=1); m=x[:,2]; diff=m-ref
    fig,ax=plt.subplots(figsize=(7.2,4.6))
    ax.scatter(ref,m,alpha=.75)
    lo=min(ref.min(),m.min())-.1; hi=max(ref.max(),m.max())+.1
    ax.plot([lo,hi],[lo,hi],linestyle='--',label='Identity line (not fitted)')
    ax.set(xlabel='Arithmetic mean of Rater1 and Rater2',ylabel='ModelScore',title='Stored automated-score series: 80 labelled records')
    ax.legend(fontsize=9); fig.tight_layout(); fig.savefig(args.out/'Figure_1_Stored_Score_Association.png',dpi=600); plt.close(fig)
    fig,ax=plt.subplots(figsize=(7.2,4.6)); ax.scatter(ref,diff,alpha=.75)
    ax.axhline(0,linestyle='--',label='Zero difference'); ax.axhline(diff.mean(),linestyle=':',label=f'Mean difference = {diff.mean():.3f}')
    ax.set(xlabel='Arithmetic mean of Rater1 and Rater2',ylabel='ModelScore minus arithmetic reference',title='Score discrepancies; no human reference standard')
    ax.legend(fontsize=9); fig.tight_layout(); fig.savefig(args.out/'Figure_2_Stored_Score_Discrepancies.png',dpi=600); plt.close(fig)
    print(json.dumps({'records':len(ids),'reference_comparison':result['reference_comparison'],'outputs':str(args.out)},indent=2))
if __name__=='__main__': main()
