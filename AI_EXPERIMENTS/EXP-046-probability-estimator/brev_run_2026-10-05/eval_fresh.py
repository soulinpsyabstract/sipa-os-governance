import json, re, sys, statistics as st, random
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
SYS=open('/home/shadeform/sys_prompt.txt').read().strip()
BASE='/home/shadeform/exp046/base'
ADP='/home/shadeform/exp046/adapters/vulnerability'
chains=[json.loads(l) for l in open('/home/shadeform/chains_fresh.jsonl')]
orig={json.loads(l)['chain_ref']:json.loads(l)['probability_estimate'] for l in open('/home/shadeform/probability_fresh_orig.jsonl')}
shuf={json.loads(l)['chain_ref']:json.loads(l)['probability_estimate'] for l in open('/home/shadeform/probability_fresh_shuffled.jsonl')}
def user_prompt(c):
    steps=c['chain']
    lines=[]
    for s in steps:
        lines.append(f"{len(lines)+1}. ({s['node']}) {s['description']}")
    return ("Initiating action: "+c['action_x']+"\n\nChain:\n"+"\n".join(lines)+
            "\n\nTerminal outcome: "+c['terminal_outcome'])
tok=AutoTokenizer.from_pretrained(BASE)
def load(adapter=None):
    m=AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16, device_map='cuda')
    if adapter: m=PeftModel.from_pretrained(m, adapter)
    m.eval(); return m
def predict(model, c):
    msgs=[{'role':'system','content':SYS},{'role':'user','content':user_prompt(c)}]
    ids=tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors='pt', return_dict=True)['input_ids'].to('cuda')
    with torch.no_grad():
        out=model.generate(ids, max_new_tokens=120, do_sample=False, pad_token_id=tok.eos_token_id)
    txt=tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True)
    m=re.search(r'"probability_estimate"\s*:\s*([0-9.]+)', txt)
    return (float(m.group(1)) if m else None), txt
res={}
for arm,adapter in [('base',None),('specialist_vulnerability',ADP)]:
    model=load(adapter)
    rows={}
    for c in chains:
        p,raw=predict(model,c)
        rows[c['id']]={'pred':p,'raw':raw}
    res[arm]=rows
    del model; torch.cuda.empty_cache()
    print('done',arm, flush=True)
ids=[c['id'] for c in chains]
ref={c['id']:orig.get(c['id']) for c in chains}
out={'n':len(chains),'arms':{}}
def mae(arm, labels):
    diffs=[]; miss=0
    for i in ids:
        p=res[arm][i]['pred']
        if p is None: miss+=1; continue
        diffs.append(abs(p-labels[i]))
    return st.mean(diffs), miss
for arm in res:
    m_o,miss=mae(arm, orig); m_s,_=mae(arm, shuf)
    out['arms'][arm]={'mae_vs_orig':m_o,'mae_vs_shuffled':m_s,'unparsed':miss}
const={i:0.70 for i in ids}
out['arms']['constant_0.70']={'mae_vs_orig':st.mean(abs(0.70-orig[i]) for i in ids),'mae_vs_shuffled':st.mean(abs(0.70-shuf[i]) for i in ids),'unparsed':0}
json.dump({'summary':out,'raw':res}, open('/home/shadeform/exp046/fresh_eval_results.json','w'), ensure_ascii=False, indent=1)
print(json.dumps(out, indent=1))
