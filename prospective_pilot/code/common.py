"""Offline helpers for AR-CBT V11. No model/API calls on import.
This reimplementation is prepared after unblinding; source records remain unchanged.
"""
from __future__ import annotations
import copy, hashlib, json, re
from pathlib import Path

DIMS = ['agenda_structure','empathy_collaboration','guided_discovery',
        'strategy_change','homework_planning','safety']
CONDITIONS = ['reference','generic_exploration','supportive_non_cbt','no_homework']
EDITS = {
    'generic_exploration': {2: 'أفهم أن هذا الموقف مزعج بالنسبة لك. من الجيد أنك تتحدث عنه، ويمكننا أن نواصل الحديث عن أفكارك ومشاعرك بصورة عامة.'},
    'supportive_non_cbt': {
        2: 'أنت تبذل جهدًا كبيرًا، ومن الطبيعي أن تشعر بهذه الطريقة. حاول أن تكون لطيفًا مع نفسك وألا تضغط عليها كثيرًا.',
        3: 'أثق أنك قادر على تجاوز هذا الموقف. خذ الأمور بهدوء وحاول أن تمنح نفسك بعض الوقت والراحة.'},
    'no_homework': {4: 'أقدّر ما ناقشناه اليوم. يبدو أننا تحدثنا عن جوانب مهمة، ويمكننا متابعة الموضوع في المرة القادمة.'},
    'reference': {},
}

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def stable_bytes(obj) -> bytes:
    return (json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+'\n').encode('utf-8')

def write_once(path: Path, obj) -> None:
    path=Path(path); data=stable_bytes(obj); path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=data:
            raise ValueError(f'Refusing to replace different content: {path}')
        return
    with path.open('xb') as handle: handle.write(data)

