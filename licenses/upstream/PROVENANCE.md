# Vendored third-party legal text provenance

## Tcl 8.6 license

- File: Tcl-8.6-license.terms
- Copyright/license owner: Tcl upstream rights holders (as stated in the notice).
- Upstream repository: https://github.com/tcltk/tcl
- Pinned upstream source revision: c79582174e32de9cb5f1a43f90e4944a5cdbae11
- Exact source URL: https://raw.githubusercontent.com/tcltk/tcl/c79582174e32de9cb5f1a43f90e4944a5cdbae11/license.terms
- Purpose: retain the required Tcl license wording in Windows preview when the Python/Tcl installation does not expose license.terms.

This copy is upstream legal text, NOT authored LocalQuote source code. Do not
rewrite or remove its terms. The known Windows preview has tcl86t.dll but its
frozen directory did not include the Tcl notice, even though Tk license.terms
was present. The upstream text is staged in THIRD_PARTY_LICENSES/Tcl at build time.

**Not proven:** the exact provenance and Tcl patch version of tcl86t.dll,
or whether additional separately licensed native components ship alongside it.
The audit emits MANUAL_PROVENANCE_REVIEW when using this fallback.
