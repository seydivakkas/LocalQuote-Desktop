param(
  [Parameter(Mandatory=$true)]
  [string]$ZipPath
)

$ErrorActionPreference = 'Stop'
$repoUrl = 'https://github.com/seydivakkas/LocalQuote-Desktop.git'
$zip = (Resolve-Path $ZipPath).Path
$work = Join-Path $env:TEMP ("LocalQuote-P0-Import-" + [guid]::NewGuid().ToString('N'))
$unzip = Join-Path $work 'unpacked'
$clone = Join-Path $work 'repo'

New-Item -ItemType Directory -Path $unzip -Force | Out-Null
Write-Host "Temporary work directory: $work"
Expand-Archive -LiteralPath $zip -DestinationPath $unzip -Force
$source = Join-Path $unzip 'LocalQuote-Desktop'
if (-not (Test-Path (Join-Path $source 'pyproject.toml'))) {
  throw "Incorrect ZIP or missing project root: $source"
}
if (-not (Test-Path (Join-Path $source 'tests\test_core.py'))) {
  throw 'Tests missing from source archive. Refusing to push.'
}

git clone $repoUrl $clone
if ($LASTEXITCODE -ne 0) { throw 'git clone failed' }
if ((git -C $clone branch --show-current).Trim() -ne 'main') {
  throw 'Expected the main branch; refusing to push to another branch.'
}
if (-not (git -C $clone status --porcelain) -eq '') {
  throw 'Git working tree is not clean.'
}

Copy-Item -Path (Join-Path $source '*') -Destination $clone -Recurse -Force
Copy-Item -Path (Join-Path $source '.gitattributes') -Destination $clone -Force
Copy-Item -Path (Join-Path $source '.gitignore') -Destination $clone -Force
Copy-Item -Path (Join-Path $source '.github') -Destination $clone -Recurse -Force

Push-Location $clone
try {
  py -3 -m pip install -e .
  if ($LASTEXITCODE -ne 0) { throw 'Dependency install failed; nothing pushed.' }
  py -3 -m unittest discover -s tests -v
  if ($LASTEXITCODE -ne 0) { throw 'P0 tests failed; nothing pushed.' }
  py -3 -m localquote --smoke --db (Join-Path $env:TEMP ('localquote-smoke-' + [guid]::NewGuid().ToString('N') + '.sqlite3'))
  if ($LASTEXITCODE -ne 0) { throw 'Smoke test failed; nothing pushed.' }

  git add -A
  git status --short
  git commit -m "feat: import tested LocalQuote P0 source, docs and CI"
  if ($LASTEXITCODE -ne 0) { throw 'git commit failed.' }
  git push origin HEAD:main
  if ($LASTEXITCODE -ne 0) { throw 'git push failed. Recheck remote HEAD before retrying.' }
  Write-Host 'PASS: P0 source pushed. Next: inspect GitHub Actions.'
} finally {
  Pop-Location
}
