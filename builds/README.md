# builds

`builds/` is an **ignored, local staging directory** for release artifacts. CI
builds the current clients here, uploads them to the GitHub `latest` release,
and then leaves them on disk. The repository tracks only the small text files
in this directory:

| File | What it is |
| --- | --- |
| `release-manifest.json` | Current release version, asset names, sizes and SHA-256 digests |
| `SHA256SUMS` | SHA-256 lines for the current binary assets, generated from GitHub's asset digests |
| `README.md` | This file |

The binaries themselves are **not in git**. They live on GitHub Releases and
are cached in the server's ignored `apps/` directory:

| Artifact | Kind |
| --- | --- |
| `mcmusic-<version>.apk` | Signed Android client |
| `mcmusic-desktop_<version>_all.deb` | Debian/Ubuntu desktop client |
| `mcmusic-x86_64.AppImage` | Portable Linux desktop client |
| `mcmusic-linux-source.zip` | Desktop sources, ready to run |
| `mcmusic-macos-<version>.app.zip` / `mcmusic-<version>.dmg` | macOS client |
| `mcmusic-windows-<version>.zip` | Windows client |
| `mcmusic-ios-simulator-<version>.app.zip` | iOS Simulator build |

`https://<server>/get` redirects to the newest signed Android build, and
`/downloads` lists the builds that are currently available. Both read the
server's `apps/` cache first; when it is empty, `src/github_builds.py` pulls
the exact bytes from the public `latest` GitHub Release and verifies them
against GitHub's SHA-256 digest. If the server cannot write or reach GitHub,
`/apps/...` redirects straight to the release asset.

Older version releases, including backfilled historical snapshots, are for
rollback only. They are deliberately **not** the GitHub `latest` release and
are never read by `/api/builds`, `/get` or the server's build cache.

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
./scripts/publish-release.sh
```

`publish_apps.sh` refuses a stale or differently signed APK, copies it to the
stable `apps/android/` names used by `/get` and `/api/builds`, then calls
`collect_builds.sh` to refresh the local staging folder. Run
`./scripts/write_release_manifest.py` after publishing to refresh the two
tracked text files from the public release.
