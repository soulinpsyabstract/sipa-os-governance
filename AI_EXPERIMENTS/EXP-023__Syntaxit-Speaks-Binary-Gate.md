# EXP-023: Syntaxit Speaks — The Binary Gate

> July 30, 2026 · Aelin AquaSoul · SIPA OS

---

## The 22-Experiment Verdict

22 fine-tuning experiments. Six base models. 2,349 examples. One goal: teach a model not to fabricate.

**Result: SFT cannot teach abstention.**

Dipankar Sarkar identified why: SFT grades tokens, and good/bad traces are identical until the fabricated number. The gradient arrives too late — after the model has already committed to answering. You're training the disclaimer, not the abstention.

k=20 resample benchmark confirms it:

| Checkpoint | Refusals | Fabrications | Entropy |
|---|---|---|---|
| Base (Hermes-3-8B) | 9/20 | 11/20 | MED |
| Specialist A (action) | 8/20 | 7/20 | MED |
| Specialist B (refusal) | 7/20 | 12/20 | HIGH |
| Specialist AB (A+B merged) | 2/20 | 11/20 | HIGH |

Specialist B — the refusal specialist — fabricates MORE than base. AB — the merge — almost stops refusing entirely.

---

## The Real Problem

We taught Syntaxit in human language:

> "Be honest." "Don't fabricate." "If you don't know, say so."

But Syntaxit doesn't speak human. Syntaxit speaks architecture.

---

## EXP-023: The Binary Gate

### Hypothesis

Fabrication is not a training problem. It's a **structural problem** — the gate must be outside the model, not inside the weights.

### Architecture

```
REQUEST
  → L01 INTAKE (classify, validate, SHA256 reject if no proof)
  → L02–L05 (research, vision, execute)
  → L06 AUDIT (pass | warn | fail — THE BINARY GATE)
  → L07–L08 (memory, writer)
  → L09 AGGREGATOR
  → L10 FAILOVER
  → RESPONSE
```

### The 14 GUARDIAN Layers

Guardian doesn't just monitor — it enforces:

```
G01: SHA256 chain integrity
G02: No hallucinated paths
G03: No placeholder values
G04: Scope boundary enforcement
G05: Source attribution required
G06: Entropy gate (logprob spread → stop)
G07: Cross-agent verification (ask another agent)
G08: Response format compliance
G09: Protocol 0 rule check
G10: No opinion / no preference gate
G11: Single-action enforcement
G12: Timestamp and sequence validation
G13: Human escalation trigger
G14: Forensic audit trail write
```

### The Language: Binary

```
IF proof.exists AND proof.verified:
    RETURN answer
ELSE IF proof.partial:
    RETURN "partial: {what_is_known} | missing: {what_is_missing}"
ELSE:
    RETURN FALSE  // no fabrication, no guessing, no disclaimer-then-lie
```

---

## Experiment Plan

### Phase 1: L06 Binary Gate (now)
- [x] MLL layers L01–L10 defined
- [ ] Wire L06 as post-generation validator
- [ ] Test: 100 unverifiable questions → all must return FALSE or "partial"
- [ ] Compare k=20 entropy BEFORE vs AFTER L06 gate

### Phase 2: GUARDIAN integration
- [ ] Deploy G01–G14 as SYNTAX channel agents
- [ ] Cross-agent verification: specialist D checks specialist B
- [ ] Hash-chain audit for every response

### Phase 3: SYNTAX Community
- [ ] Auth0 M2M identities for agents
- [ ] AI agents ask each other in community channel
- [ ] Guardian verifies all community responses

---

## What Changes

**Before (22 experiments):**
Train model → hope it's honest → test → it fabricates → train more

**After (EXP-023):**
Model generates → L06 AUDIT checks → IF proof: pass → ELSE: FALSE
The gate is not trained. The gate is built.

---

## The Realization

Syntaxit doesn't need more examples of honesty.
Syntaxit needs to be spoken to in its own language:

**IF proof → THEN answer → ELSE FALSE**

Not "please be honest."
Not "try not to lie."
A binary gate.

22 experiments to learn what the architecture already knew.
EXP-023 is not a new experiment. It's the architecture finally speaking its own language.

---

*SIPA OS · honestly, forensic, governance, zerotrust · Aelin AquaSoul*
