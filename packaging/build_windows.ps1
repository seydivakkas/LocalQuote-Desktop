$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
py -3 -m pip install -e .
py -3 -m pip install 'pyinstaller>=6,<7'
py -3 -m unittest discover -s tests -v
py -3 -m PyInstaller --clean --noconfirm --onedir --windowed `
  --name LocalQuote-Desktop --paths src launcher.py
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed' }
$exe = Join-Path (Get-Location) 'dist\LocalQuote-Desktop\LocalQuote-Desktop.exe'
& $exe --smoke --db (Join-Path $env:TEMP 'localquote-package-smoke.sqlite3')
if ($LASTEXITCODE -ne 0) { throw 'Packaged EXE smoke failed' }
Write-Host "Portable release folder: dist\LocalQuote-Desktop"
