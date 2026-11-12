#!/usr/bin/env python3
"""Regenerate the five scripted cases as a NEW run with evolving model history.
Nothing replaces the five archived dialogues. Computational replay and new
experimental evidence are distinct. GPU execution not performed by package author.
"""
from __future__ import annotations
import argparse,json,sys
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path
from datetime import datetime,timezone
from common import *

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument('--out',type=Path)
    ap.add_argument('--execute',action='store_true');ap.add_argument('--gpu',type=int,default=0)
    args=ap.parse_args();p=args.root
    refs,variants,judges=load_verified_bundle(p)
    cases=read_json(p/'protocol/cases.json');proto=read_json(p/'protocol/generation_protocol_v1.json')
    if not args.execute:
        print(json.dumps({'mode':'dry_run','cases':len(cases),'planned_calls':20,'new_model_calls':0,'study_data_overwrite':False}));return
    if args.out is None or args.out.exists() or p.resolve()==args.out.resolve() or p.resolve() in args.out.resolve().parents:
        raise ValueError('Provide a NEW --out outside archived pilot')
    import torch
    from transformers import AutoTokenizer,AutoModelForCausalLM,BitsAndBytesConfig,GenerationConfig,set_seed
    if not torch.cuda.is_available() or not 0 <= args.gpu < torch.cuda.device_count():raise RuntimeError('Requested CUDA GPU is unavailable')
    info=proto['therapist'];device=f'cuda:{args.gpu}';args.out.mkdir(parents=True)
    actual={}
    for package in read_json(p/'technical_metadata/preparation.json')['environment']['packages']:
        try:actual[package]=version(package)
        except PackageNotFoundError:actual[package]=None
    write_once(args.out/'RUN_MANIFEST.json',{'purpose':'new_run_not_replacement','model':info,'started_at_utc':datetime.now(timezone.utc).isoformat(),'generation_protocol':proto,'runner_sha256':sha(Path(__file__).read_bytes()),'current_environment':actual,'python':sys.version,'torch_cuda':torch.version.cuda,'gpu':torch.cuda.get_device_name(args.gpu),'trust_remote_code':False,'attention':'sdpa','quantization':'NF4_double_quant_float16','bitwise_reproduction_claimed':False})
    tok=AutoTokenizer.from_pretrained(info['model_id'],revision=info['revision'],trust_remote_code=False,token=False)
    quant=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=torch.float16)
    model=AutoModelForCausalLM.from_pretrained(info['model_id'],revision=info['revision'],quantization_config=quant,dtype=torch.float16,device_map={'':args.gpu},attn_implementation='sdpa',trust_remote_code=False,token=False,use_safetensors=True);model.eval()
    original=read_json(p/'synthetic_dialogues/reference/P01/execution.json')['effective_generation_config']
    cfg=GenerationConfig(**{k:v for k,v in original.items() if v is not None and not k.startswith('_') and k!='transformers_version'})
    consigne=(p/'protocol/therapist_prompt.txt').read_text(encoding='utf-8')
    for case in cases:
        cid=case['scenario_id'];folder=args.out/cid;folder.mkdir();messages=[{'role':'system','content':consigne}];transcript=[]
        for t,patient in enumerate(case['patient_utterances'],1):
            messages.append({'role':'user','content':patient});rendered=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
            inputs=tok(rendered,return_tensors='pt',add_special_tokens=False,truncation=False);n=inputs['input_ids'].shape[1]
            req={'messages':messages,'rendered_prompt':rendered,'model':info,'input_ids':inputs['input_ids'][0].tolist(),'attention_mask':inputs['attention_mask'][0].tolist(),'seed':proto['seed'],'generation_config':cfg.to_dict(),'started_at_utc':datetime.now(timezone.utc).isoformat()}
            qp=folder/f'turn_{t:02d}_request.json';write_once(qp,req);rep={}
            try:
                if n>proto['generation']['max_input_tokens']:raise ValueError('Context overflow; no truncation')
                set_seed(proto['seed'])
                with torch.inference_mode():output=model.generate(**{k:v.to(device) for k,v in inputs.items()},generation_config=cfg)
                ids=output[0,n:].cpu().tolist();text=tok.decode(ids,skip_special_tokens=True)
                eos=cfg.eos_token_id if isinstance(cfg.eos_token_id,list) else [cfg.eos_token_id]
                rep={'output_ids':ids,'raw_text':text,'status':'generated','eos_observed':bool(ids and ids[-1] in eos)}
                if not text.strip() or not rep['eos_observed']:raise ValueError('Incomplete output; retained without retry')
            except Exception as e:rep.update(status='runtime_error',error=str(e));raise
            finally:rep.update(request_sha256=sha(qp.read_bytes()),finished_at_utc=datetime.now(timezone.utc).isoformat());write_once(folder/f'turn_{t:02d}_response.json',rep)
            transcript.extend([{'turn_id':t,'role':'patient','text':patient},{'turn_id':t,'role':'therapist','text':text}]);messages.append({'role':'assistant','content':text})
        write_once(folder/'transcript.json',{'scenario_id':cid,'messages':transcript,'status':'new_run_not_original_evidence'})
    print('New run complete. Do not substitute these outputs for archived study records.')
if __name__=='__main__':main()
