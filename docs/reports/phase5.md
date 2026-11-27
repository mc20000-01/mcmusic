# mcmusic 4.2.0 — Phase 5 report

Branch: `design-4.2.0`. Parent commit: `db5e86c` (Phase 4). This phase aligns every live version carrier at 4.2.0 and prepares the release inputs; it does not publish a release or merge to `main`.

> Historical note: the committed `.deb` described below was required by the
> old version gate. Release binaries are no longer tracked; CI builds a real
> `.deb` immediately before `check-versions.sh`, and the tracked text manifest
> covers clean local checkouts.

## What changed

- Desktop source of truth `app/linux/mcmusic_linux/version.py` now reports 4.2.0. The Qt `USER_AGENT` and TUI User-Agent are derived from that constant, so they move with it.
- Android `versionName` is 4.2.0 and `versionCode` advances from 54 to 55, keeping installs over the previous signed APK valid.
- iOS `MARKETING_VERSION` is 4.2.0 and `CURRENT_PROJECT_VERSION` advances from 54 to 55. The hardcoded iOS API User-Agent was also bumped from `mcmusic-ios/4.1.0` to `mcmusic-ios/4.2.0`, so the previously drifted carrier is aligned too.
- Web `ui/package.json` is 4.2.0. `ui/package-lock.json` was regenerated with npm rather than hand-edited; only its two root version fields changed.
- Server shell cache version advances from 11 to 12 in `src/config.py`. The 4.2.0 redesign changes the offline shell contract while audio and artwork caches stay separate. `src/mcmusic.py` needs no edit: `BUILD` is derived from `SHELL_VERSION` plus the shipped web files at startup, so `/api/version` now reports shell 12 and a fresh build fingerprint without inventing a new API field.
- Built a real 4.2.0 Debian package from the Phase 4 Qt source and committed `builds/mcmusic-desktop_4.2.0_all.deb`. This is required by the existing `scripts/check-versions.sh` gate: the checker must verify a real matching `.deb`, and bypassing it would weaken release verification. The release workflow still rebuilds and recollects every current artifact and checksum on `main`.
- No design token, generated icon, UI shell, motion, palette, server API or feature-truth behavior changed in this phase. The 4.2.0 web bundle rebuilds byte-for-byte from the Phase 1 sources; only npm's reported package version changed.

## What was run

- `npm --prefix ui install --package-lock-only --ignore-scripts --no-audit --no-fund` — pass; diff is limited to the two root `4.1.0` → `4.2.0` version fields.
- `./scripts/build_ui.sh` — pass; TypeScript check and Vite build succeeded, all three local variable fonts were emitted, and both font-CDN imports were stripped. No tracked `web/ui/` output changed.
- `node scripts/gen-tokens.mjs --check && node scripts/gen-lucide.mjs --check` — pass.
- `.venv/bin/python -m pytest tests/test_no_gradients.py tests/test_contrast.py tests/test_generated_fresh.py -q` — 3 passed.
- `.venv/bin/python -m pytest tests -q` with CI's Qt/widget/update exclusions — 95 passed, 1 skipped, 2 subtests passed.
- `QT_QPA_PLATFORM=offscreen MC_MUSIC_QT_AUDIO_STUB=1 .venv/bin/python -m pytest tests/test_qt_ui.py tests/test_qt_client.py tests/test_qt_icons.py tests/test_widgets.py tests/test_no_qt_shadowing.py tests/test_qt_selftest.py tests/test_updates.py -q` — 35 passed.
- Local Android toolchain: `:app:assembleDebug :app:testDebugUnitTest --offline` — BUILD SUCCESSFUL, 45 actionable tasks.
- `bash scripts/check-versions.sh` — all live carriers agree at 4.2.0, including the newly built deb.
- `bash tests/test_check_versions.sh` — 4 checks passed; `bash tests/test_publish_release.sh` — 11 checks passed. These are hermetic fixtures; no tag or release was created.
- `.venv/bin/python -m pyflakes app/linux src music_activity tools` — pass; `.venv/bin/python -m py_compile app/linux/mcmusic_linux/*.py src/config.py src/mcmusic.py` — pass.
- `node --check web/sw.js`, `bash -n scripts/*.sh tests/*.sh`, `git diff --check` — pass.
- Tool probe: `shellcheck` is not installed in this Linux workspace; CI installs it before the release-blocking shell gate. No shell script changed in this phase.
- CI is triggered by pushing this separate phase commit to `design-4.2.0`; no CI result is claimed in this pre-push report.

