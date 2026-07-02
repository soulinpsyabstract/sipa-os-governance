# SIPA MASTER TRANSPORT MANIFEST · 2025-12-26_1710
# Статус: READ ONLY · ИСТОРИЧЕСКИЙ АРТЕФАКТ · ПЕРВЫЙ ТРАНСПОРТНЫЙ ПАКЕТ
# Источник: 3-й телефон / INCOMING / SESSION-S200 / 2026-07-02

---

## ОРИГИНАЛЬНЫЙ МАНИФЕСТ (verbatim)

```
Purpose: single source of truth for all uploaded ZIP payloads + split big payload.
Rule: Nothing is deleted. RAW/TRASH stays.

Packages in this transport set:
- ARCHIVE_MASTER_TRANSPORT_PART_A_2025-12-26_1710.zip
  — all ZIPs except the big payload (nested ZIPs included)
- ARCHIVE_MASTER_TRANSPORT_BIG_PART1_2025-12-26_1710.zip
  — big payload split part 1 (from original ^_^.zip)
- ARCHIVE_MASTER_TRANSPORT_BIG_PART2_2025-12-26_1710.zip
  — big payload split part 2 (from original ^_^.zip)
```

---

## ИНВЕНТАРЬ ПО КАТЕГОРИЯМ

### BRAND_PROTECT
| Файл | SHA256 |
|---|---|
| LUX_BRAND_PROTECT_FOR_LAWYER_2025-12-26.zip | 6a9f6e6e... |
| LUX_BRAND_PROTECT_MASTER_2025-12-26.zip | 270758d3... |
| LUX_BRAND_PROTECT_WIPO_READY_2025-12-26.zip | 531a9b25... |

### CORE_GOVERNANCE
| Файл | SHA256 |
|---|---|
| 20251226_0329_HUB_CORE_SNAPSHOT_FULL.zip | 940a6eac... |
| LUX_LOGS_ONLY_2025-12-26_12-55.zip | 10253531... |
| LUX_PROTOCOL_SNAPSHOT_2025-12-26_10-12.zip | 8cddb580... |
| PROOF_PACK__CORE_CANON__HUB_PROTOCOL__v1.0__20251225_120600Z.zip | c372d0f0... |
| PROOF_PACK__CORE_CANON__HUB_PROTOCOL__v1.1__20251225_143000Z.zip | fb563efb... |
| ZIP_PROTOCOL_CORE_v1.0.zip | 42d30922... |

### MASTER_ARCHIVE_BIG_SPLIT (из ^_^.zip)
| Файл | Размер | SHA256 |
|---|---|---|
| PAYLOAD_BIG_PART1_2025-12-26_1710.zip | 138.69 MB | dace7d60... |
| PAYLOAD_BIG_PART2_2025-12-26_1710.zip | 138.68 MB | f9dc2739... |

### RESEARCH_DOSSIER
| Файл | Размер |
|---|---|
| 2025-12-26_EN_DISSERTATION_LUX_PACK.zip | 0.03 MB |
| INSIDE_HOUSE_LUXPLUS_SNAPSHOT_2025-12-26_09-54.zip | 0.78 MB |
| SIPA_SUBMISSION_DOSSIER_SNAPSHOT_2025-12-26_0348.zip | 36.58 MB |

### RESIDENCIES_GRANTS
- LUX_ART_RESIDENCIES_GRANTS_2025-12-26.zip
- ZIP_GRANTS_v1.0.zip

### SNAPSHOTS (LUX_SNAPSHOT серия)
- 04:21 / 09:54 (29 MB) / 11:20 / 11:33 / 12:55

### PLATFORM_CHATS_SNAPSHOTS
- SIPA_COHART_CHAT + KENDALL + RARIBLE_REVERIFY

### OTHER
- Instagram statistics.zip (16.49 MB)
- LUX_OLD_MONEY × 2 (PSYCHEDELIC_SELECT + SOCIAL_CLOSE_DAY, 2025-12-24)
- ZIP_GOVERNANCE_v1.0.zip

---

## ПРОЦЕДУРА ВОССТАНОВЛЕНИЯ (оригинал)

```
1. Extract Part A into archive folder.
2. Extract Big Part 1 + Part 2 (reconstructs large payload — keep both).
3. Verify SHA256 using SHA256_2025-12-26_1710.txt
```

---

## КЛЮЧЕВЫЕ ФАКТЫ

**"^_^.zip"** = оригинальное имя большого архива (улыбка). Разбит на 2 части по ~138 MB.
**PROOF_PACK v1.0 + v1.1** = 25.12.2025 12:06Z и 14:30Z — доказательные пакеты Canon существовали ДО патчей v1.1.x
**BRAND_PROTECT + WIPO_READY** = защита бренда планировалась уже 26.12.2025
**RESIDENCIES_GRANTS** = категория грантов с первого транспортного пакета
**"Nothing is deleted. RAW/TRASH stays."** = живёт в V9 по сей день

---

## ПАРАЛЛЕЛИ С V9.6

| Элемент 2025-12-26 | Наследник в V9.6 |
|---|---|
| PROOF_PACK CORE_CANON v1.0/v1.1 | CLAUDE-BRIEF.md + NET-CANON-LOCK |
| BRAND_PROTECT + WIPO_READY | ICON 2026 / LLC Governance / SIPA токен |
| RESIDENCIES_GRANTS | EIC EUR 2.5M / IIA NIS 5M / YC |
| "Nothing is deleted" | SCRIPTS/LEGACY/ — хранить всё |
| Manifest как single source of truth | MASTER_MANIFEST.sh / MANIFEST.tsv |
| SHA256 на каждый файл | sha256sum везде |
| Split big payload | ARCHIVE_COLD_LOCK.sh |
