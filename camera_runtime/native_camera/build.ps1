param([switch]$TestsOnly)
$ErrorActionPreference = 'Stop'
$sourceRoot = $PSScriptRoot
$contract = Get-Content -Raw -LiteralPath (Join-Path $sourceRoot 'ads_contract.json') | ConvertFrom-Json
$libraryStem = "apex_camera_view_v$($contract.constants.VIEW_ABI)"
$buildRoot = Join-Path $env:TEMP 'apex_camera_runtime_build'
New-Item -ItemType Directory -Force -Path $buildRoot | Out-Null
$vcvars = 'C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat'
$environmentLines = & $env:ComSpec /d /c "`"$vcvars`" >nul && set"
if ($LASTEXITCODE -ne 0) { throw 'Compiler environment unavailable' }
foreach ($line in $environmentLines) {
    if ($line -match '^([^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
    }
}
$common = @('/nologo', '/std:c++17', '/EHsc', '/W4', '/WX', '/O2', '/MT', '/Brepro')
$anchorSources = @('anchor_pose.cpp', 'anchor_identity.cpp', 'anchor_bridge.cpp') | ForEach-Object { Join-Path $sourceRoot $_ }
& (Join-Path $sourceRoot 'build_anchor.ps1') -TestsOnly
$sources = @((Join-Path $sourceRoot 'view_target_math.cpp'),
             (Join-Path $sourceRoot 'offset_transition.cpp'),
             (Join-Path $sourceRoot 'view_performance_bridge.cpp'),
             (Join-Path $sourceRoot 'view_dispatch.cpp'),
             (Join-Path $sourceRoot 'view_target_bridge.cpp'))
Push-Location $buildRoot
try {
    & cl.exe @common (Join-Path $sourceRoot 'test_camera_builds.cpp') '/Fe:camera_builds_test.exe'
    if ($LASTEXITCODE -ne 0) { throw 'Camera build profile test build failed' }
    & .\camera_builds_test.exe
    if ($LASTEXITCODE -ne 0) { throw 'Steam camera profile test failed' }
    & .\camera_builds_test.exe epic
    if ($LASTEXITCODE -ne 0) { throw 'Epic camera profile test failed' }
    & cl.exe @common (Join-Path $sourceRoot 'test_offset_blend.cpp') '/Fe:offset_blend_test.exe'
    if ($LASTEXITCODE -ne 0) { throw 'Camera offset transition test build failed' }
    & .\offset_blend_test.exe
    if ($LASTEXITCODE -ne 0) { throw 'Camera offset transition test failed' }
    & cl.exe @common (Join-Path $sourceRoot 'test_framing_progress.cpp') '/Fe:framing_progress_test.exe'
    if ($LASTEXITCODE -ne 0) { throw 'Native progress test build failed' }
    & .\framing_progress_test.exe
    if ($LASTEXITCODE -ne 0) { throw 'Native progress cache test failed' }
    & .\framing_progress_test.exe 'refused'
    if ($LASTEXITCODE -ne 0) { throw 'Native progress refusal test failed' }
    & cl.exe @common (Join-Path $sourceRoot 'test_view_performance.cpp') (Join-Path $sourceRoot 'view_performance_bridge.cpp') '/Fe:view_performance_test.exe'
    if ($LASTEXITCODE -ne 0) { throw 'Native timing test build failed' }
    & .\view_performance_test.exe
    if ($LASTEXITCODE -ne 0) { throw 'Native timing test failed' }
    & cl.exe @common (Join-Path $sourceRoot 'framing_math.cpp') (Join-Path $sourceRoot 'test_framing_math.cpp') '/Fe:framing_math_test.exe'
    if ($LASTEXITCODE -ne 0) { throw 'Native framing math test build failed' }
    & .\framing_math_test.exe
    if ($LASTEXITCODE -ne 0) { throw 'Native framing math tests failed' }
    $framingSources = @(Get-ChildItem -LiteralPath $sourceRoot -Filter 'framing_*.cpp' | ForEach-Object { $_.FullName })
    $framingDependencies = @('ads_state.cpp', 'ads_identity.cpp', 'ads_mode.cpp', 'ads_validation.cpp', 'ads_statistics.cpp', 'ads_view.cpp', 'ads_paths.cpp', 'ads_compat.cpp') | ForEach-Object { Join-Path $sourceRoot $_ }
    & cl.exe @common @framingSources @framingDependencies (Join-Path $sourceRoot 'test_framing_view.cpp') '/Fe:framing_view_test.exe' 'bcrypt.lib'
    if ($LASTEXITCODE -ne 0) { throw 'Native framing view test build failed' }
    & .\framing_view_test.exe
    if ($LASTEXITCODE -ne 0) { throw 'Native framing view tests failed' }
    foreach ($unit in @('contract', 'identity', 'paths', 'mode', 'state', 'view', 'reticle', 'detours', 'compat', 'api')) {
        $testSources = @((Join-Path $sourceRoot "test_ads_$unit.cpp"))
        if ($unit -ne 'contract') { $testSources += Join-Path $sourceRoot "ads_$unit.cpp" }
        if ($unit -in @('state', 'view', 'reticle', 'detours', 'api')) {
            foreach ($dependency in @('identity', 'mode', 'validation', 'statistics')) {
                $testSources += Join-Path $sourceRoot "ads_$dependency.cpp"
            }
        }
        if ($unit -in @('view', 'reticle', 'detours', 'api')) {
            $testSources += Join-Path $sourceRoot 'ads_state.cpp'
            $testSources += Join-Path $sourceRoot 'ads_paths.cpp'
        }
        if ($unit -eq 'detours') { $testSources += Join-Path $sourceRoot 'ads_reticle.cpp' }
        if ($unit -eq 'api') {
            foreach ($dependency in @('reticle', 'detours', 'compat')) {
                $testSources += Join-Path $sourceRoot "ads_$dependency.cpp"
            }
        }
        $testExe = "ads_$unit`_test.exe"
        & cl.exe @common @testSources "/Fe:$testExe" 'bcrypt.lib'
        if ($LASTEXITCODE -ne 0) { throw 'Native ADS test build failed' }
        $testArguments = @()
        if ($unit -eq 'compat') {
            $testArguments += (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $buildRoot $testExe)).Hash.ToLowerInvariant()
        }
        & (Join-Path $buildRoot $testExe) @testArguments
        if ($LASTEXITCODE -ne 0) { throw 'Native ADS test failed' }
    }
    $adsSources = @(Get-ChildItem -LiteralPath $sourceRoot -Filter 'ads_*.cpp' | ForEach-Object { $_.FullName })
    & cl.exe @common '/LD' @adsSources '/Fe:ads_guard_test.dll' 'bcrypt.lib'
    if ($LASTEXITCODE -ne 0) { throw 'Native ADS library build failed' }
    # A saved script avoids the legacy Windows PowerShell argument quoting of Python -c.
    & python (Join-Path $sourceRoot 'check_outside_game.py') (Join-Path $buildRoot 'ads_guard_test.dll')
    if ($LASTEXITCODE -ne 0) { throw 'Native ADS outside-game load failed' }
    & cl.exe @common @sources @adsSources @framingSources @anchorSources (Join-Path $sourceRoot 'test_view_target_bridge.cpp') '/Fe:view_target_test.exe' 'bcrypt.lib'
    if ($LASTEXITCODE -ne 0) { throw 'Native test build failed' }
    & .\view_target_test.exe
    if ($LASTEXITCODE -ne 0) { throw 'Native bridge test failed' }
    & cl.exe @common @sources @adsSources @framingSources @anchorSources (Join-Path $sourceRoot 'test_framing_dispatch.cpp') '/Fe:framing_dispatch_test.exe' 'bcrypt.lib'
    if ($LASTEXITCODE -ne 0) { throw 'Native framing dispatch test build failed' }
    & .\framing_dispatch_test.exe
    if ($LASTEXITCODE -ne 0) { throw 'Native framing dispatch tests failed' }
    & cl.exe @common @sources @adsSources @framingSources @anchorSources (Join-Path $sourceRoot 'test_view_transitions.cpp') '/Fe:view_transitions_test.exe' 'bcrypt.lib'
    if ($LASTEXITCODE -ne 0) { throw 'Native transitions test build failed' }
    & .\view_transitions_test.exe
    if ($LASTEXITCODE -ne 0) { throw 'Native transitions test failed' }
    if ($TestsOnly) { return }
    & cl.exe @common '/LD' @sources @adsSources @framingSources @anchorSources "/Fe:$libraryStem.dll" 'bcrypt.lib'
    if ($LASTEXITCODE -ne 0) { throw 'Native library build failed' }
    $assets = Join-Path (Split-Path $sourceRoot) 'apex_camera_runtime\assets'
    New-Item -ItemType Directory -Force -Path $assets | Out-Null
    $target = Join-Path $assets "$libraryStem.dll"
    Copy-Item -LiteralPath (Join-Path $buildRoot "$libraryStem.dll") -Destination $target -Force
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $target).Hash.ToLowerInvariant()
    Set-Content -LiteralPath (Join-Path $assets "$libraryStem.sha256") -Value $hash -Encoding ascii -NoNewline
    Get-FileHash -Algorithm SHA256 -LiteralPath $target
} finally {
    Pop-Location
}
