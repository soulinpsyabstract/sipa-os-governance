"""Paired bootstrap (5000 resamples, seed 46) of merged minus specialist MAE over the same 20 eval records per
group, from the raw EXP-046 eval files in this folder. Also: bootstrap interval of the share of the specialist
gain the merge kept, and the number of records needed to resolve the observed merged-minus-specialist gap at
80% power (two-sided 5%, normal approximation: n = ((1.96 + 0.84) * sd / gap)^2).
Raised by dipankarsarkar on the HF write-up; reproduced here on the raw files."""
import json, glob, random, math, statistics as st
random.seed(46)
def load(p):
    d = json.load(open(glob.glob(p)[0])); return {r["id"]: r["abs_error"] for r in d["results"]}
print(f"{'group':22} {'gap m-s':>8} {'sd':>6} {'95% CI (merged-specialist)':>28} {'kept-share 95% CI':>22} {'n for 80%':>10}")
for g in ["vulnerability", "deletion", "sensitive_publication"]:
    b = load(f"eval_probability_results_before_{g}.json")
    s = load(f"eval_probability_results_after_specialist-prob-{g}-qwen25-lora_{g}.json")
    m = load(f"eval_probability_results_after_merged_{g}.json")
    ids = sorted(set(b) & set(s) & set(m)); n = len(ids)
    d = [m[i] - s[i] for i in ids]
    gap, sd = st.mean(d), st.stdev(d)
    diffs, kept = [], []
    for _ in range(5000):
        r = [random.choice(ids) for _ in range(n)]
        diffs.append(st.mean(m[i] - s[i] for i in r))
        bg = st.mean(b[i] - s[i] for i in r)
        kept.append(st.mean(b[i] - m[i] for i in r) / bg * 100 if bg else float("nan"))
    diffs.sort(); kept = sorted(k for k in kept if k == k)
    need = math.ceil(((1.96 + 0.84) * sd / gap) ** 2)
    print(f"{g:22} {gap:+8.4f} {sd:6.3f} [{diffs[125]:+.3f}, {diffs[4875]:+.3f}]".ljust(62) +
          f" [{kept[125]:+.0f}%, {kept[len(kept)-126]:+.0f}%]".rjust(22) + f" {need:10d}   (n={n})")
