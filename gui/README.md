# GUI

Front-end clients live here. Nothing in this folder may contain server logic:
the backend is `src/` and the only contract between them is the HTTP API that
`src/routes/` exposes.

```
gui/android/    the native Android client (Kotlin + Compose + Media3)
src/            backend: Flask app, routes, library, presence bridges
web/            the web client served by the same server
keystore/       the signing key every Android build must use
.toolchain/     local JDK, Gradle and Android SDK (git-ignored)
```

`gui/android/` is a full client: five tabs, server playlists, admin tools,
offline downloads, a Media3 player, and two home-screen widgets. Its visual
language lives in `ui/design/Design.kt`; screens share the components in
`ui/Components.kt` and the Lucide vector icons in `ui/Lucide.kt`.

```bash
JAVA_HOME=$PWD/.toolchain/jdk ANDROID_HOME=$PWD/.toolchain/sdk \
  PATH=$PWD/.toolchain/jdk/bin:$PATH \
  .toolchain/gradle/bin/gradle -p gui/android :app:assembleRelease
```

The signed APK lands in `gui/android/app/build/outputs/apk/release/`. Run
`./scripts/publish_apps.sh` from the repo root to copy it into `apps/android/`
(what `/get` and `/api/builds` serve) and snapshot it into `builds/`.

Playback is a real Media3 session (`playback/`): the service owns an ExoPlayer,
the app holds a controller, and every stream request reads the current auth
token. It keeps playing in the background from a media notification that opens
the app when tapped. The queue, shuffle, repeat and scrubbing run locally, while
track starts, heartbeats and playback snapshots are pushed to the server so
Faves, Devices, rooms and bots see the phone's real state. The sleep timer is
persisted and checked from the background loop, so it still pauses playback
after leaving the player screen. Tapping a track in Library replaces the queue;
the arrow on a row stores an offline copy (Downloads), which the player prefers
over the network.

Home screen widgets (`widget/`) are the web embeds ported to RemoteViews: a
now-playing card and a compact bar, both fed by `/api/public/now/<user>` and
painted from the shared flufi palette. Each widget can follow a different
account, and tapping its controls opens the app.
