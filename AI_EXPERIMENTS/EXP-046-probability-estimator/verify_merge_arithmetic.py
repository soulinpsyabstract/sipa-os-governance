"""Verifies, on the real EXP-046 adapters, the claim made by dipankarsarkar (2026-10-03) that the PEFT
linear merge is factor-wise arithmetic: merged A = sqrt(w*alpha/r) * (A1+A2+A3), same for B, so the merged
delta is (2/3)(B1+B2+B3)(A1+A2+A3) = a third of each specialist delta plus six cross products B_i A_j.
Run from the folder holding prob-vulnerability/, prob-deletion/, prob-sensitive_publication/ and
prob-merged/merged/ (the adapter folders currently in EXP-045-046-lora-weights-pending-hf-push/).
Needs torch + safetensors (CPU is enough). Specialists: r=16, alpha=32 (scaling 2); merged: r=16, alpha=16 (scaling 1).
"""
import torch, statistics as st, re
from safetensors import safe_open
G=["prob-vulnerability","prob-deletion","prob-sensitive_publication"]
fs=[safe_open(f"{g}/adapter_model.safetensors","pt") for g in G]
fm=safe_open("prob-merged/merged/adapter_model.safetensors","pt")
mods=sorted({k.rsplit(".lora_",1)[0] for k in fm.keys()})
print("modules:",len(mods))
# 1) factor-wise scale check on ALL modules
cA,cB,eA,eB=[],[],[],[]
for m in mods:
    for kind,cs,es in (("A",cA,eA),("B",cB,eB)):
        key=f"{m}.lora_{kind}.weight"
        S=sum(f.get_tensor(key).float() for f in fs); M=fm.get_tensor(key).float()
        c=(M*S).sum()/(S*S).sum(); r=(M-c*S).norm()/M.norm()
        cs.append(c.item()); es.append(r.item())
print(f"A: scale median {st.median(cA):.6f} (min {min(cA):.6f}, max {max(cA):.6f}); rel err max {max(eA):.2e}")
print(f"B: scale median {st.median(cB):.6f} (min {min(cB):.6f}, max {max(cB):.6f}); rel err max {max(eB):.2e}")
print("sqrt(2/3) =",(2/3)**0.5)
# 2) delta analysis on attention modules of 3 layers (specialists scaling 2, merged scaling 1)
sel=[m for m in mods if re.search(r"layers\.(0|13|27)\.self_attn\.(q|k|v|o)_proj$",m)]
cos,coef,outside,offshare=[],[],[],[]
for m in sel:
    Ds=[2.0*(f.get_tensor(f"{m}.lora_B.weight").float()@f.get_tensor(f"{m}.lora_A.weight").float()) for f in fs]
    Dm=1.0*(fm.get_tensor(f"{m}.lora_B.weight").float()@fm.get_tensor(f"{m}.lora_A.weight").float())
    V=[d.flatten() for d in Ds]; M=Dm.flatten()
    Gm=torch.stack([torch.stack([a@b for b in V]) for a in V]).double()
    c=torch.linalg.solve(Gm, torch.stack([a@M for a in V]).double())
    res=M.double()-sum(ci*v.double() for ci,v in zip(c,V))
    outside.append((res.norm()**2/(M.double().norm()**2)).item()); coef+= [x.item() for x in c]
    for i in range(3):
        for j in range(i+1,3): cos.append((V[i]@V[j]/(V[i].norm()*V[j].norm())).item())
    diag=sum((2/3)*(f.get_tensor(f"{m}.lora_B.weight").float()@f.get_tensor(f"{m}.lora_A.weight").float()) for f in fs).flatten()
    offshare.append(((M-diag).norm()/M.norm()).item())
print(f"delta analysis on {len(sel)} attention modules (layers 0/13/27):")
print(f"  median |cosine| between specialist deltas: {st.median([abs(x) for x in cos]):.3f}")
print(f"  median regression coef of merged on each specialist: {st.median(coef):.3f}")
print(f"  median share of merged energy OUTSIDE the span of the 3 specialists: {st.median(outside)*100:.0f}%")
print(f"  median ||off-diagonal terms|| / ||merged||: {st.median(offshare)*100:.0f}%")
