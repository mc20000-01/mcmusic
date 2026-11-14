# mcmusic for Windows

The Windows app is the **same native Qt client** as `app/linux` and the macOS
build, packaged with PyInstaller. Only the platform glue differs:

- MPRIS (Linux) is replaced by a no-op; Windows media-key integration via SMTC
  is a follow-up.
- Audio goes through QtMultimedia's WASAPI backend.
- Settings and the audio cache live under `%APPDATA%\mcmusic` and
  `%LOCALAPPDATA%\mcmusic`.

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
```

The script creates `.venv-windows`, installs `app\linux` in editable mode plus
PyInstaller and Pillow (to turn `web\icon-512.png` into a multi-size `.ico`),
then bundles the shared package with `--collect-data`.

Useful switches:

```powershell
.\build.ps1 -Python python3.12
.\build.ps1 -Version 1.2 -Zip
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

The build is unsigned. SmartScreen may warn on first run; choose **More info →
Run anyway**, or sign `mcmusic.exe` with `signtool` using your certificate.
`build.ps1` leaves signing out on purpose because it needs credentials.
