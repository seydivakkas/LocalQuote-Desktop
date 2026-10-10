$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
py -3 -m pip install -e . -c requirements-runtime.lock
if ($LASTEXITCODE -ne 0) { throw 'Runtime dependency install failed' }
py -3 -m pip install -r requirements-build.lock
if ($LASTEXITCODE -ne 0) { throw 'Pinned PyInstaller install failed' }
py -3 -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
py -3 -m PyInstaller --clean --noconfirm --onedir --windowed --name LocalQuote-Desktop --paths src launcher.py
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed' }
$exe = Join-Path (Get-Location) 'dist\LocalQuote-Desktop\LocalQuote-Desktop.exe'
& $exe --smoke --db (Join-Path $env:TEMP 'localquote-package-smoke.sqlite3')
if ($LASTEXITCODE -ne 0) { throw 'Packaged EXE smoke failed' }
Write-Host 'Windows package: dist\LocalQuote-Desktop (engineering preview, not commercial release)'
