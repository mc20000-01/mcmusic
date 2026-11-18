# builds

The newest client artifacts, collected by `scripts/collect_builds.sh` (also run
by `scripts/publish_apps.sh` and by `.github/workflows/release.yml`).

| File | What it is |
| --- | --- |
| `mcmusic-<version>.apk` | Android client, debug-signed, installs over the previous copy |
| `mcmusic-desktop_<version>_all.deb` | Debian/Ubuntu desktop client |
| `mcmusic-x86_64.AppImage` | Portable Linux desktop client (when present) |
| `mcmusic-linux-source.zip` | Desktop client sources, ready to run |
| `SHA256SUMS` | Checksums for every file above |

The same files are attached to the rolling **latest** GitHub Release on every
push to `main`, and `https://<server>/get` redirects to the newest Android
build. Only one version of each artifact is kept here; older files live in the
repository history and in previous release uploads.

## Android signing

The APK stays installable over the previous copy only when it is signed with
the same key. CI therefore releases the committed APK unless the original
`~/.android/debug.keystore` is supplied as the repository secret
`ANDROID_KEYSTORE_BASE64` (base64 of that file). With the secret set, CI builds
and ships a fresh APK signed with the same key; without it, CI still compiles
the source for verification but the committed APK is what ships.

Build them locally:

```bash
./scripts/build_deb.sh
./scripts/publish_apps.sh   # collects apps/ and builds/
```

The Android client is being rebuilt from scratch under `gui/`; until it is
back, `publish_apps.sh` leaves `apps/android/` alone and only the desktop
builds are refreshed.
