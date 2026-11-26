# mcmusic for iOS

A **native SwiftUI client** for the mcmusic server. There is no WebView, no
HTML, no embedded website and no JavaScript bridge: every screen is drawn with
SwiftUI and all data comes from the same `/api` endpoints the web, Android and
desktop clients use.

## What this build is

GitHub Actions builds an **unsigned iOS Simulator app** (`McMusic.app`) on a
macOS runner. That is deliberate: signing an app for a physical iPhone or
TestFlight needs an Apple Developer certificate and provisioning profile, and
none of those live in this repository.

The simulator app can be:

* installed into Xcode's iOS Simulator with `xcrun simctl install booted McMusic.app`;
* launched and exercised there;
* inspected with `plutil`, `codesign`, `class-dump`-style tooling and unit tests.

It cannot be installed on a physical iPhone or uploaded to the App Store. Once
signing credentials are supplied as GitHub Secrets, the same Xcode project can
produce an ad-hoc or App Store IPA.

## Layout

```
app/ios/
  project.yml             # XcodeGen spec; the .xcodeproj is generated in CI
  McMusic/                # SwiftUI application sources
  McMusicTests/           # XCTest unit tests for parsing/URL logic
```

## Build locally (requires macOS + Xcode)

```bash
brew install xcodegen
mkdir -p app/ios/McMusic/Assets.xcassets/AppIcon.appiconset
sips -z 1024 1024 web/icon-512.png \
  --out app/ios/McMusic/Assets.xcassets/AppIcon.appiconset/icon-1024.png
xcodegen generate --spec app/ios/project.yml --project app/ios
xcodebuild -project app/ios/McMusic.xcodeproj -scheme McMusic \
  -configuration Release -sdk iphonesimulator \
  -destination 'generic/platform=iOS Simulator' \
  CODE_SIGNING_ALLOWED=NO ARCHS='arm64 x86_64' ONLY_ACTIVE_ARCH=NO build
```

The GitHub Actions `CI` and `Release builds` workflows run exactly these steps,
plus unit tests on an available iPhone simulator and a check that the resulting
bundle contains no web engine or HTML assets.

## Connecting to a server

Set the server URL on the sign-in screen (for example
`https://mcmusic.example.com`). Plain `http://` is allowed for self-hosted LAN
servers; the Xcode project sets `NSAllowsLocalNetworking` so a local server works
without a certificate while public traffic still requires HTTPS. Builds are
checked against `/api/builds` on the Builds screen; iOS cannot swap the running
app from a downloaded file, so the updater opens the public download page. The
session cookie is stored by `HTTPCookieStorage` and
survives app restarts.

Audio uses `AVPlayer` with the same stream URLs and session cookie as the
other native clients, registers background audio, and publishes playback and
device state to the server.
