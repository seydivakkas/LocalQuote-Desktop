# P0 feature acceptance matrix — 2026-10-09

| Excel feature | Implementation | Current evidence | Status |
|---|---|---|---|
| LQ-F001 Portable offline startup | config, CLI, Tkinter | Local headless smoke PASS; clean Windows missing | PARTIAL |
| LQ-F002 Schema + migration | SQLite v1, version guard | initial schema, incompatible version rejection; v1→v2 not implemented | PARTIAL |
| LQ-F003 Customer CRUD | service, GUI | update/archive/list automated | CORE PASS; UI UNTESTED |
| LQ-F004 Service/package CRUD | services service+GUI | service CRUD PASS; multi-service packages not implemented | PARTIAL |
| LQ-F005 Manual request | services, GUI | create/due validation PASS; request editing not yet added | PARTIAL |
| LQ-F006 Request to quote | service, GUI | integration PASS | CORE PASS; UI UNTESTED |
| LQ-F007 Decimal | money/pricing | 0.1+0.2, negative, NaN, rounding PASS | CORE PASS |
| LQ-F008 Discounts/VAT | pricing | mixed VAT and discount order PASS | CORE PASS |
| LQ-F009 Revision/approval | service, GUI | draft edit, lock and status events PASS; quote revision history beyond events missing | PARTIAL |
| LQ-F010 Unicode PDF/logo | ReportLab | Unicode demo, optional logo supported; GUI/Windows verification pending | PARTIAL |
| LQ-F011 Immutable quote lines | SQLite | catalog update leaves saved line untouched PASS | CORE PASS |
| LQ-F012 Search/filters | indexed SQLite | query and injection tests PASS; 1000-row benchmark pending | PARTIAL |
| LQ-F013 CSV injection-safe export | csv module | escaping/BOM PASS | CORE PASS |
| LQ-F014 SQLite backup/restore | backup module + CLI | restoration matches snapshots PASS; Windows transfer pending | PARTIAL |
| LQ-F015 Error boundary | GUI dialog, guarded DB open | corrupt DB error test PASS, full UI error validation pending | PARTIAL |
| LQ-F016 Portable EXE | PowerShell build + Actions preview | clean Windows runtime not verified | HOLD |
| LQ-F017 Regression quality | unittest 26 cases, CI YAML | local 26/26 PASS; 2026-10-10 GitHub Actions core test matrix 4/4 PASS; preview and independent Windows customer checks tracked separately | PARTIAL |

**P0 overall: HOLD.** Do not move to Excel phase 2 until all release checks pass. GitHub repo and source import completed. CI status: see https://github.com/seydivakkas/LocalQuote-Desktop/actions. Clean Windows customer validation, missing P0 features, and licensing still require independent evidence.
