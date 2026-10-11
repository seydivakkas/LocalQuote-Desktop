# P0-04 — Windows 10/11 System-UCRT engineering candidate

**Not a commercial release.** The original Windows PyInstaller folder is preserved and keeps its current verification workflow.

## Official Microsoft evidence

Microsoft states UCRT is part of Windows 10 and 11; these operating systems use the centrally deployed version even if a program has an app-local UCRT. Local deployment is supported but discouraged. Separately licensed VC++ redistributables are NOT automatically approved.

- https://learn.microsoft.com/en-us/cpp/windows/universal-crt-deployment
- https://learn.microsoft.com/en-us/cpp/windows/determining-which-dlls-to-redistribute
- https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files

## Exact software change

packaging/system_ucrt_variant.py copies the original folder into dist/LocalQuote-Desktop-system-ucrt/ without modifying the baseline.

Only direct _internal/ DLLs named api-ms-win-core-*.dll, api-ms-win-crt-*.dll and ucrtbase.dll are removed.

The process rejects Windows earlier than version 10, overlapping source/output, missing system ucrtbase.dll, unexpectedly few UCRT files, missing VCRUNTIME140.dll, and any unintentional modification to other files. It DOES NOT remove VCRUNTIME140.dll, arbitrary DLLs, fonts, data, or licenses. Windows 7 and 8 are unsupported in this candidate.

Windows GitHub Actions builds the original, generates an independent engineering candidate, smoke-tests both, runs packaged PDF + SQLite + backup/restore checks on synthetic data, checks SHA-256 ZIP manifests, then builds both a second time on another Windows runner and compares byte-for-byte.

The evidence files are system-ucrt-variant.json, system-ucrt-windows-ci-proof.json, system-ucrt-folder/package-file-hashes.json, system-ucrt-build-comparison.json, and codec-redist-review.json.

**Limits:** Windows CI is not a clean disconnected customer laptop/VM. Real Windows 10/11 GUI, enterprise policy, missing runtimes, antivirus and backup acceptance is deferred to the LAST stage (#2 and #4).

## Codec license and REDIST matrix

codec_redist_review.py checks every enabled Pillow codec reported by the Windows runtime against the source license notice references pinned to Pillow 12.3.0. An absent source notice fails CI. It does not grant redistribution permissions or cryptographically prove the source version of statically linked codec bytes.

AVIF, JPEG, TIFF, WebP, FreeType, OpenJPEG, lcms and zlib-related subcomponents remain independently reviewable. VCRUNTIME140.dll is RETAINED and Microsoft developer license entitlement + the REDIST list still need legal verification. Owner's single-payment perpetual customer-use agreement remains DRAFT.

Issue #5 stays OPEN and the commercial release stays **HOLD**.
