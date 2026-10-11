# Native upstream release-specific license sources

Current Windows CI runtime reported OpenSSL 3.0.21 and Tcl 8.6.15. These source references are pinned to the corresponding upstream release tags. The actual DLL binaries and their copyright/patch lineage still require comparison to the corresponding official distribution build; a matching license text alone is insufficient.

- OpenSSL 3.0.21: https://github.com/openssl/openssl/blob/openssl-3.0.21/LICENSE.txt (Apache-2.0)
- Tcl 8.6.15: https://github.com/tcltk/tcl/blob/core-8-6-15/license.terms (TCL)
- Tk 8.6.15: https://github.com/tcltk/tk/blob/core-8-6-15/license.terms (TCL)
- SQLite 3.50.4 is dedicated to the public domain: https://sqlite.org/copyright.html
- zlib 1.3.1: https://github.com/madler/zlib/blob/v1.3.1/LICENSE
- libffi: libffi-8.dll ABI suffix is NOT an exact upstream release version. An upstream 3.4.6 reference notice is available but exact version remains unverified.

These texts are notices/references for distribution review, NOT a legally certified bill of materials. HOLD.
