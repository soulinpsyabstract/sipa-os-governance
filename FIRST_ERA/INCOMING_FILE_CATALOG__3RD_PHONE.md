# INCOMING FOLDER CATALOG · 3-й ТЕЛЕФОН
# Path: /storage/emulated/0/PROJECT/INCOMING
# Источник: OCR снимок экрана / SESSION-S200 / 2026-07-02
# SHA256 файла: INCOMING_FULL.sha256 (11.34 KB · 10.01.2026)
# ALL_ZIPS_SHA256.txt (9.81 KB · 03.01.2026)

---

## СТАТИСТИКА

| Дата | Файлов | Характер |
|---|---|---|
| 26.12.2025 | ~15 | снапшоты + транспортные пакеты |
| 27.12.2025 | ~5 | скаффолд + genealogy + day export |
| 28.12.2025 | ~50 | МАСШТАБНЫЙ ДЕНЬ ПАТЧЕЙ |
| 30.12.2025 | 1 | DAY_2025-12-30_PAYTON |
| 01.01.2026 | 1 | OFFICIAL_FIXATION (Новый год!) |
| 04.01.2026 | 3 текста | UPLOAD_QUEUE + MOVE_LOG |
| 07.01.2026 | 1 | ARCHITECTURE_OVERVIEW BUNDLE |
| 10.01.2026 | 1 | INCOMING_FULL.sha256 (финальный реестр) |

---

## КЛЮЧЕВЫЕ ФАЙЛЫ ПО КАТЕГОРИЯМ

### КРУПНЫЕ СНАПШОТЫ (большой объём)
```
DAY_SNAPSHOT_2025-12-26_2010.zip          7.96 ГБ  ← самый большой
DAY_SNAPSHOT_v1_1_2025-12-26_2130.zip    2.06 ГБ
SNAPSHOT_V1_2025-12-26_2118.zip          2.09 ГБ
TERMINAL_SNAPSHOT_2025-12-28_15-21-32    755.79 МБ
TERMINAL_SNAPSHOT_2025-12-28_15-23-54    1.47 ГБ   (OCR: ТБ → ГБ)
DEDUP_ARCHIVE_2025-12-28_13-16-42.zip    377.53 МБ
WEEKLY_FULL_2025-12-27.zip               1.33 ГБ
ARCHIVE_MASTER_TRANSPORT_PART_A_1710     88.36 МБ  ← уже в манифесте
ARCHIVE_MASTER_TRANSPORT_BIG_PART1_1732  93.00 МБ  ← НОВЫЙ (1732≠1710!)
```

### 28.12.2025 — ДЕНЬ ПАТЧЕЙ v1.1.6→v1.1.26 (50+ файлов)
```
CORE_CANON_FIXATION_v1.1.6               ← первая именованная патч-версия
PATCH01_CORE_RUNTIME_RULES
PATCH03_SCHEDULER_STATUS
PATCH05_WEEKLY_CLOSURE_PROTOCOL
PATCH06_AMBIGUITY_STOP                   ← 2 версии
PATCH06_1_AMBIGUITY_STOP_CLARIFICATION  ← 2 версии
PATCH_CHAIN_FIXATION                     ← 3 версии (37-52, 37-58, 38-27)
CORE_CANON_v1.1.8_DELEGATION_PRINCIPLE
CORE_CANON_v1.1.9_DORMANT_STATE         ← 2 версии
CORE_CANON_v1.1.26_IMPORTANT_SAFE_AUTOPRESENCE  ← ФИНАЛЬНАЯ
V115_DAY_SNAPSHOT + WEEK_SNAPSHOT
V115_PATCH01_DASHBOARD_SCOPE
V115_PATCH02_WATCHDOG_COSMETIC_CLEANUP
V115_SCHEDULER_EXPECTATION
V116_PATCH01_SYSTEM_SCOPE_DECLARATION
V116_PATCH02_NON_AUTHORITY_CLAUSE
CORE_CANON_RUNLINE_CHECKIN ×7           ← 21:05, 21:05, 21:25-20, 21:25-28, 21:27-03, 21:52-29, v1.1.8
CORE_CANON_RUNLINE_CHECKIN_v1.1.8 ×2
SANITY_CHECK_ENV ×3                     ← 21:41, 21:51-18, 21:51-30
SANITY_CHECK_SHELL_EXEC
FORENSIC_TIMELINE
CONTROL_TIMELINE_MASTER + VALIDATION
RUNTIME_4H + RUNTIME_DAILY
TERMINAL_SNAPSHOT ×4
PAYTON_FIXATION + PAYTON_HUB_GLOBAL_TIMELINE
```

