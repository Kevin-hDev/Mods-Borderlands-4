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
    & cl.exe @common @sources (Join-Path $sourceRoot 'test_view_target_bridge.cpp') '/Fe:view_target_test.exe'
    if ($LASTEXITCODE -ne 0) { throw 'Native test build failed' }
    & .\view_target_test.exe
    if ($LASTEXITCODE -ne 0) { throw 'Native bridge test failed' }
    & cl.exe @common '/LD' @sources '/Fe:apex_camera_view_v4.dll'
    if ($LASTEXITCODE -ne 0) { throw 'Native library build failed' }
    $assets = Join-Path (Split-Path $sourceRoot) 'apex_camera_runtime\assets'
    New-Item -ItemType Directory -Force -Path $assets | Out-Null
    $target = Join-Path $assets 'apex_camera_view_v4.dll'
    Copy-Item -LiteralPath (Join-Path $buildRoot 'apex_camera_view_v4.dll') -Destination $target -Force
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $target).Hash.ToLowerInvariant()
    Set-Content -LiteralPath (Join-Path $assets 'apex_camera_view_v4.sha256') -Value $hash -Encoding ascii -NoNewline
    Get-FileHash -Algorithm SHA256 -LiteralPath $target
} finally {
    Pop-Location
}
