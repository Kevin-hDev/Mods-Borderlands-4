$ErrorActionPreference = 'Stop'
$sourceRoot = $PSScriptRoot
$buildRoot = Join-Path $env:TEMP 'apex_camera_interaction_build'
New-Item -ItemType Directory -Force -Path $buildRoot | Out-Null
$vcvars = 'C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat'
$environmentLines = & $env:ComSpec /d /c "`"$vcvars`" >nul && set"
if ($LASTEXITCODE -ne 0) { throw 'Compiler environment unavailable' }
foreach ($line in $environmentLines) {
    if ($line -match '^([^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
    }
}
$common = @('/nologo', '/std:c++17', '/EHsc', '/W4', '/WX', '/O2', '/MT', '/Brepro', '/DNOMINMAX')
$sources = @((Join-Path $sourceRoot 'interaction_alignment.cpp'),
             (Join-Path $sourceRoot 'interaction_bridge.cpp'))
Push-Location $buildRoot
try {
    foreach ($test in @('test_interaction_alignment', 'test_interaction_bridge')) {
        & cl.exe @common @sources (Join-Path $sourceRoot "$test.cpp") "/Fe:$test.exe"
        if ($LASTEXITCODE -ne 0) { throw 'Native test build failed' }
        & (Join-Path $buildRoot "$test.exe")
        if ($LASTEXITCODE -ne 0) { throw 'Native interaction test failed' }
    }
    & cl.exe @common '/LD' @sources '/Fe:apex_camera_interaction_v1.dll'
    if ($LASTEXITCODE -ne 0) { throw 'Native library build failed' }
    $assets = Join-Path (Split-Path $sourceRoot) 'apex_camera_runtime\assets'
    $target = Join-Path $assets 'apex_camera_interaction_v1.dll'
    Copy-Item -LiteralPath (Join-Path $buildRoot 'apex_camera_interaction_v1.dll') -Destination $target -Force
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $target).Hash.ToLowerInvariant()
    Set-Content -LiteralPath (Join-Path $assets 'apex_camera_interaction_v1.sha256') -Value $hash -Encoding ascii -NoNewline
    Write-Output "RESULTAT: OK - native interaction built: $hash"
} finally {
    Pop-Location
}
