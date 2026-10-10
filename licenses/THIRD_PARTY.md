# Third-party notices — P0-04 preliminary audit

**Release HOLD:** This repository is public but contains no project-owned open-source LICENSE grant. All rights remain with the relevant copyright holders unless the owner decides otherwise. Any commercial customer delivery requires separately agreed license/usage terms.

The runtime dependencies are **ReportLab 4.4.9** (BSD-3-Clause), **Pillow 12.3.0** (MIT-CMU), and **charset-normalizer 3.4.7** (MIT). Versions are constrained by requirements-runtime.lock; their installed wheel license text files are copied into THIRD_PARTY_LICENSES/ of the preview package.

**Platform components still require review:** CPython (PSF), Tcl/Tk (TCL), SQLite (public domain), Windows native libraries, reportlab/fonts including separately licensed fonts. Fonts installed on the customer's own OS are not intentionally bundled in source.

**Build tool:** PyInstaller 6.22.3 uses GPL with a bootloader exception permitting commercial distribution of the generated executable, subject to dependency license compliance. 

See docs/p0_04_license_sbom.md for precise SBOM generation, SHA-256 evidence, limitations, and remaining release gates. A green CI workflow is not commercial approval.