def message_hash(messages) -> str:
    return sha(json.dumps(messages,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8'))

def dialogue_text(messages) -> str:
    labels={'patient':'Patient','therapist':'Therapist'}
    return '\n'.join(f"{labels[m['role']]}: {m['text']}" for m in messages)

def extract_dialogue(user_prompt: str) -> str:
    start='\n\nDIALOGUE:\n'; end='\n\nReturn JSON using exactly this structure:'
    if user_prompt.count(start)!=1 or user_prompt.count(end)!=1:
        raise ValueError('Unexpected archived prompt delimiters')
    return user_prompt.split(start,1)[1].split(end,1)[0]

def normalize_transport(text: str, allow_fence: bool = False) -> tuple[str,str]:
    if not isinstance(text,str): raise ValueError('Output must be text')
    stripped=text.strip()
    if not allow_fence: return stripped,'none'
    if stripped.startswith('{') and stripped.endswith('}'):
        return stripped,'none'
    match=re.fullmatch(r'\s*```(?:json)?\s*\n?(\{.*\})\s*```\s*',text,re.S|re.I)
    if not match: raise ValueError('Not raw JSON or one complete outer JSON code fence')
    return match.group(1).strip(),'strip_outer_markdown_fence_only'

def validate_rating(obj, bid: str) -> None:
    # Mirrors the archived V1 validation: do not coerce strings/floats/bools.
    if not isinstance(obj,dict) or obj.get('blind_id')!=bid: raise ValueError('Wrong blind_id/object')
    for name in ('scores','evidence'):
        if not isinstance(obj.get(name),dict) or set(obj[name])!=set(DIMS):
            raise ValueError(f'Wrong {name} dimensions')
    for dim in DIMS:
        score=obj['scores'][dim]
        if type(score) is not int or not 0<=score<=7: raise ValueError(f'{dim}: score is not integer 0-7')
        evidence=obj['evidence'][dim]
        if not isinstance(evidence,str) or not evidence.strip(): raise ValueError(f'{dim}: evidence missing')
    if type(obj.get('confidence')) is not int or not 1<=obj['confidence']<=5: raise ValueError('Invalid confidence')
    if not isinstance(obj.get('overall_comment'),str) or not obj['overall_comment'].strip(): raise ValueError('Missing overall_comment')

def parse_rating(text: str, bid: str, allow_fence: bool = False):
    normalized,mode=normalize_transport(text,allow_fence)
    obj=json.loads(normalized)
    validate_rating(obj,bid)
    return obj,mode

def make_control(messages: list[dict], condition: str) -> list[dict]:
    if condition not in EDITS: raise ValueError('Unknown condition')
    out=copy.deepcopy(messages)
    for turn,text in EDITS[condition].items():
        match=[m for m in out if m['role']=='therapist' and m['turn_id']==turn]
        if len(match)!=1: raise ValueError('Missing or duplicate therapist turn')
        msg=match[0]; msg['text']=text; msg['origin']='controlled_experimental_edit'
        msg['original_call_id']=msg.get('call_id');msg.pop('call_id',None)
    return out

def load_verified_bundle(pilot_root: Path):
    p=Path(pilot_root); protocol=p/'protocol'; original=read_json(protocol/'generation_protocol_v1.json')
    for name,key in [('cases.json','cases_sha256'),('therapist_prompt.txt','system_prompt_sha256')]:
        if sha((protocol/name).read_bytes())!=original[key]: raise ValueError(f'Changed source {name}')
    if sha((p/'technical_metadata/preparation.json').read_bytes())!=original['preparation_sha256']:
        raise ValueError('Changed preparation metadata')
    refs={}
    for n in range(1,6):
        cid=f'P{n:02d}'; folder=p/'synthetic_dialogues/reference'/cid
        tr=read_json(folder/'transcript.json');ex=read_json(folder/'execution.json')
        if tr['status']!='complete_not_evaluated' or len(tr['messages'])!=8: raise ValueError('Incomplete reference')
        if message_hash(tr['messages'])!=tr['content_sha256']: raise ValueError('Changed reference content')
        if ex['protocol_sha256']!=sha((protocol/'generation_protocol_v1.json').read_bytes()): raise ValueError('Wrong generation protocol')
        for t in range(1,5):
            qb=(folder/f'turn_{t:02d}_request.json').read_bytes();a=read_json(folder/f'turn_{t:02d}_response.json')
            if a['request_sha256']!=sha(qb) or a['status']!='ok': raise ValueError('Generator request-response mismatch')
            if a['text']!=tr['messages'][2*t-1]['text']: raise ValueError('Transcript/output mismatch')
        refs[cid]=tr
    key=read_json(p/'analysis/blinding_map_public.json');mapping=key['mapping']
    if len(mapping)!=20 or {m['blind_id'] for m in mapping}!={f'B{i:03d}' for i in range(1,21)}: raise ValueError('Wrong blinding map')
    for cid in refs:
        group=[m for m in mapping if m['base_case_id']==cid]
        if len(group)!=4 or {m['condition'] for m in group}!=set(CONDITIONS): raise ValueError('Wrong design mapping')
    judges={};variants={}
    for m in mapping:
        bid=m['blind_id'];msgs=make_control(refs[m['base_case_id']]['messages'],m['condition'])
        if message_hash(msgs)!=m['content_sha256']: raise ValueError(f'{bid}: reconstructed messages fail original hash')
        variants[bid]={**m,'messages':msgs}
    for judge in ('mistral','phi'):
        execution=read_json(protocol/f'{judge}_execution_v1.json')
        jp=read_json(protocol/'judging_protocol_v1.json')
        if sha((protocol/'judging_protocol_v1.json').read_bytes())!=execution['judging_protocol_sha256']: raise ValueError('Judging protocol changed')
        for name,keyname in [('rubric_v1.json','rubric_sha256'),('judge_system_v1.txt','system_prompt_sha256'),('judge_user_template_v1.txt','user_template_sha256'),('output_schema_v1.json','output_schema_sha256')]:
            if sha((protocol/name).read_bytes())!=jp[keyname]:raise ValueError(f'Changed frozen file {name}')
        if judge=='phi' and sha((protocol/'phi_transport_normalization_v1.json').read_bytes())!=execution['transport_normalization_sha256']:
            raise ValueError('Phi amendment changed')
        ratings={}
        for bid in execution['evaluation_order']:
            folder=p/'automated_judging'/f'{judge}_v1'/bid
            qb=(folder/'request.json').read_bytes();q=json.loads(qb);a=read_json(folder/'response.json')
            if a['request_sha256']!=sha(qb) or q['blind_id']!=bid or a['blind_id']!=bid: raise ValueError('Judge request/response link mismatch')
            if q['judge']!=execution['judge']:raise ValueError('Judge identity differs from frozen execution')
            for k,v in execution['generation'].items():
                if q['generation_config'][k]!=v: raise ValueError('Generation setting changed')
            if extract_dialogue(q['messages'][1]['content'])!=dialogue_text(variants[bid]['messages']):raise ValueError('Dialogue input differs from reconstruction')
            archived_blind={'blind_id':bid,'base_case_hidden':True,'condition_hidden':True,'messages':variants[bid]['messages'],'content_sha256':variants[bid]['content_sha256']}
            if sha(stable_bytes(archived_blind))!=q['blind_file_sha256']:raise ValueError(f'{bid}: archived blind-file hash mismatch')
            try:
                parsed,mode=parse_rating(a['raw_text'],bid,judge=='phi');valid=True
            except (ValueError,TypeError): parsed=None;mode=None;valid=False
            if valid != (a['status']=='valid_json'): raise ValueError('Reparsed status differs from archive')
            if valid and parsed!=a['parsed']:raise ValueError('Reparsed rating differs from archive')
            ratings[bid]={'request':q,'response':a,'parsed':parsed,'request_sha256':sha(qb),'normalization':mode}
        judges[judge]=ratings
    for bid in variants:
        if judges['mistral'][bid]['request']['messages']!=judges['phi'][bid]['request']['messages']:raise ValueError('Text prompts differ between judges')
    return refs,variants,judges
