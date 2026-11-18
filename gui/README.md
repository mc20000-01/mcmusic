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
