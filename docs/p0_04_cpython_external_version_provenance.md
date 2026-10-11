# CPython v3.13.15 Windows external source mapping

Official source: https://github.com/python/cpython/blob/v3.13.15/PCbuild/get_externals.bat and https://github.com/python/cpython/blob/v3.13.15/PCbuild/python.props

| External | CPython source pin | Windows CI runtime/PE evidence |
|---|---|---|
| libffi | libffi-3.4.4 | libffi-8.dll byte-identical to installed Python 3.13.15, PSF signed; library-specific PE version absent |
| OpenSSL | openssl-3.0.21 | ssl.OPENSSL_VERSION and PE FileVersion 3.0.21, PSF signed |
| SQLite | sqlite-3.50.4.0 | sqlite3.sqlite_version=3.50.4 and PE FileVersion 3.50.4.0, PSF signed; hash differs from official embeddable ZIP, investigation required |
| Tcl/Tk | tcltk-8.6.15.0 | Tcl runtime 8.6.15 and PE 8.6.15 |
| zlib | zlib-1.3.1 | zlib runtime 1.3.1 |

These CPython dependency pins are stronger attribution evidence than guessed versions based only on filenames. They do NOT prove that every bundled DLL was bitwise reconstructed from a particular upstream source tarball, or that Microsoft's UCRT files may be redistributed. Release HOLD.
