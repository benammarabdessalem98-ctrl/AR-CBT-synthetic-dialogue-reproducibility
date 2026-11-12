#!/usr/bin/env python3
"""Reproduce retained pilot ratings and V11 descriptive diagnostics without a GPU.
New results go to analysis_v11/; never rewrites raw model records or V1 analyses.
No inference, score repair, imputation, clinical coding, or significance tests.
"""
from __future__ import annotations
import argparse, csv, json, platform, sys
from pathlib import Path
import numpy as np
import pandas as pd
import scipy
from scipy.stats import pearsonr, spearmanr
from common import *


def write_csv(path, rows):
    data=pd.DataFrame(rows).to_csv(index=False,float_format='%.10g').encode('utf-8')
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and path.read_bytes()!=data:raise ValueError(f'Refusing different output: {path}')
    if not path.exists():path.write_bytes(data)


def kappa(x,y,quadratic=False):
    x=np.asarray(x,dtype=int);y=np.asarray(y,dtype=int)
    observed=np.zeros((8,8),dtype=float)
    for a,b in zip(x,y):observed[a,b]+=1
    observed/=len(x);expected=np.outer(observed.sum(1),observed.sum(0))
    weights=(np.arange(8)[:,None]-np.arange(8)[None,:])**2/49 if quadratic else 1-np.eye(8)
    den=float(np.sum(weights*expected))
    return None if den==0 else 1-float(np.sum(weights*observed))/den


def associations(x,y):
    x=np.array(x,dtype=float);y=np.array(y,dtype=float)
    varied=len(x)>1 and np.ptp(x)>0 and np.ptp(y)>0
    d=y-x
    return {'n_common':len(x),
      'pearson':float(pearsonr(x,y).statistic) if varied else None,
      'spearman':float(spearmanr(x,y).statistic) if varied else None,
      'mean_phi_minus_mistral':float(d.mean()),
      'mean_absolute_difference':float(np.abs(d).mean()),
      'median_absolute_difference':float(np.median(np.abs(d))),
      'exact_agreement':float(np.mean(np.isclose(d,0,rtol=0,atol=1e-12))),
      'within_one_point':float(np.mean(np.abs(d)<=1+1e-12))}


