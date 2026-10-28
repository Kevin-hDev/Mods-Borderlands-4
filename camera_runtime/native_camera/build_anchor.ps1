param([switch]$TestsOnly, [string]$TrialAssets)
$ErrorActionPreference = 'Stop'
$sourceRoot = $PSScriptRoot
$cameraRoot = $sourceRoot
$buildRoot = Join-Path $env:TEMP 'apex_native_climb_anchor_build'
New-Item -ItemType Directory -Force -Path $buildRoot | Out-Null
$vcvars = 'C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat'
$environmentLines = & $env:ComSpec /d /c "`"$vcvars`" >nul && set"
if ($LASTEXITCODE -ne 0) { throw 'Compiler environment unavailable' }
foreach ($line in $environmentLines) {
    if ($line -match '^([^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
    }
}
$common = @('/nologo', '/std:c++17', '/EHsc', '/W4', '/WX', '/O2', '/MT', '/Brepro', "/I$cameraRoot")
Push-Location $buildRoot
try {
    & cl.exe @common (Join-Path $sourceRoot 'anchor_pose.cpp') (Join-Path $sourceRoot 'test_anchor_pose.cpp') '/Fe:anchor_pose_test.exe'
    if ($LASTEXITCODE -ne 0) { throw 'Anchor test build failed' }
    & .\anchor_pose_test.exe
    if ($LASTEXITCODE -ne 0) { throw 'Anchor tests failed' }
    New-Item -ItemType Directory -Force -Path 'anchor_test_sdk' | Out-Null
    & cl.exe @common '/LD' (Join-Path $sourceRoot 'test_anchor_sdk_fixture.cpp') '/Fe:anchor_test_sdk/unrealsdk.dll'
    if ($LASTEXITCODE -ne 0) { throw 'SDK boundary fixture build failed' }
    $identitySources = @('anchor_identity.cpp', 'test_anchor_identity.cpp') | ForEach-Object { Join-Path $sourceRoot $_ }
    $identitySources += @('ads_identity.cpp', 'ads_mode.cpp') | ForEach-Object { Join-Path $cameraRoot $_ }
    & cl.exe @common @identitySources '/Fe:anchor_identity_test.exe'
    if ($LASTEXITCODE -ne 0) { throw 'Anchor identity test build failed' }
    & .\anchor_identity_test.exe
    if ($LASTEXITCODE -ne 0) { throw 'Anchor identity tests failed' }
    $bridgeSources = @('anchor_bridge.cpp', 'test_anchor_bridge.cpp') | ForEach-Object { Join-Path $sourceRoot $_ }
    & cl.exe @common @bridgeSources '/Fe:anchor_bridge_test.exe'
    if ($LASTEXITCODE -ne 0) { throw 'Anchor bridge test build failed' }
    & .\anchor_bridge_test.exe
    if ($LASTEXITCODE -ne 0) { throw 'Anchor bridge tests failed' }
    if ($TestsOnly) { return }
    $sources = @('anchor_pose.cpp', 'anchor_identity.cpp', 'anchor_bridge.cpp') | ForEach-Object { Join-Path $sourceRoot $_ }
    $sources += @('ads_identity.cpp', 'ads_mode.cpp', 'ads_compat.cpp') | ForEach-Object { Join-Path $cameraRoot $_ }
    & cl.exe @common '/LD' @sources '/Fe:apex_climb_anchor_trial.dll' 'bcrypt.lib'
    if ($LASTEXITCODE -ne 0) { throw 'Anchor trial build failed' }
    if (-not $TrialAssets) { throw 'Trial assets destination required' }
    $assets = $TrialAssets
    New-Item -ItemType Directory -Force -Path $assets | Out-Null
    Copy-Item -LiteralPath 'apex_climb_anchor_trial.dll' -Destination $assets -Force
    $hash = Get-FileHash -LiteralPath (Join-Path $assets 'apex_climb_anchor_trial.dll') -Algorithm SHA256
    Set-Content -LiteralPath (Join-Path $assets 'apex_climb_anchor_trial.dll.sha256') -Value $hash.Hash.ToLowerInvariant() -Encoding ascii -NoNewline
    $hash
} finally { Pop-Location }
