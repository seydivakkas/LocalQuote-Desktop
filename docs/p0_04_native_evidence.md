# P0-04 — Native binaries and wheel hash evidence

**Status:** preview evidence only; commercial release **HOLD**. A successful CI job does not prove that all upstream licenses have been independently audited.

## Build and verification chain

1. Download binary wheels for pinned ReportLab, Pillow and charset-normalizer.
2. Read package/version from each wheel METADATA and compute SHA-256. Reject duplicate, unexpected or missing wheels.
3. Build the EXE using pip --no-index --require-hashes from the downloaded wheelhouse.
4. Install the identical wheel bytes in an isolated Python SBOM/audit environment.
5. Generate Python runtime CycloneDX inventory and installed package notices.
6. Inspect the completed Windows portable folder; copy actual CPython, Tcl and Tk license files if available; explicitly report missing ones.
7. Enumerate all EXE/PYD/DLL items with SHA-256 and inferred component families. Unknown families are not silently approved.
8. Create a deterministic-order preview ZIP, reopen it, and verify every member hash against the folder manifest.

## CI evidence artifact contents

- runtime-hashed.txt: transient hash lock for wheels downloaded in CI.
- wheel-provenance.json and wheelhouse/: exact wheel filenames, versions, SHA-256 and bytes.
- runtime.cdx.json: Python environment SBOM, not a complete native software bill of materials.
- native-components.json: native binary inventory, classification and open findings.
- package-file-hashes.json: final folder SHA-256 file inventory.
- LocalQuote-Windows-preview-integrity.zip and archive-sha256.txt: hash-verified preview archive.
- license-audit.json, notices/, build-freeze.txt: existing dependency auditing evidence.

Native component family names are **heuristic labels**, not legal determinations of binary ownership or redistribution rights.

## Explicit outstanding release gates

- Download-time hashes attest build/audit byte equality but are not independent preapproved wheel hashes.
- PyInstaller/build-tool transitive wheels still require dedicated hash locking and review.
- OpenSSL, libffi, zlib, Pillow codec dependencies and Microsoft C runtime redistributables need actual provenance and legal notice review.
- CPython, Tcl/Tk and other copyright notices must be checked against the precise redistribution binaries; missing notices are blockers.
- Separate external font files are not intentionally bundled, but customer OS font embedding requires review.
- No first-party LICENSE grant has been selected. The repository being public does not grant redistribution rights.
- Independent reproduction and real disconnected Windows 10/11 GUI acceptance (#2, #4) remain deferred.

**Release remains HOLD.**
