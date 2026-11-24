# Build the Windows build from the shared Qt client in app\linux.
#
#   .\build.ps1                 -> dist\mcmusic\mcmusic.exe
#   .\build.ps1 -Zip            -> also dist\mcmusic-windows-x64.zip
#   .\build.ps1 -Version 1.2    -> override the bundle version
#
# Everything is written under app\windows\{.venv-windows,build,dist}, none of
# which is committed. Release checklist: set WINDOWS_CERT and
# WINDOWS_CERT_PASSWORD to Authenticode-sign the exe, publish the zip to
# apps\windows, and verify SMTC metadata/media keys in the packaged build.
[CmdletBinding()]
param(
    [string]$Python = "python",
    [string]$Version = "",
    [switch]$Zip,
    [switch]$NoPublish
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)

$Root = (Resolve-Path (Join-Path $PWD "..\..")).Path
$Linux = Join-Path $Root "app\linux"

if (-not (Test-Path $Linux)) { throw "missing shared client: $Linux" }

# The shared client version.py is the single source of truth for every bundle.
if (-not $Version) {
    $Shared = Join-Path $Linux "mcmusic_linux\version.py"
    $Match = Select-String -Path $Shared -Pattern '^FALLBACK_VERSION\s*=\s*"([^"]+)"' |
        Select-Object -First 1
    if (-not $Match) { throw "could not read the version from $Shared" }
    $Version = $Match.Matches[0].Groups[1].Value
}

Write-Host "==> Python environment (.venv-windows)"
if (-not (Test-Path ".venv-windows")) {
    & $Python -m venv .venv-windows
}
$VenvPython = Join-Path $PWD ".venv-windows\Scripts\python.exe"
& $VenvPython -m pip install --upgrade pip wheel | Out-Null
if ($LASTEXITCODE -ne 0) { throw "could not upgrade pip/wheel" }
& $VenvPython -m pip install -e "$Linux[windows-media]" pyinstaller pillow | Out-Null
if ($LASTEXITCODE -ne 0) { throw "could not install Windows build dependencies" }

Write-Host "==> Icon"
New-Item -ItemType Directory -Force -Path "build" | Out-Null
& $VenvPython -c @"
from PIL import Image
im = Image.open(r'$Root\web\icon-512.png').convert('RGBA')
im.save(r'$PWD\build\mcmusic.ico', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
"@

Write-Host "==> PyInstaller"
Remove-Item -Recurse -Force "build\mcmusic", "dist\mcmusic" -ErrorAction SilentlyContinue
& $VenvPython -m PyInstaller `
    --noconfirm --clean --windowed `
    --name mcmusic `
    --icon "build\mcmusic.ico" `
    --collect-data mcmusic_linux `
    --hidden-import winsdk.windows.media `
    "launcher.py"

# Authenticode is optional: release machines with a certificate can wire it in
# without forcing local development builds to install the Windows SDK.
if ($env:WINDOWS_CERT -and $env:WINDOWS_CERT_PASSWORD) {
    $SignTool = if ($env:SIGNTOOL) { $env:SIGNTOOL } else { "signtool" }
    Write-Host "==> Signing mcmusic.exe"
    & $SignTool sign /f $env:WINDOWS_CERT /p $env:WINDOWS_CERT_PASSWORD `
        /tr "http://timestamp.digicert.com" /fd sha256 `
        "dist\mcmusic\mcmusic.exe"
}

# Version metadata lives beside the exe so Finder/Explorer and the app agree.
& $VenvPython -c @"
import json, pathlib
pathlib.Path(r'$PWD\dist\mcmusic\version.json').write_text(
    json.dumps({'name': 'mcmusic', 'version': '$Version'}, indent=2)
)
"@

if ($Zip) {
    Write-Host "==> Zip"
    $out = "dist\mcmusic-windows-x64.zip"
    Remove-Item -Force $out -ErrorAction SilentlyContinue
    Compress-Archive -Path "dist\mcmusic\*" -DestinationPath $out
    Write-Host "wrote $out"
}

if (-not $NoPublish) {
    Write-Host "==> Publishing to apps/windows (-NoPublish to skip)"
    $Target = Join-Path $Root "apps\windows"
    New-Item -ItemType Directory -Force -Path $Target | Out-Null
    if (-not $Zip) {
        $out = "dist\mcmusic-windows-x64.zip"
        Compress-Archive -Force -Path "dist\mcmusic\*" -DestinationPath $out
    }
    Copy-Item -Force "dist\mcmusic-windows-x64.zip" `
        (Join-Path $Target "mcmusic-$Version-windows-x64.zip")
    Copy-Item -Force "dist\mcmusic-windows-x64.zip" `
        (Join-Path $Target "mainbuild.zip")
}

Write-Host ""
Write-Host "Done: dist\mcmusic\mcmusic.exe"
Write-Host "Unsigned builds may trip SmartScreen; use 'More info -> Run anyway'."
