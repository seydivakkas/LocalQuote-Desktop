# P0-04 native licensing evidence — release HOLD

The verified main preview before this change listed 81 native EXE/DLL/PYD files.
This matrix records what is confirmed by CI versus what still requires legal review.

| Component | Verified by tooling | Official license source | Remaining gate |
|---|---|---|---|
| CPython | Interpreter version, SHA-matched installed binaries, PE version/signature and packaged notice | https://docs.python.org/3.13/license.html | Tie precise interpreter release to upstream distributable and complete embedded notices |
| Tcl/Tk | DLL SHA, Tcl runtime patchlevel, compiler Tk version, PE metadata, copied notices | https://www.tcl-lang.org/software/tcltk/license.html | Prove DLL-to-upstream patch/source correspondence |
| SQLite | sqlite3 runtime version, DLL and module SHA, PE identity | https://www.sqlite.org/copyright.html | Code is public domain; binary provenance still needs evidence |
| OpenSSL | Runtime reported OpenSSL version, two native DLL hashes, PE metadata | https://www.openssl.org/source/license.html | Match exact DLL version to OpenSSL 3 Apache-2.0 source and any notices |
| libffi | libffi-8.dll SHA and PE metadata, reference license | https://github.com/libffi/libffi | DLL ABI suffix is not an exact library patch version |
| zlib | zlib runtime version, DLL SHA and PE metadata | https://zlib.net/zlib_license.html | Confirm exact bundled native version/source |
| Pillow | Exact Pillow 12.3.0 wheel/PYD matches and packaged Pillow license | https://pillow.readthedocs.io/en/stable/installation/building-from-source.html | Audit embedded JPEG/AVIF/TIFF/WebP/LCMS codecs and attribution |
| Microsoft CRT/UCRT/APISet | Separate native file hashes, installed Windows copy comparison, PE vendor/signature status | https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files | Licensee rights and Microsoft REDIST list for EVERY bundled DLL |
| PyInstaller | Exact hashed build-tool wheels, license collection, bootloader file hash | https://pyinstaller.org/en/stable/license.html | Review bootloader exception and shipped build components |

## GitHub Actions evidence

- native-source-evidence.json: per-file wheel / installed-Python / Windows copy hash matches; runtime library versions.
- windows-pe-identity.json: per-file version resources, publisher and Authenticode fields.
- native-evidence-integrity.json: all SHA-256 values and paths cross-checked against final package manifest.
- build-licenses/build-tool-license-notices.json: exact hashed build-wheel license files including vendored files.
- native-components.json: third-party references, inventory, unresolved manual-review flags.

INSTALLED_COPY_EXACT proves equal bytes to a runner file, not upstream origin or redistribution rights.
WHEEL_EXACT proves equal bytes to a CI-downloaded wheel, not an approved publisher signature.
A Valid Authenticode signature is publisher evidence, NOT a license grant.
UPSTREAM_REFERENCES_UNVERIFIED are legal text references, NOT a guarantee the text matches bundled DLL patch versions.

## Release blockers

1. Match every native DLL to original version/source and required notices, especially Pillow embedded libraries.
2. Verify licensed Visual Studio redist entitlement or choose/test a lawful no-bundling alternative.
3. Review build-tool redistribution/bootloader exception and any nonstandard third-party notices.
4. First-party contract remains DRAFT without owner's explicit authorization.
5. Clean disconnected Windows GUI/backup acceptance (#2, #4) remains LAST.

Issue #5 and commercial release remain HOLD, regardless of green automated CI.
