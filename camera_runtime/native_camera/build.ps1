param([switch]$TestsOnly)
$ErrorActionPreference = 'Stop'
$sourceRoot = $PSScriptRoot
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
$sources = @((Join-Path $sourceRoot 'view_target_math.cpp'),
             (Join-Path $sourceRoot 'view_target_bridge.cpp'))
Push-Location $buildRoot
try {
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
        & (Join-Path $buildRoot $testExe)
        if ($LASTEXITCODE -ne 0) { throw 'Native ADS test failed' }
    }
    $adsSources = @(Get-ChildItem -LiteralPath $sourceRoot -Filter 'ads_*.cpp' | ForEach-Object { $_.FullName })
    & cl.exe @common '/LD' @adsSources '/Fe:ads_guard_test.dll' 'bcrypt.lib'
    if ($LASTEXITCODE -ne 0) { throw 'Native ADS library build failed' }
    & python -c 'import ctypes,sys; lib=ctypes.CDLL(sys.argv[1]); assert lib.ads_prepare() != 0; print("RESULTAT: OK (DLL loaded outside game; preparation refused)")' (Join-Path $buildRoot 'ads_guard_test.dll')
    if ($LASTEXITCODE -ne 0) { throw 'Native ADS outside-game load failed' }
    & cl.exe @common @sources @adsSources (Join-Path $sourceRoot 'test_view_target_bridge.cpp') '/Fe:view_target_test.exe' 'bcrypt.lib'
    if ($LASTEXITCODE -ne 0) { throw 'Native test build failed' }
    & .\view_target_test.exe
    if ($LASTEXITCODE -ne 0) { throw 'Native bridge test failed' }
    if ($TestsOnly) { return }
    & cl.exe @common '/LD' @sources @adsSources '/Fe:apex_camera_view_v6.dll' 'bcrypt.lib'
    if ($LASTEXITCODE -ne 0) { throw 'Native library build failed' }
    $assets = Join-Path (Split-Path $sourceRoot) 'apex_camera_runtime\assets'
    New-Item -ItemType Directory -Force -Path $assets | Out-Null
    $target = Join-Path $assets 'apex_camera_view_v6.dll'
    Copy-Item -LiteralPath (Join-Path $buildRoot 'apex_camera_view_v6.dll') -Destination $target -Force
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $target).Hash.ToLowerInvariant()
    Set-Content -LiteralPath (Join-Path $assets 'apex_camera_view_v6.sha256') -Value $hash -Encoding ascii -NoNewline
    Get-FileHash -Algorithm SHA256 -LiteralPath $target
} finally {
    Pop-Location
}
