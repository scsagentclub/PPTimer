param([string]$Version)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
if (-not $Version) {
    $Version = (Get-Content (Join-Path $projectRoot 'VERSION') -Raw).Trim()
}
if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    throw 'MSI version must have the form major.minor.patch.'
}
$parts = $Version.Split('.')
if ([int]$parts[0] -gt 255 -or [int]$parts[1] -gt 255 -or [int]$parts[2] -gt 65535) {
    throw 'MSI version exceeds the Windows Installer version limits.'
}
$exe = Join-Path $projectRoot 'dist/PPTimer.exe'
if (-not (Test-Path $exe)) {
    throw 'Missing dist/PPTimer.exe. Run python build.py on Windows first.'
}
Get-Command wix -ErrorAction Stop | Out-Null
$output = Join-Path $projectRoot "dist/PPTimer-$Version-win64.msi"
& wix build (Join-Path $PSScriptRoot 'PPTimer.wxs') -arch x64 `
    -d "ProductVersion=$Version" -d "SourceExe=$exe" `
    -d "IconPath=$(Join-Path $projectRoot 'timer_icon.ico')" -o $output
if ($LASTEXITCODE -ne 0) {
    throw "WiX build failed with exit code $LASTEXITCODE."
}
if (-not (Test-Path $output)) {
    throw "MSI output was not created: $output"
}
Write-Host "Built $output"
