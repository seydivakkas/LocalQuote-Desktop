# P0-04 — Third-party licenses and CycloneDX SBOM

**Current status: HOLD.** This engineering audit does not authorize commercial distribution or replace Windows end-user acceptance.

### Pinned Python dependencies

LocalQuote → ReportLab 4.4.9 → Pillow 12.3.0 and charset-normalizer 3.4.7. Python wheel metadata and license files are collected from an isolated virtual environment. Runtime versions are fixed in requirements-runtime.lock. This is NOT a hash-locked/reproducible build specification.

| Component | License | Notes |
|---|---|---|
| ReportLab | BSD-3-Clause | Wheel notice collected |
| Pillow | MIT-CMU | Native libraries may need additional notices |
| charset-normalizer | MIT | Wheel notice collected |
| CPython | PSF | Full bundled runtime review pending |
| Tcl/Tk | TCL | Full bundled runtime review pending |
| SQLite | Public domain | Verify bundled copy |
| PyInstaller 6.22.3 | GPL with bootloader exception | Build only, exception applies |
| Fonts | Varies | Font embedding and bundled file check pending |

### CI outputs

The Windows preview CI runs unit/integration tests, creates the Windows folder, checks PDF/backup behavior, installs a separate **runtime-only** Python environment, generates **CycloneDX 1.6 JSON** with cyclonedx-bom==7.5.0, and runs packaging/license_audit.py against that environment. Files are uploaded under the LocalQuote-P0-04-SBOM-License-Evidence artifact.

- runtime.cdx.json — isolated Python dependency SBOM (not a complete native binary SBOM).
- license-audit.json — expected version checks, full installed license texts and release HOLD.
- notices/ — actual wheel license files, with SHA-256 hashes.
- bundle-manifest.json — per-file SHA-256 hashes and size for the exact Windows preview directory.
- build-freeze.txt — installed build-environment Python versions.

The audit includes full wheel notices in the preview under THIRD_PARTY_LICENSES. It detects font files in the bundle but **does not automatically approve their legal terms**.

### Remaining release blockers

- [ ] Review native runtime files: exact CPython, Tcl/Tk, SQLite, compiled Pillow dependencies and notices.
- [ ] Review ReportLab package font data (including separately licensed DarkGarden fonts) and rights to embed OS fonts in PDFs.
- [ ] Complete full wheel hashes / independently reproduced artifacts and verify source commit/SBOM/binary correspondence.
- [ ] Owner must decide the first-party source code distribution license (a public GitHub repo does not grant redistribution rights).
- [ ] Finally perform true offline GUI acceptance on a clean Windows PC for #2 and #4.

**Issue #5 remains OPEN; general commercial release remains HOLD.**

### Interpreter-consistency gate

Windows CI explicitly checks and uses **Python 3.13** via the setup-python-managed `python` command for EXE packaging, independent license inventory and the SBOM. Do **not** use `py -3` (it chooses the latest installed Python on the runner). The previous PR preview inadvertently built with Python 3.14 and is not accepted as release evidence.
