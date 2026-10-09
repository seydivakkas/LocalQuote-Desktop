# Technical architecture

```text
Tkinter GUI / CLI
    ↓
service.py (validation, transitions, workflow)
    ├── domain/money.py + pricing.py (Decimal & integer kuruş)
    ├── storage/db.py (SQLite schema v1)
    ├── storage/backup.py (sqlite3.backup + validated new-path restore)
    └── export/pdf.py and export/csv_export.py
```

- No background HTTP endpoints, API keys, analytics, telemetry or network requests.
- SQLite schema is managed by `PRAGMA user_version=1`; unknown and newer schemas fail closed instead of silently overwriting user data.
- Current schema is v1; v1→v2 migration requires an additional migration and repeatable data-preservation test **before** v2 release.
- No floats for money: cents are integers in storage; quantity, discount, VAT are finite Decimal strings.
- Rounding policy: quantity × price → gross kuruş HALF_UP; gross × discount% → discount kuruş HALF_UP; taxable × VAT% → VAT kuruş HALF_UP. Then sum rounded line amounts.
- Quote lines are stored as price snapshots; catalog edits never retroactively change prior quotes.
- All mutations performed only on DRAFT except APPROVED→EXPORTED. No direct delete of historical quotes.
- PDF requires user OS installed Unicode font. Font files are not copied into this repository or distributed with the application.
- SQLite not suitable for multiple employees editing the same DB from a shared network drive. Use one computer or separately designed LAN server product later.
- Database default on Windows: `%LOCALAPPDATA%\LocalQuote\localquote.sqlite3` (data folder is separate from executable). Override via `LOCALQUOTE_DATA_DIR`.

## Threat model highlights
- SQL injection: parameter binding; fixed internal table allowlist; LIKE wildcards escaped.
- CSV formula injection: leading spreadsheet expressions escaped; UTF-8 BOM.
- Untrusted customer text: validated length, HTML-escaped before ReportLab Paragraph rendering.
- Backup: never overwrite existing backup; restore rejects invalid or existing target.
- Logs: not collected by default; no customer data sent to telemetry.
- Security boundary is the logged-in Windows user. SQLite data is not encrypted at rest; Windows permissions/BitLocker needed when appropriate.
