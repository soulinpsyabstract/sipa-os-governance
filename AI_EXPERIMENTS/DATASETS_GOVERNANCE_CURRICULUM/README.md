# Governance curriculum dataset (EXP-044)

Original 881-pair instruction/response dataset (`sipa_os_finetune_dataset.jsonl`) covering SIPA OS internal operational canon (471 pairs) and external published governance/protocol docs (410 pairs) -- source for EXP-044's 8-stage curriculum fine-tune.

Split into 8 thematic groups (keyword-heuristic classification, see EXP-044 writeup for methodology):

| File | Pairs | Group |
|---|---|---|
| `external_research.jsonl` | 42 | External research |
| `architecture_system.jsonl` | 51 | Architecture / system |
| `business_legal_finance.jsonl` | 52 | Business / legal / finance |
| `identity_bio.jsonl` | 178 | Identity / bio |
| `governance_protocol_safety_a.jsonl` | 108 | Governance / protocol / safety (half A) |
| `governance_protocol_safety_b.jsonl` | 108 | Governance / protocol / safety (half B) |
| `infra_devops_a.jsonl` | 171 | Infra / devops (half A) |
| `infra_devops_b.jsonl` | 171 | Infra / devops (half B) |

Sum of splits = 881, matches the original file.

See `EXP-044__hermes3-8b-governance-8stage-curriculum-tune-vs-catastrophic-forgetting.md` (one directory up, in `AI_EXPERIMENTS/`) for the full experiment writeup, per-stage results, and the judge_v5 correction.
