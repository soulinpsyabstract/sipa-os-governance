# Generation scripts for the causal-chain / probability / risk datasets

The three scripts that produced the 21 Sep 2026 datasets in the parent folder, copied here on 2026-10-04 so the
provenance is public. They were run on 2026-09-21 and had been kept only in a working directory, not committed.

| Script | Produces | Model | Temperature | Batch |
|---|---|---|---|---|
| `gen_causal_chains.py` | `causal_chain_*.jsonl` (200 per group) | `nousresearch/hermes-4-405b` via OpenRouter | 0.9 | 8 chains per call |
| `gen_probability_annotations.py` | `probability_*.jsonl` (annotates the chains) | same | 0.7 | 8 chains per call |
| `gen_risk_candidates.py` | `risk_candidates_*.jsonl` | same | see script | see script |

The probability labels are one model's estimates (the prompt asks it to vary them, with some chains low, 0.05 to 0.25),
not measured frequencies. They are copied unchanged from the run; the paths inside refer to the machine they ran on.

**Edited for publication.** Only two kinds of lines differ from what ran: the output-directory constant now points at the
parent folder relative to the script, and the API-key lookup reads the file named in `KEYS_FILE` (default `.env`, line
`OPENROUTER_API_KEY=...`) instead of the machine's own key files. Prompts, models, temperatures and batch sizes are unchanged.
