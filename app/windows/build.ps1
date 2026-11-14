# Build the Windows build from the shared Qt client in app\linux.
#
#   .\build.ps1                 -> dist\mcmusic\mcmusic.exe
#   .\build.ps1 -Zip            -> also dist\mcmusic-windows-x64.zip
#   .\build.ps1 -Version 1.2    -> override the bundle version
#
# Everything is written under app\windows\{.venv-windows,build,dist}, none of
# which is committed.
[CmdletBinding()]
param(
    [string]$Python = "python",
    [string]$Version = "1.1",
    [switch]$Zip
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)

$Root = (Resolve-Path (Join-Path $PWD "..\..")).Path
$Linux = Join-Path $Root "app\linux"

if (-not (Test-Path $Linux)) { throw "missing shared client: $Linux" }

Write-Host "==> Python environment (.venv-windows)"
if (-not (Test-Path ".venv-windows")) {
    & $Python -m venv .venv-windows
}
$VenvPython = Join-Path $PWD ".venv-windows\Scripts\python.exe"
& $VenvPython -m pip install --upgrade pip wheel | Out-Null
& $VenvPython -m pip install -e $Linux pyinstaller pillow | Out-Null

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
    "launcher.py"

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

Write-Host ""
Write-Host "Done: dist\mcmusic\mcmusic.exe"
Write-Host "Unsigned builds may trip SmartScreen; use 'More info -> Run anyway'."
