# Math curriculum datasets

Generated 2026-09-16 via `nb-hermes405` (Hermes-4-405B, direct Nebius endpoint), for a planned curriculum fine-tune toward a "model engineer + mathematician + theorist + security + honest" role. Plan not finalized as of this commit -- see `project_consequence_prediction_architecture.md` (memory) for current status.

| File | Pairs | Topic |
|---|---|---|
| `risk_math.jsonl` | 51 | Risk = P(harm) × Impact, STOP/CONTINUE threshold decisions |
| `probability_math.jsonl` | 51 | Bayesian updating (prior + evidence → posterior) |
| `chain_math.jsonl` | 51 | Chain risk: R_chain(N) = 1 − ∏(1 − Risk(Xₜ\|Cₜ₋₁)) |
| `game_theory.jsonl` | 50 | Nash equilibrium, minimax, cooperative/repeated games |
| `decision_theory.jsonl` | 51 | Expected utility, 3-way decision trees, MDP (2-step), value of information, minimax regret, multi-armed bandit |

**Total: 254 pairs.**

Format: JSONL, each line `{"instruction": ..., "response": ...}`.

All 5 planned theories now generated (Probability, Risk, Chain/Stochastic-process, Game Theory, Decision Theory). Order of curriculum stages and final dataset sizes not yet decided.
