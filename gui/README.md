# GUI

Front-end clients live here. Nothing in this folder may contain server logic:
the backend is `src/` and the only contract between them is the HTTP API that
`src/routes/` exposes.

```
gui/            clients (the new Android app will be gui/android/)
src/            backend: Flask app, routes, library, presence bridges
web/            the existing web client, untouched while the new GUI is built
keystore/       the signing key every Android build must use
.toolchain/     local JDK, Gradle and Android SDK (git-ignored)
```

The previous Android client (`app/android/`, Kotlin + Compose + Media3) was
removed in full, including its build files, resources and release wiring. Its
history is still in git if anything needs to be recovered from it.

`gui/android/` is the new client. It currently holds only scaffolding — one
screen over a colourful stage so the glass is visible — while the real GUI is
specified. Glass lives entirely in `ui/Glass.kt` (`Modifier.liquidGlass`), built
on [Backdrop](https://github.com/Kyant0/AndroidLiquidGlass) 1.0.6, so the
renderer can be replaced without touching a screen.

```bash
JAVA_HOME=$PWD/.toolchain/jdk ANDROID_HOME=$PWD/.toolchain/sdk \
  PATH=$PWD/.toolchain/jdk/bin:$PATH \
  .toolchain/gradle/bin/gradle -p gui/android :app:assembleDebug
```

The APK lands in `gui/android/app/build/outputs/apk/debug/` and is signed with
`keystore/mcmusic.p12`, so it installs over the 2.7.0 copy.

Home screen widgets (`widget/`) are the web embeds ported to RemoteViews: a
now-playing card and a compact bar, both fed by `/api/public/now/<user>` and
painted from the same seven palettes. They refresh every 30 minutes, when the
app is opened and whenever the palette or design language changes. RemoteViews
cannot render Backdrop glass, so the surface is a palette gradient — the iOS or
One UI corner radius depending on the selected language.