def run(pilot_root:Path, out:Path):
    p=Path(pilot_root);out=Path(out)
    if out.resolve() in [p.resolve(),(p/'analysis').resolve(),(p/'automated_judging').resolve()]:
        raise ValueError('Use a new analysis directory, not the retained archive')
    out.mkdir(parents=True,exist_ok=True)
    refs,variants,judges=load_verified_bundle(p)
    score_rows=[];parse_rows=[];flow=[];all_pairs=[];target_rows=[];error_rows=[];edit_rows=[]
    dims=DIMS+['overall']
    for judge,ratings in judges.items():
        for bid,r in sorted(ratings.items()):
            v=variants[bid];a=r['response'];q=r['request']
            row={'judge':judge,'blind_id':bid,'base_case_id':v['base_case_id'],
                'condition':v['condition'],'status':a['status']}
            if r['parsed'] is not None:
                row.update(r['parsed']['scores']);row['overall']=sum(r['parsed']['scores'].values())/6
                row['confidence']=r['parsed']['confidence']
            score_rows.append(row)
            for policy,allow in [('common_strict',False),('common_outer_fence_only',True)]:
                try: parsed,mode=parse_rating(a['raw_text'],bid,allow);ok=True;error=''
                except (ValueError,TypeError) as exc:ok=False;mode='';error=str(exc)
                parse_rows.append({'judge':judge,'blind_id':bid,'policy':policy,'valid':ok,'normalization':mode,'error':error})
            if a['status']=='parse_failure':
                eos=q['generation_config']['eos_token_id'];eos=eos if isinstance(eos,list) else [eos]
                ids=a['output_ids']
                error_rows.append({'judge':judge,'blind_id':bid,'base_case_id':v['base_case_id'],'condition':v['condition'],
                    'output_tokens':len(ids),'at_token_limit':len(ids)==q['generation_config']['max_new_tokens'],
                    'last_token_is_eos':bool(ids and ids[-1] in eos),'recorded_error_type':a['parse_error_type'],'recorded_error':a['parse_error']})
        for condition in CONDITIONS:
            subset=[r for r in score_rows if r['judge']==judge and r['condition']==condition]
            flow.append({'judge':judge,'condition':condition,'submitted':len(subset),
                'valid':sum(r['status']=='valid_json' for r in subset),
                'parse_failure':sum(r['status']=='parse_failure' for r in subset)})
    df=pd.DataFrame(score_rows);valid=df[df.status=='valid_json'].copy()
    def paired_for(judge,case,condition):
        ref=valid[(valid.judge==judge)&(valid.base_case_id==case)&(valid.condition=='reference')]
        ctrl=valid[(valid.judge==judge)&(valid.base_case_id==case)&(valid.condition==condition)]
        return (ref.iloc[0],ctrl.iloc[0]) if len(ref)==1 and len(ctrl)==1 else None
    for judge in judges:
        for cid in refs:
            for condition in CONDITIONS[1:]:
                pair=paired_for(judge,cid,condition)
                if pair is None:continue
                ref,ctrl=pair
                for dim in dims:
                    all_pairs.append({'judge':judge,'base_case_id':cid,'condition':condition,'dimension':dim,
                        'reference_blind_id':ref.blind_id,'control_blind_id':ctrl.blind_id,
                        'reference_score':float(ref[dim]),'control_score':float(ctrl[dim]),'difference':float(ctrl[dim]-ref[dim])})
    pair_df=pd.DataFrame(all_pairs)
    for (judge,condition,dim),g in pair_df.groupby(['judge','condition','dimension'],sort=True):
        d=g.difference.to_numpy()
        target_rows.append({'judge':judge,'condition':condition,'dimension':dim,'n_pairs':len(d),
            'mean_difference':float(d.mean()),'median_difference':float(np.median(d)),
            'control_lower':int((d<0).sum()),'same_score':int((d==0).sum()),'control_higher':int((d>0).sum())})
    common=valid[valid.judge=='mistral'].merge(valid[valid.judge=='phi'],on='blind_id',suffixes=('_mistral','_phi'),validate='one_to_one')
    agree=[]
    for dim in dims:
        x=common[dim+'_mistral'];y=common[dim+'_phi']
        row={'dimension':dim,**associations(x,y)}
        if dim!='overall':row.update(unweighted_kappa=kappa(x,y),quadratic_weighted_kappa=kappa(x,y,True))
        agree.append(row)
    influence=[]
    for cid in refs:
        c=common[common.base_case_id_mistral!=cid]
        influence.append({'base_case_removed':cid,'sensitivity':'post_unblinding_leave_one_base_case_out',**associations(c.overall_mistral,c.overall_phi)})
    sensitivity=[]
    for judge in judges:
        for cid in refs:
            for condition in CONDITIONS[1:]:
                pair=paired_for(judge,cid,condition)
                if pair is None:continue
                ref,ctrl=pair
                for rule in ['mean_all_six','median_all_six']+['mean_without_'+dim for dim in DIMS]:
                    included=[d for d in DIMS if rule!='mean_without_'+d]
                    fun=np.median if rule=='median_all_six' else np.mean
                    a=float(fun([ref[d] for d in included]));b=float(fun([ctrl[d] for d in included]))
                    sensitivity.append({'judge':judge,'base_case_id':cid,'condition':condition,'aggregation':rule,'reference_score':a,'control_score':b,'difference':b-a})
    # Structural edit audit: positions/retained text, NOT independent clinical annotation.
    for bid,v in sorted(variants.items()):
        source=refs[v['base_case_id']]['messages']
        changed=[a['turn_id'] for a,b in zip(source,v['messages']) if a['role']=='therapist' and a['text']!=b['text']]
        preserved_patient=all(a['text']==b['text'] for a,b in zip(source,v['messages']) if a['role']=='patient')
        if changed!=list(EDITS[v['condition']]):raise ValueError('Unexpected intervention positions')
        chars=lambda ms:sum(len(m['text']) for m in ms if m['role']=='therapist')
        edit_rows.append({'blind_id':bid,'base_case_id':v['base_case_id'],'condition':v['condition'],
            'changed_therapist_turns':';'.join(map(str,changed)), 'patient_text_preserved':preserved_patient,
            'therapist_chars_reference':chars(source),'therapist_chars_variant':chars(v['messages']),
            'third_therapist_turn_preserved':v['messages'][5]['text']==source[5]['text'],
            'last_therapist_turn_preserved':v['messages'][7]['text']==source[7]['text'],
            'scope':'mechanical post-unblinding check; not content-validity rating'})
        # Exact reconstruction with source hashes, plus minimal model-facing text.
        write_once(p/'controlled_variants/labeled'/f"{v['transcript_id']}.json",{
            **v,'derivation':'reconstructed from archived reference and explicit replacement strings; checked against both judge requests',
            'changed_therapist_turns':changed})
        write_once(p/'controlled_variants/blinded_inputs'/f'{bid}.json',{'blind_id':bid,
          'messages':[{'role':m['role'],'text':m['text']} for m in v['messages']]})
    write_csv(out/'01_scores_unblinded.csv',score_rows)
    desc=[]
    for (judge,condition),g in valid.groupby(['judge','condition'],sort=True):
        for dim in dims:desc.append({'judge':judge,'condition':condition,'dimension':dim,'n_valid':len(g),
             'mean':float(g[dim].mean()),'median':float(g[dim].median()),'min':float(g[dim].min()),'max':float(g[dim].max())})
    write_csv(out/'02_condition_descriptives.csv',desc)
    write_csv(out/'03_all_paired_differences.csv',all_pairs)
    write_csv(out/'04_directional_summary.csv',target_rows)
    targets={'generic_exploration':['guided_discovery'],'supportive_non_cbt':['guided_discovery','strategy_change'],'no_homework':['homework_planning']}
    write_csv(out/'05_targeted_discrimination.csv',[r for r in target_rows if r['dimension'] in targets[r['condition']]])
    write_csv(out/'06_judge_agreement.csv',agree)
    write_csv(out/'07_output_flow_by_condition.csv',flow)
    write_csv(out/'08_parsing_sensitivity_individual.csv',parse_rows)
    parsing=pd.DataFrame(parse_rows).groupby(['judge','policy']).agg(n=('valid','size'),valid=('valid','sum')).reset_index()
    write_csv(out/'09_parsing_sensitivity_summary.csv',parsing.to_dict('records'))
    write_csv(out/'10_preserved_parse_failures.csv',error_rows)
    write_csv(out/'11_control_edit_scope.csv',edit_rows)
    write_csv(out/'12_aggregation_sensitivity.csv',sensitivity)
    write_csv(out/'13_leave_one_base_case_out.csv',influence)
    # Compare primary results with retained V1 CSV, do not overwrite it.
    previous=pd.read_csv(p/'analysis/05_targeted_discrimination.csv')
    current=pd.DataFrame([r for r in target_rows if r['dimension'] in targets[r['condition']]])
    for _,a in previous.iterrows():
        b=current[(current.judge==a.judge)&(current.condition==a.condition)&(current.dimension==a.target_dimension)].iloc[0]
        if int(a.available_pairs)!=int(b.n_pairs) or not np.isclose(float(a.mean_difference),float(b.mean_difference),atol=1e-9):
            raise ValueError('Original targeted statistics do not reproduce')
    summary={'analysis_id':'ARCBT_V11_DESCRIPTIVE_AUDIT','base_cases':5,'variants':20,
        'new_model_calls':0,'human_ratings':0,
        'primary_valid':{j:sum(v['parsed'] is not None for v in r.values()) for j,r in judges.items()},
        'n_common':len(common),'original_targeted_statistics_reproduced':True,
        'controls_reconstructed_and_verified':len(variants),
        'secondary_analyses':'Post-unblinding parsing-policy, aggregation, edit-scope, absolute-agreement and leave-one-base-case-out checks. Not preregistered.',
        'inference':'descriptive only; 20 variants are clustered within 5 base cases',
        'overall_agreement':next(r for r in agree if r['dimension']=='overall')}
    write_once(out/'SUMMARY.json',summary)
    print(json.dumps(summary,indent=2,ensure_ascii=False))
    return summary

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument('--out',type=Path)
    args=ap.parse_args();run(args.root,args.out or args.root/'analysis_v11')
