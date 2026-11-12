#!/usr/bin/env python3
"""New-run-only replay of archived model calls (never changes the study data).
Default --dry-run needs no GPU and downloads nothing. GPU replay is NOT a new
clinical validation. Therapist calls use the archived history for each turn;
this is conditional call replay, not a claim to regenerate a new interactive cohort.
"""
from __future__ import annotations
import argparse, gc, json, platform, sys
from pathlib import Path
from datetime import datetime,timezone
from importlib.metadata import version,PackageNotFoundError
from common import *

def planned_calls(root,role):
    refs,variants,judges=load_verified_bundle(root)
    if role=='therapist':
        for cid in sorted(refs):
            for t in range(1,5):
                f=root/f'synthetic_dialogues/reference/{cid}/turn_{t:02d}_request.json'
                q=read_json(f)
                yield f'{cid}_turn_{t:02d}',q['model'],q['input_ids'],q['attention_mask'],q['effective_generation_config'],q.get('seed'),sha(f.read_bytes()),q['rendered_prompt']
    else:
        for bid,r in sorted(judges[role].items()):
            q=r['request'];seed=20261106 if role=='mistral' else 20261109
            yield bid,q['judge'],q['input_ids'],q['attention_mask'],q['generation_config'],seed,r['request_sha256'],q['rendered_prompt']

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument('--role',choices=['therapist','mistral','phi'],required=True)
    ap.add_argument('--dry-run',action='store_true')
    ap.add_argument('--execute',action='store_true',help='Explicitly authorize downloads and new GPU calls')
    ap.add_argument('--out',type=Path)
    ap.add_argument('--gpu',type=int,default=0)
    ap.add_argument('--allow-environment-drift',action='store_true')
    args=ap.parse_args();calls=list(planned_calls(args.root,args.role))
    if args.dry_run or not args.execute:
        print(json.dumps({'mode':'dry_run','role':args.role,'planned_calls':len(calls),'model':calls[0][1],
          'new_model_calls':0,'outputs_unchanged':True,'purpose':'conditional replay; not historical recovery or new validation'},indent=2));return
    if args.out is None:raise ValueError('--out must specify a new directory outside the archived pilot')
    root=args.root.resolve();out=args.out.resolve()
    if out==root or root in out.parents or out.exists():raise ValueError('Output must be new and outside the archived pilot directory')
    import torch
    from transformers import AutoTokenizer,AutoModelForCausalLM,BitsAndBytesConfig,GenerationConfig,set_seed
    if not torch.cuda.is_available() or args.gpu>=torch.cuda.device_count():raise RuntimeError('Requested CUDA device unavailable')
    recorded=read_json(root/'technical_metadata/preparation.json')['environment']['packages']
    actual={}
    for name in recorded:
        try:actual[name]=version(name)
        except PackageNotFoundError:actual[name]=None
    drift={k:{'recorded':v,'current':actual[k]} for k,v in recorded.items() if actual[k]!=v}
    if drift and not args.allow_environment_drift:raise RuntimeError(f'Environment differs: {drift}. No run performed. Record differences before using --allow-environment-drift.')
    out.mkdir(parents=True,exist_ok=False)
    info=calls[0][1];device=f'cuda:{args.gpu}'
    manifest={'purpose':'new_conditional_replay_not_original_run','role':args.role,'model':info,
        'created_at_utc':datetime.now(timezone.utc).isoformat(),'environment':actual,'environment_drift':drift,
        'seed_provenance':'therapist request; judge seed from supplied notebook workflow, absent from archived judge requests',
        'trust_remote_code':False,'quantization':'NF4 double quant float16',
        'runner_sha256':sha(Path(__file__).read_bytes()),'original_records_writable':False}
    write_once(out/'RUN_MANIFEST.json',manifest)
    tokenizer=AutoTokenizer.from_pretrained(info['model_id'],revision=info['revision'],trust_remote_code=False,token=False)
    quant=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=torch.float16)
    kwargs={'revision':info['revision'],'quantization_config':quant,'dtype':torch.float16,'device_map':{'':args.gpu},'use_safetensors':True,'trust_remote_code':False,'token':False}
    if args.role!='phi':kwargs['attn_implementation']='sdpa'
    model=AutoModelForCausalLM.from_pretrained(info['model_id'],**kwargs);model.eval()
    for ident,info,ids,mask,cfg,seed,source_sha,prompt in calls:
        folder=out/ident;folder.mkdir()
        if tokenizer(prompt,add_special_tokens=False)['input_ids']!=ids:
            raise RuntimeError('Tokenizer output differs from recorded input_ids; stopped before generation')
        effective={k:v for k,v in cfg.items() if v is not None and not k.startswith('_') and k!='transformers_version'}
        config=GenerationConfig(**effective)
        q={'id':ident,'source_request_sha256':source_sha,'model':info,'input_ids':ids,'attention_mask':mask,
            'rendered_prompt':prompt,'generation_config':config.to_dict(),'seed':seed,'started_at_utc':datetime.now(timezone.utc).isoformat()}
        write_once(folder/'request.json',q);response={}
        try:
            if seed is not None:set_seed(seed)
            with torch.inference_mode():
                output=model.generate(input_ids=torch.tensor([ids],device=device),attention_mask=torch.tensor([mask],device=device),generation_config=config)
            new=output[0,len(ids):].cpu().tolist();text=tokenizer.decode(new,skip_special_tokens=True)
            response={'output_ids':new,'raw_text':text,'text_with_special_tokens':tokenizer.decode(new,skip_special_tokens=False),'status':'generated_not_study_data'}
            if args.role!='therapist':
                try:parsed,mode=parse_rating(text,ident,args.role=='phi');response.update(parsed=parsed,normalization=mode,parsing_status='valid_json')
                except ValueError as e:response.update(parsing_status='parse_failure',parse_error=str(e))
        except Exception as e:
            response.update(status='runtime_error',error_type=type(e).__name__,error=str(e));raise
        finally:
            response.update(finished_at_utc=datetime.now(timezone.utc).isoformat(),request_sha256=sha((folder/'request.json').read_bytes()))
            write_once(folder/'response.json',response)
        print(ident,response['status'],flush=True)
    del model;gc.collect();torch.cuda.empty_cache()
if __name__=='__main__':main()