## What was not done and why

- No GitHub release, tag, or `main` merge: release publication changes public artifacts and the server's downloadable builds, and branch sync was not authorized. The existing `release.yml` publishes only from `main` after CI passes; no PR was created.
- No local macOS, Windows or iOS build: Xcode/Windows packaging toolchains are unavailable in this Linux workspace. Their CI jobs verify the bumped version carriers.
- No signed 4.2.0 APK collected locally: CI's Android job builds, signs, verifies the embedded version and signer certificate, and uploads the release APK. The local debug build and JVM tests passed.
- No deviceless visual verification: Phase 5 changes no UI code, and no mockups or device render targets were supplied in any phase.
- No build pruning or `SHA256SUMS` rewrite: older APKs stay available for rollback, and `scripts/collect_builds.sh` regenerates current-file checksums when a real release is assembled. The committed 4.2.0 deb is a real version-check input, not a claim that all other 4.2.0 artifacts already exist locally.
- No new network call, CDN font, tracker, analytics key, server settings key or live database change.
- No version field invented in `web/manifest.webmanifest` or a root `package.json`: both are intentionally absent and the checker already skips them without weakening the live carriers.
- No test fixture was rewritten to 4.2.0: `tests/test_check_versions.sh` and `tests/test_publish_release.sh` deliberately use fixed historical values to prove mismatch detection, not to mirror the current release.
- No generated marker block was hand-edited; no palette, icon or token source changed in this phase.

## Full authored file contents

Generated artifacts (`ui/package-lock.json` and `builds/mcmusic-desktop_4.2.0_all.deb`) are committed and reproducible but are not duplicated here. The authored files below are reproduced in full.

### `app/linux/mcmusic_linux/version.py`

```python
"""Single source of truth for the desktop client version.

The installed package metadata is canonical; the constant is the fallback for
running straight from a source checkout (and for the packaging scripts, which
read this file before the package is installed).
"""
from __future__ import annotations

FALLBACK_VERSION = "4.2.0"


def app_version() -> str:
    try:
        from importlib.metadata import PackageNotFoundError, version
        return version("mcmusic-desktop")
    except (ImportError, PackageNotFoundError, ValueError):
        return FALLBACK_VERSION


VERSION = app_version()
USER_AGENT = f"mcmusic-desktop/{VERSION} (Qt)"
```

### `gui/android/app/build.gradle.kts`

```kotlin
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace = "dev.mcmusic.app"
    compileSdk = 36

    defaultConfig {
        applicationId = "dev.mcmusic.app"
        minSdk = 34
        targetSdk = 34
        versionCode = 55
        versionName = "4.2.0"
        buildConfigField("String", "DEFAULT_SERVER", "\"https://mcmusic.sdisk.us\"")
    }

    // Same key as every previous release, so an update installs over an existing
    // copy instead of failing with "conflicts with another package".
    val projectKey = file("../../../keystore/mcmusic.p12")
    if (!projectKey.exists()) error("Missing keystore/mcmusic.p12 — refusing unsigned release")
    signingConfigs {
        create("mcmusic") {
            storeFile = projectKey
            storeType = "pkcs12"
            storePassword = "mcmusic"
            keyAlias = "mcmusic"
            keyPassword = "mcmusic"
        }
    }

    buildTypes {
        getByName("debug") {
            signingConfig = if (projectKey.exists()) signingConfigs.getByName("mcmusic") else null
        }
        release {
            // Keep rules in proguard-rules.pro cover the manifest/AppWidget
            // entry points, Media3 and Compose reflection. CI builds this
            // configuration on every release, so it is validated there.
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
            signingConfig = if (projectKey.exists()) signingConfigs.getByName("mcmusic") else null
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlin {
        compilerOptions {
            jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
        }
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    packaging {
        resources.excludes += "/META-INF/{AL2.0,LGPL2.1}"
    }
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2026.03.01")
    implementation(composeBom)

    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.activity:activity-compose:1.9.2")

    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.foundation:foundation")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui-tooling-preview")

    // HCT tonal roles for cover- and wallpaper-derived colours. Pinned to the
    // last release built with the Kotlin version used by this app.
    implementation("com.materialkolor:material-color-utilities:4.1.1")

    val media3 = "1.11.1"
    implementation("androidx.media3:media3-exoplayer:$media3")
    implementation("androidx.media3:media3-session:$media3")

    debugImplementation("androidx.compose.ui:ui-tooling")

    testImplementation("junit:junit:4.13.2")
}
```

