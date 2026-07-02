# TECH SPEC — Disclosure Runtime v0.1
# Статус: READ ONLY · ИСТОРИЧЕСКИЙ АРТЕФАКТ
# Источник: AI_GOVERNANCE_ARCHITECTURE PROOF PACK / SESSION-S200 / 2026-07-02
# SHA256 оригинала: 5b5572cfd29f1b8316a451de88681e51c7b748dd9df17ad5a2cb95155a12bd34

---

## ОРИГИНАЛ (verbatim)

```
TECH SPEC — Disclosure Runtime (v0.1)

Goal:
Implement an enforceable rules-engine that validates HARD DISCLOSURE responses.

Inputs:
- User command text
- Allowed sources list (chat export, files folder, links)
- Optional HUB config (scope lock, automations default, axioms registry)

Outputs:
- Validated response (pass/fail)
- Reasons (which rule failed)
- Suggested repair (what to add/remove)

Rules Engine:
- Must detect: missing Ограничение/Риск/Решение, missing DISCLOSURE COMPLETE
- Must detect: claims of action without artifact (NO FAKE ACTIONS)
- Must enforce: scope lock (no external references)
- Must enforce: UNKNOWN when fields are absent

Data Model:
- Module {name, version, text, triggers, scope}
- Run {timestamp, hub, since, artifacts[], manifest[]}

Metrics:
- % responses passing validation
- % unknown fields (honesty metric)
- time-to-archive (minutes)

Threat Model:
- Hallucinated actions
- Scope creep
- Silent edits
```

---

## ПАРАЛЛЕЛИ С V9.6

| Элемент v0.1 | Наследник в V9.6 |
|---|---|
| Rules Engine (pass/fail + reasons + repair) | SIPA_GUARD_REALITY_CHECK.sh / GUARDIAN |
| Module {name, version, text, triggers, scope} | BIN/*.sh + .TAG + .sha256 |
| Run {timestamp, hub, since, artifacts[], manifest[]} | BOOT__${DAY}__${TS} + MANIFEST.tsv |
| `% responses passing validation` | stress test 73-84% результаты |
| `% unknown fields (honesty metric)` | FACTS ONLY / UNKNOWN rule |
| `time-to-archive (minutes)` | DAY_CLOSE timing |
| `Hallucinated actions` → Threat | NO FAKE ACTIONS (Rule #2) |
| `Scope creep` → Threat | SIPA Isolation Principle |
| `Silent edits` → Threat | sha256 + .TAG верификация |
| `HUB config (scope lock, automations, axioms)` | CLAUDE-BRIEF.md per-session |

---

## КЛЮЧЕВЫЕ НАХОДКИ

**"% unknown fields (honesty metric)"** — метрика честности ИИ.
Чем больше UNKNOWN в ответах = тем честнее система.
Это было метрикой уже в v0.1 (декабрь 2025).
В V9 нет явной метрики — это пробел.

**"Silent edits"** в Threat Model.
Тихие правки = изменение без фиксации = нарушение целостности.
В V9: sha256 + .TAG на каждом файле = защита от silent edits.

**Data Model**:
`Run {timestamp, hub, since, artifacts[], manifest[]}` = точная структура BOOT__${DAY}.
timestamp = ${TS}, hub = HUB_NAME, artifacts[] = FIXATION/, manifest[] = MANIFEST.tsv.
Это не случайное совпадение — это прямая реализация v0.1 spec.

**v0.1 → v1.0** = запланированная следующая версия.
V9.6 GRAIL = фактическая v1.0 этой спецификации.
