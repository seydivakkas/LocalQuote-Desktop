$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
python -c "import sys; assert sys.version_info[:2] == (3, 13), sys.version"
python -m pip install --no-index --find-links docs/license-evidence/wheelhouse --require-hashes -r docs/license-evidence/runtime-hashed.txt
if ($LASTEXITCODE -ne 0) { throw 'Hash-checked runtime wheel install failed' }
python -m pip install -e . --no-deps
if ($LASTEXITCODE -ne 0) { throw 'Local package install failed' }
python -m pip install --no-index --find-links docs/license-evidence/build-wheelhouse --require-hashes -r docs/license-evidence/build-hashed.txt
if ($LASTEXITCODE -ne 0) { throw 'Pinned PyInstaller install failed' }
python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
python -m PyInstaller --clean --noconfirm --onedir --windowed --name LocalQuote-Desktop --paths src launcher.py
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed' }
$exe = Join-Path (Get-Location) 'dist\LocalQuote-Desktop\LocalQuote-Desktop.exe'
& $exe --smoke --db (Join-Path $env:TEMP 'localquote-package-smoke.sqlite3')
if ($LASTEXITCODE -ne 0) { throw 'Packaged EXE smoke failed' }
Write-Host 'Windows package: dist\LocalQuote-Desktop (engineering preview, not commercial release)'