### `app/ios/project.yml`

```yaml
# XcodeGen spec for the native iOS client.
#
# The project file itself is generated in CI, so there is no Xcode project to
# keep in sync by hand. Builds are unsigned simulator builds by design: no
# Apple Developer credentials live in this repository.
name: McMusic

options:
  bundleIdPrefix: dev.mcmusic
  deploymentTarget:
    iOS: "17.0"
  createIntermediateGroups: true
  groupSortPosition: top

configs:
  Debug: debug
  Release: release

targets:
  McMusic:
    type: application
    platform: iOS
    deploymentTarget: "17.0"
    sources:
      - path: McMusic
    resources:
      - path: McMusic/Assets.xcassets
      - path: McMusic/PrivacyInfo.xcprivacy
    info:
      path: McMusic/Info.plist
      properties:
        CFBundleDisplayName: mcmusic
        CFBundleIdentifier: dev.mcmusic.ios
        CFBundleName: McMusic
        UILaunchScreen: {}
        UIBackgroundModes:
          - audio
        # Default ATS applies everywhere; only local-network HTTP is allowed.
        NSAppTransportSecurity:
          NSAllowsLocalNetworking: true
        ITSAppUsesNonExemptEncryption: false
        UIRequiredDeviceCapabilities:
          - arm64
    settings:
      base:
        PRODUCT_NAME: McMusic
        PRODUCT_BUNDLE_IDENTIFIER: dev.mcmusic.ios
        MARKETING_VERSION: "4.2.0"
        CURRENT_PROJECT_VERSION: "55"
        SWIFT_VERSION: "5.10"
        TARGETED_DEVICE_FAMILY: "1,2"
        ENABLE_PREVIEWS: YES
        CLANG_ENABLE_MODULES: YES
        SWIFT_EMIT_LOC_STRINGS: YES
        CODE_SIGN_STYLE: Manual
        CODE_SIGN_IDENTITY: ""
        PROVISIONING_PROFILE_SPECIFIER: ""
        ENABLE_TESTABILITY: YES

  McMusicTests:
    type: bundle.unit-test
    platform: iOS
    deploymentTarget: "17.0"
    sources:
      - path: McMusicTests
    dependencies:
      - target: McMusic
    settings:
      base:
        PRODUCT_NAME: McMusicTests
        SWIFT_VERSION: "5.10"
        CODE_SIGNING_ALLOWED: NO

schemes:
  # App-only scheme: builds the shippable bundle without XCTest frameworks.
  McMusicApp:
    build:
      targets:
        McMusic: all
    run:
      target: McMusic
    profile:
      target: McMusic
    analyze:
      target: McMusic
    archive:
      target: McMusic

  McMusic:
    build:
      targets:
        McMusic: all
        McMusicTests: [test, run]
    test:
      targets:
        - McMusicTests
    run:
      target: McMusic
    profile:
      target: McMusic
    analyze:
      target: McMusic
    archive:
      target: McMusic
```

### `app/ios/McMusic/APIClient.swift`

