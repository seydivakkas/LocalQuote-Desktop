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


## Further upstream *reference* licenses (not binary-version attestations)

These notices are included for transparency and carried into the preview folder
under THIRD_PARTY_LICENSES/UPSTREAM_REFERENCES_UNVERIFIED. They do **not**
mean the installed native DLL has been proven to come from the cited source
tag/revision. The exact DLL file version, installed-source SHA match and
Authenticode status are recorded independently by CI.

| File | Official upstream reference | Interpretation |
|---|---|---|
| OpenSSL-3.x-LICENSE.txt | https://github.com/openssl/openssl/blob/openssl-3.0/LICENSE.txt | Apache-2.0 template for OpenSSL 3.x; exact bundled DLL patch version must be recorded |
| libffi-3.4.4-LICENSE | https://github.com/libffi/libffi/blob/v3.4.4/LICENSE | MIT-like libffi terms; a filename libffi-8.dll does not prove version 3.4.6 |
| zlib-1.3.1-LICENSE | https://github.com/madler/zlib/blob/v1.3.1/LICENSE | zlib terms; actual bundled DLL's patch/version is independently checked |

SQLite is different: the deliverable SQLite library is expressly dedicated to
the public domain; source: https://www.sqlite.org/copyright.html. Do not
invent an SPDX license text from the URL.

For Microsoft components, no permissive OSS notice is assumed. Microsoft
restricts Visual C++ redistributable file rights according to Visual Studio
license entitlements and the applicable REDIST list:
https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files
https://learn.microsoft.com/en-us/cpp/windows/determining-which-dlls-to-redistribute

The preview is **HOLD** until individual native licensing/provenance gates
have been reviewed and signed off by the product owner with suitable advice.
