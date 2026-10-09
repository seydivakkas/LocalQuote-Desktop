# LocalQuote Desktop

**Offline-first Turkish customer proposal and pricing tool. P0 engineering preview — NOT PRODUCTION-READY.**

> LocalQuote turns manual agency requests into priced, approved PDF proposals on the customer's own Windows computer. No SaaS subscription, no paid API, and no LLM needed for its core operation.

## Current features
- Tkinter desktop GUI: customers, service catalog, manual requests, quote editor and basic search.
- SQLite on local disk; version-guarded schema; archive/deactivate instead of destructive deletion.
- Integer kuruş storage + `Decimal` quantities, discounts, and VAT with explicit HALF_UP policy.
- Immutable quote-line snapshots; `DRAFT → APPROVED → EXPORTED` workflow with event trail.
- Unicode Turkish A4 PDF (ReportLab + OS-installed font), optional company logo via Python function.
- UTF-8-SIG CSV with injection-resistant text handling; consistent backup and validated new-path restore.
- CLI smoke/demo; automated regression tests; Windows CI workflow and preview packaging script.

## Quick start for developers

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
python -m localquote --gui
```

The developer needs to install Python/dependencies during build. The *customer* should receive a built application folder and should not have to install Python. A clean Windows build is **not yet verified**.

## Headless demo / smoke

```bash
python -m localquote --smoke --db /tmp/localquote-smoke.db
python -m localquote --demo demo.pdf --db /tmp/localquote-demo.db
```

Windows PowerShell example:

```powershell
python -m localquote --smoke --db "$env:TEMP\localquote-smoke.db"
python -m localquote --demo "$env:TEMP\localquote-demo.pdf" --db "$env:TEMP\localquote-demo.db"
```

The PDF shows **synthetic** test data. Never commit real customer records, DBs, contacts or quotations.

## Windows portable build

```powershell
.\packaging\build_windows.ps1
```

Once confirmed, copy the **entire** `dist\LocalQuote-Desktop\` directory. In `--windowed` packaging, CLI status messages may be hidden but exit codes remain testable. No internet is needed to use the packaged core. Building may require an initial download of open-source dependencies.

## Backup and recovery

UI: *Teklifler → Veritabanı Yedeği*. No overwrite of existing backups.

Recover **only into a fresh directory, with application closed**:

```bash
python -m localquote --restore backup.sqlite3 --db /path/to/EMPTY/new.sqlite3
```

Restart with environment variable `LOCALQUOTE_DATA_DIR` pointed to the **directory** of that restored database; standard filename there is `localquote.sqlite3`. Do not rename a backup into the same running DB or edit SQLite file from multiple computers simultaneously.

## Technical plan and gates

- [P0 scope and requirements](docs/requirements.md)
- [Architecture, safety and data](docs/architecture.md)
- [P0 evidence matrix](docs/p0_acceptance_matrix.md)
- [Windows offline validation](docs/windows_validation.md)
- [Benchmark protocol](docs/benchmark.md)
- [Licensing inventory](licenses/dependencies.csv) / [Third-party release checkpoint](licenses/THIRD_PARTY.md)

**Current release status: HOLD.** Linux headless smoke and local tests pass; GUI has not been exercised on a real Windows PC; clean Windows portable EXE, installed dependency SBOM and offline end-to-end evidence are missing. Local LLM/RAG are intentionally out of P0.

## Intellectual property

Repository-owner source license has not been selected. No LICENSE file is published yet. External dependencies keep their own licenses and notice obligations. Commercial rights and distribution should be reviewed before sale.