```swift
import Foundation

enum APIError: LocalizedError {
    case invalidURL(String)
    case status(Int, String)
    case decoding

    var errorDescription: String? {
        switch self {
        case .invalidURL(let value): return "Invalid server address: \(value)"
        case .status(let code, let message): return code == 0 ? message : "\(code): \(message)"
        case .decoding: return "Could not read the server response"
        }
    }
}

/// Thin async wrapper around the same HTTP API the other native clients use.
/// Cookies are kept in `HTTPCookieStorage.shared`, so a session survives a
/// restart of the app just like it does in the Qt and Android clients.
final class APIClient {
    static let shared = APIClient()

    private let session: URLSession = {
        let config = URLSessionConfiguration.default
        config.httpCookieStorage = .shared
        config.httpCookieAcceptPolicy = .always
        config.httpShouldSetCookies = true
        config.timeoutIntervalForRequest = 30
        return URLSession(configuration: config)
    }()

    private(set) var baseURL: String
    let outbox = Outbox.shared
    private var cookieStorage: HTTPCookieStorage { .shared }

    init(baseURL: String? = nil) {
        self.baseURL = Self.normalize(baseURL ?? UserDefaults.standard.string(forKey: "server_url") ?? "http://127.0.0.1:8000")
        UserDefaults.standard.set(self.baseURL, forKey: "server_url")
    }

    static func normalize(_ raw: String) -> String {
        var value = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        if !value.hasPrefix("http://") && !value.hasPrefix("https://") {
            value = "http://" + value
        }
        return value.replacingOccurrences(of: "/+$", with: "", options: .regularExpression)
    }

    func setBaseURL(_ raw: String) {
        baseURL = Self.normalize(raw)
        UserDefaults.standard.set(baseURL, forKey: "server_url")
    }

    var isSignedIn: Bool {
        let names = ["mcmusic_session", "session"]
        return cookieStorage.cookies?.contains { names.contains($0.name) && !$0.value.isEmpty } ?? false
    }

    func clearCookies() {
        for cookie in cookieStorage.cookies ?? [] {
            cookieStorage.deleteCookie(cookie)
        }
    }

    func absoluteURL(_ path: String, query: [String: String]? = nil) throws -> URL {
        var components: URLComponents
        if path.hasPrefix("http://") || path.hasPrefix("https://") {
            guard let parsed = URLComponents(string: path) else { throw APIError.invalidURL(path) }
            components = parsed
        } else {
            let clean = path.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
            let apiPath = clean.hasPrefix("api/") ? clean : "api/" + clean
            guard let parsed = URLComponents(string: baseURL + "/" + apiPath) else {
                throw APIError.invalidURL(path)
            }
            components = parsed
        }
        if let query, !query.isEmpty {
            components.queryItems = (components.queryItems ?? []) + query.map { URLQueryItem(name: $0.key, value: $0.value) }
        }
        guard let url = components.url else { throw APIError.invalidURL(path) }
        return url
    }

    @discardableResult
    func request(
        _ method: String,
        _ path: String,
        query: [String: String]? = nil,
        json: [String: Any]? = nil,
        form: [String: String]? = nil
    ) async throws -> JSON {
        let url = try absoluteURL(path, query: query)
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.setValue("mcmusic-ios/4.2.0", forHTTPHeaderField: "User-Agent")
        if let form {
            request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
            let pairs = form.map { key, value in
                "\(Self.encode(key))=\(Self.encode(value))"
            }
            request.httpBody = pairs.joined(separator: "&").data(using: .utf8)
        } else if let json {
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try? JSONSerialization.data(withJSONObject: json)
        }

        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await session.data(for: request)
        } catch {
            // Normalise transport failures so the outbox can recognise them.
            throw APIError.status(0, error.localizedDescription)
        }
        let status = (response as? HTTPURLResponse)?.statusCode ?? 0
        let body = try? JSON(data)
        if !(200..<300).contains(status) {
            let message = body?["error"]?.string
                ?? body?["message"]?.string
                ?? String(data: data, encoding: .utf8)?.prefix(200).description
                ?? "Request failed"
            throw APIError.status(status, String(message))
        }
        return body ?? .null
    }

    func get(_ path: String, query: [String: String]? = nil) async throws -> JSON {
        try await request("GET", path, query: query)
    }

    func post(_ path: String, json: [String: Any]? = nil, form: [String: String]? = nil) async throws -> JSON {
        try await request("POST", path, json: json, form: form)
    }

    func put(_ path: String, json: [String: Any]? = nil) async throws -> JSON {
        try await request("PUT", path, json: json)
    }

    func delete(_ path: String) async throws -> JSON {
        try await request("DELETE", path)
    }

    /// Download a track through the signed-in session, then hand a local file
    /// to AVFoundation. AVPlayer does not use HTTPCookieStorage on its own.
    func download(to url: URL, from path: String) async throws {
        let remote = try absoluteURL(path)
        let (data, response) = try await session.data(from: remote)
        let status = (response as? HTTPURLResponse)?.statusCode ?? 0
        guard (200..<300).contains(status) else {
            throw APIError.status(status, "Could not load audio")
        }
        try data.write(to: url)
    }

    func artworkURL(_ value: Any?) -> URL? {
        let text: String?
        switch value {
        case let string as String: text = string
        case let json as JSON: text = json.string
        default: text = nil
        }
        guard let text, !text.isEmpty else { return nil }
        if text.hasPrefix("http://") || text.hasPrefix("https://") {
            return URL(string: text)
        }
        return try? absoluteURL(text)
    }

    private static func encode(_ value: String) -> String {
        value.addingPercentEncoding(withAllowedCharacters: .alphanumerics) ?? value
    }
}
```

