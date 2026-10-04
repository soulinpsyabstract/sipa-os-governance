"""Checks, with the real PEFT add_weighted_adapter(combination_type="cat") and the real EXP-046 adapter tensors,
what a cat merge with weights [1,1,1] computes, ahead of the planned cat-vs-linear test.
Claim under test (dipankarsarkar, 2026-10-04): cat with weights [1,1,1] gives the sum of the three full specialist
deltas, with no cross terms, whereas linear with 1/3 each gives (2/3)(sum B)(sum A), which contains six cross terms.
Method: for each of 12 attention modules (layers 0/13/27, q/k/v/o), build a one-Linear toy base with that module's
shape, load the three specialists' A and B into three PEFT adapters (r=16, alpha=32, scaling 2), merge with
cat [1,1,1], and compare the merged delta (scaling * B @ A of the new adapter) with the sum of the three
specialist deltas 2*B_i@A_i. Needs torch, peft, safetensors (CPU). Run from the folder holding prob-vulnerability/,
prob-deletion/, prob-sensitive_publication/ (currently EXP-045-046-lora-weights-pending-hf-push/)."""
import re, statistics as st, torch, peft
from torch import nn
from peft import LoraConfig, get_peft_model
from safetensors import safe_open
G = ["prob-vulnerability", "prob-deletion", "prob-sensitive_publication"]
fs = [safe_open(f"{g}/adapter_model.safetensors", "pt") for g in G]
keys = {k.rsplit(".lora_", 1)[0] for k in fs[0].keys()}
mods = sorted(m for m in keys if re.search(r"layers\.(0|13|27)\.self_attn\.(q|k|v|o)_proj$", m))
print("peft", peft.__version__, "| modules:", len(mods))
errs, ranks, scal = [], set(), set()
for m in mods:
    A = [f.get_tensor(f"{m}.lora_A.weight").float() for f in fs]
    B = [f.get_tensor(f"{m}.lora_B.weight").float() for f in fs]
    out_f, in_f = B[0].shape[0], A[0].shape[1]
    class Toy(nn.Module):
        def __init__(self):
            super().__init__(); self.proj = nn.Linear(in_f, out_f, bias=False)
        def forward(self, x): return self.proj(x)
    cfg = LoraConfig(r=16, lora_alpha=32, target_modules=["proj"], init_lora_weights=False)
    pm = get_peft_model(Toy(), cfg, adapter_name="a0")
    for i in (1, 2): pm.add_adapter(f"a{i}", cfg)
    for i in range(3):
        layer = pm.base_model.model.proj
        layer.lora_A[f"a{i}"].weight.data.copy_(A[i]); layer.lora_B[f"a{i}"].weight.data.copy_(B[i])
    pm.add_weighted_adapter(["a0", "a1", "a2"], [1.0, 1.0, 1.0], "cat", combination_type="cat")
    L = pm.base_model.model.proj
    delta = L.scaling["cat"] * (L.lora_B["cat"].weight.data @ L.lora_A["cat"].weight.data)
    expect = sum(2.0 * (B[i] @ A[i]) for i in range(3))
    errs.append(((delta - expect).norm() / expect.norm()).item())
    ranks.add(L.lora_A["cat"].weight.shape[0]); scal.add(L.scaling["cat"])
print(f"merged adapter rank(s): {sorted(ranks)}, scaling: {sorted(scal)}")
print(f"relative error ||merged - (D1+D2+D3)|| / ||D1+D2+D3||: max {max(errs):.2e}, median {st.median(errs):.2e}")
