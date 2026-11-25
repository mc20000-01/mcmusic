# mcmusic for Windows

The Windows app is the **same native Qt client** as `app/linux` and the macOS
build, packaged with PyInstaller. Only the platform glue differs:

- MPRIS (Linux) is replaced by System Media Transport Controls (SMTC), supplied
  by the optional `windows-media` extra. Metadata and media keys work in the
  Windows volume panel, lock screen and keyboard controls.
- Audio goes through QtMultimedia's WASAPI backend.
- Settings and the audio cache live under `%APPDATA%\mcmusic` and
  `%LOCALAPPDATA%\mcmusic`.

New to mcmusic? The [self-hosting guide](../../docs/selfhost.md) covers server
setup, HTTPS and connecting this desktop client.

```
app/windows/
  launcher.py   # frozen-app entry point (imports mcmusic_linux.cli)
  build.ps1     # venv → PyInstaller → dist\mcmusic\mcmusic.exe
```

## Build

On Windows 10/11 with Python 3.10+:

```powershell
cd app\windows
powershell -ExecutionPolicy Bypass -File build.ps1
```

Output:

```
dist\mcmusic\mcmusic.exe        # portable folder
dist\mcmusic-windows-x64.zip    # zip the folder for sharing
apps\windows\mainbuild.zip      # published for /api/builds unless -NoPublish
```

The script creates `.venv-windows`, installs `app\linux` in editable mode plus
PyInstaller and Pillow (to turn `web\icon-512.png` into a multi-size `.ico`),
then bundles the shared package. The PyInstaller step is explicit about the
shared client so an editable install cannot leave `mcmusic_linux.cli` out of
the frozen app:

```powershell
python -m PyInstaller --noconfirm --clean --windowed `
  --name mcmusic --icon build\mcmusic.ico `
  --paths ..\linux `
  --hidden-import mcmusic_linux.cli `
  --collect-submodules mcmusic_linux --collect-data mcmusic_linux `
  --hidden-import winsdk.windows.media launcher.py
```

Settings live in `%APPDATA%\mcmusic\mcmusic-desktop.ini` and cached audio in
`%LOCALAPPDATA%\mcmusic\audio`. MPRIS is not imported on Windows; SMTC is
provided by the same `MediaBridge` the macOS build uses.

Useful switches:

```powershell
.\build.ps1 -Python python3.12
.\build.ps1 -Version 1.2 -Zip
.\build.ps1 -NoPublish               # build only, skip apps\windows
```

## Running from a checkout

```powershell
cd app\linux
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python mcmusic-desktop
```

## Signing

Local builds are unsigned, so SmartScreen may warn on first run; choose
**More info → Run anyway**. On a release machine, set `WINDOWS_CERT` and
`WINDOWS_CERT_PASSWORD` (and optionally `SIGNTOOL`) to Authenticode-sign
`mcmusic.exe`, then verify SMTC metadata and keyboard media controls in the
packaged build before publishing `apps\windows`.