### `ui/package.json`

```json
{
  "name": "mcmusic-ui",
  "private": true,
  "version": "4.2.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc --noEmit -p tsconfig.app.json && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@fontsource-variable/inter": "^5.3.0",
    "@fontsource-variable/jetbrains-mono": "^5.3.0",
    "@fontsource-variable/lexend": "^5.3.0",
    "@preact/signals": "^2.11.1",
    "flufi-ui": "^0.1.0",
    "lucide-preact": "^1.70.0",
    "preact": "^10.27.2",
    "preact-iso": "^2.12.2"
  },
  "devDependencies": {
    "@material/material-color-utilities": "^0.3.0",
    "@preact/preset-vite": "^2.10.2",
    "@types/node": "^24.10.1",
    "lucide-static": "^1.80.0",
    "typescript": "~5.9.3",
    "vite": "^7.3.1"
  }
}
```

### `src/config.py`

```python
"""mcmusic configuration — all environment-driven, with sensible defaults."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# Defaults point at the project root, not src/, so CLI tools (dedupe, scan)
# read the same database the service does even without the service env file.
PROJECT_DIR = os.path.dirname(HERE)
MUSIC_DIR = os.path.abspath(os.environ.get("MUSIC_DIR", os.path.join(PROJECT_DIR, "music")))
DATA_DIR = os.path.abspath(os.environ.get("DATA_DIR", os.path.join(PROJECT_DIR, "data")))
DL_SCRIPT = os.environ.get("DL_SCRIPT", os.path.join(HERE, "yt_playlist_to_mp3.py"))
DL_ARGS = os.environ.get("DL_ARGS", "--turbo")
STAGING_DIR = os.environ.get("STAGING_DIR", os.path.join(MUSIC_DIR, ".staging"))

INVITE_CODE = os.environ.get("INVITE_CODE", "")
AUTO_APPROVE = os.environ.get("AUTO_APPROVE", "1") == "1"
YT_ENRICH = os.environ.get("YT_ENRICH", "1") == "1"
# Fold duplicates after every library scan, not only at the end of a download.
DEDUPE_AFTER_SCAN = os.environ.get("DEDUPE_AFTER_SCAN", "1") == "1"
# 0 keeps a deliberately emptied library empty: start-up will not re-import
# files that are still on disk (downloads still trigger their own scan).
SCAN_ON_START = os.environ.get("SCAN_ON_START", "1").lower() not in ("0", "false", "no")
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "0") == "1"

# --------------------------------------------------------------------- RoturLink
# Sign in with Rotur is OAuth 2.0 + PKCE (S256) at api.rotur.dev.
# Scopes are "profile" (and optionally "email"); there is no openid scope.
# Status/activity writes need the account:profile permission, so ask for it up
# front; accounts linked before this change must re-run the sign-in.
ROTUR_APP = os.environ.get("ROTUR_APP", "")
ROTUR_SECRET = os.environ.get("ROTUR_SECRET", "")  # server-side only
ROTUR_BASE_URL = os.environ.get("ROTUR_BASE_URL", "https://api.rotur.dev").rstrip("/")
ROTUR_SCOPE = os.environ.get("ROTUR_SCOPE", "profile account:profile email")
ROTUR_AUTHORIZE_PATH = "/oauth/authorize"
ROTUR_TOKEN_PATH = "/oauth/token"
ROTUR_USERINFO_PATH = "/oauth/userinfo"
ROTUR_CALLBACK_PATH = "/api/auth/rotur/callback"
ROTUR_STATE_TTL = 600

# ------------------------------------------------------------- control channels
# Shared bot credential. Bots never hold user credentials.
BOT_TOKEN = os.environ.get("MCMUSIC_BOT_TOKEN", "") or os.environ.get("DISCORD_ADMIN_TOKEN", "")
BOT_USER = os.environ.get("MCMUSIC_BOT_USER", "")

DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
DISCORD_GUILD_ID = os.environ.get("DISCORD_GUILD_ID", "")
DISCORD_ADMIN_TOKEN = os.environ.get("DISCORD_ADMIN_TOKEN", "")

# Discord account linking (OAuth2). Register <public-url>/api/auth/discord/callback
# in the Discord developer portal. The secret stays on the server.
# The bot deployment already has DISCORD_APPLICATION_ID; accept it as the
# OAuth client id too, so only the client secret needs to be added.
DISCORD_CLIENT_ID = (
    os.environ.get("DISCORD_CLIENT_ID", "")
    or os.environ.get("DISCORD_APPLICATION_ID", "")
    or os.environ.get("DISCORD_APP_ID", "")
)
DISCORD_CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET", "")
DISCORD_REDIRECT_URI = os.environ.get("DISCORD_REDIRECT_URI", "")
DISCORD_SCOPE = os.environ.get("DISCORD_SCOPE", "identify")

# OriginChats: any REST chat bridge exposing the documented message contract.
ORIGINCHATS_BASE = os.environ.get("ORIGINCHATS_BASE", "").rstrip("/")
ORIGINCHATS_TOKEN = os.environ.get("ORIGINCHATS_TOKEN", "")
ORIGINCHATS_CHANNEL = os.environ.get("ORIGINCHATS_CHANNEL", "")

DASHBOARD_INTERVAL = float(os.environ.get("DASHBOARD_INTERVAL", "4"))

# ------------------------------------------------------------------ rate limiting
API_RATE_LIMIT = int(os.environ.get("API_RATE_LIMIT", "1200"))
API_RATE_WINDOW = float(os.environ.get("API_RATE_WINDOW", "60"))
API_BAN_BASE = float(os.environ.get("API_BAN_BASE", "10"))
API_BAN_MAX = float(os.environ.get("API_BAN_MAX", "600"))
API_BAN_WINDOW = float(os.environ.get("API_BAN_WINDOW", "1800"))
API_AUTH_LIMIT = int(os.environ.get("API_AUTH_LIMIT", "40"))
API_AUTH_WINDOW = float(os.environ.get("API_AUTH_WINDOW", "300"))
# No cross-origin access unless an operator opts in. Leave empty for the
# same-origin web app and native clients (OkHttp/URLSession/Qt do not enforce
# CORS); set to one trusted origin, e.g. https://music.example.com, when a
# separate browser origin really needs the API. An empty value generates no
# usable Allow-Origin grant, so browsers reject cross-origin reads.
CORS_ORIGIN = os.environ.get("CORS_ORIGIN", "").strip()

# ----------------------------------------------------------------------- paths
DB_PATH = os.path.join(DATA_DIR, "mcmusic.db")
LOG_DIR = os.path.join(DATA_DIR, "logs")

# ----------------------------------------------------------------------- audio
AUDIO_EXTS = {".mp3", ".m4a", ".aac", ".opus", ".flac", ".wav", ".webm", ".ogg"}
YT_HOSTS = {
    "youtube.com", "www.youtube.com", "m.youtube.com",
    "music.youtube.com", "youtu.be",
}

os.makedirs(MUSIC_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# --------------------------------------------------------------------- session
SESSION_COOKIE_NAME = "mcmusic_session"
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_HTTPONLY = True
PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 90  # 90 days

# ------------------------------------------------------------------- mail / resets
# Password reset links and password-change notices go out over plain SMTP, so a
# self-hosted server needs no vendor account. With SMTP_HOST empty the reset
# endpoint still answers normally (no account enumeration) and simply does not
# send anything.
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "") or SMTP_USER
SMTP_STARTTLS = os.environ.get("SMTP_STARTTLS", "1") == "1"
# Reset links are single use and short lived.
RESET_TTL = int(os.environ.get("RESET_TTL", "3600"))
# Absolute base for links in mail; falls back to the request's own origin.
PUBLIC_URL = os.environ.get("PUBLIC_URL", "").rstrip("/")

# ---------------------------------------------------------------------- assets
# Bump when the offline cache contract changes (audio/art caches are separate
# from the shell cache so an update never discards downloaded media). Shell 12
# is the 4.2.0 redesign; older cached shells are deliberately invalidated.
SHELL_VERSION = os.environ.get("SHELL_VERSION", "12")
MEDIA_CACHE = "mcmusic-media-v1"
```
