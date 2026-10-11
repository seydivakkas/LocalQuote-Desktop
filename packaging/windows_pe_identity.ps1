<#
Records PE version resources and Windows Authenticode status for the exact
packaged EXE, DLL and PYD files. A valid Microsoft signature proves signing,
NOT that LocalQuote holds redistribution rights.
#>
param(
  [Parameter(Mandatory=$true)][string]$Bundle,
  [Parameter(Mandatory=$true)][string]$Output
)
$ErrorActionPreference = "Stop"
$bundleRoot = (Resolve-Path -LiteralPath $Bundle).Path
$items = @()
$files = @(Get-ChildItem -LiteralPath $bundleRoot -Recurse -File | Where-Object {
  $_.Extension.ToLowerInvariant() -in @(".exe",".pyd",".dll")
})
foreach ($file in $files) {
  $rel = $file.FullName.Substring($bundleRoot.Length).TrimStart("\","/").Replace("\","/")
  $v = $file.VersionInfo
  $sig = Get-AuthenticodeSignature -LiteralPath $file.FullName
  $items += [pscustomobject]@{
    path = $rel
    sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    file_version = [string]$v.FileVersion
    product_version = [string]$v.ProductVersion
    product_name = [string]$v.ProductName
    company_name = [string]$v.CompanyName
    original_filename = [string]$v.OriginalFilename
    authenticode_status = [string]$sig.Status
    signing_subject = if ($null -ne $sig.SignerCertificate) { [string]$sig.SignerCertificate.Subject } else { $null }
    signing_thumbprint = if ($null -ne $sig.SignerCertificate) { [string]$sig.SignerCertificate.Thumbprint } else { $null }
  }
}
if ($items.Count -eq 0) { throw "No PE binaries found" }
$outParent = Split-Path -Parent $Output
if ($outParent) { New-Item -ItemType Directory -Force $outParent | Out-Null }
@{
 schema = "localquote-windows-pe-metadata-v1"
 evidence_only = $true
 commercial_license_cleared = $false
 files = $items
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $Output -Encoding utf8
Write-Host "Recorded file versions and signatures for $($items.Count) native binaries (NOT a redistributability approval)"