### УНИКАЛЬНЫЕ / РАНЕЕ НЕ ЗАМЕЧЕННЫЕ
```
HUB_GENEALOGY_2025-12-27_22-58.zip      ← genealogy хаб (27.12, до скаффолда?)
OFFICIAL_FIXATION_2026-01-01_19-04.zip  ← НОВОГОДНЯЯ фиксация!
DAY_2025-12-30_PAYTON.zip + .sha256     ← 30.12 + первый файл с собственным .sha256
PSY_DISSERTATION_TIMELINE_2025-12-28    ← психологическая диссертация
PSY_SYSTEM_MAP_2025-12-28              ← карта системы
CORE_DISTRIBUTION_ROLE_FIXATION         ← роли дистрибуции
2025-12-27_18-41_ART_SALES_DISCLOSURE_STACK_FIXATION ← ровно то время что в SCAFFOLD (18:41)
```

### ТЕКСТОВЫЕ ФАЙЛЫ (не ZIP)
```
ALL_ZIPS_SHA256.txt           9.81 КБ   03.01.2026  ← промежуточный реестр
INCOMING_FULL.sha256         11.34 КБ   10.01.2026  ← финальный реестр
ZIP_CANON_POLICY.txt           254 Б    03.01.2026  ← политика ZIP-упаковки
DUP_HASH_ONLY.txt              325 Б    03.01.2026
DUPLICATES_ALL_MATCHES.txt    1002 Б    03.01.2026
DUPLICATES_HASHES.txt          503 Б    03.01.2026
MOVE_LOG_2026-01-04 (×2)               04.01.2026
UPLOAD_QUEUE_BIGZIPS_2026-01-04.txt    04.01.2026
UPLOADED_OK_2026-01-04.txt             06.01.2026
```

---

## ВАЖНЫЕ НАХОДКИ

**1. ARCHIVE_MASTER_TRANSPORT_BIG_PART1_1732** (93 МБ)
Отличается от _1710 (138.69 МБ) — другой timestamp, другой объём.
Вероятно: пересборка того же пакета в 17:32 после 17:10.
Обе версии хранятся → "Nothing is deleted."

**2. ДЕDUП-файлы (03.01.2026)**
DUP_HASH_ONLY / DUPLICATES_ALL_MATCHES / DUPLICATES_HASHES + MOVE_LOG ×2 (04.01)
= дедупликация проводилась 03-04 января 2026. После упаковки и архивации.
В V9: DEDUP_STANDARD.sh = та же задача.

**3. DAY_2025-12-30_PAYTON.zip.sha256** (первый .sha256 рядом с ZIP)
30.12.2025 — первый файл где SHA256 сразу создаётся рядом.
До этого SHA256 жили в отдельных текстовых файлах.
В V9: каждый файл имеет .sha256 рядом = стандарт.

**4. OFFICIAL_FIXATION_2026-01-01_19-04.zip**
Новый год 2026, 19:04. Первая фиксация нового года.
Размер: ~46-47 МБ (OCR показал ТБ = явная ошибка).

**5. V115/V116** — версионирование системы
V115 = версия 1.15 (или V11.5?). V116 = 1.16.
PATCH01_DASHBOARD_SCOPE + PATCH02_NON_AUTHORITY_CLAUSE = уже 28.12.2025.

**6. PSY_DISSERTATION_TIMELINE + PSY_SYSTEM_MAP**
"Диссертация" существовала как концепт 28.12.2025.
В FIRST_ERA есть 2025-12-26_EN_DISSERTATION_LUX_PACK — связан?

**7. 28.12.2025 = самый плотный день первой эпохи**
~50 файлов. Патчи v1.1.6 → v1.1.26. 7 RUNLINE_CHECKIN за вечер.
SANITY_CHECK ×3 в течение 10 минут (21:41, 21:51-18, 21:51-30).
= активная верификация каждого патча в реальном времени.
