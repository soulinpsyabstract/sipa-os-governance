"""Paired bootstrap (5000 resamples, seed 46) over the 20 eval records per group, from the raw EXP-046 eval files
in this folder. Reports base/specialist/merged MAE, the share of the specialist gain the merge kept, and the 95% CI
of the paired MAE difference vs base. Specialist files are the clean re-run after the filename fix."""
import json,glob,random
random.seed(46)
groups=["vulnerability","deletion","sensitive_publication"]
def load(pattern):
    d=json.load(open(glob.glob(pattern)[0])); return {r["id"]:r["abs_error"] for r in d["results"]}, d["mae"], d["parse_failures"]
print(f"{'group':22} {'base':>6} {'spec':>6} {'merged':>7} | gain kept by merge | 95% CI (merged-base) | 95% CI (spec-base)")
for g in groups:
    b,bm,_=load(f"eval_probability_results_before_{g}.json")
    s,sm,_=load(f"eval_probability_results_after_specialist-prob-{g}-qwen25-lora_{g}.json")
    m,mm,pf=load(f"eval_probability_results_after_merged_{g}.json")
    ids=sorted(set(b)&set(s)&set(m)); n=len(ids)
    def ci(x,y):
        diffs=sorted(sum(x[i]-y[i] for i in (random.choice(ids) for _ in range(n)))/n for _ in range(5000))
        return diffs[125],diffs[4875]
    lo,hi=ci(m,b); lo2,hi2=ci(s,b)
    print(f"{g:22} {bm:6.3f} {sm:6.3f} {mm:7.3f} | {(bm-mm)/(bm-sm)*100:5.0f}% of spec gain | [{lo:+.3f}, {hi:+.3f}] | [{lo2:+.3f}, {hi2:+.3f}]  (n={n})")
