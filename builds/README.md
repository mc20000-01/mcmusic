# builds

The newest client artifacts, collected by `scripts/collect_builds.sh` (also run
by `scripts/publish_apps.sh` and by `.github/workflows/release.yml`).

| File | What it is |
| --- | --- |
| `mcmusic-<version>.apk` | Android client (release build), signed with `keystore/mcmusic.p12`, installs over the previous copy |
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

The Android client now lives under `gui/android/` (backend and clients are
separate trees) and is not built by CI, which has neither the signing key nor a
Gradle wrapper for it. Publish one by hand:

```bash
JAVA_HOME=$PWD/.toolchain/jdk ANDROID_HOME=$PWD/.toolchain/sdk \
  .toolchain/gradle/bin/gradle -p gui/android :app:assembleRelease
cp gui/android/app/build/outputs/apk/release/app-release.apk \
  builds/mcmusic-$(grep -oP 'versionName\s*=\s*"\K[^"]+' gui/android/app/build.gradle.kts).apk
(cd builds && sha256sum $(find . -maxdepth 1 -type f ! -name SHA256SUMS ! -name README.md -printf '%P\n' | sort) > SHA256SUMS)
```

`collect_builds.sh` only touches APKs when `app/android/` exists, so the
committed copy survives the desktop-only release workflow.
