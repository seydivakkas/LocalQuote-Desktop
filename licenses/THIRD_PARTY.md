# Third-party notices / licensing checkpoint

The LocalQuote repository's own distribution license is **undecided**. There is no general permission to redistribute user-owned software merely because it has a public GitHub repository. The project owner must select an appropriate license before commercial distribution.

External components: CPython (PSF), SQLite (public domain / blessing), Tcl/Tk (Tcl license), ReportLab (BSD-3-Clause), plus ReportLab's actual installed transitive dependencies (review the exact resolved environment). PyInstaller's bootloader has a GPL exception, subject to its requirements. Do not bundle third-party fonts from the development container.

**Release HOLD:** before sending EXE to customers, generate an SBOM for the precise frozen package, retain full license texts and copyright attributions as required, verify build artifacts and all transitive dependencies including Tcl/Tk/Pillow/ReportLab. Do not treat this inventory as completed legal due diligence.
