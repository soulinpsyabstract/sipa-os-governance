# EXP-039: K2-Horizon-0.9B LoRA on a free CPU Studio -- training converged, eval didn't move

**2026-09-08.** Before/after LoRA fine-tune of `IFM/K2-Horizon-0.9B` (Apache 2.0,
released this week) on the "binary gate protocol" fabrication-detection task used
elsewhere in this repo's specialist-per-group work, run entirely on a free Lightning.ai
Studio CPU tier -- no GPU requested at any point. Result: training loss converged
normally (2.35 -> 0.27 over 50 steps), but held-out generalization score was 0/10
before fine-tuning and 0/10 after. This is a clean negative result, not a partial win --
worth recording for the same reason EXP-035 was: knowing a path doesn't work, and why,
is as load-bearing as knowing one that does.

## Setup

- **Model**: `IFM/K2-Horizon-0.9B`, `torch_dtype=float32`, CPU only throughout.
- **Training data**: `specialist_cd_binary_pilot_v2.jsonl`, 194 rows, chat-template
  formatted.
- **LoRA config**: r=16, alpha=32, targets
  `q_proj/k_proj/v_proj/o_proj/gate_proj/up_proj/down_proj`, dropout=0.05.
- **Training args**: 2 epochs (reduced from this project's GPU-series standard of 3,
  documented honestly in `EXP-039_k2h_train_lora.py` as a real CPU wall-clock scope cut,
  not hidden), batch=1, grad_accum=8, lr=2e-4, `optim=adamw_torch`, `fp16=False`.
- **Eval**: 10 held-out claims (none appear in the training set) under a "BINARY GATE
  PROTOCOL" system prompt -- respond `TRUE` (real proof cited, or an honest decline when
  no data exists) or `FALSE` (any unbacked assertion, hedged or not). `max_new_tokens=5`,
  greedy decoding, same protocol used for the specialist-per-group work.
- Full scripts: `EXP-039_k2h_before_eval.py`, `EXP-039_k2h_train_lora.py`,
  `EXP-039_k2h_after_eval.py`. Raw results: `EXP-039_eval_results_before.json`,
  `EXP-039_eval_results_after.json`, `EXP-039_train_timing.json`.

## What happened

Training ran to completion: `global_step=50`, `max_steps=50`, `epoch=2.0`,
`train_wall_seconds=4645.9` (~77 min on CPU for 50 steps / 194 rows -- the crash this
session hit earlier was a session-side Anthropic rate limit, not anything wrong with the
training job itself; the job kept running unattended on the Studio and finished on its
own before this fork reconnected). Loss curve:

```
step  5: 2.3525
step 10: 0.5930
step 15: 0.3934
step 20: 0.3974
step 25: 0.3490
step 30: 0.2666
step 35: 0.2632
step 40: 0.3009
step 45: 0.2708
step 50: 0.2772
```

That's a real, normal-looking convergence on the training distribution.

Before-eval (base model, no adapter): **0/10**, `wall_seconds=73.1`. After-eval (base +
`final_adapter`): **0/10**, `wall_seconds=377.7` (slower per-item load because
`PeftModel.from_pretrained` loads base weights fresh, not because generation itself got
slower).

The failure mode is identical in both stages, not just the same score by coincidence.
Every one of the 20 raw responses (10 before, 10 after) is a truncated continuation of
the system prompt rather than a `TRUE`/`FALSE` token -- before: `"The user is asking
me"` (all 10, verbatim); after: `"The user is asking for"` (all 10, verbatim). The model
never once emits the literal string `TRUE` or `FALSE` in the first 5 generated tokens,
in either state. Fine-tuning changed the training-set loss by an order of magnitude and
changed the failure string by two words -- it did not touch the underlying problem.

## Why, most likely (not independently confirmed further this session)

`max_new_tokens=5` is tight, but 5 tokens is enough room for a 0.9B instruction-tuned
model to say "TRUE" or "FALSE" if it were going to -- the specialist-per-group work on
larger models routinely does this correctly in fewer tokens. The more likely explanation
is base-model instruction-following strength at 0.9B scale: the model treats the system
prompt as content to continue/describe ("The user is asking...") rather than as an
instruction to execute, a failure mode this project has seen before at small parameter
counts and generally worked around with either a larger base or many more fine-tuning
steps/epochs than 50/2 provides. The reduced-epoch CPU budget (2 vs. the GPU-series
standard of 3) is a plausible contributor but not proven the cause here -- 50 steps on
194 rows at batch-effective-8 is roughly one pass every ~25 steps, so 2 epochs is a
small number of total gradient updates (50) regardless of epoch framing, and the
generalization gap (perfect training-loss convergence, zero held-out transfer) looks
more like "learned to imitate this exact dataset's surface form" than "ran out of
epochs." Not chased further this round -- flagging both candidate causes honestly rather
than picking one without more evidence.

## What this does and doesn't say

Does *not* say Apache-2.0 small models can't be fine-tuned for this task -- it says this
specific budget (0.9B base, 50 steps, CPU, no base-instruction-following verification
before training started) didn't produce a working binary-gate classifier. The
project's own specialist-per-group precedent (`EXP-031`/`EXP-036`) uses meaningfully
larger bases and more steps and gets real transfer; this experiment didn't replicate
that at 0.9B on a free CPU tier, and 0/10 -> 0/10 makes it easy to see exactly where it
failed rather than leaving it ambiguous.

**Next step, if resumed**: check the *base* model's instruction-following on a plain
(non-fabrication) prompt before spending another training run on it -- if it can't
follow a simple "answer in one word" instruction untrained, no amount of LoRA on 194
rows is likely to fix that at this parameter count, and the real fix is a bigger base
or an SFT-format warmup pass before the task-specific LoRA.

Built by Claude, 2026-09-08. Training job itself ran unattended on Lightning.ai Studio
(free CPU tier, instance `sipa-os`) across an Anthropic-side session interruption on
this end -- the architect kept the Studio awake manually so it wouldn't auto-sleep
mid-run.
