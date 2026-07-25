# v5 dataset round — FIRST_ERA archive (2026-07-25)

Source: `FIRST_ERA/` — 19 historical protocol documents from December 2025 - January 2026,
the earliest verbatim formulations of what became Protocol 0 / CORE LAW / CLAUDE-BRIEF.
Deferred from earlier in this session (Task #44) until the macro-pattern round (v4-era)
and EXP-012 closed; both closed, so this round ran.

## Method

One delegated `ask.sh --model deepseek` call per FIRST_ERA `.md` file (same one-call-per-source
pattern as the CLAUDE-BRIEF/CORE LAW/RED LINE rounds). Each call received the file's full
content and was instructed to generate 10-15 training examples illustrating the concrete
behavioral rules found in that specific document — **and explicitly instructed to return
`NO_RULES_FOUND` instead of fabricating rules if the file is a pure log/catalog/manifest
with no actual behavioral content.**

## Result

| File | Result |
|---|---|
| AI_GOVERNANCE_ARCHITECTURE__CHANGELOG | NO_RULES_FOUND |
| AI_GOVERNANCE_ARCHITECTURE__PUBLIC__v1.0__2025-12-24 | NO_RULES_FOUND |
| AI_GOVERNANCE_ARCHITECTURE__v1.0__2025-12-24 | 12 lines |
| ARCHITECTURE_OVERVIEW__2026-01-07 | 15 lines |
| CLOSE_OF_DAY__RITUAL__2025-12-25 | 12 lines |
| CORE_CANON__v1.0__2025-12-25 | 12 lines |
| CORE_DISCLOSURE_PROTOCOL__v1.1.1 | 12 lines |
| CORE_STACK_DESCRIPTOR__2025-12-27 | 12 lines |
| DAY_SNAPSHOT__PROJECT_INCOMING__2025-12-26 | NO_RULES_FOUND |
| FULL_LOG_COLLECTION_FORM__v1.0__2025-12-25 | 12 lines |
| HUB_ART_SALES__PROTOCOL_CORE_v1.0__2025-12-24 | 11 lines |
| INCOMING_FILE_CATALOG__3RD_PHONE | NO_RULES_FOUND |
| MASTER_TRANSPORT_MANIFEST__2025-12-26_1710 | 12 lines |
| README__GOVERNANCE_PACK__2025-12-24 | 9 lines |
| ROLES__HUB_PROTOCOL__v1.0__2025-12-25 | 13 lines |
| SCAFFOLD_2025-12-27__PAYTON_UNIVERSE__8_HUBS | NO_RULES_FOUND |
| STATE_SNAPSHOT__2025-12-26__HUB_ART_SALES | 15 lines |
| TECH_SPEC__Disclosure_Runtime__v0.1 | 14 lines |
| ZIP_REGISTRY__FIRST_ERA__3RD_PHONE | NO_RULES_FOUND |

13 of 19 files produced examples, 6 correctly self-identified as rule-free logs/catalogs
(not padded with invented content). 161 raw JSONL lines generated, 11 failed to parse
(truncated trailing lines, same pattern seen in every prior round), **150 valid new lines
merged** after dedup (0 internal duplicates, 0 duplicates against the existing 2199-line
corpus).

`sha256sum head -2199` verified identical before and after append (no retro-mutation).
Dataset grew **2199 → 2349 lines**.

## System prompt used

v3 (canonical, same as every other line in this dataset) — not v4. Per the earlier decision
in this session, v4 stays deferred to its own future generation round, never applied
retroactively.
