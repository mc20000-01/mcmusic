# builds

The newest client artifacts, collected by `scripts/collect_builds.sh` (also run
by `scripts/publish_apps.sh` and by `.github/workflows/release.yml`).

| File | What it is |
| --- | --- |
| `mcmusic-<version>.apk` | Android client (release build), signed with `keystore/mcmusic.p12`, installs over the previous copy |
| `mcmusic-desktop_<version>_all.deb` | Debian/Ubuntu desktop client |
| `mcmusic-x86_64.AppImage` | Portable Linux desktop client (when present) |
| `mcmusic-linux-source.zip` | Desktop client sources, ready to run |
| `SHA256SUMS` | Checksums for the current files above only; the immutable release must not describe files it does not carry |

The current files are attached to the rolling **latest** GitHub Release on
every push to `main`, and `https://<server>/get` redirects to the newest Android
build. When the desktop `FALLBACK_VERSION` changes, that run also creates an
immutable `v<version>` release with the same versioned artifacts. Version
releases are never overwritten and are deliberately not marked GitHub Latest;
`latest` is the only release the server's build fallback reads. Older versioned
APKs may remain here for rollback, but neither release advertises them.

## Android signing

The APK stays installable over the previous copy only when it is signed with
the same key. CI builds the signed APK from source with the committed
`keystore/mcmusic.p12`, then verifies both the embedded version and the signer
certificate before publishing it. A missing keystore fails the build instead of
producing an unsigned APK.

```bash
export JAVA_HOME="$PWD/.toolchain/jdk"
export ANDROID_HOME="$PWD/.toolchain/sdk"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export PATH="$JAVA_HOME/bin:$PATH"
./scripts/build_deb.sh
(cd gui/android && ./gradlew :app:assembleRelease --no-daemon)
./scripts/publish_apps.sh
```

`publish_apps.sh` refuses a stale or differently signed APK, copies it to the
stable `apps/android/` names used by `/get` and `/api/builds`, then calls
`collect_builds.sh` to refresh `builds/` and `SHA256SUMS`. Do not copy an APK
straight into `builds/`; `apps/` is where the server reads from.
