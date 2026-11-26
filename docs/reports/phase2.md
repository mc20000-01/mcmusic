# mcmusic 4.2.0 — Phase 2 report

Branch: `design-4.2.0`. Parent commit: `a1c32e2` (Phase 1). This phase is the Android client only; no version bump or release action is included.

## What changed

- Added an authored HCT runtime layer (`DynamicColour.kt`) backed by pinned `com.materialkolor:material-color-utilities:4.1.1`. The five generated family palettes and every legacy alias remain the source of truth for stored ids; the runtime overlays a 2021 tonal-spot scheme derived from the playing cover's quantised dominant colour. Missing or neutral artwork restores the selected family, and real artwork is never recoloured.
- Added an Android 12+ `Wallpaper` palette choice. `refreshWallpaper()` reads the system wallpaper's primary colour on create/resume; selecting Wallpaper uses that seed through the same HCT path. No wallpaper or storage permission was added.
- Wired the playing cover only: the mini player and the settled player page mark their `Cover` as dynamic; lists and other tiles never clear or replace the live seed. Cover placeholders are deterministic flat tonal Lucide tiles (circle, squircle, cookie, flower, pentagon) from the Phase 1 generated icon set.
- Reworked `McTheme` to pass full Material 3 tonal roles into `darkColorScheme`/`lightColorScheme`, rather than mapping every role to the accent. Dialogs, switches, text fields and sliders now follow the resolved cover/family scheme.
- Applied the 4px shape contract: 28dp cards, 36dp hero artwork, 20–28dp covers, pill buttons/chips and a 48dp touch target. Hardcoded 6/7/8/9/12dp card corners were replaced with shared tokens; the remaining 4/8/16dp values are on the allowed scale.
- Added shared playful motion: medium springs with damping 0.7, 0.96 press scale, a play/pause pill-to-squircle morph with icon rotation, a flat progress line that waves only while playing, and a touch-friendly seek target. Tab changes, pager scaling, lyric auto-scroll and the lyric visualiser now honour the same switch.
- Added system haptics through `View.performHapticFeedback()` for taps, transport and navigation, with the `VIBRATE` permission declared. No custom vibration waveform or continuous feedback was introduced.
- Stored the local `playfulMotion` switch (default on) and a `dynamic_colour` switch. The legacy `motion` key is still written and read so old installs keep working, but the shared 4.2.0 key is authoritative. Android's `ANIMATOR_DURATION_SCALE` and `TRANSITION_ANIMATION_SCALE` still win.
- Corrected truth-sensitive Home copy: no invented “Your mix” claim, and “Made for you” copy appears only when the server actually returned a populated personalised shelf. `Start radio` remains because `/api/radio/<tid>` is real.
- Added the `Wallpaper` and `Colour from cover` controls to Settings, updated the motion switch copy, and kept all five family names and stored aliases intact.

## What was run

- `node scripts/gen-tokens.mjs --check && node scripts/gen-lucide.mjs --check` — pass; no token or icon source changed, so no generated file needed regeneration.
- `.venv/bin/python -m pytest tests -q` (excluding local-only Qt/widget/update suites that need CI images) — 95 passed, 1 skipped, 2 subtests passed; this includes the flatness, contrast and generated-freshness gates.
- Flatness grep over `gui/android/app/src/main/java` and `res` for every banned gradient/glass/shadow token — no matches.
- `JAVA_HOME=.toolchain/jdk ANDROID_HOME=.toolchain/sdk ./gradlew :app:dependencies --configuration debugRuntimeClasspath` — pass; the pinned MaterialKolor Android variant resolves and Kotlin stdlib is aligned to 2.3.21.
- `JAVA_HOME=.toolchain/jdk ANDROID_HOME=.toolchain/sdk ./gradlew :app:assembleDebug :app:testDebugUnitTest` — pass locally with the offline SDK/JDK toolchain; this includes Kotlin compilation, debug packaging and the Android JVM unit tests.
- `bash tests/test_check_versions.sh` — 4 checks passed; all version carriers remain 4.1.0 until Phase 5.
- `git diff --check` — pass.
- CI is triggered by pushing this separate phase commit to `design-4.2.0`; no CI result is claimed in this pre-push report.

## What was not done and why

- No version bump or release publication: Phase 5 owns that, after Phases 2–4 are CI-green.
- No web, iOS or Qt redesign in this commit: those are Phases 1, 3 and 4. No shared token or generated icon source was changed here.
- No device rendering or visual comparison: no Android device/emulator image is available locally, and no mockup was supplied. The written M3 Expressive contract is the only visual specification; CI covers compilation and unit tests.
- No server-side `playfulMotion` or dynamic-colour preference: both are local device settings, so no server schema, API or live database was touched.
- No wallpaper permission: `WallpaperManager.getWallpaperColors()` needs none, and the app never reads wallpaper pixels directly.
- No new remote network call, CDN font, tracker or analytics: the HCT seed comes from the cover bitmap the player already downloads and from Android's local wallpaper colour API.
- No fake Mix/Radio/Chart, Dolby/Spatial label, fake lossless badge or fabricated explicit badge: the feature-truth audit and real endpoints remain unchanged.
- No generated blocks were hand-edited. Generated palettes stay inside `Design.kt`'s marker block and generated Lucide ids stay inside `Lucide.kt`'s marker block.
- No live database changes, branch sync, redeploy or secret rotation: those require explicit permission and are outside this design phase.

## Full authored file contents

The files below are reproduced in full. Generated marker blocks are shown only as context in the authored files that contain them; no generated output was changed in this phase.

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
        versionCode = 54
        versionName = "4.1.0"
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

### `gui/android/app/src/main/AndroidManifest.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.WAKE_LOCK" />
    <!-- Standard haptic feedback uses this permission on devices that gate it. -->
    <uses-permission android:name="android.permission.VIBRATE" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_MEDIA_PLAYBACK" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
    <!-- In-app updates hand the downloaded APK to the system installer. -->
    <uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES" />

    <application
        android:icon="@mipmap/ic_launcher"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:label="@string/app_name"
        android:supportsRtl="true"
        android:theme="@style/Theme.MCMusic"
        android:networkSecurityConfig="@xml/network_security_config">

        <activity
            android:name=".MainActivity"
            android:configChanges="orientation|screenSize|screenLayout|keyboardHidden|uiMode"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
            <intent-filter>
                <action android:name="android.intent.action.VIEW" />
                <category android:name="android.intent.category.DEFAULT" />
                <category android:name="android.intent.category.BROWSABLE" />
                <data android:scheme="mcmusic" android:host="oauth" />
            </intent-filter>
        </activity>

        <provider
            android:name="androidx.core.content.FileProvider"
            android:authorities="${applicationId}.fileprovider"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/file_paths" />
        </provider>

        <service
            android:name=".playback.PlaybackService"
            android:exported="true"
            android:foregroundServiceType="mediaPlayback">
            <intent-filter>
                <action android:name="androidx.media3.session.MediaSessionService" />
            </intent-filter>
        </service>

        <activity
            android:name=".widget.WidgetConfigActivity"
            android:exported="true"
            android:theme="@android:style/Theme.Material.NoActionBar">
            <intent-filter>
                <action android:name="android.appwidget.action.APPWIDGET_CONFIGURE" />
            </intent-filter>
        </activity>

        <receiver
            android:name=".widget.WidgetControlReceiver"
            android:exported="false" />

        <receiver
            android:name=".widget.NowWidgetProvider"
            android:exported="true"
            android:label="@string/widget_now_label">
            <intent-filter>
                <action android:name="android.appwidget.action.APPWIDGET_UPDATE" />
            </intent-filter>
            <meta-data
                android:name="android.appwidget.provider"
                android:resource="@xml/widget_now_info" />
        </receiver>

        <receiver
            android:name=".widget.BarWidgetProvider"
            android:exported="true"
            android:label="@string/widget_bar_label">
            <intent-filter>
                <action android:name="android.appwidget.action.APPWIDGET_UPDATE" />
            </intent-filter>
            <meta-data
                android:name="android.appwidget.provider"
                android:resource="@xml/widget_bar_info" />
        </receiver>
    </application>
</manifest>
```

### `gui/android/app/src/main/java/dev/mcmusic/app/MainActivity.kt`

```kotlin
package dev.mcmusic.app

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.content.ContextCompat
import androidx.activity.SystemBarStyle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.DisposableEffect
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch
import dev.mcmusic.app.data.Account
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.AutoDownload
import dev.mcmusic.app.data.Downloads
import dev.mcmusic.app.data.LinkEvents
import dev.mcmusic.app.data.Prefs
import dev.mcmusic.app.ui.McShell
import dev.mcmusic.app.ui.design.DesignLanguage
import dev.mcmusic.app.ui.design.DynamicColour
import dev.mcmusic.app.ui.design.McTheme
import dev.mcmusic.app.ui.design.Palettes
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.widget.Widgets

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Prefs.init(applicationContext)
        DynamicColour.refreshWallpaper(applicationContext)
        // Restore the last verified identity before the first composition, so a
        // background/service blip never flashes the sign-in gate on cold start.
        Account.restoreCached()
        Api.init(applicationContext)
        Downloads.init(applicationContext)
        Playback.init(applicationContext)
        AutoDownload.register(applicationContext)
        Thread { runCatching { kotlinx.coroutines.runBlocking { AutoDownload.runIfAllowed() } } }.start()
        handleOAuthIntent(intent)

        // The playback notification is how a stream keeps running off-screen.
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) !=
            PackageManager.PERMISSION_GRANTED
        ) {
            registerForActivityResult(ActivityResultContracts.RequestPermission()) { }.launch(Manifest.permission.POST_NOTIFICATIONS)
        }

        // Widgets are redrawn from the same prefs: opening the app is the
        // cheapest moment to bring them up to date.
        Thread { runCatching { Widgets.refresh(applicationContext) } }.start()

        val dark = DynamicColour.resolve(Prefs.palette, isSystemDark()).dark
        enableEdgeToEdge(
            statusBarStyle = if (dark) SystemBarStyle.dark(android.graphics.Color.TRANSPARENT)
            else SystemBarStyle.light(android.graphics.Color.TRANSPARENT, android.graphics.Color.TRANSPARENT),
            navigationBarStyle = if (dark) SystemBarStyle.dark(android.graphics.Color.TRANSPARENT)
            else SystemBarStyle.light(android.graphics.Color.TRANSPARENT, android.graphics.Color.TRANSPARENT),
        )

        setContent {
            McTheme(paletteId = Prefs.palette, language = DesignLanguage.from(Prefs.language)) {
                val darkPalette = DynamicColour.resolve(Prefs.palette, isSystemDark()).dark
                val view = LocalView.current
                DisposableEffect(darkPalette) {
                    val window = (view.context as? ComponentActivity)?.window
                    if (window != null) {
                        WindowCompat.getInsetsController(window, view).apply {
                            isAppearanceLightStatusBars = !darkPalette
                            isAppearanceLightNavigationBars = !darkPalette
                        }
                    }
                    onDispose {}
                }
                Box(Modifier.fillMaxSize()) {
                    McShell()
                }
            }
        }
    }

    override fun onResume() {
        super.onResume()
        DynamicColour.refreshWallpaper(applicationContext)
        // Revalidate in the background without dropping the cached identity.
        // Account.refresh() keeps the saved Me on transient failures and only
        // clears the session on a real 401.
        if (!Prefs.token.isNullOrBlank() || !Prefs.pendingToken.isNullOrBlank()) {
            lifecycleScope.launch { Account.refresh() }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleOAuthIntent(intent)
    }

    private fun handleOAuthIntent(intent: Intent?) {
        val data = intent?.data ?: return
        if (data.scheme != "mcmusic" || data.host != "oauth") return
        intent.data = null
        val linked = data.getQueryParameter("linked")
        if (!linked.isNullOrBlank()) {
            val label = when (linked) {
                "rotur" -> "Rotur"
                "discord" -> "Discord"
                else -> linked.replaceFirstChar { it.uppercase() }
            }
            Toast.makeText(this, "$label linked to your mcmusic account", Toast.LENGTH_LONG).show()
            LinkEvents.changed()
            return
        }
        val token = data.getQueryParameter("token")
        if (token.isNullOrBlank()) {
            Toast.makeText(this, "Rotur sign-in was cancelled", Toast.LENGTH_LONG).show()
            return
        }
        lifecycleScope.launch {
            Account.acceptRoturToken(token).fold(
                onSuccess = {
                    Toast.makeText(this@MainActivity, "Signed in as ${it.username}", Toast.LENGTH_LONG).show()
                },
                onFailure = {
                    Toast.makeText(
                        this@MainActivity,
                        Account.status ?: it.message ?: "Rotur sign-in failed",
                        Toast.LENGTH_LONG,
                    ).show()
                },
            )
        }
    }

    private fun isSystemDark(): Boolean =
        (resources.configuration.uiMode and android.content.res.Configuration.UI_MODE_NIGHT_MASK) ==
            android.content.res.Configuration.UI_MODE_NIGHT_YES
}
```

### `gui/android/app/src/main/java/dev/mcmusic/app/data/Prefs.kt`

```kotlin
package dev.mcmusic.app.data

import android.content.Context
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import dev.mcmusic.app.BuildConfig
import org.json.JSONArray
import org.json.JSONObject
import kotlin.math.abs

/** Discrete Lucide stroke multipliers shared by all appearance pickers. */
enum class IconStroke(val key: String, val label: String, val scale: Float) {
    ONE("1", "1x", 1f),
    ONE_AND_HALF("1.5", "1.5x", 1.5f),
    TWO("2", "2x", 2f),
    ;

    companion object {
        val DEFAULT = ONE
        val choices = entries
    }
}

/** Snap a hand-edited numeric value to the nearest picker choice. */
internal fun snapIconStroke(value: Float): IconStroke {
    if (!value.isFinite()) return IconStroke.DEFAULT
    return IconStroke.choices.minByOrNull { abs(it.scale - value) } ?: IconStroke.DEFAULT
}

/** Unknown keys and unparsable values fall back to 1x; numeric keys snap. */
internal fun String?.toIconStroke(): IconStroke {
    if (isNullOrBlank()) return IconStroke.DEFAULT
    IconStroke.choices.firstOrNull { it.key == this }?.let { return it }
    return toFloatOrNull()?.let { snapIconStroke(it) } ?: IconStroke.DEFAULT
}

/**
 * Small, synchronous settings store. Compose state so switching the palette or
 * the design language repaints immediately, and SharedPreferences so both
 * survive a restart. Home screen widgets read the same values.
 */
/** One automatic-download target, with its own connection rule. */
data class DownloadSource(
    val kind: String, // playlist | likes | artist | album
    val ref: String,
    val name: String,
    val network: String = "wifi", // wifi | stable | any
)

object Prefs {
    private const val FILE = "mcmusic"
    private var sp: android.content.SharedPreferences? = null

    const val DEFAULT_SERVER = BuildConfig.DEFAULT_SERVER

    /** iOS-style or One UI-style layout and styling. */
    var language by mutableStateOf("ios")
        private set

    /** Palette id from [dev.mcmusic.app.ui.design.Palettes], or "auto". */
    var palette by mutableStateOf("auto")
        private set

    /** Lucide outline width multiplier; filled-icon mode is not available. */
    var iconStroke by mutableStateOf(IconStroke.DEFAULT)
        private set

    var server by mutableStateOf(DEFAULT_SERVER)
        private set

    var username by mutableStateOf<String?>(null)
        private set

    /** Long-lived device token (`mcd_…`); every request sends it as a bearer. */
    var token by mutableStateOf<String?>(null)
        private set

    /** A Rotur token that arrived while the server was unreachable. */
    var pendingToken by mutableStateOf<String?>(null)
        private set

    /** Whose listening the home screen widgets show; falls back to the signed-in account. */
    var widgetUser by mutableStateOf<String?>(null)
        private set

    /** Downloads wait for Wi-Fi instead of using cellular data. */
    var wifiOnly by mutableStateOf(false)
        private set

    /** Keep the metrics-ranked Faves playlist on this device. */
    var autoFaves by mutableStateOf(false)
        private set

    /** Connection rule used by Faves: wifi, stable or any. */
    var autoFavesNetwork by mutableStateOf("wifi")
        private set

    /** User-managed playlists/artists/albums to keep offline. */
    var downloadSources by mutableStateOf<List<DownloadSource>>(emptyList())
        private set

    /** Legacy tab-transition flag; kept in sync with [playfulMotion]. */
    var motion by mutableStateOf(true)
        private set

    /** Springs, shape morphs and haptics. Stored under the shared 4.2.0 key. */
    var playfulMotion by mutableStateOf(true)
        private set

    /** Tint the app from the dominant colour of the playing cover. */
    var dynamicColour by mutableStateOf(true)
        private set

    /** Keep filling the queue from radio when the last track ends. */
    var autoplay by mutableStateOf(true)
        private set

    /** Share listening with the account's Rotur activity socket. */
    var roturActivity by mutableStateOf(true)
        private set

    /** Share listening with the account's Discord presence. */
    var discordActivity by mutableStateOf(false)
        private set

    /** Covers in lists and tiles. */
    var showCovers by mutableStateOf(true)
        private set

    /** Hide tracks the server flagged explicit. */
    var hideExplicit by mutableStateOf(false)
        private set

    fun init(context: Context) {
        if (sp != null) return
        val p = context.getSharedPreferences(FILE, Context.MODE_PRIVATE)
        sp = p
        language = p.getString("language", "ios") ?: "ios"
        palette = p.getString("palette", "auto") ?: "auto"
        iconStroke = p.getString("icon_stroke", null).toIconStroke()
        server = (p.getString("server", DEFAULT_SERVER) ?: DEFAULT_SERVER).trimEnd('/')
        username = p.getString("username", null)
        token = p.getString("token", null)
        pendingToken = p.getString("pending_token", null)?.takeIf { it.isNotBlank() }
        widgetUser = p.getString("widget_user", null)?.takeIf { it.isNotBlank() }
        sleepEndsAt = p.getLong("sleep_ends_at", 0L)
        wifiOnly = p.getBoolean("wifi_only", false)
        autoFaves = p.getBoolean("auto_faves", false)
        autoFavesNetwork = normalizeNetwork(p.getString("auto_faves_network", "wifi"))
        downloadSources = readSources(p.getString("download_sources", null))
        val legacyMotion = p.getBoolean("motion", true)
        playfulMotion = p.getBoolean("playfulMotion", legacyMotion)
        motion = playfulMotion
        dynamicColour = p.getBoolean("dynamic_colour", true)
        autoplay = p.getBoolean("autoplay", true)
        roturActivity = p.getBoolean("rotur_activity", true)
        discordActivity = p.getBoolean("discord_activity", false)
        showCovers = p.getBoolean("show_covers", true)
        hideExplicit = p.getBoolean("hide_explicit", false)
    }

    fun saveWidgetUser(name: String?) {
        widgetUser = name?.trim()?.takeIf { it.isNotBlank() }
        sp?.edit()?.apply {
            if (widgetUser == null) remove("widget_user") else putString("widget_user", widgetUser)
        }?.apply()
    }

    /** Per-widget override; widgets can follow different accounts. */
    fun widgetUserFor(id: Int): String? =
        sp?.getString("widget_user_$id", null)?.takeIf { it.isNotBlank() }

    fun saveWidgetUser(id: Int, name: String?) {
        val clean = name?.trim()?.takeIf { it.isNotBlank() }
        sp?.edit()?.apply {
            if (clean == null) remove("widget_user_$id") else putString("widget_user_$id", clean)
        }?.apply()
    }

    /** Persisted sleep deadline so the timer survives a screen restart. */
    var sleepEndsAt by mutableStateOf(0L)
        private set

    fun saveSleepEndsAt(value: Long) {
        sleepEndsAt = value
        sp?.edit()?.apply {
            if (value <= 0L) remove("sleep_ends_at") else putLong("sleep_ends_at", value)
        }?.apply()
    }

    fun saveWifiOnly(enabled: Boolean) {
        wifiOnly = enabled
        sp?.edit()?.putBoolean("wifi_only", enabled)?.apply()
    }

    private fun normalizeNetwork(value: String?): String = when (value) {
        "stable", "any" -> value
        else -> "wifi"
    }

    private fun readSources(raw: String?): List<DownloadSource> = runCatching {
        val arr = JSONArray(raw ?: "[]")
        buildList {
            for (i in 0 until arr.length()) {
                val o = arr.optJSONObject(i) ?: continue
                val kind = o.optString("kind")
                val ref = o.optString("ref")
                if (kind.isBlank() || ref.isBlank()) continue
                add(
                    DownloadSource(
                        kind = kind,
                        ref = ref,
                        name = o.optString("name").ifBlank { ref },
                        network = normalizeNetwork(o.optString("network")),
                    ),
                )
            }
        }
    }.getOrDefault(emptyList())

    fun saveAutoFaves(enabled: Boolean) {
        autoFaves = enabled
        sp?.edit()?.putBoolean("auto_faves", enabled)?.apply()
    }

    fun saveAutoFavesNetwork(network: String) {
        autoFavesNetwork = normalizeNetwork(network)
        sp?.edit()?.putString("auto_faves_network", autoFavesNetwork)?.apply()
    }

    fun saveDownloadSources(sources: List<DownloadSource>) {
        downloadSources = sources
        val arr = JSONArray()
        sources.forEach { source ->
            arr.put(
                JSONObject()
                    .put("kind", source.kind)
                    .put("ref", source.ref)
                    .put("name", source.name)
                    .put("network", normalizeNetwork(source.network)),
            )
        }
        sp?.edit()?.putString("download_sources", arr.toString())?.apply()
    }

    /** One switch for playful motion; the legacy key stays usable by old code. */
    fun savePlayfulMotion(enabled: Boolean) {
        playfulMotion = enabled
        motion = enabled
        sp?.edit()
            ?.putBoolean("playfulMotion", enabled)
            ?.putBoolean("motion", enabled)
            ?.apply()
    }

    fun saveMotion(enabled: Boolean) = savePlayfulMotion(enabled)

    fun saveDynamicColour(enabled: Boolean) {
        dynamicColour = enabled
        sp?.edit()?.putBoolean("dynamic_colour", enabled)?.apply()
    }

    fun saveAutoplay(enabled: Boolean) {
        autoplay = enabled
        sp?.edit()?.putBoolean("autoplay", enabled)?.apply()
    }

    fun saveRoturActivity(enabled: Boolean) {
        roturActivity = enabled
        sp?.edit()?.putBoolean("rotur_activity", enabled)?.apply()
    }

    fun saveDiscordActivity(enabled: Boolean) {
        discordActivity = enabled
        sp?.edit()?.putBoolean("discord_activity", enabled)?.apply()
    }

    fun saveShowCovers(enabled: Boolean) {
        showCovers = enabled
        sp?.edit()?.putBoolean("show_covers", enabled)?.apply()
    }

    fun saveHideExplicit(enabled: Boolean) {
        hideExplicit = enabled
        sp?.edit()?.putBoolean("hide_explicit", enabled)?.apply()
    }

    fun saveLanguage(id: String) {
        language = id
        sp?.edit()?.putString("language", id)?.apply()
    }

    fun savePalette(id: String) {
        palette = id
        sp?.edit()?.putString("palette", id)?.apply()
    }

    fun saveIconStroke(option: IconStroke) {
        iconStroke = option
        sp?.edit()?.putString("icon_stroke", option.key)?.apply()
    }

    fun saveServer(url: String) {
        val clean = url.trim().trimEnd('/').ifEmpty { DEFAULT_SERVER }
        val changed = clean != server
        server = clean
        sp?.edit()?.putString("server", clean)?.apply()
        // A token belongs to one server. Keeping it across a server switch made
        // the app look signed in while every request was rejected.
        if (changed) {
            saveToken(null)
            saveUsername(null)
            savePendingToken(null)
            saveCachedMe(null)
            Api.clearCookies()
        }
    }

    fun saveToken(value: String?) {
        token = value
        sp?.edit()?.apply { if (value == null) remove("token") else putString("token", value) }?.apply()
    }

    fun savePendingToken(value: String?) {
        pendingToken = value?.takeIf { it.isNotBlank() }
        sp?.edit()?.apply {
            if (pendingToken == null) remove("pending_token") else putString("pending_token", pendingToken)
        }?.apply()
    }

    fun saveUsername(name: String?) {
        username = name
        sp?.edit()?.apply { if (name == null) remove("username") else putString("username", name) }?.apply()
    }

    /** Last verified /api/me response, restored optimistically on cold start. */
    fun saveCachedMe(me: Me?) {
        val json = me?.let {
            JSONObject()
                .put("id", it.id)
                .put("username", it.username)
                .put("is_admin", it.isAdmin)
                .put("email", it.email)
                .put("rotur_linked", it.roturLinked)
                .toString()
        }
        sp?.edit()?.apply { if (json == null) remove("cached_me") else putString("cached_me", json) }?.apply()
    }

    fun cachedMe(): Me? {
        val raw = sp?.getString("cached_me", null) ?: return null
        return runCatching {
            val j = JSONObject(raw)
            Me(
                id = j.optInt("id"),
                username = j.optString("username"),
                isAdmin = j.optBoolean("is_admin"),
                email = j.optString("email").takeIf { it.isNotBlank() },
                roturLinked = j.optBoolean("rotur_linked"),
            )
        }.getOrNull()
    }

    /** The player service can be recreated while the app is in the background. */
    fun saveQueue(snapshot: QueueSnapshot?) {
        val json = snapshot?.let { q ->
            val tracks = org.json.JSONArray()
            q.tracks.forEach { t ->
                tracks.put(
                    JSONObject()
                        .put("id", t.id)
                        .put("title", t.title)
                        .put("artist", t.artist)
                        .put("album", t.album)
                        .put("duration", t.duration)
                        .put("explicit", t.explicit)
                        .put("liked", t.liked),
                )
            }
            JSONObject()
                .put("tracks", tracks)
                .put("index", q.index)
                .put("position", q.positionMs)
                .put("repeat_mode", q.repeatMode)
                .put("shuffle", q.shuffle)
                .put("autoplay", q.autoplay)
                .toString()
        }
        sp?.edit()?.apply { if (json == null) remove("queue") else putString("queue", json) }?.apply()
    }

    fun savedQueue(): QueueSnapshot? {
        val raw = sp?.getString("queue", null) ?: return null
        return runCatching {
            val j = JSONObject(raw)
            val arr = j.optJSONArray("tracks") ?: return@runCatching null
            val tracks = buildList {
                for (i in 0 until arr.length()) {
                    val t = arr.optJSONObject(i) ?: continue
                    val id = t.optInt("id")
                    if (id > 0) add(
                        Track(
                            id = id,
                            title = t.optString("title"),
                            artist = t.optString("artist"),
                            album = t.optString("album"),
                            duration = t.optDouble("duration"),
                            explicit = t.optBoolean("explicit"),
                            liked = t.optBoolean("liked"),
                        ),
                    )
                }
            }
            if (tracks.isEmpty()) null else QueueSnapshot(
                tracks = tracks,
                index = j.optInt("index", 0).coerceIn(0, tracks.lastIndex),
                positionMs = j.optLong("position", 0L).coerceAtLeast(0L),
                repeatMode = j.optInt("repeat_mode", 0),
                shuffle = j.optBoolean("shuffle", false),
                autoplay = j.optBoolean("autoplay", true),
            )
        }.getOrNull()
    }
}

/** Everything ExoPlayer needs to pick up a queue after process death. */
data class QueueSnapshot(
    val tracks: List<Track>,
    val index: Int,
    val positionMs: Long,
    val repeatMode: Int,
    val shuffle: Boolean,
    val autoplay: Boolean,
)
```

### `gui/android/app/src/main/java/dev/mcmusic/app/ui/Components.kt`

```kotlin
package dev.mcmusic.app.ui

import androidx.annotation.DrawableRes
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateDpAsState
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.spring
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.indication
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.SwipeToDismissBox
import androidx.compose.material3.SwipeToDismissBoxValue
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.rememberSwipeToDismissBoxState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Account
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.LibraryState
import dev.mcmusic.app.data.Playlist
import dev.mcmusic.app.data.Prefs
import dev.mcmusic.app.data.Track
import dev.mcmusic.app.ui.design.DynamicColour
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.PlayfulMotion
import dev.mcmusic.app.ui.design.mcSurface
import dev.mcmusic.app.ui.design.playfulMotionEnabled
import dev.mcmusic.app.ui.design.rememberPlayfulHaptic
import kotlinx.coroutines.launch
import android.widget.Toast
import kotlin.math.PI
import kotlin.math.sin

/* ── text ──────────────────────────────────────────────────────────────── */

/** Page title, as the web client's h1. */
@Composable
fun ScreenTitle(title: String, subtitle: String? = null, modifier: Modifier = Modifier) {
    val design = LocalDesign.current
    Column(modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(3.dp)) {
        Text(title, color = design.fg, fontSize = design.titleSize, fontWeight = design.titleWeight)
        if (subtitle != null) {
            Text(subtitle, color = design.dim, fontSize = 13.sp, maxLines = 2, overflow = TextOverflow.Ellipsis)
        }
    }
}

/** Small uppercase section heading, optionally with a trailing action. */
@Composable
fun SectionLabel(text: String, modifier: Modifier = Modifier, action: (@Composable () -> Unit)? = null) {
    val design = LocalDesign.current
    Row(
        modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Text(
            text.uppercase(),
            color = design.dim,
            fontSize = design.sectionSize,
            fontWeight = design.sectionWeight,
            letterSpacing = 1.1.sp,
        )
        action?.invoke()
    }
}

@Composable
fun Muted(text: String, modifier: Modifier = Modifier, size: Int = 13) {
    Text(text, modifier = modifier, color = LocalDesign.current.dim, fontSize = size.sp)
}

/* ── buttons ───────────────────────────────────────────────────────────── */

@Composable
fun PrimaryButton(text: String, modifier: Modifier = Modifier, enabled: Boolean = true, onClick: () -> Unit) {
    val design = LocalDesign.current
    val haptic = rememberPlayfulHaptic()
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(50))
            .background(if (enabled) design.accent else design.accent.copy(alpha = 0.35f))
            .clickable(enabled = enabled) {
                haptic(PlayfulMotion.CLICK)
                onClick()
            }
            .padding(horizontal = 20.dp, vertical = 14.dp),
        contentAlignment = Alignment.Center,
    ) {
        Text(text, color = design.onAccent, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
fun GhostButton(text: String, modifier: Modifier = Modifier, danger: Boolean = false, onClick: () -> Unit) {
    val design = LocalDesign.current
    val haptic = rememberPlayfulHaptic()
    val tint = if (danger) design.palette.error else design.fg
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(50))
            .border(
                1.dp,
                if (danger) design.palette.error.copy(alpha = 0.5f) else design.hairline,
                RoundedCornerShape(50),
            )
            .clickable {
                haptic(PlayfulMotion.KEY)
                onClick()
            }
            .padding(horizontal = 18.dp, vertical = 13.dp),
        contentAlignment = Alignment.Center,
    ) {
        Text(text, color = tint, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
fun IconButton(
    @DrawableRes icon: Int,
    modifier: Modifier = Modifier,
    size: Dp = 20.dp,
    tint: Color? = null,
    onClick: () -> Unit,
) {
    val design = LocalDesign.current
    val motion = playfulMotionEnabled()
    val haptic = rememberPlayfulHaptic()
    val interaction = remember { MutableInteractionSource() }
    val pressed by interaction.collectIsPressedAsState()
    val scale by animateFloatAsState(
        if (pressed && motion) PlayfulMotion.PRESS_SCALE else 1f,
        spring(dampingRatio = PlayfulMotion.DAMPING_RATIO, stiffness = PlayfulMotion.STIFFNESS),
    )
    Box(
        modifier = modifier
            .size(design.touchTarget)
            .clip(CircleShape)
            .background(if (pressed && motion) design.accentWash else Color.Transparent)
            .graphicsLayer { scaleX = scale; scaleY = scale }
            .clickable(interactionSource = interaction, indication = null) {
                haptic(PlayfulMotion.KEY)
                onClick()
            },
        contentAlignment = Alignment.Center,
    ) {
        LucideIcon(icon, tint ?: design.dim, size = size)
    }
}

/** Play/pause pill-to-squircle morph. The icon and haptics follow the same switch. */
@Composable
fun PlayPauseButton(
    playing: Boolean,
    modifier: Modifier = Modifier,
    size: Dp = 58.dp,
    onClick: () -> Unit,
) {
    val design = LocalDesign.current
    val motion = playfulMotionEnabled()
    val haptic = rememberPlayfulHaptic()
    val interaction = remember { MutableInteractionSource() }
    val pressed by interaction.collectIsPressedAsState()
    val corner by animateDpAsState(
        if (playing) 16.dp else size / 2,
        spring(dampingRatio = PlayfulMotion.DAMPING_RATIO, stiffness = PlayfulMotion.STIFFNESS),
    )
    val scale by animateFloatAsState(
        if (pressed && motion) PlayfulMotion.PRESS_SCALE else 1f,
        spring(dampingRatio = PlayfulMotion.DAMPING_RATIO, stiffness = PlayfulMotion.STIFFNESS),
    )
    val rotation by animateFloatAsState(
        if (playing) 90f else 0f,
        spring(dampingRatio = PlayfulMotion.DAMPING_RATIO, stiffness = PlayfulMotion.STIFFNESS),
    )
    Box(
        modifier = modifier
            .size(size)
            .clip(RoundedCornerShape(if (motion) corner else 16.dp))
            .background(design.accent)
            .graphicsLayer { scaleX = scale; scaleY = scale }
            .clickable(interactionSource = interaction, indication = null) {
                haptic(PlayfulMotion.CLICK)
                onClick()
            },
        contentAlignment = Alignment.Center,
    ) {
        Box(Modifier.graphicsLayer { rotationZ = if (motion) rotation else 0f }) {
            LucideIcon(
                if (playing) Lucide.Pause else Lucide.Play,
                design.onAccent,
                size = size * 0.36f,
            )
        }
    }
}

/**
 * Flat progress line. While playing, a small wave rides the filled portion;
 * paused state is one flat bar. Reduced motion and the local switch flatten it.
 */
@Composable
fun PlayfulProgress(
    fraction: Float,
    playing: Boolean,
    modifier: Modifier = Modifier,
) {
    val design = LocalDesign.current
    val motion = playfulMotionEnabled()
    val transition = rememberInfiniteTransition()
    val phase by transition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 1818, easing = androidx.compose.animation.core.LinearEasing),
            repeatMode = RepeatMode.Restart,
        ),
    )
    val filled = fraction.coerceIn(0f, 1f)
    Canvas(
        modifier
            .height(6.dp)
            .clip(RoundedCornerShape(50))
            .background(design.hairline),
    ) {
        val width = size.width * filled
        if (width <= 0f) return@Canvas
        val mid = size.height / 2f
        if (!playing || !motion) {
            drawLine(design.accent, Offset(0f, mid), Offset(width, mid), strokeWidth = 2.dp.toPx())
            return@Canvas
        }
        val path = Path()
        val steps = (width / (4.dp.toPx())).toInt().coerceAtLeast(2)
        val amplitude = minOf(size.height * 0.28f, 2.dp.toPx())
        for (index in 0..steps) {
            val x = width * index / steps
            val envelope = sin(PI * index / steps).toFloat().coerceAtLeast(0f)
            val y = mid + sin(index * 0.36f + phase * 2f * PI.toFloat()) * amplitude * envelope
            if (index == 0) path.moveTo(x, y) else path.lineTo(x, y)
        }
        drawPath(path, design.accent, style = Stroke(width = 2.dp.toPx()))
    }
}

/** Touch-friendly seek target carrying the flat progress line. */
@Composable
fun PlayfulSeek(
    fraction: Float,
    playing: Boolean,
    onSeek: (Float) -> Unit,
    modifier: Modifier = Modifier,
) {
    val value = fraction.coerceIn(0f, 1f)
    Box(
        modifier
            .fillMaxWidth()
            .height(designTouchTarget())
            .pointerInput(value) {
                detectTapGestures { offset -> onSeek((offset.x / size.width).coerceIn(0f, 1f)) }
            }
            .pointerInput(value) {
                detectDragGestures { change, _ ->
                    onSeek((change.position.x / size.width).coerceIn(0f, 1f))
                }
            },
        contentAlignment = Alignment.Center,
    ) {
        PlayfulProgress(value, playing, Modifier.fillMaxWidth())
    }
}

/** Kept as a function so the shared touch target stays in one place. */
@Composable
private fun designTouchTarget(): Dp = LocalDesign.current.touchTarget

/* ── text field ────────────────────────────────────────────────────────── */

@Composable
fun McField(
    value: String,
    onValueChange: (String) -> Unit,
    label: String,
    modifier: Modifier = Modifier,
    password: Boolean = false,
    keyboard: KeyboardOptions = KeyboardOptions(imeAction = ImeAction.Next),
    actions: KeyboardActions = KeyboardActions.Default,
) {
    val design = LocalDesign.current
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        label = { Text(label, fontSize = 12.sp) },
        singleLine = true,
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(design.tileRadius),
        textStyle = androidx.compose.ui.text.TextStyle(color = design.fg, fontSize = 14.sp),
        visualTransformation = if (password) PasswordVisualTransformation() else VisualTransformation.None,
        keyboardOptions = keyboard,
        keyboardActions = actions,
        colors = OutlinedTextFieldDefaults.colors(
            focusedTextColor = design.fg,
            unfocusedTextColor = design.fg,
            focusedBorderColor = design.accentText,
            unfocusedBorderColor = design.hairline,
            focusedLabelColor = design.accentText,
            unfocusedLabelColor = design.dim,
            cursorColor = design.accentText,
            focusedContainerColor = design.cardFill,
            unfocusedContainerColor = design.cardFill,
        ),
    )
}

/* ── status ────────────────────────────────────────────────────────────── */

@Composable
fun LiveDot(active: Boolean, size: Dp = 6.dp) {
    val design = LocalDesign.current
    Box(
        Modifier
            .size(size)
            .clip(CircleShape)
            .background(if (active) design.accent else design.dim.copy(alpha = 0.4f)),
    )
}

@Composable
fun Pill(text: String, active: Boolean = true, modifier: Modifier = Modifier) {
    val design = LocalDesign.current
    Row(
        modifier
            .clip(RoundedCornerShape(50))
            .background(design.accentWash)
            .border(1.dp, design.hairline, RoundedCornerShape(50))
            .padding(horizontal = 11.dp, vertical = 5.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        LiveDot(active, 6.dp)
        Text(text, color = if (active) design.fg else design.dim, fontSize = 11.sp, fontWeight = FontWeight.Medium)
    }
}

@Composable
fun Loading(text: String = "Loading…", modifier: Modifier = Modifier) {
    val design = LocalDesign.current
    Row(
        modifier.fillMaxWidth().padding(vertical = 28.dp),
        horizontalArrangement = Arrangement.Center,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        CircularProgressIndicator(
            modifier = Modifier.size(16.dp),
            strokeWidth = 2.dp,
            color = design.accentText,
        )
        Box(Modifier.width(10.dp))
        Text(text, color = design.dim, fontSize = 13.sp)
    }
}

@Composable
fun ErrorLine(message: String, modifier: Modifier = Modifier) {
    val design = LocalDesign.current
    Text(
        message,
        modifier = modifier.fillMaxWidth().clip(RoundedCornerShape(design.cardRadius))
            .background(design.palette.error.copy(alpha = 0.10f))
            .border(1.dp, design.palette.error.copy(alpha = 0.35f), RoundedCornerShape(design.cardRadius))
            .padding(horizontal = 12.dp, vertical = 9.dp),
        color = design.palette.error,
        fontSize = 12.sp,
    )
}

@Composable
fun EmptyState(
    @DrawableRes icon: Int,
    title: String,
    body: String,
    modifier: Modifier = Modifier,
    actionLabel: String? = null,
    onAction: (() -> Unit)? = null,
) {
    val design = LocalDesign.current
    Column(
        modifier.fillMaxWidth().mcSurface().padding(horizontal = 24.dp, vertical = 32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Box(Modifier.size(56.dp).clip(CircleShape).background(design.accentSoft), Alignment.Center) {
            LucideIcon(icon, design.accentText, size = 24.dp)
        }
        Text(title, color = design.fg, fontSize = 17.sp, fontWeight = FontWeight.SemiBold, textAlign = TextAlign.Center)
        Text(body, color = design.dim, fontSize = 13.sp, lineHeight = 19.sp, textAlign = TextAlign.Center)
        if (actionLabel != null && onAction != null) {
            PrimaryButton(actionLabel, Modifier.padding(top = 2.dp), onClick = onAction)
        }
    }
}

@Composable
fun ScreenBack(onBack: () -> Unit) {
    Row(
        Modifier
            .clip(RoundedCornerShape(50))
            .background(LocalDesign.current.accentWash)
            .clickable { onBack() }
            .padding(vertical = 9.dp, horizontal = 14.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        LucideIcon(Lucide.ChevronLeft, LocalDesign.current.accent, size = 16.dp)
        Text("Back", color = LocalDesign.current.fg, fontSize = 13.sp, fontWeight = FontWeight.Medium)
    }
}

/* ── music pieces ──────────────────────────────────────────────────────── */

/** Square cover that falls back to a neutral tile when a track has no art. */
@Composable
fun TrackCover(
    track: Track,
    size: Dp = 48.dp,
    radius: Dp = 20.dp,
    dynamic: Boolean = false,
) {
    val design = LocalDesign.current
    val url = trackCoverUrl(track.id)
    if (!Prefs.showCovers) {
        // A list tile only hides its own art; the player owns the live seed.
        if (dynamic) DynamicColour.clearCover(url)
        Box(
            Modifier.size(size).clip(RoundedCornerShape(radius)).background(design.accentSoft),
            Alignment.Center,
        ) {
            LucideIcon(Lucide.ListMusic, design.accentText, size = size / 2)
        }
        return
    }
    Cover(
        url = url,
        shape = RoundedCornerShape(radius),
        modifier = Modifier.size(size),
        fallback = design.accentSoft,
        dynamic = dynamic,
    )
}

/** Appearance setting: filter tracks the server flagged explicit. */
fun List<Track>.visibleTracks(): List<Track> =
    if (Prefs.hideExplicit) filterNot { it.explicit } else this

@OptIn(ExperimentalFoundationApi::class, ExperimentalMaterial3Api::class)
@Composable
fun TrackRow(
    track: Track,
    modifier: Modifier = Modifier,
    subtitle: String? = null,
    trailing: (@Composable RowScope.() -> Unit)? = null,
    menu: Boolean = false,
    onClick: () -> Unit,
    onOpenArtist: ((String) -> Unit)? = null,
) {
    val design = LocalDesign.current
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val current = dev.mcmusic.app.playback.Playback.state.track?.id == track.id
    var menuOpen by remember { mutableStateOf(false) }
    var confirmRemove by remember { mutableStateOf(false) }

    fun toggleLike() {
        scope.launch {
            Api.toggleLike(track.id).fold(
                onSuccess = {
                    Toast.makeText(
                        context,
                        if (it) "Added to likes" else "Removed from likes",
                        Toast.LENGTH_SHORT,
                    ).show()
                    LibraryState.changed()
                },
                onFailure = {
                    Toast.makeText(context, it.message ?: "Could not update like", Toast.LENGTH_SHORT).show()
                },
            )
        }
    }

    fun askRemove() {
        if (!Account.isAdmin) {
            Toast.makeText(context, "Only admins can remove tracks", Toast.LENGTH_SHORT).show()
            return
        }
        confirmRemove = true
    }

    fun removeTrack() {
        confirmRemove = false
        scope.launch {
            Api.deleteTrack(track.id).fold(
                onSuccess = {
                    dev.mcmusic.app.playback.Playback.removeTrack(track.id)
                    LibraryState.changed()
                    Toast.makeText(context, "Removed ${track.title} from mcmusic", Toast.LENGTH_SHORT).show()
                },
                onFailure = {
                    Toast.makeText(context, it.message ?: "Could not remove track", Toast.LENGTH_SHORT).show()
                },
            )
        }
    }

    val dismissState = rememberSwipeToDismissBoxState(
        confirmValueChange = { value ->
            when (value) {
                SwipeToDismissBoxValue.StartToEnd -> toggleLike()
                SwipeToDismissBoxValue.EndToStart -> askRemove()
                SwipeToDismissBoxValue.Settled -> Unit
            }
            // Always settle back; the action (or confirmation) is the result.
            false
        },
    )

    SwipeToDismissBox(
        state = dismissState,
        modifier = modifier.fillMaxWidth(),
        enableDismissFromStartToEnd = menu,
        enableDismissFromEndToStart = menu && Account.isAdmin,
        backgroundContent = {
            Row(
                Modifier.fillMaxSize().padding(horizontal = 20.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                if (menu) {
                    LucideIcon(
                        Lucide.Heart,
                        if (track.liked) design.palette.error else design.accentText,
                        size = 24.dp,
                        contentDescription = if (track.liked) "Unlike" else "Like",
                    )
                } else {
                    Box(Modifier.weight(1f))
                }
                if (menu && Account.isAdmin) {
                    LucideIcon(
                        Lucide.Trash,
                        design.palette.error,
                        size = 24.dp,
                        contentDescription = "Remove track",
                    )
                }
            }
        },
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(design.tileRadius))
                .background(if (current) design.accentWash else Color.Transparent)
                .combinedClickable(
                    onClick = onClick,
                    onLongClick = if (menu) ({ menuOpen = true }) else null,
                )
                .padding(horizontal = 10.dp, vertical = 9.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            TrackCover(track, 48.dp, 20.dp)
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Text(
                    track.title,
                    color = if (current) design.accentText else design.fg,
                    fontSize = 15.sp,
                    fontWeight = FontWeight.Medium,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                Text(
                    subtitle ?: listOf(track.artist, track.album).filter { it.isNotBlank() }.joinToString(" · "),
                    color = design.dim,
                    fontSize = 12.sp,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }
            trailing?.invoke(this)
            if (menu) {
                TrackActionsMenu(
                    track = track,
                    expanded = menuOpen,
                    onExpandedChange = { menuOpen = it },
                    onRemove = ::askRemove,
                    onOpenArtist = onOpenArtist,
                )
            }
        }
    }

    if (confirmRemove) {
        AlertDialog(
            onDismissRequest = { confirmRemove = false },
            title = { Text("Remove track?") },
            text = {
                Text(
                    "\"${track.title}\" will be deleted from mcmusic for everyone. " +
                        "Playlists, likes and queues pointing at it are updated too.",
                )
            },
            confirmButton = {
                TextButton(onClick = ::removeTrack) { Text("Remove", color = design.palette.error) }
            },
            dismissButton = {
                TextButton(onClick = { confirmRemove = false }) { Text("Cancel") }
            },
        )
    }
}

/**
 * Track actions: like, playlist, radio, artist and info. The playlists load
 * when the menu opens (also on a long press), so ordinary browsing makes no
 * extra requests. Admins also get Remove from mcmusic. [onOpenArtist] is only
 * supplied from screens that can show an artist collection.
 */
@Composable
fun TrackActionsMenu(
    track: Track,
    expanded: Boolean,
    onExpandedChange: (Boolean) -> Unit,
    modifier: Modifier = Modifier,
    onRemove: () -> Unit,
    onOpenArtist: ((String) -> Unit)? = null,
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val design = LocalDesign.current
    var picker by remember { mutableStateOf(false) }
    var showInfo by remember { mutableStateOf(false) }
    var playlists by remember { mutableStateOf<List<Playlist>>(emptyList()) }
    var busy by remember { mutableStateOf(false) }

    LaunchedEffect(expanded) {
        if (expanded) Api.playlists().onSuccess { playlists = it }
    }

    Box(modifier) {
        IconButton(Lucide.Ellipsis, size = 16.dp, onClick = { onExpandedChange(true) })
        DropdownMenu(expanded, onDismissRequest = { onExpandedChange(false) }) {
            DropdownMenuItem(
                text = { Text(if (track.liked) "Unlike" else "Like", fontSize = 13.sp) },
                leadingIcon = { LucideIcon(Lucide.Heart, LocalDesign.current.accent, size = 16.dp) },
                onClick = {
                    onExpandedChange(false)
                    scope.launch {
                        Api.toggleLike(track.id).fold(
                            onSuccess = {
                                Toast.makeText(
                                    context,
                                    if (it) "Added to likes" else "Removed from likes",
                                    Toast.LENGTH_SHORT,
                                ).show()
                                LibraryState.changed()
                            },
                            onFailure = {
                                Toast.makeText(context, it.message ?: "Could not update like", Toast.LENGTH_SHORT).show()
                            },
                        )
                    }
                },
            )
            DropdownMenuItem(
                text = { Text("Play next", fontSize = 13.sp) },
                leadingIcon = { LucideIcon(Lucide.ListPlus, design.accentText, size = 16.dp) },
                onClick = {
                    onExpandedChange(false)
                    dev.mcmusic.app.playback.Playback.playNext(track)
                    Toast.makeText(context, "Playing ${track.title} next", Toast.LENGTH_SHORT).show()
                },
            )
            DropdownMenuItem(
                text = { Text("Add to queue", fontSize = 13.sp) },
                leadingIcon = { LucideIcon(Lucide.ListMusic, design.accentText, size = 16.dp) },
                onClick = {
                    onExpandedChange(false)
                    dev.mcmusic.app.playback.Playback.addToQueue(track)
                    Toast.makeText(context, "Added ${track.title} to the queue", Toast.LENGTH_SHORT).show()
                },
            )
            DropdownMenuItem(
                text = { Text("Add to playlist", fontSize = 13.sp) },
                leadingIcon = { LucideIcon(Lucide.ListPlus, design.accentText, size = 16.dp) },
                onClick = { onExpandedChange(false); picker = true },
            )
            DropdownMenuItem(
                text = { Text("Start radio", fontSize = 13.sp) },
                leadingIcon = { LucideIcon(Lucide.Radio, design.accentText, size = 16.dp) },
                onClick = {
                    onExpandedChange(false)
                    scope.launch {
                        Api.radio(track.id).fold(
                            onSuccess = { suggestions ->
                                val queue = buildList {
                                    add(track)
                                    suggestions
                                        .filter { it.id > 0 && it.id != track.id }
                                        .distinctBy { it.id }
                                        .forEach { add(it) }
                                }
                                dev.mcmusic.app.playback.Playback.play(queue, 0)
                                Toast.makeText(
                                    context,
                                    "Radio started from ${track.title}",
                                    Toast.LENGTH_SHORT,
                                ).show()
                            },
                            onFailure = {
                                Toast.makeText(context, it.message ?: "Could not start radio", Toast.LENGTH_SHORT).show()
                            },
                        )
                    }
                },
            )
            onOpenArtist?.let { openArtist ->
                DropdownMenuItem(
                    text = { Text("Go to artist", fontSize = 13.sp) },
                    leadingIcon = { LucideIcon(Lucide.User, design.accentText, size = 16.dp) },
                    onClick = { onExpandedChange(false); openArtist(track.artist) },
                )
            }
            DropdownMenuItem(
                text = { Text("Track info", fontSize = 13.sp) },
                leadingIcon = { LucideIcon(Lucide.Info, design.accentText, size = 16.dp) },
                onClick = { onExpandedChange(false); showInfo = true },
            )
            if (Account.isAdmin) {
                DropdownMenuItem(
                    text = { Text("Remove from mcmusic", color = design.palette.error, fontSize = 13.sp) },
                    leadingIcon = { LucideIcon(Lucide.Trash, design.palette.error, size = 16.dp) },
                    onClick = { onExpandedChange(false); onRemove() },
                )
            }
        }
    }

    if (picker) {
        Dialog(onDismissRequest = { picker = false }) {
            Column(
                Modifier.fillMaxWidth().mcSurface(RoundedCornerShape(design.cardRadius)).padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Text("Add to playlist", color = LocalDesign.current.fg, fontSize = 16.sp, fontWeight = FontWeight.SemiBold)
                Text(track.title, color = LocalDesign.current.dim, fontSize = 12.sp, maxLines = 1)
                if (playlists.isEmpty()) {
                    Muted("Create a playlist first, then add tracks from here.")
                } else {
                    playlists.forEach { playlist ->
                        Row(
                            Modifier.fillMaxWidth().clip(RoundedCornerShape(design.cardRadius))
                                .clickable(enabled = !busy) {
                                    busy = true
                                    scope.launch {
                                        Api.addToPlaylist(playlist.id, track.id).fold(
                                            onSuccess = {
                                                Toast.makeText(context, "Added to ${playlist.name}", Toast.LENGTH_SHORT).show()
                                                picker = false
                                            },
                                            onFailure = {
                                                Toast.makeText(context, it.message ?: "Could not add track", Toast.LENGTH_SHORT).show()
                                            },
                                        )
                                        busy = false
                                    }
                                }
                                .padding(horizontal = 10.dp, vertical = 11.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            LucideIcon(Lucide.ListMusic, LocalDesign.current.accent, size = 16.dp)
                            Text(playlist.name, color = LocalDesign.current.fg, fontSize = 13.sp)
                        }
                    }
                }
                GhostButton("Close") { picker = false }
            }
        }
    }

    if (showInfo) {
        AlertDialog(
            onDismissRequest = { showInfo = false },
            title = { Text("Track info") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    listOf(
                        "Title" to track.title,
                        "Artist" to track.artist.ifBlank { "Unknown artist" },
                        "Album" to track.album.ifBlank { "Unknown album" },
                        "Duration" to formatDuration(track.duration),
                        "Explicit" to if (track.explicit) "Yes" else "No",
                        "Track ID" to track.id.toString(),
                    ).forEach { (label, value) ->
                        Column(verticalArrangement = Arrangement.spacedBy(1.dp)) {
                            Text(label, color = design.dim, fontSize = 11.sp)
                            Text(value, color = design.fg, fontSize = 13.sp)
                        }
                    }
                }
            },
            confirmButton = { TextButton(onClick = { showInfo = false }) { Text("Close") } },
        )
    }
}

/** Cover + two lines, used in horizontal rows of albums/artists/playlists. */
@Composable
fun MediaCard(
    title: String,
    subtitle: String,
    coverUrl: String,
    modifier: Modifier = Modifier,
    width: Dp = 132.dp,
    round: Boolean = false,
    fill: Boolean = false,
    onClick: () -> Unit,
) {
    val design = LocalDesign.current
    val cardModifier = if (fill) modifier.fillMaxWidth() else modifier.width(width)
    Column(
        cardModifier.clip(RoundedCornerShape(design.tileRadius)).clickable { onClick() },
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Cover(
            url = coverUrl,
            shape = if (round) CircleShape else RoundedCornerShape(design.tileRadius),
            modifier = if (fill) Modifier.fillMaxWidth().aspectRatio(1f) else Modifier.size(width),
            fallback = design.accentSoft,
        )
        Text(
            title,
            color = design.fg,
            fontSize = 14.sp,
            fontWeight = FontWeight.SemiBold,
            maxLines = 2,
            overflow = TextOverflow.Ellipsis,
        )
        Text(subtitle, color = design.dim, fontSize = 12.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
    }
}

/* ── settings pieces ───────────────────────────────────────────────────── */

/** Card that groups settings rows. */
@Composable
fun SettingCard(modifier: Modifier = Modifier, content: @Composable () -> Unit) {
    Column(modifier.fillMaxWidth().mcSurface().padding(horizontal = 14.dp, vertical = 2.dp)) {
        content()
    }
}

@Composable
fun SettingRow(
    title: String,
    subtitle: String? = null,
    @DrawableRes icon: Int? = null,
    value: String? = null,
    danger: Boolean = false,
    onClick: (() -> Unit)? = null,
    trailing: (@Composable () -> Unit)? = null,
) {
    val design = LocalDesign.current
    val tint = if (danger) design.palette.error else design.fg
    Row(
        Modifier
            .fillMaxWidth()
            .then(if (onClick != null) Modifier.clickable { onClick() } else Modifier)
            .padding(vertical = 14.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(11.dp),
    ) {
        if (icon != null) {
            Box(
                Modifier.size(28.dp).clip(RoundedCornerShape(8.dp))
                    .background(if (danger) design.palette.error.copy(alpha = 0.12f) else design.accentSoft),
                Alignment.Center,
            ) {
                LucideIcon(icon, if (danger) design.palette.error else design.accentText, size = 14.dp)
            }
        }
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(1.dp)) {
            Text(
                title,
                color = tint,
                fontSize = 14.sp,
                fontWeight = FontWeight.Medium,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            if (subtitle != null) {
                Text(subtitle, color = design.dim, fontSize = 11.sp, lineHeight = 15.sp)
            }
        }
        if (value != null) {
            Text(
                value,
                color = design.dim,
                fontSize = 12.sp,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        }
        trailing?.invoke()
    }
}

@Composable
fun SettingDivider() {
    Box(Modifier.fillMaxWidth().height(1.dp).background(LocalDesign.current.hairline))
}

@Composable
fun SwitchRow(
    title: String,
    subtitle: String? = null,
    @DrawableRes icon: Int? = null,
    checked: Boolean,
    onChange: (Boolean) -> Unit,
) {
    val design = LocalDesign.current
    SettingRow(title = title, subtitle = subtitle, icon = icon) {
        Switch(
            checked = checked,
            onCheckedChange = onChange,
            colors = SwitchDefaults.colors(
                checkedThumbColor = design.onAccent,
                checkedTrackColor = design.accentText,
                uncheckedThumbColor = design.dim,
                uncheckedTrackColor = design.palette.surface2,
                uncheckedBorderColor = design.hairline,
            ),
        )
    }
}

/* ── helpers ───────────────────────────────────────────────────────────── */

fun formatDuration(seconds: Double): String {
    if (seconds <= 0) return "--:--"
    val total = seconds.toLong()
    return "%d:%02d".format(total / 60, total % 60)
}

fun formatMillis(ms: Long): String = formatDuration(ms / 1000.0)

fun formatBytes(bytes: Long): String = when {
    bytes >= 1L shl 30 -> "%.1f GB".format(bytes / (1L shl 30).toDouble())
    bytes >= 1L shl 20 -> "%.1f MB".format(bytes / (1L shl 20).toDouble())
    bytes >= 1L shl 10 -> "%.0f KB".format(bytes / 1024.0)
    else -> "$bytes B"
}

fun trackCoverUrl(id: Int): String = Api.url("/api/tracks/$id/cover")

fun emptyModifier(): Modifier = Modifier.fillMaxSize()
```

### `gui/android/app/src/main/java/dev/mcmusic/app/ui/Cover.kt`

```kotlin
package dev.mcmusic.app.ui

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.LruCache
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.dp
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.Prefs
import dev.mcmusic.app.ui.design.DynamicColour
import dev.mcmusic.app.ui.design.LocalDesign

private val cache = LruCache<String, Bitmap>(64)

private val placeholderGlyphs = listOf(
    Lucide.Circle,
    Lucide.Squircle,
    Lucide.Cookie,
    Lucide.Flower,
    Lucide.Pentagon,
)

/** A stable, varied glyph for sleeves with no artwork. Real art is never altered. */
internal fun coverPlaceholder(key: String): Int =
    placeholderGlyphs[(key.hashCode().toLong() and 0x7fff_ffffL).mod(placeholderGlyphs.size.toLong()).toInt()]

/**
 * Cover art straight from the public API. A tiny cache plus a request per URL
 * is enough here: covers are 72 px and the API sets a short max-age.
 *
 * [dynamic] is only true for the playing cover; other tiles never retint the app.
 */
@Composable
fun Cover(
    url: String,
    shape: Shape,
    modifier: Modifier = Modifier,
    fallback: Color = Color.White.copy(alpha = 0.06f),
    dynamic: Boolean = false,
) {
    val design = LocalDesign.current
    var bitmap by remember(url) { mutableStateOf(cache.get(url)) }

    LaunchedEffect(url) {
        if (bitmap == null && url.isNotBlank()) {
            val bytes = Api.cover(url) ?: return@LaunchedEffect
            BitmapFactory.decodeByteArray(bytes, 0, bytes.size)?.let {
                cache.put(url, it)
                bitmap = it
            }
        }
    }

    LaunchedEffect(url, bitmap, dynamic, Prefs.dynamicColour, Prefs.showCovers) {
        // Non-dynamic tiles must never clear a seed that the player owns, even
        // when they show the same URL in a list.
        if (!dynamic) return@LaunchedEffect
        if (!Prefs.dynamicColour || !Prefs.showCovers) {
            DynamicColour.clearCover(url)
            return@LaunchedEffect
        }
        val art = bitmap
        if (art != null) DynamicColour.setCover(art, url) else DynamicColour.clearCover(url)
    }

    Box(
        modifier
            .clip(shape)
            .background(fallback)
            .border(1.dp, design.hairline, shape),
    ) {
        if (bitmap == null) {
            BoxWithConstraints(Modifier.fillMaxSize(), Alignment.Center) {
                LucideIcon(
                    coverPlaceholder(url),
                    design.accentText,
                    size = minOf(maxWidth, maxHeight) * 0.42f,
                )
            }
        }
        bitmap?.let {
            Image(
                bitmap = it.asImageBitmap(),
                contentDescription = null,
                modifier = Modifier.fillMaxSize().clip(shape),
                contentScale = ContentScale.Crop,
            )
        }
    }
}
```

### `gui/android/app/src/main/java/dev/mcmusic/app/ui/Shell.kt`

```kotlin
package dev.mcmusic.app.ui

import androidx.activity.compose.BackHandler
import androidx.annotation.DrawableRes
import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.spring
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Account
import dev.mcmusic.app.data.Prefs
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.PlayfulMotion
import dev.mcmusic.app.ui.design.mcSurface
import dev.mcmusic.app.ui.design.playfulMotionEnabled
import dev.mcmusic.app.ui.design.rememberPlayfulHaptic
import dev.mcmusic.app.ui.screens.AdminScreen
import dev.mcmusic.app.ui.screens.DownloadsScreen
import dev.mcmusic.app.ui.screens.HomeScreen
import dev.mcmusic.app.ui.screens.LikesScreen
import dev.mcmusic.app.ui.screens.LibraryScreen
import dev.mcmusic.app.ui.screens.PlaylistsScreen
import dev.mcmusic.app.ui.screens.PlayerScreen
import dev.mcmusic.app.ui.screens.SearchScreen
import dev.mcmusic.app.ui.screens.AuthSplash
import dev.mcmusic.app.ui.screens.SignInScreen
import dev.mcmusic.app.ui.screens.SettingsScreen
import dev.mcmusic.app.ui.screens.VideosScreen

enum class Tab(val label: String, @param:DrawableRes val icon: Int) {
    Home("Home", Lucide.House),
    Search("Search", Lucide.Search),
    Library("Library", Lucide.Library),
    Downloads("Downloads", Lucide.Download),
    Videos("Videos", Lucide.Film),
    Settings("Settings", Lucide.Settings),
    Playlists("Playlists", Lucide.ListMusic),
    Likes("Likes", Lucide.Heart),
    Player("Player", Lucide.Play),
    Admin("Admin", Lucide.User);

    val inBar: Boolean get() = this in listOf(Home, Search, Library, Downloads, Settings)
    val fullScreen: Boolean get() = this == Player || this == Admin || this == Likes || this == Videos
}

/** Brand mark plus account, kept above the scroll area like the site header. */
@Composable
private fun TopBar(onAccount: () -> Unit) {
    val design = LocalDesign.current
    val me = Account.me
    Row(
        Modifier
            .fillMaxWidth()
            .statusBarsPadding()
            .padding(start = 18.dp, end = 12.dp, top = 10.dp, bottom = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Box(
            Modifier.size(34.dp).clip(CircleShape).background(design.accent),
            Alignment.Center,
        ) {
            Text("m", color = design.onAccent, fontSize = 18.sp, fontWeight = FontWeight.Black)
        }
        Column(verticalArrangement = Arrangement.spacedBy(1.dp)) {
            Text("mcmusic", color = design.fg, fontSize = 16.sp, fontWeight = FontWeight.Bold)
            Text(
                Account.status ?: "your room, your rules",
                color = if (Account.status != null) design.accentText else design.dim,
                fontSize = 10.sp,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        }
        Box(Modifier.weight(1f))
        Box(
            Modifier
                .clip(RoundedCornerShape(50))
                .background(design.accentWash)
                .clickable { onAccount() }
                .padding(horizontal = 10.dp, vertical = 6.dp),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                if (me != null) "@${me.username}" else "Sign in",
                color = design.accentText,
                fontSize = 11.sp,
                fontWeight = FontWeight.SemiBold,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        }
    }
}

/** Floating now-playing card: artwork, title, transport and a hairline progress. */
@Composable
private fun MiniPlayer(onOpen: () -> Unit) {
    val state = Playback.state
    val track = state.track ?: return
    val design = LocalDesign.current
    val fraction = if (state.duration > 0) {
        (state.position.toFloat() / state.duration).coerceIn(0f, 1f)
    } else 0f
    val shape = RoundedCornerShape(design.cardRadius)
    val haptic = rememberPlayfulHaptic()
    Column(
        Modifier
            .fillMaxWidth()
            .padding(horizontal = 12.dp, vertical = 6.dp)
            .mcSurface(shape),
    ) {
        Row(
            Modifier
                .fillMaxWidth()
                .clickable {
                    haptic(PlayfulMotion.CLICK)
                    onOpen()
                }
                .padding(start = 8.dp, end = 8.dp, top = 8.dp, bottom = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(11.dp),
        ) {
            TrackCover(track, 48.dp, 20.dp, dynamic = true)
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Text(
                    track.title,
                    color = design.fg,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.SemiBold,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                Text(
                    if (state.buffering) "buffering…" else track.artist.ifBlank { "unknown artist" },
                    color = design.dim,
                    fontSize = 11.sp,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }
            IconButton(Lucide.SkipForward, size = 18.dp) { Playback.next() }
            PlayPauseButton(state.playing, size = 44.dp) { Playback.toggle() }
        }
        PlayfulProgress(fraction, state.playing, Modifier.fillMaxWidth())
    }
}

/** Flat tab dock, grouped into one pill. */
@Composable
private fun BottomBar(tab: Tab, onTab: (Tab) -> Unit) {
    val design = LocalDesign.current
    val haptic = rememberPlayfulHaptic()
    Row(
        Modifier
            .fillMaxWidth()
            .navigationBarsPadding()
            .padding(horizontal = 12.dp, vertical = 8.dp)
            .mcSurface(RoundedCornerShape(design.cardRadius))
            .padding(horizontal = 6.dp, vertical = 6.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Tab.entries.filter { it.inBar }.forEach { entry ->
            val selected = entry == tab
            Column(
                Modifier
                    .weight(1f)
                    .clip(RoundedCornerShape(design.cardRadius))
                    .background(if (selected) design.accentSoft else Color.Transparent)
                    .clickable {
                        haptic(PlayfulMotion.KEY)
                        onTab(entry)
                    }
                    .padding(vertical = 12.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(3.dp),
            ) {
                LucideIcon(
                    entry.icon,
                    if (selected) design.accentText else design.dim,
                    size = 20.dp,
                )
                Text(
                    entry.label,
                    color = if (selected) design.accentText else design.dim,
                    fontSize = 10.sp,
                    fontWeight = if (selected) FontWeight.SemiBold else FontWeight.Medium,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }
        }
    }
}

@Composable
private fun TabContent(
    tab: Tab,
    onTab: (Tab) -> Unit,
    onPlaylist: (Int) -> Unit,
    playlistId: Int?,
    videoId: String?,
    videoStartMs: Long,
    onBack: () -> Unit,
    onVideo: (String?, Long) -> Unit,
    onVideoClosed: (Long?) -> Unit,
) {
    val motion = playfulMotionEnabled()
    val appear = remember(tab, motion) { Animatable(if (motion) 0f else 1f) }
    LaunchedEffect(tab, motion) {
        if (motion) {
            appear.animateTo(
                1f,
                spring(
                    dampingRatio = PlayfulMotion.DAMPING_RATIO,
                    stiffness = PlayfulMotion.STIFFNESS,
                ),
            )
        } else {
            appear.snapTo(1f)
        }
    }
    Box(
        Modifier
            .fillMaxSize()
            .graphicsLayer {
                alpha = appear.value
                translationY = (1f - appear.value) * 12.dp.toPx()
            },
    ) {
        when (tab) {
            Tab.Home -> HomeScreen(onOpenSearch = { onTab(Tab.Search) }, onOpenPlayer = { onTab(Tab.Player) })
            Tab.Search -> SearchScreen(onPlaylist = onPlaylist, onOpenPlayer = { onTab(Tab.Player) })
            Tab.Library -> LibraryScreen(
                onOpenPlaylist = onPlaylist,
                onOpenLikes = { onTab(Tab.Likes) },
                onOpenPlayer = { onTab(Tab.Player) },
            )
            Tab.Likes -> LikesScreen(onBack = onBack, onOpenPlayer = { onTab(Tab.Player) })
            Tab.Playlists -> PlaylistsScreen(
                playlistId = playlistId,
                onOpenPlaylist = onPlaylist,
                onOpenPlayer = { onTab(Tab.Player) },
                onBack = onBack,
            )
            Tab.Downloads -> DownloadsScreen(
                onOpenPlayer = { onTab(Tab.Player) },
                onOpenVideos = { onVideo(null, 0L) },
            )
            Tab.Settings -> SettingsScreen(onAdmin = { onTab(Tab.Admin) }, onSignedOut = { onTab(Tab.Home) })
            Tab.Player -> PlayerScreen(onBack = onBack, onVideo = onVideo)
            Tab.Videos -> VideosScreen(
                ytId = videoId,
                startMs = videoStartMs,
                onBack = onBack,
                onPlay = { id, start -> onVideo(id, start) },
                onClosed = onVideoClosed,
            )
            Tab.Admin -> AdminScreen(onBack = onBack)
        }
    }
}

/**
 * App shell: brand header, current page, floating player and tab dock. The
 * player and admin pages take over the screen and return to where they opened.
 */
@Composable
fun McShell() {
    // Verify the saved token before any screen can render. A cold start shows
    // a short splash; a missing or rejected token shows only the sign-in gate.
    LaunchedEffect(Unit) { Account.refresh() }
    if (!Account.loaded) {
        AuthSplash()
        return
    }
    if (!Account.signedIn) {
        SignInScreen()
        return
    }

    var tab by rememberSaveable { mutableStateOf(Tab.Home) }
    var previous by rememberSaveable { mutableStateOf(Tab.Home) }
    var playlistId by rememberSaveable { mutableStateOf<Int?>(null) }
    var videoId by rememberSaveable { mutableStateOf<String?>(null) }
    var videoStartMs by rememberSaveable { mutableStateOf(0L) }

    LaunchedEffect(Account.isAdmin) {
        if (!Account.isAdmin && tab == Tab.Admin) tab = Tab.Home
    }

    val open: (Tab) -> Unit = { next ->
        if (next != tab) previous = tab
        tab = next
    }

    // A detail pane is one level deep: Back closes it before leaving Playlists.
    val back: () -> Unit = {
        if (playlistId != null) {
            playlistId = null
        } else if (tab.fullScreen) {
            tab = previous
        } else {
            tab = Tab.Home
        }
    }
    BackHandler(enabled = tab.fullScreen || playlistId != null, onBack = back)

    val openPlaylist: (Int) -> Unit = { id ->
        playlistId = id
        open(Tab.Playlists)
    }

    val openVideo: (String?, Long) -> Unit = { id, start ->
        if (id != null) {
            videoStartMs = start
            videoId = id
            tab = Tab.Videos
        }
    }
    val closeVideo: (Long?) -> Unit = { _ ->
        videoId = null
        videoStartMs = 0L
        back()
    }

    Box(Modifier.fillMaxSize()) {
        if (tab.fullScreen) {
            Box(Modifier.fillMaxSize().statusBarsPadding().navigationBarsPadding()) {
                TabContent(
                    tab = tab,
                    onTab = open,
                    onPlaylist = openPlaylist,
                    playlistId = playlistId,
                    videoId = videoId,
                    videoStartMs = videoStartMs,
                    onBack = if (videoId != null) { { closeVideo(null) } } else back,
                    onVideo = openVideo,
                    onVideoClosed = closeVideo,
                )
            }
        } else {
            Column(Modifier.fillMaxSize()) {
                TopBar(onAccount = { open(Tab.Settings) })
                Box(Modifier.weight(1f)) {
                    TabContent(
                        tab = tab,
                        onTab = open,
                        onPlaylist = openPlaylist,
                        playlistId = playlistId,
                        videoId = videoId,
                        videoStartMs = videoStartMs,
                        onBack = if (videoId != null) { { closeVideo(null) } } else back,
                        onVideo = openVideo,
                        onVideoClosed = closeVideo,
                    )
                }
                MiniPlayer(onOpen = { open(Tab.Player) })
                BottomBar(tab = tab, onTab = open)
            }
        }
    }
}
```

### `gui/android/app/src/main/java/dev/mcmusic/app/ui/design/Design.kt`

```kotlin
package dev.mcmusic.app.ui.design

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.compositionLocalOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Prefs

/**
 * Material 3 shape, type and colour roles with Lucide as the only icon source.
 *
 * Five palette families come from the supplied swatch sheet. Each family has a
 * light variant from the top half of the sheet and a dark variant from the
 * bottom half, so "System" follows the device appearance without a second
 * settings control. Replace the token values here when colours change again.
 */
enum class DesignLanguage(val id: String, val label: String, val blurb: String) {
    Flufi("flufi", "Flufi", "Material 3 surfaces, one Lucide icon language");

    companion object {
        fun from(id: String?): DesignLanguage = Flufi
    }
}

/** Concrete Material 3 token set for one light or dark variant. */
@Immutable
data class McPalette(
    val id: String,
    val label: String,
    val bg: Color,
    val bg2: Color,
    val surface: Color,
    val surface2: Color,
    val fg: Color,
    val dim: Color,
    val dim2: Color,
    val line: Color,
    val line2: Color,
    val accent: Color,
    /** Accent shade used as text/icon on surfaces; bright accents stay fills. */
    val accentText: Color,
    val accentFg: Color,
    val dark: Boolean,
    // Generated Material 3 tonal roles (HCT from this family's accent seed).
    val primary: Color, val onPrimary: Color,
    val primaryContainer: Color, val onPrimaryContainer: Color,
    val secondary: Color, val onSecondary: Color,
    val secondaryContainer: Color, val onSecondaryContainer: Color,
    val tertiary: Color, val onTertiary: Color,
    val tertiaryContainer: Color, val onTertiaryContainer: Color,
    val error: Color, val onError: Color,
    val errorContainer: Color, val onErrorContainer: Color,
    val background: Color, val onBackground: Color, val onSurface: Color,
    val surfaceVariant: Color, val onSurfaceVariant: Color,
    val surfaceContainerLowest: Color, val surfaceContainerLow: Color,
    val surfaceContainer: Color, val surfaceContainerHigh: Color,
    val surfaceContainerHighest: Color,
    val outline: Color, val outlineVariant: Color,
    val inverseSurface: Color, val inverseOnSurface: Color,
    val inversePrimary: Color, val scrim: Color, val shadow: Color,
)

/** One family = one light variant + one dark variant from the same hues. */
@Immutable
data class PaletteFamily(
    val id: String,
    val label: String,
    val light: McPalette,
    val dark: McPalette,
) {
    fun resolve(systemDark: Boolean): McPalette = if (systemDark) dark else light
}

// BEGIN GENERATED PALETTES
object Palettes {
    private fun color(hex: String) = Color(android.graphics.Color.parseColor("#$hex"))

    private fun variant(
        family: String, label: String, dark: Boolean,
        bg: String, bg2: String, surface: String, surface2: String,
        fg: String, dim: String, dim2: String, line: String, line2: String,
        accent: String, accentText: String, accentFg: String,
    primary: String,
    onPrimary: String,
    primaryContainer: String,
    onPrimaryContainer: String,
    secondary: String,
    onSecondary: String,
    secondaryContainer: String,
    onSecondaryContainer: String,
    tertiary: String,
    onTertiary: String,
    tertiaryContainer: String,
    onTertiaryContainer: String,
    error: String,
    onError: String,
    errorContainer: String,
    onErrorContainer: String,
    background: String,
    onBackground: String,
    onSurface: String,
    surfaceVariant: String,
    onSurfaceVariant: String,
    surfaceContainerLowest: String,
    surfaceContainerLow: String,
    surfaceContainer: String,
    surfaceContainerHigh: String,
    surfaceContainerHighest: String,
    outline: String,
    outlineVariant: String,
    inverseSurface: String,
    inverseOnSurface: String,
    inversePrimary: String,
    scrim: String,
    shadow: String,
    ) = McPalette(
        id = "$family-" + (if (dark) "dark" else "light"),
        label = label, dark = dark,
        bg = color(bg), bg2 = color(bg2), surface = color(surface), surface2 = color(surface2),
        fg = color(fg), dim = color(dim), dim2 = color(dim2), line = color(line), line2 = color(line2),
        accent = color(accent), accentText = color(accentText), accentFg = color(accentFg),
        primary = color(primary),
        onPrimary = color(onPrimary),
        primaryContainer = color(primaryContainer),
        onPrimaryContainer = color(onPrimaryContainer),
        secondary = color(secondary),
        onSecondary = color(onSecondary),
        secondaryContainer = color(secondaryContainer),
        onSecondaryContainer = color(onSecondaryContainer),
        tertiary = color(tertiary),
        onTertiary = color(onTertiary),
        tertiaryContainer = color(tertiaryContainer),
        onTertiaryContainer = color(onTertiaryContainer),
        error = color(error),
        onError = color(onError),
        errorContainer = color(errorContainer),
        onErrorContainer = color(onErrorContainer),
        background = color(background),
        onBackground = color(onBackground),
        onSurface = color(onSurface),
        surfaceVariant = color(surfaceVariant),
        onSurfaceVariant = color(onSurfaceVariant),
        surfaceContainerLowest = color(surfaceContainerLowest),
        surfaceContainerLow = color(surfaceContainerLow),
        surfaceContainer = color(surfaceContainer),
        surfaceContainerHigh = color(surfaceContainerHigh),
        surfaceContainerHighest = color(surfaceContainerHighest),
        outline = color(outline),
        outlineVariant = color(outlineVariant),
        inverseSurface = color(inverseSurface),
        inverseOnSurface = color(inverseOnSurface),
        inversePrimary = color(inversePrimary),
        scrim = color(scrim),
        shadow = color(shadow),
    )

    val violet = PaletteFamily(
        id = "violet",
        label = "Violet",
        light = variant("violet", "Violet", false, bg = "F5F2FF", bg2 = "EDE7FF", surface = "FFFFFF", surface2 = "F7F4FF", fg = "08060D", dim = "473872", dim2 = "6A54AA", line = "DACDFF", line2 = "CAB8FF", accent = "9F7EFF", accentText = "5B3F9E", accentFg = "08060D", primary = "64558F", onPrimary = "FFFFFF", primaryContainer = "E8DDFF", onPrimaryContainer = "4C3E76", secondary = "615B71", onSecondary = "FFFFFF", secondaryContainer = "E8DEF8", onSecondaryContainer = "494458", tertiary = "7D5261", onTertiary = "FFFFFF", tertiaryContainer = "FFD9E3", onTertiaryContainer = "633B49", error = "BA1A1A", onError = "FFFFFF", errorContainer = "FFDAD6", onErrorContainer = "93000A", background = "FFFBFF", onBackground = "1D1927", onSurface = "1D1927", surfaceVariant = "E7DFF3", onSurfaceVariant = "494454", surfaceContainerLowest = "FFFBFF", surfaceContainerLow = "F8F1FF", surfaceContainer = "F3EAFE", surfaceContainerHigh = "EDE5F9", surfaceContainerHighest = "E7DFF3", outline = "79757F", outlineVariant = "878192", inverseSurface = "322E3D", inverseOnSurface = "F5EEFF", inversePrimary = "CEBDFE", scrim = "000000", shadow = "000000"),
        dark = variant("violet", "Violet", true, bg = "171721", bg2 = "222130", surface = "2A293C", surface2 = "444361", fg = "FFFFFF", dim = "AAAAB7", dim2 = "8B8A9D", line = "35344B", line2 = "605F78", accent = "9F7EFF", accentText = "C6B2FF", accentFg = "08060D", primary = "CEBDFE", onPrimary = "35275D", primaryContainer = "4C3E76", onPrimaryContainer = "E8DDFF", secondary = "CBC3DC", onSecondary = "332E41", secondaryContainer = "494458", onSecondaryContainer = "E8DEF8", tertiary = "EFB8C9", onTertiary = "492533", tertiaryContainer = "633B49", onTertiaryContainer = "FFD9E3", error = "FFB4AB", onError = "690005", errorContainer = "93000A", onErrorContainer = "FFDAD6", background = "15111F", onBackground = "F5EEFF", onSurface = "F5EEFF", surfaceVariant = "3B3746", onSurfaceVariant = "CBC3D6", surfaceContainerLowest = "0F0C19", surfaceContainerLow = "1D1927", surfaceContainer = "211E2B", surfaceContainerHigh = "2C2836", surfaceContainerHighest = "373341", outline = "938F99", outlineVariant = "878192", inverseSurface = "F5EEFF", inverseOnSurface = "322E3D", inversePrimary = "64558F", scrim = "000000", shadow = "000000"),
    )

    val indigo = PaletteFamily(
        id = "indigo",
        label = "Indigo",
        light = variant("indigo", "Indigo", false, bg = "F2F4FF", bg2 = "E8EBFF", surface = "FFFFFF", surface2 = "F5F6FF", fg = "08060D", dim = "3B4172", dim2 = "5761AA", line = "CFD5FF", line2 = "BAC3FF", accent = "8293FF", accentText = "4A56A8", accentFg = "08060D", primary = "525A92", onPrimary = "FFFFFF", primaryContainer = "DEE0FF", onPrimaryContainer = "3A4379", secondary = "5B5D72", onSecondary = "FFFFFF", secondaryContainer = "E0E1F9", onSecondaryContainer = "434559", tertiary = "77536D", onTertiary = "FFFFFF", tertiaryContainer = "FFD7F1", onTertiaryContainer = "5D3C54", error = "BA1A1A", onError = "FFFFFF", errorContainer = "FFDAD6", onErrorContainer = "93000A", background = "FFFBFF", onBackground = "191B26", onSurface = "191B26", surfaceVariant = "E2E1F2", onSurfaceVariant = "454653", surfaceContainerLowest = "FFFBFF", surfaceContainerLow = "F4F2FF", surfaceContainer = "EDECFD", surfaceContainerHigh = "E7E7F7", surfaceContainerHighest = "E2E1F2", outline = "767680", outlineVariant = "828391", inverseSurface = "2E303C", inverseOnSurface = "F0EFFF", inversePrimary = "BBC3FF", scrim = "000000", shadow = "000000"),
        dark = variant("indigo", "Indigo", true, bg = "12171F", bg2 = "1B212D", surface = "212838", surface2 = "36425B", fg = "FFFFFF", dim = "A4A9B5", dim2 = "828999", line = "2A3346", line2 = "545E73", accent = "8293FF", accentText = "B4BEFF", accentFg = "08060D", primary = "BBC3FF", onPrimary = "232C61", primaryContainer = "3A4379", onPrimaryContainer = "DEE0FF", secondary = "C4C5DD", onSecondary = "2D2F42", secondaryContainer = "434559", onSecondaryContainer = "E0E1F9", tertiary = "E6BAD7", onTertiary = "45263D", tertiaryContainer = "5D3C54", onTertiaryContainer = "FFD7F1", error = "FFB4AB", onError = "690005", errorContainer = "93000A", onErrorContainer = "FFDAD6", background = "11131E", onBackground = "F0EFFF", onSurface = "F0EFFF", surfaceVariant = "373845", onSurfaceVariant = "C5C5D5", surfaceContainerLowest = "0C0D18", surfaceContainerLow = "191B26", surfaceContainer = "1D1F2B", surfaceContainerHigh = "282935", surfaceContainerHighest = "333440", outline = "90909A", outlineVariant = "828391", inverseSurface = "F0EFFF", inverseOnSurface = "2E303C", inversePrimary = "525A92", scrim = "000000", shadow = "000000"),
    )

    val sky = PaletteFamily(
        id = "sky",
        label = "Sky",
        light = variant("sky", "Sky", false, bg = "F1F8FE", bg2 = "E7F3FE", surface = "FFFFFF", surface2 = "F4F9FE", fg = "08060D", dim = "385272", dim2 = "527CA9", line = "CCE5FE", line2 = "B6DAFE", accent = "7BBDFE", accentText = "235F93", accentFg = "08060D", primary = "32628D", onPrimary = "FFFFFF", primaryContainer = "CFE5FF", onPrimaryContainer = "134A74", secondary = "526070", onSecondary = "FFFFFF", secondaryContainer = "D6E4F7", onSecondaryContainer = "3A4857", tertiary = "695779", onTertiary = "FFFFFF", tertiaryContainer = "F0DBFF", onTertiaryContainer = "514060", error = "BA1A1A", onError = "FFFFFF", errorContainer = "FFDAD6", onErrorContainer = "93000A", background = "FCFCFF", onBackground = "161C23", onSurface = "161C23", surfaceVariant = "DDE3ED", onSurfaceVariant = "41474F", surfaceContainerLowest = "FCFCFF", surfaceContainerLow = "EEF4FE", surfaceContainer = "E9EEF8", surfaceContainerHigh = "E3E8F2", surfaceContainerHighest = "DDE3ED", outline = "73777F", outlineVariant = "7E848D", inverseSurface = "2B3138", inverseOnSurface = "ECF1FB", inversePrimary = "9DCBFC", scrim = "000000", shadow = "000000"),
        dark = variant("sky", "Sky", true, bg = "182127", bg2 = "222F39", surface = "2A3A46", surface2 = "455F72", fg = "FFFFFF", dim = "ABB7BF", dim2 = "8B9BA7", line = "354A58", line2 = "607787", accent = "7BBDFE", accentText = "A9D5FF", accentFg = "08060D", primary = "9DCBFC", onPrimary = "003355", primaryContainer = "134A74", onPrimaryContainer = "CFE5FF", secondary = "BAC8DA", onSecondary = "243240", secondaryContainer = "3A4857", onSecondaryContainer = "D6E4F7", tertiary = "D4BEE6", onTertiary = "392A49", tertiaryContainer = "514060", onTertiaryContainer = "F0DBFF", error = "FFB4AB", onError = "690005", errorContainer = "93000A", onErrorContainer = "FFDAD6", background = "0E141B", onBackground = "ECF1FB", onSurface = "ECF1FB", surfaceVariant = "343A41", onSurfaceVariant = "C1C7D0", surfaceContainerLowest = "090F15", surfaceContainerLow = "161C23", surfaceContainer = "1A2027", surfaceContainerHigh = "242A32", surfaceContainerHighest = "2F353D", outline = "8C9199", outlineVariant = "7E848D", inverseSurface = "ECF1FB", inverseOnSurface = "2B3138", inversePrimary = "32628D", scrim = "000000", shadow = "000000"),
    )

    val aqua = PaletteFamily(
        id = "aqua",
        label = "Aqua",
        light = variant("aqua", "Aqua", false, bg = "F1FBFC", bg2 = "E7F9FA", surface = "FFFFFF", surface2 = "F4FCFD", fg = "08060D", dim = "386168", dim2 = "53939A", line = "CDF3F5", line2 = "B6EDF1", accent = "7CE0E6", accentText = "126F77", accentFg = "08060D", primary = "00696E", onPrimary = "FFFFFF", primaryContainer = "9CF0F6", onPrimaryContainer = "004F53", secondary = "4A6364", onSecondary = "FFFFFF", secondaryContainer = "CCE8E9", onSecondaryContainer = "324B4C", tertiary = "4E5F7D", onTertiary = "FFFFFF", tertiaryContainer = "D6E3FF", onTertiaryContainer = "364764", error = "BA1A1A", onError = "FFFFFF", errorContainer = "FFDAD6", onErrorContainer = "93000A", background = "F4FEFE", onBackground = "141D1E", onSurface = "141D1E", surfaceVariant = "DAE4E5", onSurfaceVariant = "3F4949", surfaceContainerLowest = "F4FEFE", surfaceContainerLow = "EBF6F6", surfaceContainer = "E6F0F0", surfaceContainerHigh = "E0EAEA", surfaceContainerHighest = "DAE4E5", outline = "6F7979", outlineVariant = "7C8686", inverseSurface = "293233", inverseOnSurface = "E9F3F3", inversePrimary = "80D4D9", scrim = "000000", shadow = "000000"),
        dark = variant("aqua", "Aqua", true, bg = "15241C", bg2 = "1F3328", surface = "263F32", surface2 = "3E6751", fg = "FFFFFF", dim = "A8BAB0", dim2 = "87A093", line = "30503F", line2 = "5A7D6B", accent = "7CE0E6", accentText = "A6EFF3", accentFg = "08060D", primary = "80D4D9", onPrimary = "003739", primaryContainer = "004F53", onPrimaryContainer = "9CF0F6", secondary = "B1CCCD", onSecondary = "1B3436", secondaryContainer = "324B4C", onSecondaryContainer = "CCE8E9", tertiary = "B6C7E9", onTertiary = "1F314C", tertiaryContainer = "364764", onTertiaryContainer = "D6E3FF", error = "FFB4AB", onError = "690005", errorContainer = "93000A", onErrorContainer = "FFDAD6", background = "0C1516", onBackground = "E9F3F3", onSurface = "E9F3F3", surfaceVariant = "313B3B", onSurfaceVariant = "BEC8C9", surfaceContainerLowest = "071010", surfaceContainerLow = "141D1E", surfaceContainer = "182122", surfaceContainerHigh = "222C2C", surfaceContainerHighest = "2D3637", outline = "899393", outlineVariant = "7C8686", inverseSurface = "E9F3F3", inverseOnSurface = "293233", inversePrimary = "00696E", scrim = "000000", shadow = "000000"),
    )

    val mint = PaletteFamily(
        id = "mint",
        label = "Mint",
        light = variant("mint", "Mint", false, bg = "F1FFF5", bg2 = "E7FFEE", surface = "FFFFFF", surface2 = "F4FFF7", fg = "08060D", dim = "386E4C", dim2 = "52A76F", line = "CCFFDC", line2 = "B6FFCC", accent = "7BFFA4", accentText = "216A43", accentFg = "08060D", primary = "316A42", onPrimary = "FFFFFF", primaryContainer = "B3F1BF", onPrimaryContainer = "16512C", secondary = "506352", onSecondary = "FFFFFF", secondaryContainer = "D2E8D3", onSecondaryContainer = "394B3C", tertiary = "3A656E", onTertiary = "FFFFFF", tertiaryContainer = "BDEAF5", onTertiaryContainer = "204D56", error = "BA1A1A", onError = "FFFFFF", errorContainer = "FFDAD6", onErrorContainer = "93000A", background = "F5FFF3", onBackground = "121E14", onSurface = "121E14", surfaceVariant = "D7E7D6", onSurfaceVariant = "3C4A3E", surfaceContainerLowest = "F5FFF3", surfaceContainerLow = "E8F8E7", surfaceContainer = "E3F2E1", surfaceContainerHigh = "DDECDC", surfaceContainerHighest = "D7E7D6", outline = "717971", outlineVariant = "798879", inverseSurface = "263428", inverseOnSurface = "E5F5E4", inversePrimary = "98D5A4", scrim = "000000", shadow = "000000"),
        dark = variant("mint", "Mint", true, bg = "15241A", bg2 = "1F3425", surface = "26412E", surface2 = "3E694B", fg = "FFFFFF", dim = "A8BBAE", dim2 = "87A28F", line = "30513A", line2 = "5A7F66", accent = "7BFFA4", accentText = "A9FFC2", accentFg = "08060D", primary = "98D5A4", onPrimary = "00391A", primaryContainer = "16512C", onPrimaryContainer = "B3F1BF", secondary = "B7CCB7", onSecondary = "223526", secondaryContainer = "394B3C", onSecondaryContainer = "D2E8D3", tertiary = "A2CED9", onTertiary = "01363F", tertiaryContainer = "204D56", onTertiaryContainer = "BDEAF5", error = "FFB4AB", onError = "690005", errorContainer = "93000A", onErrorContainer = "FFDAD6", background = "0A160D", onBackground = "E5F5E4", onSurface = "E5F5E4", surfaceVariant = "2F3C31", onSurfaceVariant = "BBCBBB", surfaceContainerLowest = "051108", surfaceContainerLow = "121E14", surfaceContainer = "162218", surfaceContainerHigh = "202D22", surfaceContainerHighest = "2B382D", outline = "8B938A", outlineVariant = "798879", inverseSurface = "E5F5E4", inverseOnSurface = "263428", inversePrimary = "316A42", scrim = "000000", shadow = "000000"),
    )

    /** Exactly five chooser entries; each adapts to system light/dark. */
    val families = listOf(violet, indigo, sky, aqua, mint)

    private val byConcreteId: Map<String, McPalette> = families.flatMap { listOf(it.light, it.dark) }
        .associateBy { it.id }

    private val byFamilyId: Map<String, PaletteFamily> = families.associateBy { it.id }

    const val AUTO = "auto"

    /** Legacy ids keep the light/dark half they used to imply. */
    private val aliases = mapOf(
        "auto" to AUTO,
        "system" to AUTO,
        "flufi" to "violet-dark",
        "dark" to "violet-dark",
        "dusk" to "violet-dark",
        "paper" to "violet-light",
        "light" to "violet-light",
        "ink" to "indigo-dark",
        "amoled" to "indigo-dark",
        "midnight" to "sky-dark",
        "tide" to "aqua-dark",
        "forest" to "mint-dark",
        "rose" to "violet-dark",
        "copper" to "violet-dark",
        "mocha" to "violet-dark",
    )

    private fun canonicalID(id: String?): String {
        val key = (id ?: AUTO).lowercase().trim()
        return aliases[key] ?: key
    }

    /** `auto`, `system`, empty and bare family ids follow system appearance. */
    fun resolve(id: String?, systemDark: Boolean): McPalette {
        val key = canonicalID(id)
        return byConcreteId[key]
            ?: byFamilyId[key]?.resolve(systemDark)
            ?: violet.resolve(systemDark)
    }
}
// END GENERATED PALETTES

/**
 * Radii, sizes and surface treatment shared by every screen. Keeping these in
 * one place is what makes the app read as one product instead of ten pages.
 */
@Immutable
class McDesign(
    val language: DesignLanguage,
    val palette: McPalette,
) {
    /** Retained so older call sites still compile. */
    val ios: Boolean get() = false

    // 4.2.0 shape scale: 4/8/12/16/28/36 + pill. Large, friendly corners
    // are structural, not decoration; covers stay inside the 20-28 range.
    val cardRadius = 28.dp
    val tileRadius = 28.dp
    val heroRadius = 36.dp
    val coverRadius = 28.dp
    val chipRadius = 50
    val screenPadding = 16.dp
    val gap = 12.dp
    val touchTarget = 48.dp

    val displaySize = 36.sp
    val headlineSize = 28.sp
    val titleSize = 22.sp
    val titleWeight = FontWeight.Bold
    val sectionSize = 12.sp
    val sectionWeight = FontWeight.SemiBold

    val fg = palette.fg
    val dim = palette.dim
    val accent = palette.accent
    val accentText = palette.accentText
    val onAccent = palette.accentFg

    /** Translucent accent layers for chips, covers and flat tonal containers. */
    val accentSoft = palette.accent.copy(alpha = if (palette.dark) 0.18f else 0.12f)
    val accentWash = palette.accent.copy(alpha = if (palette.dark) 0.09f else 0.06f)
    val hairline = palette.line

    /** Material 3 surface container: a calm fill with a tonal edge. */
    val cardFill = palette.surfaceContainerLow
}

val LocalDesign = compositionLocalOf { McDesign(DesignLanguage.Flufi, Palettes.violet.dark) }

/** Flat tonal stage: one calm palette colour behind every screen. */
@Composable
private fun Stage(modifier: Modifier, design: McDesign) {
    Box(modifier.background(design.palette.bg))
}

private val McTypography = Typography(
    displayLarge = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Bold, fontSize = 36.sp, lineHeight = 44.sp),
    displayMedium = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Bold, fontSize = 28.sp, lineHeight = 36.sp),
    displaySmall = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.SemiBold, fontSize = 24.sp, lineHeight = 32.sp),
    headlineLarge = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Bold, fontSize = 28.sp, lineHeight = 36.sp),
    headlineMedium = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.SemiBold, fontSize = 24.sp, lineHeight = 32.sp),
    headlineSmall = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.SemiBold, fontSize = 22.sp, lineHeight = 28.sp),
    titleLarge = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Bold, fontSize = 22.sp, lineHeight = 28.sp),
    titleMedium = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.SemiBold, fontSize = 16.sp, lineHeight = 24.sp),
    titleSmall = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.SemiBold, fontSize = 14.sp, lineHeight = 20.sp),
    bodyLarge = TextStyle(fontFamily = FontFamily.Default, fontSize = 16.sp, lineHeight = 24.sp),
    bodyMedium = TextStyle(fontFamily = FontFamily.Default, fontSize = 14.sp, lineHeight = 20.sp),
    bodySmall = TextStyle(fontFamily = FontFamily.Default, fontSize = 12.sp, lineHeight = 16.sp),
    labelLarge = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.SemiBold, fontSize = 14.sp, lineHeight = 20.sp),
    labelMedium = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.SemiBold, fontSize = 12.sp, lineHeight = 16.sp),
    labelSmall = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Medium, fontSize = 11.sp, lineHeight = 16.sp),
)

/**
 * Provides the resolved palette and a complete Material 3 scheme so dialogs,
 * switches and text fields inherit the same colours as hand-painted screens.
 */
@Composable
fun McTheme(
    paletteId: String = Palettes.AUTO,
    language: DesignLanguage = DesignLanguage.Flufi,
    content: @Composable () -> Unit,
) {
    val systemDark = isSystemInDarkTheme()
    val coverSeed = DynamicColour.coverSeed
    val wallpaperSeed = DynamicColour.wallpaperSeed
    val followCover = Prefs.dynamicColour
    val palette = remember(paletteId, systemDark, coverSeed, wallpaperSeed, followCover) {
        DynamicColour.resolve(paletteId, systemDark)
    }
    val design = remember(palette, language) { McDesign(language, palette) }
    val scheme = if (palette.dark) {
        darkColorScheme(
            primary = palette.primary,
            onPrimary = palette.onPrimary,
            primaryContainer = palette.primaryContainer,
            onPrimaryContainer = palette.onPrimaryContainer,
            secondary = palette.secondary,
            onSecondary = palette.onSecondary,
            secondaryContainer = palette.secondaryContainer,
            onSecondaryContainer = palette.onSecondaryContainer,
            tertiary = palette.tertiary,
            onTertiary = palette.onTertiary,
            tertiaryContainer = palette.tertiaryContainer,
            onTertiaryContainer = palette.onTertiaryContainer,
            error = palette.error,
            onError = palette.onError,
            errorContainer = palette.errorContainer,
            onErrorContainer = palette.onErrorContainer,
            background = palette.background,
            onBackground = palette.onBackground,
            surface = palette.surfaceContainerLow,
            onSurface = palette.onSurface,
            surfaceVariant = palette.surfaceVariant,
            onSurfaceVariant = palette.onSurfaceVariant,
            surfaceTint = palette.primary,
            outline = palette.outline,
            outlineVariant = palette.outlineVariant,
            inverseSurface = palette.inverseSurface,
            inverseOnSurface = palette.inverseOnSurface,
            inversePrimary = palette.inversePrimary,
            scrim = palette.scrim,
        )
    } else {
        lightColorScheme(
            primary = palette.primary,
            onPrimary = palette.onPrimary,
            primaryContainer = palette.primaryContainer,
            onPrimaryContainer = palette.onPrimaryContainer,
            secondary = palette.secondary,
            onSecondary = palette.onSecondary,
            secondaryContainer = palette.secondaryContainer,
            onSecondaryContainer = palette.onSecondaryContainer,
            tertiary = palette.tertiary,
            onTertiary = palette.onTertiary,
            tertiaryContainer = palette.tertiaryContainer,
            onTertiaryContainer = palette.onTertiaryContainer,
            error = palette.error,
            onError = palette.onError,
            errorContainer = palette.errorContainer,
            onErrorContainer = palette.onErrorContainer,
            background = palette.background,
            onBackground = palette.onBackground,
            surface = palette.surfaceContainerLow,
            onSurface = palette.onSurface,
            surfaceVariant = palette.surfaceVariant,
            onSurfaceVariant = palette.onSurfaceVariant,
            surfaceTint = palette.primary,
            outline = palette.outline,
            outlineVariant = palette.outlineVariant,
            inverseSurface = palette.inverseSurface,
            inverseOnSurface = palette.inverseOnSurface,
            inversePrimary = palette.inversePrimary,
            scrim = palette.scrim,
        )
    }
    CompositionLocalProvider(LocalDesign provides design) {
        MaterialTheme(colorScheme = scheme, typography = McTypography) {
            Box(Modifier.fillMaxSize()) {
                Stage(Modifier.fillMaxSize(), design)
                content()
            }
        }
    }
}

/** Flat Material 3 surface container: a solid tonal fill and one hairline edge.
 *  One helper keeps every card on the same scale. */
@Composable
fun Modifier.mcSurface(
    shape: Shape = RoundedCornerShape(LocalDesign.current.cardRadius),
    tint: Color = Color.Transparent,
): Modifier {
    val design = LocalDesign.current
    val fill = if (tint == Color.Transparent) design.cardFill else tint
    return clip(shape)
        .background(fill, shape)
        .border(1.dp, design.hairline, shape)
}

/** Reads the saved language; every value maps to the single flufi language. */
fun currentDesignLanguage(): DesignLanguage = DesignLanguage.from(null)
```

### `gui/android/app/src/main/java/dev/mcmusic/app/ui/design/DynamicColour.kt`

```kotlin
package dev.mcmusic.app.ui.design

import android.app.WallpaperColors
import android.app.WallpaperManager
import android.content.Context
import android.graphics.Bitmap
import android.graphics.Color as FrameworkColor
import android.os.Build
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.graphics.Color
import com.materialkolor.hct.Hct
import com.materialkolor.scheme.SchemeTonalSpot
import dev.mcmusic.app.data.Prefs

/**
 * Runtime colour seeds for the 4.2.0 Android theme.
 *
 * The five family palettes remain the generated source of truth for stored ids
 * and legacy aliases. This layer only supplies an HCT seed: cover art and (when
 * chosen explicitly) the Android wallpaper generate a tonal-spot scheme with
 * the same 2021 spec used by the generator, and the resulting roles are layered
 * over the selected family. No bitmap is recoloured and no family id is rewritten.
 */
object DynamicColour {
    const val WALLPAPER = "wallpaper"

    private var coverKey: String? = null
    private val coverSeedState = mutableStateOf<Int?>(null)
    private val wallpaperSeedState = mutableStateOf<Int?>(null)

    val coverSeed: Int? get() = coverSeedState.value
    val wallpaperSeed: Int? get() = wallpaperSeedState.value

    /** Call from the currently playing cover only, so list tiles never retint the app. */
    fun setCover(bitmap: Bitmap, key: String) {
        val argb = dominantArgb(bitmap) ?: return
        if (coverKey == key && coverSeedState.value == argb) return
        coverKey = key
        coverSeedState.value = argb
    }

    /** A failed or missing current cover restores the selected family palette. */
    fun clearCover(key: String) {
        if (coverKey != key) return
        coverKey = null
        coverSeedState.value = null
    }

    /** Called when the playing track changes, before its replacement loads. */
    fun clearCover() {
        coverKey = null
        coverSeedState.value = null
    }

    /** Android 12+ exposes wallpaper colours as a system signal, not a network call. */
    fun refreshWallpaper(context: Context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) return
        val colors: WallpaperColors = runCatching {
            WallpaperManager.getInstance(context).getWallpaperColors(WallpaperManager.FLAG_SYSTEM)
        }.getOrNull() ?: return
        val argb = colors.primaryColor.toArgb()
        if (argb != wallpaperSeedState.value) wallpaperSeedState.value = argb
    }

    /**
     * Quantised dominant colour from a small copy of the artwork. Near-white,
     * near-black and very low-chroma pixels are ignored so a logo on a white
     * sleeve does not wash the theme out. A neutral sleeve yields no seed.
     */
    private fun dominantArgb(bitmap: Bitmap): Int? {
        if (bitmap.width <= 0 || bitmap.height <= 0) return null
        val thumb = runCatching {
            Bitmap.createScaledBitmap(bitmap, 24, 24, false)
        }.getOrNull() ?: return null
        val pixels = IntArray(thumb.width * thumb.height)
        thumb.getPixels(pixels, 0, thumb.width, 0, 0, thumb.width, thumb.height)
        if (thumb !== bitmap) thumb.recycle()

        val counts = HashMap<Int, Int>()
        var total = 0
        for (pixel in pixels) {
            if (FrameworkColor.alpha(pixel) < 200) continue
            val r = FrameworkColor.red(pixel)
            val g = FrameworkColor.green(pixel)
            val b = FrameworkColor.blue(pixel)
            val max = maxOf(r, g, b)
            val min = minOf(r, g, b)
            if (max < 36 || min > 232 || max - min < 14) continue
            val bucket = (r / 32 shl 10) or (g / 32 shl 5) or (b / 32)
            counts[bucket] = (counts[bucket] ?: 0) + 1
            total++
        }
        if (total == 0) return null

        val winner = counts.maxByOrNull { it.value }?.key ?: return null
        val r = ((winner shr 10) and 0x1f) * 8 + 4
        val g = ((winner shr 5) and 0x1f) * 8 + 4
        val b = (winner and 0x1f) * 8 + 4
        return FrameworkColor.rgb(r.coerceIn(0, 255), g.coerceIn(0, 255), b.coerceIn(0, 255))
    }

    /** Resolve the stored id, then overlay an HCT tonal scheme when a seed exists. */
    fun resolve(id: String, systemDark: Boolean): McPalette {
        val base = Palettes.resolve(if (id == WALLPAPER) Palettes.AUTO else id, systemDark)
        val seed = when {
            id == WALLPAPER -> wallpaperSeed
            Prefs.dynamicColour -> coverSeed
            else -> null
        } ?: return base

        val scheme = SchemeTonalSpot(Hct.fromInt(seed), systemDark, 0.0)
        return base.copy(
            bg = Color(scheme.background),
            bg2 = Color(scheme.surfaceContainerLow),
            surface = Color(scheme.surfaceContainerLow),
            surface2 = Color(scheme.surfaceContainerHigh),
            fg = Color(scheme.onSurface),
            dim = Color(scheme.onSurfaceVariant),
            dim2 = Color(scheme.onSurfaceVariant),
            line = Color(scheme.outlineVariant),
            line2 = Color(scheme.outline),
            accent = Color(scheme.primary),
            accentText = Color(scheme.primary),
            accentFg = Color(scheme.onPrimary),
            primary = Color(scheme.primary),
            onPrimary = Color(scheme.onPrimary),
            primaryContainer = Color(scheme.primaryContainer),
            onPrimaryContainer = Color(scheme.onPrimaryContainer),
            secondary = Color(scheme.secondary),
            onSecondary = Color(scheme.onSecondary),
            secondaryContainer = Color(scheme.secondaryContainer),
            onSecondaryContainer = Color(scheme.onSecondaryContainer),
            tertiary = Color(scheme.tertiary),
            onTertiary = Color(scheme.onTertiary),
            tertiaryContainer = Color(scheme.tertiaryContainer),
            onTertiaryContainer = Color(scheme.onTertiaryContainer),
            error = Color(scheme.error),
            onError = Color(scheme.onError),
            errorContainer = Color(scheme.errorContainer),
            onErrorContainer = Color(scheme.onErrorContainer),
            background = Color(scheme.background),
            onBackground = Color(scheme.onBackground),
            onSurface = Color(scheme.onSurface),
            surfaceVariant = Color(scheme.surfaceVariant),
            onSurfaceVariant = Color(scheme.onSurfaceVariant),
            surfaceContainerLowest = Color(scheme.surfaceContainerLowest),
            surfaceContainerLow = Color(scheme.surfaceContainerLow),
            surfaceContainer = Color(scheme.surfaceContainer),
            surfaceContainerHigh = Color(scheme.surfaceContainerHigh),
            surfaceContainerHighest = Color(scheme.surfaceContainerHighest),
            outline = Color(scheme.outline),
            outlineVariant = Color(scheme.outlineVariant),
            inverseSurface = Color(scheme.inverseSurface),
            inverseOnSurface = Color(scheme.inverseOnSurface),
            inversePrimary = Color(scheme.inversePrimary),
            scrim = Color(scheme.scrim),
        )
    }
}
```

### `gui/android/app/src/main/java/dev/mcmusic/app/ui/design/Motion.kt`

```kotlin
package dev.mcmusic.app.ui.design

import android.content.Context
import android.provider.Settings
import android.view.HapticFeedbackConstants
import android.view.View
import androidx.compose.animation.core.Spring
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import dev.mcmusic.app.data.Prefs

/** Shared 4.2.0 motion values. All are flat, short and dismissible. */
object PlayfulMotion {
    const val PRESS_SCALE = 0.96f
    const val DAMPING_RATIO = 0.7f
    val STIFFNESS = Spring.StiffnessMedium

    const val CLICK = HapticFeedbackConstants.CONTEXT_CLICK
    const val KEY = HapticFeedbackConstants.VIRTUAL_KEY
    const val LONG_PRESS = HapticFeedbackConstants.LONG_PRESS
}

/** Honour both the local switch and Android's reduced-animation system settings. */
@Composable
fun playfulMotionEnabled(): Boolean {
    val context = LocalContext.current
    val systemScale = remember(context) {
        runCatching {
            val resolver = context.contentResolver
            minOf(
                Settings.Global.getFloat(resolver, Settings.Global.ANIMATOR_DURATION_SCALE, 1f),
                Settings.Global.getFloat(resolver, Settings.Global.TRANSITION_ANIMATION_SCALE, 1f),
            )
        }.getOrDefault(1f)
    }
    return Prefs.playfulMotion && Prefs.motion && systemScale > 0f
}

/** Standard system haptics only; no custom waveform or continuous feedback. */
@Composable
fun rememberPlayfulHaptic(): (Int) -> Unit {
    val view: View = LocalView.current
    val enabled = playfulMotionEnabled()
    return remember(view, enabled) { { effect: Int ->
        if (enabled) runCatching { view.performHapticFeedback(effect) }
    } }
}

/** Exposed for settings copy and tests; no animation runs when this is false. */
fun platformMotionScale(context: Context): Float = runCatching {
    val resolver = context.contentResolver
    minOf(
        Settings.Global.getFloat(resolver, Settings.Global.ANIMATOR_DURATION_SCALE, 1f),
        Settings.Global.getFloat(resolver, Settings.Global.TRANSITION_ANIMATION_SCALE, 1f),
    )
}.getOrDefault(1f)
```

### `gui/android/app/src/main/java/dev/mcmusic/app/ui/screens/Admin.kt`

```kotlin
package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Account
import dev.mcmusic.app.data.AdminStats
import dev.mcmusic.app.data.AdminUser
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.DownloadRequest
import dev.mcmusic.app.data.InviteCode
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.ErrorLine
import dev.mcmusic.app.ui.GhostButton
import dev.mcmusic.app.ui.Loading
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.Muted
import dev.mcmusic.app.ui.PrimaryButton
import dev.mcmusic.app.ui.ScreenBack
import dev.mcmusic.app.ui.SectionLabel
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface
import dev.mcmusic.app.ui.formatBytes
import kotlinx.coroutines.launch

/**
 * Admin parity with the web panel: server stats, user roles, invite codes and
 * the download request queue. Everything calls the same admin endpoints, so the
 * phone can do whatever the site can.
 */
@Composable
fun AdminScreen(onBack: () -> Unit) {
    val design = LocalDesign.current
    val scope = rememberCoroutineScope()
    var tab by remember { mutableIntStateOf(0) }
    var reload by remember { mutableIntStateOf(0) }
    var error by remember { mutableStateOf<String?>(null) }
    var notice by remember { mutableStateOf<String?>(null) }
    var stats by remember { mutableStateOf<AdminStats?>(null) }
    var users by remember { mutableStateOf<List<AdminUser>?>(null) }
    var invites by remember { mutableStateOf<List<InviteCode>?>(null) }
    var requests by remember { mutableStateOf<List<DownloadRequest>?>(null) }
    var inviteUses by remember { mutableStateOf("1") }
    var inviteHours by remember { mutableStateOf("24") }
    var inviteNote by remember { mutableStateOf("") }
    var lastCode by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(reload, tab) {
        when (tab) {
            0 -> Api.adminStats().fold(onSuccess = { stats = it }, onFailure = { error = it.message ?: "could not load stats" })
            1 -> Api.adminUsers().fold(onSuccess = { users = it }, onFailure = { error = it.message ?: "could not load users" })
            2 -> Api.adminInvites().fold(onSuccess = { invites = it }, onFailure = { error = it.message ?: "could not load invites" })
            3 -> Api.adminRequests().fold(onSuccess = { requests = it }, onFailure = { error = it.message ?: "could not load the queue" })
        }
    }

    LazyColumn(
        contentPadding = PaddingValues(design.screenPadding, 10.dp, design.screenPadding, 32.dp),
        verticalArrangement = Arrangement.spacedBy(9.dp),
    ) {
        item { ScreenBack(onBack = onBack) }
        item { ScreenTitle("Admin", Account.me?.username ?: "server") }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                listOf("Overview", "Users", "Invites", "Queue").forEachIndexed { index, label ->
                    val selected = tab == index
                    Box(
                        Modifier.clip(RoundedCornerShape(design.cardRadius))
                            .then(if (selected) Modifier.mcSurface(RoundedCornerShape(design.cardRadius)) else Modifier)
                            .clickable { tab = index; error = null }
                            .padding(horizontal = 10.dp, vertical = 7.dp),
                    ) {
                        Text(
                            label,
                            color = if (selected) design.fg else design.dim,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Medium,
                        )
                    }
                }
            }
        }
        error?.let { item { ErrorLine(it) } }
        notice?.let { item { Muted(notice!!) } }

        when (tab) {
            0 -> {
                val s = stats
                if (s == null) {
                    item { Loading("Loading stats…") }
                } else {
                    item { SectionLabel("Library") }
                    item { StatRow("Tracks", "${s.tracks}", "Albums", "${s.albums}") }
                    item { StatRow("Playlists", "${s.playlists}", "Plays", "${s.plays}") }
                    item { SectionLabel("People") }
                    item { StatRow("Users", "${s.users}", "Admins", "${s.admins}") }
                    item { StatRow("Rooms", "${s.rooms}", "Uptime", "${s.uptime / 3600}h") }
                    item { SectionLabel("Downloads") }
                    item { StatRow("Pending", "${s.pending}", "Running", "${s.running}") }
                    item { StatRow("Approved", "${s.approved}", "Done", "${s.done}") }
                    item { StatRow("Failed", "${s.failed}", "Queue", "${s.queue}") }
                    item { SectionLabel("Storage") }
                    item { StatRow("Music", formatBytes(s.musicBytes), "Free", formatBytes(s.diskFree)) }
                    item { Muted("Disk total ${formatBytes(s.diskTotal)}") }
                    item {
                        Row(Modifier.padding(top = 4.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            GhostButton("Rescan library") {
                                scope.launch {
                                    Api.adminScan().fold(
                                        onSuccess = { (t, a) ->
                                            notice = "Scanned $t tracks and $a albums."
                                            reload++
                                        },
                                        onFailure = { error = it.message ?: "scan failed" },
                                    )
                                }
                            }
                            GhostButton("Refresh") { reload++ }
                        }
                    }
                }
            }
            1 -> {
                val list = users
                if (list == null) {
                    item { Loading("Loading users…") }
                } else {
                    item { SectionLabel("Users", Modifier) { GhostButton("Refresh") { reload++ } } }
                    items(list, key = { it.id }) { user ->
                        Column(Modifier.fillMaxWidth().mcSurface(RoundedCornerShape(design.cardRadius)).padding(11.dp)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Column(Modifier.weight(1f)) {
                                    Text(
                                        user.username + if (user.isAdmin) "  · admin" else "",
                                        color = if (user.isAdmin) design.accentText else design.fg,
                                        fontSize = 14.sp,
                                        fontWeight = FontWeight.Medium,
                                        maxLines = 1,
                                        overflow = TextOverflow.Ellipsis,
                                    )
                                    Muted(
                                        "${user.plays} plays · ${user.likes} likes · ${user.playlists} playlists" +
                                            (user.email?.let { " · $it" } ?: ""),
                                        size = 10,
                                    )
                                }
                                if (user.id != Account.me?.id) {
                                    GhostButton(if (user.isAdmin) "Demote" else "Promote") {
                                        scope.launch {
                                            Api.adminSetRole(user.id, !user.isAdmin).fold(
                                                onSuccess = { reload++ },
                                                onFailure = { error = it.message ?: "could not change the role" },
                                            )
                                        }
                                    }
                                    Box(Modifier.padding(start = 6.dp)) {
                                        GhostButton("Delete", danger = true) {
                                            scope.launch {
                                                Api.adminDeleteUser(user.id).fold(
                                                    onSuccess = { reload++ },
                                                    onFailure = { error = it.message ?: "could not delete the user" },
                                                )
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            2 -> {
                item { SectionLabel("Create invite") }
                item {
                    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                            Box(Modifier.weight(1f)) {
                                dev.mcmusic.app.ui.McField(inviteUses, { inviteUses = it }, "Uses")
                            }
                            Box(Modifier.weight(1f)) {
                                dev.mcmusic.app.ui.McField(inviteHours, { inviteHours = it }, "Hours")
                            }
                        }
                        dev.mcmusic.app.ui.McField(inviteNote, { inviteNote = it }, "Note (optional)")
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            PrimaryButton("Create") {
                                scope.launch {
                                    Api.adminCreateInvite(
                                        inviteUses.toIntOrNull() ?: 1,
                                        inviteHours.toIntOrNull() ?: 24,
                                        inviteNote.trim(),
                                    ).fold(
                                        onSuccess = { lastCode = it; reload++ },
                                        onFailure = { error = it.message ?: "could not create the invite" },
                                    )
                                }
                            }
                            GhostButton("Refresh") { reload++ }
                        }
                        lastCode?.let { Muted("New code: $it", size = 12) }
                    }
                }
                val list = invites
                if (list == null) {
                    item { Loading("Loading invites…") }
                } else if (list.isEmpty()) {
                    item { EmptyState(Lucide.Lock, "No invite codes", "Create one above to let someone sign up.") }
                } else {
                    items(list, key = { it.id }) { code ->
                        Column(Modifier.fillMaxWidth().mcSurface(RoundedCornerShape(design.cardRadius)).padding(11.dp)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Column(Modifier.weight(1f)) {
                                    Text(code.code, color = design.fg, fontSize = 14.sp, fontWeight = FontWeight.Medium)
                                    Muted(
                                        "${code.uses}/${code.maxUses} uses" +
                                            (code.note.takeIf { it.isNotBlank() }?.let { " · $it" } ?: "") +
                                            (code.usedBy.takeIf { it.isNotEmpty() }?.joinToString(", ")?.let { " · used by $it" } ?: ""),
                                        size = 10,
                                    )
                                }
                                GhostButton("Revoke", danger = true) {
                                    scope.launch {
                                        Api.adminRevokeInvite(code.id).fold(
                                            onSuccess = { reload++ },
                                            onFailure = { error = it.message ?: "could not revoke the code" },
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }
            else -> {
                item { SectionLabel("Download requests") { GhostButton("Refresh") { reload++ } } }
                val list = requests
                if (list == null) {
                    item { Loading("Loading queue…") }
                } else if (list.isEmpty()) {
                    item { EmptyState(Lucide.Download, "Queue is empty", "New requests appear here for approval.") }
                } else {
                    items(list, key = { it.id }) { request ->
                        Column(Modifier.fillMaxWidth().mcSurface(RoundedCornerShape(design.cardRadius)).padding(11.dp)) {
                            Text(
                                request.url,
                                color = design.fg,
                                fontSize = 12.sp,
                                maxLines = 2,
                                overflow = TextOverflow.Ellipsis,
                            )
                            Muted(
                                "${request.username} · ${request.status}" +
                                    (if (request.running) " · running ${request.elapsed}s" else ""),
                                size = 10,
                            )
                            Row(
                                Modifier.padding(top = 6.dp),
                                horizontalArrangement = Arrangement.spacedBy(5.dp),
                            ) {
                                val actions = when (request.status) {
                                    "pending" -> listOf("approve", "reject")
                                    "approved" -> listOf("cancel")
                                    "running" -> listOf("cancel")
                                    "failed" -> listOf("retry", "delete")
                                    else -> listOf("delete")
                                }
                                actions.forEach { action ->
                                    GhostButton(action.replaceFirstChar { it.uppercase() }, danger = action == "delete" || action == "reject") {
                                        scope.launch {
                                            Api.adminRequestAction(request.id, action).fold(
                                                onSuccess = { reload++ },
                                                onFailure = { error = it.message ?: "could not $action the request" },
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun StatRow(left: String, leftValue: String, right: String, rightValue: String) {
    val design = LocalDesign.current
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        StatTile(left, leftValue, Modifier.weight(1f))
        StatTile(right, rightValue, Modifier.weight(1f))
    }
}

@Composable
private fun StatTile(label: String, value: String, modifier: Modifier = Modifier) {
    val design = LocalDesign.current
    Column(modifier.mcSurface(RoundedCornerShape(design.cardRadius)).padding(11.dp)) {
        Text(label, color = design.dim, fontSize = 10.sp)
        Text(value, color = design.fg, fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
    }
}
```

### `gui/android/app/src/main/java/dev/mcmusic/app/ui/screens/Detail.kt`

```kotlin
package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.ArtistSummary
import dev.mcmusic.app.data.LibraryState
import dev.mcmusic.app.data.Track
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.ErrorLine
import dev.mcmusic.app.ui.Loading
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.ScreenBack
import dev.mcmusic.app.ui.TrackRow
import dev.mcmusic.app.ui.visibleTracks
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface

enum class CollectionKind { Album, Artist, Playlist }

/**
 * Album/artist/playlist contents in a sheet. The web client routes these to
 * `/set/<album>` and `/artist/<name>`; a phone-width sheet is the same page
 * without losing the list you came from.
 */
@Composable
fun CollectionSheet(
    kind: CollectionKind,
    name: String,
    onDismiss: () -> Unit,
    onOpenPlayer: () -> Unit,
) {
    val design = LocalDesign.current
    var tracks by remember(name, kind) { mutableStateOf<List<Track>?>(null) }
    var error by remember(name, kind) { mutableStateOf<String?>(null) }
    var artist by remember { mutableStateOf<ArtistSummary?>(null) }
    val shown = tracks.orEmpty().visibleTracks()

    LaunchedEffect(name, kind, LibraryState.revision) {
        val result = when (kind) {
            CollectionKind.Album -> Api.albumTracks(name)
            CollectionKind.Artist -> Api.artistTracks(name)
            CollectionKind.Playlist -> null
        }
        result?.fold(
            onSuccess = { tracks = it },
            onFailure = { error = it.message ?: "could not load $name" },
        )
    }

    Dialog(onDismissRequest = onDismiss) {
        Column(
            Modifier
                .fillMaxWidth()
                .heightIn(max = 560.dp)
                .mcSurface(RoundedCornerShape(design.cardRadius))
                .padding(14.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            ScreenBack(onBack = onDismiss)
            Text(name, color = design.fg, fontSize = 20.sp, fontWeight = FontWeight.SemiBold)
            Text(
                when (kind) {
                    CollectionKind.Album -> "Album"
                    CollectionKind.Artist -> "Artist"
                    CollectionKind.Playlist -> "Playlist"
                },
                color = design.dim,
                fontSize = 12.sp,
            )
            Box(Modifier.weight(1f, fill = false)) {
                when {
                    error != null -> ErrorLine(error!!)
                    tracks == null -> Loading()
                    shown.isEmpty() -> EmptyState(
                        icon = Lucide.ListMusic,
                        title = "Nothing here",
                        body = "No tracks matched this $name.",
                    )
                    else -> LazyColumn {
                        items(shown, key = { it.id }) { track ->
                            TrackRow(track, menu = true, onClick = {
                                Playback.play(shown, shown.indexOf(track))
                                onDismiss()
                                onOpenPlayer()
                            }, onOpenArtist = { name ->
                                artist = ArtistSummary(name, 0, 0, track.id)
                            })
                        }
                    }
                }
            }
        }
    }
    artist?.let {
        CollectionSheet(
            CollectionKind.Artist,
            it.artist,
            onDismiss = { artist = null },
            onOpenPlayer = onOpenPlayer,
        )
    }
}
```

### `gui/android/app/src/main/java/dev/mcmusic/app/ui/screens/Home.kt`

```kotlin
package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Account
import dev.mcmusic.app.data.AlbumSummary
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.ArtistSummary
import dev.mcmusic.app.data.HomeFeed
import dev.mcmusic.app.data.LibraryState
import dev.mcmusic.app.data.Listener
import dev.mcmusic.app.data.Track
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.ui.Cover
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.ErrorLine
import dev.mcmusic.app.ui.Loading
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.MediaCard
import dev.mcmusic.app.ui.Pill
import dev.mcmusic.app.ui.SectionLabel
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.TrackRow
import dev.mcmusic.app.ui.visibleTracks
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface
import dev.mcmusic.app.ui.formatDuration

/**
 * The signed-in feed the website shows, plus the public "listening now" row that
 * works without an account. Recently added and all-tracks sections fall back to
 * public endpoints, so a fresh install is useful before signing in.
 */
@Composable
fun HomeScreen(onOpenSearch: () -> Unit, onOpenPlayer: () -> Unit) {
    val design = LocalDesign.current
    val me = Account.me
    var feed by remember { mutableStateOf<HomeFeed?>(null) }
    var listeners by remember { mutableStateOf<List<Listener>>(emptyList()) }
    var recent by remember { mutableStateOf<List<Track>>(emptyList()) }
    var errors by remember { mutableStateOf<List<String>>(emptyList()) }
    var loading by remember { mutableStateOf(true) }
    var reload by remember { mutableIntStateOf(0) }
    var album by remember { mutableStateOf<AlbumSummary?>(null) }
    var artist by remember { mutableStateOf<ArtistSummary?>(null) }

    LaunchedEffect(reload, me != null, LibraryState.revision) {
        loading = true
        val failures = mutableListOf<String>()
        Api.listening().fold(
            onSuccess = { listeners = it },
            onFailure = { failures += "Listening now: ${it.message ?: "unavailable"}" },
        )
        if (me != null) {
            Api.home().fold(
                onSuccess = { feed = it },
                onFailure = { failures += "Home feed: ${it.message ?: "unavailable"}" },
            )
            Api.tracks(limit = 60).fold(
                onSuccess = { recent = it },
                onFailure = { failures += "Library: ${it.message ?: "unavailable"}" },
            )
        } else {
            feed = null
            recent = emptyList()
        }
        errors = failures
        loading = false
    }

    val shownRecent = recent.visibleTracks()

    LazyColumn(
        contentPadding = PaddingValues(
            start = design.screenPadding,
            end = design.screenPadding,
            top = 10.dp,
            bottom = 24.dp,
        ),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            ScreenTitle(
                if (me != null) "Hi, ${me.username}" else "mcmusic",
                subtitle = when {
                    feed?.sections?.isNotEmpty() == true ->
                        "A shelf built from your listening, the live room and what just landed."
                    me != null -> "Your library, the live room and what just landed."
                    else -> "Sign in for playlists, downloads and a feed built from your listening."
                },
            )
        }

        if (loading) item { Loading("Building your feed…") }
        errors.forEach { message -> item { ErrorLine(message) } }

        if (listeners.isNotEmpty()) {
            item {
                SectionLabel("Listening now") {
                    Pill("${listeners.count { it.listening }} live")
                }
            }
            item {
                LazyRow(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    items(listeners, key = { it.username }) { listener ->
                        ListenerCard(listener)
                    }
                }
            }
        }

        feed?.sections?.forEach { section ->
            item { SectionLabel(section.title) }
            item {
                LazyRow(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    items(section.tracks, key = { it.id }) { track ->
                        TrackCard(track, onPlay = {
                            Playback.play(section.tracks, section.tracks.indexOf(track))
                            onOpenPlayer()
                        })
                    }
                }
            }
        }

        if (!feed?.albums.isNullOrEmpty()) {
            item { SectionLabel("Recently added") }
            item {
                LazyRow(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    items(feed!!.albums, key = { it.album }) { entry ->
                        MediaCard(
                            title = entry.album,
                            subtitle = entry.artist,
                            coverUrl = albumCoverUrl(entry.coverId),
                            onClick = { album = entry },
                        )
                    }
                }
            }
        }

        if (me != null) {
            item { SectionLabel("All tracks") }
            if (shownRecent.isEmpty() && !loading) {
                item {
                    EmptyState(
                        icon = Lucide.Library,
                        title = "No tracks yet",
                        body = "The server has not returned any tracks.",
                        actionLabel = "Retry",
                        onAction = { reload++ },
                    )
                }
            }
        }
        items(shownRecent, key = { it.id }) { track ->
            TrackRow(track, menu = true, onClick = {
                Playback.play(shownRecent, shownRecent.indexOf(track))
                onOpenPlayer()
            }, onOpenArtist = { name ->
                artist = ArtistSummary(name, 0, 0, track.id)
            })
        }
    }

    album?.let { entry ->
        CollectionSheet(
            kind = CollectionKind.Album,
            name = entry.album,
            onDismiss = { album = null },
            onOpenPlayer = onOpenPlayer,
        )
    }
    artist?.let { entry ->
        CollectionSheet(
            kind = CollectionKind.Artist,
            name = entry.artist,
            onDismiss = { artist = null },
            onOpenPlayer = onOpenPlayer,
        )
    }
}

@Composable
private fun ListenerCard(listener: Listener) {
    val design = LocalDesign.current
    val uriHandler = LocalUriHandler.current
    val track = listener.track
    Row(
        Modifier
            .width(210.dp)
            .mcSurface(RoundedCornerShape(design.cardRadius))
            .clickable(enabled = listener.profileUrl.isNotBlank()) {
                Api.externalUrl(listener.profileUrl)?.let { runCatching { uriHandler.openUri(it) } }
            }
            .padding(8.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(9.dp),
    ) {
        Cover(
            url = listener.coverUrl.ifBlank { listener.profileUrl },
            shape = CircleShape,
            modifier = Modifier.size(38.dp),
            fallback = design.accentSoft,
        )
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(5.dp)) {
                Text(listener.username, color = design.accentText, fontSize = 12.sp, fontWeight = FontWeight.Medium, maxLines = 1)
                dev.mcmusic.app.ui.LiveDot(listener.listening, 5.dp)
            }
            Text(
                track?.let { "${it.title} · ${it.artist}" }
                    ?: if (listener.listening) "listening" else "offline",
                color = design.fg,
                fontSize = 10.sp,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                Pill(if (listener.listening) "listening" else "paused", listener.listening)
                if (track != null && track.duration > 0) {
                    Text(
                        "${formatDuration(listener.position)} / ${formatDuration(track.duration)}",
                        color = design.dim,
                        fontSize = 10.sp,
                    )
                }
            }
        }
    }
}

@Composable
private fun TrackCard(track: Track, onPlay: () -> Unit) {
    val design = LocalDesign.current
    Column(
        Modifier.width(132.dp).clip(RoundedCornerShape(design.cardRadius)).clickable { onPlay() },
        verticalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        Box {
            Cover(
                url = dev.mcmusic.app.ui.trackCoverUrl(track.id),
                shape = RoundedCornerShape(20.dp),
                modifier = Modifier.size(132.dp),
                fallback = design.accentSoft,
            )
            Box(
                Modifier.align(Alignment.BottomEnd).padding(6.dp).size(24.dp).clip(CircleShape)
                    .background(design.accent),
                Alignment.Center,
            ) {
                dev.mcmusic.app.ui.LucideIcon(Lucide.Play, design.onAccent, size = 11.dp)
            }
        }
        Text(track.title, color = design.fg, fontSize = 12.sp, fontWeight = FontWeight.Medium, maxLines = 1, overflow = TextOverflow.Ellipsis)
        Text(
            "${track.artist} · ${formatDuration(track.duration)}",
            color = design.dim, fontSize = 10.sp, maxLines = 1, overflow = TextOverflow.Ellipsis,
        )
    }
}

fun albumCoverUrl(coverId: Int?): String = coverId?.let { Api.url("/api/tracks/$it/cover") } ?: ""
```

### `gui/android/app/src/main/java/dev/mcmusic/app/ui/screens/LyricVisualizer.kt`

```kotlin
package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.dp
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.playfulMotionEnabled
import kotlin.math.PI
import kotlin.math.sin

/** The three lyric visualizer modes, shared by name with web/desktop/iOS. */
enum class LyricVisualizerMode(val label: String) {
    Bars("Bars"),
    Wave("Wave"),
    Glow("Glow"),
    ;

    fun next(): LyricVisualizerMode = values()[(ordinal + 1) % values().size]
}

/**
 * A small deterministic visualizer for the lyrics pane. It uses playback
 * position and the highlighted lyric line, so it animates in sync with the
 * music without a separate analyser or microphone permission.
 */
@Composable
fun LyricVisualizer(
    mode: LyricVisualizerMode,
    positionMs: Long,
    activeLine: Int,
    playing: Boolean,
    onCycle: () -> Unit,
) {
    val design = LocalDesign.current
    val motion = playfulMotionEnabled()
    // Reduced motion keeps the same flat, deterministic shape without a pulse.
    val seconds = if (motion) positionMs / 1000f else 0f
    val pulse = if (activeLine >= 0) 1f else 0.72f
    val alpha = if (playing) 1f else 0.55f
    val visualAccent = if (design.palette.dark) design.accent else design.accentText
    Box(
        Modifier
            .fillMaxWidth()
            .height(58.dp)
            .clip(RoundedCornerShape(design.cardRadius))
            .background(design.accentWash)
            .clickable(onClick = onCycle),
        contentAlignment = Alignment.Center,
    ) {
        Canvas(Modifier.fillMaxWidth().height(58.dp).padding(horizontal = 12.dp, vertical = 8.dp)) {
            val w = size.width
            val h = size.height
            val tint = visualAccent.copy(alpha = alpha)
            when (mode) {
                LyricVisualizerMode.Bars -> {
                    val count = 36
                    val gap = 3.dp.toPx()
                    val barWidth = ((w - gap * (count - 1)) / count).coerceAtLeast(1f)
                    for (i in 0 until count) {
                        val wave = (sin(seconds * 3.1f + i * 0.48f) + 1f) / 2f
                        val shimmer = (sin(seconds * 7.7f - i * 0.21f) + 1f) / 2f
                        val target = (0.14f + wave * 0.55f + shimmer * 0.18f) * pulse
                        val barHeight = (h * target.coerceIn(0.08f, 1f))
                        drawRoundRect(
                            color = tint.copy(alpha = 0.35f + wave * 0.55f),
                            topLeft = Offset(i * (barWidth + gap), h - barHeight),
                            size = Size(barWidth, barHeight),
                            cornerRadius = androidx.compose.ui.geometry.CornerRadius(barWidth / 2),
                        )
                    }
                }
                LyricVisualizerMode.Wave -> {
                    val steps = 90
                    val path = androidx.compose.ui.graphics.Path()
                    for (i in 0..steps) {
                        val x = w * i / steps
                        val envelope = (sin(PI * i / steps).toFloat()).coerceAtLeast(0f)
                        val y = h / 2 + sin(i * 0.17f - seconds * 3.4f) * h * 0.32f * envelope * pulse
                        if (i == 0) path.moveTo(x, y) else path.lineTo(x, y)
                    }
                    drawPath(path, tint, style = Stroke(width = 2.5.dp.toPx()))
                }
                LyricVisualizerMode.Glow -> {
                    val radius = (h * 0.36f) * pulse
                    for (i in 6 downTo 1) {
                        val r = radius * (1f + i * 0.22f)
                        drawCircle(
                            color = visualAccent.copy(alpha = 0.10f * alpha / i),
                            center = Offset(w / 2, h / 2),
                            radius = r,
                        )
                    }
                    drawCircle(
                        color = visualAccent.copy(alpha = 0.85f * alpha),
                        center = Offset(w / 2, h / 2),
                        radius = radius * (0.55f + 0.08f * sin(seconds * 3f)),
                    )
                }
            }
        }
    }
}
```

### `gui/android/app/src/main/java/dev/mcmusic/app/ui/screens/Player.kt`

```kotlin
package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.gestures.detectDragGesturesAfterLongPress
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyListState
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.SwipeToDismissBox
import androidx.compose.material3.SwipeToDismissBoxValue
import androidx.compose.material3.Text
import androidx.compose.material3.rememberSwipeToDismissBoxState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.Lyrics
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.ui.Cover
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.ErrorLine
import dev.mcmusic.app.ui.GhostButton
import dev.mcmusic.app.ui.IconButton
import dev.mcmusic.app.ui.Loading
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.LucideIcon
import dev.mcmusic.app.ui.Muted
import dev.mcmusic.app.ui.PlayPauseButton
import dev.mcmusic.app.ui.PlayfulSeek
import dev.mcmusic.app.ui.ScreenBack
import dev.mcmusic.app.ui.SectionLabel
import dev.mcmusic.app.ui.SwitchRow
import dev.mcmusic.app.ui.design.DynamicColour
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface
import dev.mcmusic.app.ui.design.playfulMotionEnabled
import dev.mcmusic.app.ui.formatMillis
import dev.mcmusic.app.ui.formatDuration
import dev.mcmusic.app.ui.trackCoverUrl
import dev.mcmusic.app.data.Track
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.collect
import kotlin.math.abs

/**
 * Now playing, with the same queue the service is playing. The scrubber writes
 * through to ExoPlayer, and the sleep timer is Playback's own (it pauses the
 * controller when the clock runs out).
 */
@OptIn(ExperimentalFoundationApi::class)
@Composable
fun PlayerScreen(onBack: () -> Unit, onVideo: (String?, Long) -> Unit = { _, _ -> }) {
    val design = LocalDesign.current
    val state = Playback.state
    val motion = playfulMotionEnabled()
    var scrub by remember { mutableStateOf<Float?>(null) }
    var lyricsOpen by remember { mutableStateOf(false) }
    // YouTube Music-style artwork carousel: one page per queue entry. The
    // settled page is the source of truth for playback, not the live page
    // during a fling, so a half-swipe never changes the song.
    val pagerState = rememberPagerState(
        initialPage = state.index.coerceAtLeast(0),
        pageCount = { state.queue.size.coerceAtLeast(1) },
    )
    LaunchedEffect(state.index) {
        val last = state.queue.lastIndex.coerceAtLeast(0)
        if (pagerState.currentPage != state.index && !pagerState.isScrollInProgress) {
            pagerState.animateScrollToPage(state.index.coerceIn(0, last))
        }
    }
    LaunchedEffect(Unit) {
        snapshotFlow { pagerState.settledPage }.collect { page ->
            if (page != state.index && page < state.queue.size) Playback.playIndex(page)
        }
    }

    val listState = rememberLazyListState()
    var heldRow by remember { mutableIntStateOf(-1) }
    var dragOffset by remember { mutableFloatStateOf(0f) }
    var dropSlot by remember { mutableIntStateOf(-1) }

    fun rowCenter(index: Int): Float? =
        listState.layoutInfo.visibleItemsInfo
            .firstOrNull { it.key == "queue-$index" }
            ?.let { it.offset + it.size / 2f }

    fun startQueueDrag(index: Int) {
        heldRow = index
        dropSlot = index
        dragOffset = 0f
    }

    fun dragQueue(dy: Float) {
        dragOffset += dy
        val index = heldRow
        val center = if (index >= 0) rowCenter(index) else null
        dropSlot = center?.let { listState.nearestQueueIndex(it + dragOffset) }
            ?.coerceIn(0, state.queue.lastIndex.coerceAtLeast(0)) ?: index
    }

    fun endQueueDrag() {
        val from = heldRow
        val to = dropSlot
        heldRow = -1
        dropSlot = -1
        dragOffset = 0f
        if (from >= 0 && to >= 0 && from != to && to < state.queue.size) Playback.move(from, to)
    }

    val queueDrag = QueueDragState(
        index = heldRow,
        offset = dragOffset,
        target = dropSlot,
        onStart = ::startQueueDrag,
        onDrag = ::dragQueue,
        onEnd = ::endQueueDrag,
    )

    LaunchedEffect(Unit) {
        while (true) {
            Playback.tick()
            delay(500)
        }
    }

    // A new playing track drops the old seed before its artwork is sampled.
    LaunchedEffect(state.track?.id) { DynamicColour.clearCover() }

    val track = state.track
    if (track == null) {
        LazyColumn(contentPadding = PaddingValues(design.screenPadding)) {
            item { ScreenBack(onBack) }
            item {
                EmptyState(
                    icon = Lucide.Play,
                    title = "Nothing playing",
                    body = "Pick a track from Home, Search or the Library and it will start here.",
                )
            }
        }
        return
    }

    val fraction = if (state.duration > 0) {
        scrub ?: (state.position.toFloat() / state.duration).coerceIn(0f, 1f)
    } else 0f

    LazyColumn(
        contentPadding = PaddingValues(design.screenPadding, 10.dp, design.screenPadding, 24.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        item { ScreenBack(onBack) }
        item {
            HorizontalPager(
                state = pagerState,
                modifier = Modifier.fillMaxWidth(),
                contentPadding = PaddingValues(horizontal = 44.dp),
                pageSpacing = 12.dp,
                verticalAlignment = Alignment.Top,
            ) { page ->
                val pageTrack = state.queue.getOrNull(page)
                val distance = abs(page - (pagerState.currentPage + pagerState.currentPageOffsetFraction))
                    .coerceAtMost(2f)
                Box(
                    Modifier
                        .fillMaxWidth()
                        .heightIn(min = 288.dp)
                        .graphicsLayer {
                            val weighted = if (motion) distance else 0f
                            val scale = 1f - 0.07f * weighted
                            scaleX = scale
                            scaleY = scale
                            alpha = 1f - 0.22f * weighted
                        }
                        .clickable {
                            if (page != state.index && pageTrack != null) Playback.playIndex(page)
                        },
                    Alignment.Center,
                ) {
                    Box(
                        Modifier
                            .size(268.dp)
                            .clip(RoundedCornerShape(design.heroRadius))
                            .background(design.accentSoft),
                        Alignment.Center,
                    ) {
                        Cover(
                            url = pageTrack?.let { trackCoverUrl(it.id) } ?: "",
                            shape = RoundedCornerShape(design.coverRadius),
                            modifier = Modifier.size(244.dp),
                            fallback = design.accentWash,
                            dynamic = page == state.index,
                        )
                    }
                }
            }
            Row(
                Modifier.fillMaxWidth().padding(top = 2.dp),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                repeat(state.queue.size.coerceAtMost(12)) { dot ->
                    Box(
                        Modifier
                            .padding(horizontal = 3.dp)
                            .clip(CircleShape)
                            .background(if (dot == pagerState.currentPage) design.accent else design.hairline)
                            .size(if (dot == pagerState.currentPage) 7.dp else 5.dp)
                            .clickable { if (dot < state.queue.size) Playback.playIndex(dot) },
                    )
                }
            }
        }
        item {
            Column(
                Modifier.fillMaxWidth().padding(top = 6.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(3.dp),
            ) {
                Text(
                    track.title,
                    color = design.fg,
                    fontSize = 20.sp,
                    fontWeight = FontWeight.SemiBold,
                    textAlign = TextAlign.Center,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                )
                Text(
                    "${track.artist} · ${track.album}",
                    color = design.dim,
                    fontSize = 12.sp,
                    textAlign = TextAlign.Center,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                Muted(
                    "Swipe artwork to change song · hold a queue row to reorder · swipe left to remove",
                    size = 10,
                )
                state.error?.let { message ->
                    Text(message, color = design.palette.error, fontSize = 11.sp, textAlign = TextAlign.Center)
                }
            }
        }
        if (!lyricsOpen && track.id > 0) {
            item { NowLyric(track.id) { lyricsOpen = true } }
        }
        item {
            PlayfulSeek(fraction, state.playing, onSeek = { value ->
                scrub = value
                Playback.seekFraction(value)
                scrub = null
            })
        }
        item {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Muted(formatMillis((fraction * state.duration).toLong()), size = 11)
                Muted(formatMillis(state.duration), size = 11)
            }
        }
        item {
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                IconButton(Lucide.Shuffle, size = 20.dp, tint = if (state.shuffle) design.accentText else design.dim) {
                    Playback.toggleShuffle()
                }
                IconButton(Lucide.SkipBack, size = 26.dp) { Playback.previous() }
                PlayPauseButton(state.playing, size = 58.dp) { Playback.toggle() }
                IconButton(Lucide.SkipForward, size = 26.dp) { Playback.next() }
                IconButton(Lucide.Repeat, size = 20.dp, tint = if (state.repeat) design.accentText else design.dim) {
                    Playback.cycleRepeat()
                }
                IconButton(
                    Lucide.ListMusic,
                    size = 20.dp,
                    tint = if (lyricsOpen) design.accentText else design.dim,
                ) { lyricsOpen = !lyricsOpen }
            }
        }
        if (lyricsOpen && track.id > 0) item { LyricsPanel(track.id) }
        if (!track.ytId.isNullOrBlank()) {
            item {
                Row(
                    Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.Center,
                ) {
                    GhostButton("Watch video") { onVideo(track.ytId, state.position) }
                }
            }
        }
        item {
            Column(
                Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(8.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                ) {
                    LucideIcon(Lucide.Clock, design.dim, size = 14.dp)
                    Text(
                        when {
                            state.sleepMinutes == 0 -> "Sleep timer off"
                            state.sleepRemaining > 0 -> "Sleeping in ${((state.sleepRemaining / 60000) + 1)} min"
                            else -> "Sleep timer"
                        },
                        color = design.dim,
                        fontSize = 12.sp,
                    )
                }
                FlowRow(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.Center,
                    verticalArrangement = Arrangement.spacedBy(6.dp),
                ) {
                    listOf(0, 15, 30, 60).forEach { minutes ->
                        val selected = state.sleepMinutes == minutes
                        Box(
                            Modifier
                                .padding(horizontal = 3.dp)
                                .clip(RoundedCornerShape(50))
                                .background(if (selected) design.accent else design.accentWash)
                                .clickable { Playback.setSleep(minutes) }
                                .padding(horizontal = 16.dp, vertical = 12.dp),
                        ) {
                            Text(
                                if (minutes == 0) "Off" else "${minutes}m",
                                color = if (selected) design.onAccent else design.dim,
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Medium,
                            )
                        }
                    }
                }
            }
        }
        item { SectionLabel("Queue") }
        if (state.queue.isEmpty()) {
            item { Muted("The queue is empty.") }
        }
        itemsIndexed(state.queue, key = { index, _ -> "queue-$index" }) { index, item ->
            QueueRow(index, item, state, queueDrag)
        }
        item {
            SwitchRow(
                title = "Autoplay",
                subtitle = "When the last song ends, add up to 5 similar tracks",
                icon = Lucide.Radio,
                checked = state.autoplay,
                onChange = { Playback.setAutoplay(it) },
            )
        }
    }
}

/** Which queue row is held, how far it moved, and where it would land. */
private data class QueueDragState(
    val index: Int = -1,
    val offset: Float = 0f,
    val target: Int = -1,
    val onStart: (Int) -> Unit = {},
    val onDrag: (Float) -> Unit = {},
    val onEnd: () -> Unit = {},
)

/** Queue row under the nearest visible row centre, used as the drop slot. */
private fun LazyListState.nearestQueueIndex(centerY: Float): Int? =
    layoutInfo.visibleItemsInfo
        .filter { (it.key as? String)?.startsWith("queue-") == true }
        .minByOrNull { abs(it.offset + it.size / 2f - centerY) }
        ?.let { (it.key as String).removePrefix("queue-").toIntOrNull() }

/** One queue entry. Hold to lift/reorder; swipe left past the edge to remove. */
@OptIn(ExperimentalFoundationApi::class, ExperimentalMaterial3Api::class)
@Composable
private fun QueueRow(
    index: Int,
    item: Track,
    state: dev.mcmusic.app.playback.PlaybackState,
    drag: QueueDragState,
) {
    val design = LocalDesign.current
    val motion = playfulMotionEnabled()
    val lifted = drag.index == index
    val current = index == state.index
    val dismissState = rememberSwipeToDismissBoxState(
        confirmValueChange = { value ->
            if (value == SwipeToDismissBoxValue.EndToStart) {
                Playback.removeFromQueue(index)
                true
            } else false
        },
    )
    SwipeToDismissBox(
        state = dismissState,
        enableDismissFromStartToEnd = false,
        backgroundContent = {
            Row(
                Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(design.cardRadius))
                    .background(design.palette.error.copy(alpha = 0.16f))
                    .padding(horizontal = 14.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.End,
            ) {
                Text("Remove from queue", color = design.palette.error, fontSize = 12.sp)
            }
        },
    ) {
        Row(
            Modifier
                .fillMaxWidth()
                .graphicsLayer {
                    translationY = if (lifted) drag.offset else 0f
                    val scale = if (lifted && motion) 1.02f else 1f
                    scaleX = scale
                    scaleY = scale
                }
                .clip(RoundedCornerShape(design.cardRadius))
                .background(if (lifted || current) design.accentSoft else design.palette.bg)
                .pointerInput(index) {
                    detectDragGesturesAfterLongPress(
                        onDragStart = { drag.onStart(index) },
                        onDrag = { _, amount -> drag.onDrag(amount.y) },
                        onDragEnd = { drag.onEnd() },
                        onDragCancel = { drag.onEnd() },
                    )
                }
                .clickable { if (!lifted) Playback.play(state.queue, index) }
                .padding(horizontal = 8.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(9.dp),
        ) {
            Box(Modifier.width(20.dp), Alignment.Center) {
                when {
                    lifted && drag.target >= 0 ->
                        Text("${drag.target + 1}", color = design.accentText, fontSize = 12.sp)
                    current -> LucideIcon(
                        Lucide.Play,
                        design.accentText,
                        size = 14.dp,
                        contentDescription = "Now playing",
                    )
                    else -> Text("${index + 1}", color = design.dim, fontSize = 12.sp)
                }
            }
            Column(Modifier.weight(1f)) {
                Text(
                    item.title,
                    color = if (current || lifted) design.accentText else design.fg,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Medium,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                Text(
                    if (lifted && drag.target >= 0 && drag.target != index)
                        "Move to ${drag.target + 1}" else item.artist,
                    color = if (lifted) design.accentText else design.dim,
                    fontSize = 10.sp,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }
            Muted(formatDuration(item.duration), size = 10)
            LucideIcon(
                Lucide.GripVertical,
                design.dim,
                size = 16.dp,
                contentDescription = "Hold to reorder",
            )
        }
    }
}

private data class LyricLine(val time: Double, val text: String)

/** LRC timestamps plus plain text, honouring `[offset:]` and word stamps. */
private fun parseLyrics(text: String): List<LyricLine> {
    val stamps = Regex("\\[(\\d{1,2}):(\\d{2})(?:[.:](\\d{1,3}))?\\]")
    val metadata = Regex("^\\[(?:ar|ti|al|by|re|ue|length):", RegexOption.IGNORE_CASE)
    val offsetLine = Regex("^\\[offset:([+-]?\\d+)\\]", RegexOption.IGNORE_CASE)
    val inlineWords = Regex("<[^>]+>")
    var offsetMs = 0
    return buildList {
        for (raw in text.lineSequence()) {
            val line = raw.trim()
            if (line.isEmpty()) continue
            offsetLine.find(line)?.let { offsetMs = it.groupValues[1].toIntOrNull() ?: 0 }
            if (metadata.containsMatchIn(line) || offsetLine.containsMatchIn(line)) continue
            val times = mutableListOf<Double>()
            var lastEnd = 0
            for (match in stamps.findAll(line)) {
                val fraction = match.groupValues[3]
                val fractionSeconds = if (fraction.isEmpty()) 0.0 else "0.$fraction".toDouble()
                times += match.groupValues[1].toDouble() * 60 + match.groupValues[2].toDouble() + fractionSeconds
                lastEnd = match.range.last + 1
            }
            val words = inlineWords.replace(line.substring(lastEnd).trim(), "").trim()
            if (words.isEmpty()) continue
            if (times.isEmpty()) {
                add(LyricLine(-1.0, words))
            } else {
                val shift = offsetMs / 1000.0
                times.forEach { add(LyricLine((it - shift).coerceAtLeast(0.0), words)) }
            }
        }
    }.sortedBy { it.time }
}

/**
 * Lyrics panel, only composed while the Player toggle is on. The fetch is
 * keyed to the visible track (and a retry counter), so opening the panel is
 * the only thing that makes a lyrics request and switching tracks refetches.
 */
@Composable
private fun LyricsPanel(trackId: Int) {
    val design = LocalDesign.current
    val motion = playfulMotionEnabled()
    var lyrics by remember(trackId) { mutableStateOf<Lyrics?>(null) }
    var error by remember(trackId) { mutableStateOf<String?>(null) }
    var loading by remember(trackId) { mutableStateOf(true) }
    var reload by remember(trackId) { mutableIntStateOf(0) }
    var visualizerMode by remember(trackId) { mutableStateOf(LyricVisualizerMode.Bars) }
    val listState = rememberLazyListState()

    LaunchedEffect(trackId, reload) {
        loading = true
        error = null
        lyrics = null
        Api.lyrics(trackId).fold(
            onSuccess = { lyrics = it; loading = false },
            onFailure = { error = it.message ?: "could not load lyrics"; loading = false },
        )
    }

    val lines = remember(lyrics?.text) { parseLyrics(lyrics?.text.orEmpty()) }
    val positionSeconds = Playback.state.position / 1000.0
    var activeIndex = -1
    for (index in lines.indices) {
        val time = lines[index].time
        if (time < 0) continue
        if (time <= positionSeconds) activeIndex = index else break
    }
    LaunchedEffect(activeIndex) {
        if (activeIndex < 0) return@LaunchedEffect
        if (motion) listState.animateScrollToItem(activeIndex) else listState.scrollToItem(activeIndex)
    }

    val source = lyrics?.source.orEmpty()
    val via = when {
        source.contains("lrclib", ignoreCase = true) -> " · via LRCLIB"
        source.isNotBlank() -> " · $source"
        else -> ""
    }
    val kind = (if (lines.any { it.time >= 0 }) "Synced" else "Plain") + via

    Column(
        Modifier.fillMaxWidth().mcSurface(RoundedCornerShape(design.cardRadius)).padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(7.dp)) {
            LucideIcon(Lucide.ListMusic, design.accentText, size = 15.dp)
            Text("Lyrics", color = design.fg, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
            Box(Modifier.weight(1f))
            Muted(kind, size = 11)
        }
        LyricVisualizer(
            mode = visualizerMode,
            positionMs = Playback.state.position,
            activeLine = activeIndex,
            playing = Playback.state.playing,
            onCycle = { visualizerMode = visualizerMode.next() },
        )
        Muted("Visualizer: ${visualizerMode.label} · tap to change", size = 10)
        when {
            loading -> Loading("Loading lyrics…")
            error != null -> {
                ErrorLine(error!!)
                GhostButton("Retry") { reload++ }
            }
            lines.isEmpty() -> Muted("No lyrics found for this track yet.")
            else -> LazyColumn(
                modifier = Modifier.fillMaxWidth().heightIn(max = 280.dp),
                state = listState,
                verticalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                itemsIndexed(lines) { index, line ->
                    val active = index == activeIndex
                    Text(
                        line.text,
                        color = if (active) design.accentText else design.dim,
                        fontSize = if (active) 15.sp else 13.sp,
                        fontWeight = if (active) FontWeight.SemiBold else FontWeight.Normal,
                        modifier = Modifier.clickable(enabled = line.time >= 0) {
                            Playback.seekTo((line.time * 1000).toLong())
                        },
                    )
                }
            }
        }
    }
}

/** A single live lyric line above the scrubber; tap it to open the full pane. */
@Composable
private fun NowLyric(trackId: Int, onOpen: () -> Unit) {
    val design = LocalDesign.current
    var raw by remember(trackId) { mutableStateOf<String?>(null) }
    LaunchedEffect(trackId) {
        raw = Api.lyrics(trackId).getOrNull()?.text
    }
    val lines = remember(raw) { parseLyrics(raw.orEmpty()) }
    val position = Playback.state.position / 1000.0
    val current = lines.lastOrNull { it.time >= 0 && it.time <= position }?.text
        ?: lines.firstOrNull { it.time < 0 }?.text
    if (current.isNullOrBlank()) return
    Row(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(design.cardRadius))
            .background(design.accentSoft)
            .clickable(onClick = onOpen)
            .padding(horizontal = 12.dp, vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        LucideIcon(Lucide.ListMusic, design.accentText, size = 14.dp)
        Text(
            current,
            color = design.accentText,
            fontSize = 12.sp,
            fontWeight = FontWeight.Medium,
            maxLines = 2,
            overflow = TextOverflow.Ellipsis,
        )
    }
}
```

### `gui/android/app/src/main/java/dev/mcmusic/app/ui/screens/Playlists.kt`

```kotlin
package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Account
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.ArtistSummary
import dev.mcmusic.app.data.LibraryState
import dev.mcmusic.app.data.Playlist
import dev.mcmusic.app.data.Track
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.ui.Cover
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.ErrorLine
import dev.mcmusic.app.ui.GhostButton
import dev.mcmusic.app.ui.IconButton
import dev.mcmusic.app.ui.Loading
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.McField
import dev.mcmusic.app.ui.Muted
import dev.mcmusic.app.ui.PrimaryButton
import dev.mcmusic.app.ui.ScreenBack
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.SectionLabel
import dev.mcmusic.app.ui.TrackRow
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface
import kotlinx.coroutines.launch

/**
 * Playlists, the one library feature that needs an account. When [playlistId]
 * is null this is the index; otherwise it is one playlist with rename, delete
 * and remove-track controls, mirroring the web's `/playlists` pages.
 */
@Composable
fun PlaylistsScreen(playlistId: Int?, onOpenPlaylist: (Int) -> Unit, onOpenPlayer: () -> Unit, onBack: () -> Unit) {
    if (playlistId == null) {
        PlaylistIndex(onOpenPlaylist)
    } else {
        PlaylistDetail(playlistId, onOpenPlayer, onBack)
    }
}

@Composable
private fun PlaylistIndex(onOpenPlaylist: (Int) -> Unit) {
    val design = LocalDesign.current
    val scope = rememberCoroutineScope()
    var playlists by remember { mutableStateOf<List<Playlist>?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var newName by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var reload by remember { mutableIntStateOf(0) }

    LaunchedEffect(reload, LibraryState.revision) {
        Api.playlists().fold(
            onSuccess = { playlists = it; error = null },
            onFailure = { error = it.message ?: "could not load playlists"; playlists = emptyList() },
        )
    }

    LazyColumn(
        contentPadding = PaddingValues(design.screenPadding, 10.dp, design.screenPadding, 24.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        item { ScreenTitle("Playlists", "Everything you have saved, in order.") }
        if (Account.me == null) {
            item {
                EmptyState(
                    icon = Lucide.LogIn,
                    title = "Sign in for playlists",
                    body = "Playlists belong to an account. Sign in from Settings and they appear here.",
                )
            }
            return@LazyColumn
        }
        error?.let { item { ErrorLine(it) } }
        item {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Box(Modifier.weight(1f)) {
                    McField(newName, { newName = it }, "New playlist")
                }
                PrimaryButton(if (busy) "…" else "Create", enabled = newName.isNotBlank() && !busy) {
                    busy = true
                    scope.launch {
                        Api.createPlaylist(newName.trim()).fold(
                            onSuccess = { newName = ""; reload++ },
                            onFailure = { error = it.message ?: "could not create the playlist" },
                        )
                        busy = false
                    }
                }
            }
        }
        when {
            playlists == null -> item { Loading("Loading playlists…") }
            playlists!!.isEmpty() -> item {
                EmptyState(
                    icon = Lucide.ListMusic,
                    title = "No playlists yet",
                    body = "Create one above, then add tracks from any album or search result.",
                )
            }
            else -> items(playlists!!, key = { it.id }) { playlist ->
                Row(
                    Modifier.fillMaxWidth().mcSurface(RoundedCornerShape(design.cardRadius))
                        .clickable { onOpenPlaylist(playlist.id) }
                        .padding(10.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    Cover(
                        url = albumCoverUrl(playlist.coverId),
                        shape = RoundedCornerShape(20.dp),
                        modifier = Modifier.size(42.dp),
                        fallback = design.accentSoft,
                    )
                    Column(Modifier.weight(1f)) {
                        Text(playlist.name, color = design.fg, fontSize = 14.sp, fontWeight = FontWeight.Medium, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        Text("${playlist.count} tracks", color = design.dim, fontSize = 11.sp)
                    }
                    dev.mcmusic.app.ui.LucideIcon(Lucide.ChevronRight, design.dim, size = 16.dp)
                }
            }
        }
    }
}

@Composable
private fun PlaylistDetail(id: Int, onOpenPlayer: () -> Unit, onBack: () -> Unit) {
    val design = LocalDesign.current
    val scope = rememberCoroutineScope()
    var name by remember(id) { mutableStateOf("") }
    var tracks by remember(id) { mutableStateOf<List<Track>?>(null) }
    var error by remember(id) { mutableStateOf<String?>(null) }
    var renaming by remember(id) { mutableStateOf(false) }
    var draft by remember(id) { mutableStateOf("") }
    var reload by remember(id) { mutableIntStateOf(0) }
    var artist by remember(id) { mutableStateOf<ArtistSummary?>(null) }

    LaunchedEffect(id, reload, LibraryState.revision) {
        Api.playlist(id).fold(
            onSuccess = { (title, list) ->
                name = title
                tracks = list
                draft = title
                error = null
            },
            onFailure = { error = it.message ?: "could not load this playlist" },
        )
    }

    LazyColumn(
        contentPadding = PaddingValues(design.screenPadding, 10.dp, design.screenPadding, 24.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        item { ScreenBack(onBack = onBack) }
        item {
            ScreenTitle(
                name.ifBlank { "Playlist" },
                "${tracks?.size ?: 0} tracks",
            )
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                GhostButton(if (renaming) "Cancel" else "Rename", onClick = { renaming = !renaming })
                GhostButton("Delete", danger = true) {
                    scope.launch {
                        Api.deletePlaylist(id).onSuccess { tracks = emptyList(); name = "Deleted" }
                            .onFailure { error = it.message ?: "could not delete the playlist" }
                    }
                }
                if (!tracks.isNullOrEmpty()) {
                    PrimaryButton("Play all") {
                        Playback.play(tracks!!, 0)
                        onOpenPlayer()
                    }
                }
            }
        }
        if (renaming) {
            item {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Box(Modifier.weight(1f)) { McField(draft, { draft = it }, "Playlist name") }
                    PrimaryButton("Save", enabled = draft.isNotBlank()) {
                        scope.launch {
                            Api.renamePlaylist(id, draft.trim()).fold(
                                onSuccess = { name = draft.trim(); renaming = false },
                                onFailure = { error = it.message ?: "could not rename the playlist" },
                            )
                        }
                    }
                }
            }
        }
        error?.let { item { ErrorLine(it) } }
        when {
            tracks == null -> item { Loading("Loading playlist…") }
            tracks!!.isEmpty() -> item {
                EmptyState(
                    icon = Lucide.ListMusic,
                    title = "Empty playlist",
                    body = "Add tracks from an album or a search result.",
                )
            }
            else -> items(tracks!!, key = { it.id }) { track ->
                TrackRow(
                    track,
                    menu = true,
                    onClick = {
                        Playback.play(tracks!!, tracks!!.indexOf(track))
                        onOpenPlayer()
                    },
                    trailing = {
                        IconButton(Lucide.Trash) {
                            scope.launch {
                                Api.removeFromPlaylist(id, track.id).fold(
                                    onSuccess = { reload++ },
                                    onFailure = { error = it.message ?: "could not remove the track" },
                                )
                            }
                        }
                    },
                    onOpenArtist = { name ->
                        artist = ArtistSummary(name, 0, 0, track.id)
                    },
                )
            }
        }
        if (tracks != null) {
            item { Muted("Tracks can also be added from the web client; this list is the same data.", Modifier.padding(top = 6.dp)) }
        }
    }
    artist?.let {
        CollectionSheet(
            CollectionKind.Artist,
            it.artist,
            onDismiss = { artist = null },
            onOpenPlayer = onOpenPlayer,
        )
    }
}
```

### `gui/android/app/src/main/java/dev/mcmusic/app/ui/screens/Search.kt`

```kotlin
package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Account
import dev.mcmusic.app.data.AlbumSummary
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.ArtistSummary
import dev.mcmusic.app.data.LibraryState
import dev.mcmusic.app.data.Listener
import dev.mcmusic.app.data.SearchResults
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.ui.Cover
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.ErrorLine
import dev.mcmusic.app.ui.Loading
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.McField
import dev.mcmusic.app.ui.Muted
import dev.mcmusic.app.ui.SectionLabel
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.TrackRow
import dev.mcmusic.app.ui.visibleTracks
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

/** Grouped search, the same three buckets `/api/search` returns to the site. */
@Composable
fun SearchScreen(onPlaylist: (Int) -> Unit, onOpenPlayer: () -> Unit) {
    val design = LocalDesign.current
    val uriHandler = LocalUriHandler.current
    var query by remember { mutableStateOf("") }
    var results by remember { mutableStateOf<SearchResults?>(null) }
    var people by remember { mutableStateOf<List<Listener>>(emptyList()) }
    var error by remember { mutableStateOf<String?>(null) }
    var searching by remember { mutableStateOf(false) }
    var album by remember { mutableStateOf<AlbumSummary?>(null) }
    var artist by remember { mutableStateOf<ArtistSummary?>(null) }
    var searchJob by remember { mutableStateOf<Job?>(null) }

    suspend fun runSearch(text: String) {
        if (text.isBlank()) {
            results = null
            people = emptyList()
            error = null
            searching = false
            return
        }
        searching = true
        // The public directory works before sign-in; the music index does not.
        Api.listening().fold(
            onSuccess = { all ->
                people = all.filter { it.username.contains(text.trim(), ignoreCase = true) }
            },
            onFailure = { people = emptyList() },
        )
        Api.now(text.trim()).fold(
            onSuccess = { exact ->
                if (exact != null && people.none { it.username.equals(exact.username, ignoreCase = true) }) {
                    people = listOf(exact) + people
                }
            },
            onFailure = {},
        )
        if (Account.me == null) {
            results = null
            searching = false
            return
        }
        Api.search(text).fold(
            onSuccess = { results = it; error = null },
            onFailure = { error = it.message ?: "search failed"; results = null },
        )
        searching = false
    }

    // Cancel the previous request so a slow earlier query cannot overwrite the
    // results of a newer one.
    LaunchedEffect(query, Account.me?.id, LibraryState.revision) {
        searchJob?.cancel()
        searchJob = launch {
            delay(250)
            runSearch(query)
        }
    }

    LazyColumn(
        contentPadding = PaddingValues(start = design.screenPadding, end = design.screenPadding, top = 10.dp, bottom = 24.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        item { ScreenTitle("Search", "Tracks, albums, artists and people.") }
        item {
            McField(
                value = query,
                onValueChange = { query = it },
                label = "What do you want to hear?",
                keyboard = KeyboardOptions(imeAction = ImeAction.Search),
                actions = KeyboardActions(onSearch = { }),
            )
        }
        if (searching) item { Loading("Searching…") }
        error?.let { item { ErrorLine(it) } }

        val found = results
        if (!searching && found == null && query.isBlank()) {
            item {
                EmptyState(
                    icon = Lucide.Search,
                    title = "Find something to play",
                    body = "Search by song, album or artist. Results come from the same index the website uses.",
                )
            }
        }
        if (people.isNotEmpty()) {
            item { SectionLabel("People") }
            items(people, key = { "p-${it.username}" }) { person ->
                Row(
                    Modifier.fillMaxWidth().mcSurface(RoundedCornerShape(design.cardRadius))
                        .clickable(enabled = person.profileUrl.isNotBlank()) {
                            Api.externalUrl(person.profileUrl)?.let { runCatching { uriHandler.openUri(it) } }
                        }
                        .padding(10.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    Cover(
                        url = person.coverUrl.ifBlank { person.profileUrl },
                        shape = CircleShape,
                        modifier = Modifier.size(40.dp),
                        fallback = design.accentSoft,
                    )
                    Column(Modifier.weight(1f)) {
                        Text(person.username, color = design.accentText, fontSize = 14.sp, fontWeight = FontWeight.Medium)
                        Text(
                            person.track?.let { "${it.title} · ${it.artist}" }
                                ?: if (person.listening) "listening" else "offline",
                            color = design.dim,
                            fontSize = 11.sp,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                        )
                    }
                    dev.mcmusic.app.ui.LucideIcon(Lucide.User, design.dim, size = 16.dp)
                }
            }
        }
        if (found != null) {
            val shownTracks = found.tracks.visibleTracks()
            if (found.artists.isNotEmpty()) {
                item { SectionLabel("Artists") }
                items(found.artists, key = { "a-${it.artist}" }) { entry ->
                    Row(
                        Modifier.fillMaxWidth().mcSurface(RoundedCornerShape(design.cardRadius))
                            .clickable { artist = entry }
                            .padding(10.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(10.dp),
                    ) {
                        Cover(
                            url = albumCoverUrl(entry.coverId),
                            shape = CircleShape,
                            modifier = Modifier.size(40.dp),
                            fallback = design.accentSoft,
                        )
                        Column(Modifier.weight(1f)) {
                            Text(entry.artist, color = design.fg, fontSize = 14.sp, fontWeight = FontWeight.Medium)
                            Text(
                                if (entry.albums > 0) "${entry.count} tracks · ${entry.albums} albums"
                                else "${entry.count} tracks",
                                color = design.dim,
                                fontSize = 11.sp,
                            )
                        }
                    }
                }
            }
            if (found.albums.isNotEmpty()) {
                item { SectionLabel("Albums") }
                items(found.albums, key = { "b-${it.album}" }) { entry ->
                    Row(
                        Modifier.fillMaxWidth().mcSurface(RoundedCornerShape(design.cardRadius))
                            .clickable { album = entry }
                            .padding(10.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(10.dp),
                    ) {
                        Cover(
                            url = albumCoverUrl(entry.coverId),
                            shape = RoundedCornerShape(20.dp),
                            modifier = Modifier.size(40.dp),
                            fallback = design.accentSoft,
                        )
                        Column(Modifier.weight(1f)) {
                            Text(entry.album, color = design.fg, fontSize = 14.sp, fontWeight = FontWeight.Medium, maxLines = 1, overflow = TextOverflow.Ellipsis)
                            Text("${entry.artist} · ${entry.count} tracks", color = design.dim, fontSize = 11.sp, maxLines = 1)
                        }
                    }
                }
            }
            if (shownTracks.isNotEmpty()) {
                item { SectionLabel("Tracks") }
                items(shownTracks, key = { "t-${it.id}" }) { track ->
                    TrackRow(track, menu = true, onClick = {
                        Playback.play(shownTracks, shownTracks.indexOf(track))
                        onOpenPlayer()
                    }, onOpenArtist = { name ->
                        artist = ArtistSummary(name, 0, 0, track.id)
                    })
                }
            }
            if (shownTracks.isEmpty() && found.albums.isEmpty() && found.artists.isEmpty() && people.isEmpty()) {
                item {
                    EmptyState(
                        icon = Lucide.Search,
                        title = "No matches",
                        body = "Nothing matched \"$query\". Try a shorter phrase.",
                    )
                }
            }
        }
    }

    album?.let {
        CollectionSheet(CollectionKind.Album, it.album, onDismiss = { album = null }, onOpenPlayer = onOpenPlayer)
    }
    artist?.let {
        CollectionSheet(CollectionKind.Artist, it.artist, onDismiss = { artist = null }, onOpenPlayer = onOpenPlayer)
    }
}
```

### `gui/android/app/src/main/java/dev/mcmusic/app/ui/screens/Settings.kt`

```kotlin
package dev.mcmusic.app.ui.screens

import android.content.Intent
import android.net.Uri
import android.os.Build
import android.provider.Settings as AndroidSettings
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.BuildConfig
import dev.mcmusic.app.data.Account
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.AppUpdate
import dev.mcmusic.app.data.IconStroke
import dev.mcmusic.app.data.SELFHOST_GUIDE_URL
import dev.mcmusic.app.data.AutoDownload
import dev.mcmusic.app.data.Downloads
import dev.mcmusic.app.data.DownloadSource
import dev.mcmusic.app.data.LinkEvents
import dev.mcmusic.app.data.LinkStatus
import dev.mcmusic.app.data.Prefs
import dev.mcmusic.app.data.Updater
import dev.mcmusic.app.ui.ErrorLine
import dev.mcmusic.app.ui.GhostButton
import dev.mcmusic.app.ui.IconButton
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.McField
import dev.mcmusic.app.ui.Muted
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.SectionLabel
import dev.mcmusic.app.ui.SettingCard
import dev.mcmusic.app.ui.SettingDivider
import dev.mcmusic.app.ui.SettingRow
import dev.mcmusic.app.ui.SwitchRow
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.ui.design.DesignLanguage
import dev.mcmusic.app.ui.design.DynamicColour
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.Palettes
import dev.mcmusic.app.ui.formatBytes
import dev.mcmusic.app.widget.Widgets
import kotlinx.coroutines.launch

/**
 * Settings is the web client's account + preferences page: who you are, which
 * server you talk to, motion, download rules and local storage. The admin entry
 * only appears for admins, and signing out drops the shell back to Home.
 */
@Composable
fun SettingsScreen(onAdmin: () -> Unit, onSignedOut: () -> Unit) {
    val design = LocalDesign.current
    val scope = rememberCoroutineScope()
    val context = LocalContext.current
    val me = Account.me

    var error by remember { mutableStateOf<String?>(null) }
    var notice by remember { mutableStateOf<String?>(null) }
    var palettePicker by remember { mutableStateOf(false) }
    var iconStrokePicker by remember { mutableStateOf(false) }
    var addSource by remember { mutableStateOf(false) }

    var server by remember { mutableStateOf(Prefs.server) }
    var email by remember { mutableStateOf("") }
    var oldPassword by remember { mutableStateOf("") }
    var newPassword by remember { mutableStateOf("") }
    var showAccountTools by remember { mutableStateOf(false) }

    var update by remember { mutableStateOf<AppUpdate?>(null) }
    var checking by remember { mutableStateOf(false) }
    var downloading by remember { mutableStateOf(false) }
    var progress by remember { mutableIntStateOf(0) }
    var updateError by remember { mutableStateOf<String?>(null) }

    var roturStatus by remember { mutableStateOf<LinkStatus?>(null) }
    var discordStatus by remember { mutableStateOf<LinkStatus?>(null) }
    var linking by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(me?.id) { email = me?.email.orEmpty() }

    fun loadLinkStatus() {
        scope.launch {
            roturStatus = Api.linkStatus("rotur").getOrNull()
            discordStatus = Api.linkStatus("discord").getOrNull()
        }
    }

    // The browser hands the finished OAuth flow back through mcmusic://oauth.
    LaunchedEffect(LinkEvents.revision) { loadLinkStatus() }

    fun beginLink(provider: String) {
        linking = provider
        scope.launch {
            Api.linkTicket(provider).fold(
                onSuccess = { ticket ->
                    val url = Api.linkAuthorizeUrl(provider, ticket)
                    runCatching { context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url))) }
                        .onFailure { error = it.message ?: "no browser available" }
                },
                onFailure = { error = it.message ?: "could not start linking" },
            )
            linking = null
        }
    }

    fun finishUnlink(provider: String) {
        linking = provider
        scope.launch {
            Api.unlink(provider).fold(
                onSuccess = {
                    notice = when (provider) {
                        "rotur" -> "Rotur account unlinked."
                        else -> "Discord account unlinked."
                    }
                    loadLinkStatus()
                },
                onFailure = { error = it.message ?: "could not unlink" },
            )
            linking = null
        }
    }

    fun openUrl(url: String) {
        runCatching { context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url))) }
            .onFailure { error = it.message ?: "no browser available" }
    }

    fun linkSubtitle(status: LinkStatus?): String = when {
        status == null -> "Status unavailable — pull to retry"
        !status.configured -> "Not configured on this server"
        status.linked && status.username != null -> "Linked as ${status.username}"
        status.linked -> "Linked"
        status.reason.isNotBlank() -> "Not linked · ${status.reason}"
        else -> "Not linked — connect to share activity"
    }

    fun checkUpdate() {
        checking = true
        updateError = null
        scope.launch {
            Updater.check().fold(
                onSuccess = { update = it },
                onFailure = { updateError = it.message ?: "could not check for updates" },
            )
            checking = false
        }
    }

    fun installUpdate() {
        val found = update ?: return
        downloading = true
        progress = 0
        updateError = null
        scope.launch {
            Updater.download(context, found) { progress = it }.fold(
                onSuccess = { file ->
                    runCatching { Updater.install(context, file) }
                        .onFailure { updateError = it.message ?: "could not start the installer" }
                    downloading = false
                },
                onFailure = {
                    updateError = it.message ?: "download failed"
                    downloading = false
                },
            )
        }
    }

    LaunchedEffect(Unit) { checkUpdate() }

    LazyColumn(
        contentPadding = PaddingValues(design.screenPadding, 10.dp, design.screenPadding, 32.dp),
        verticalArrangement = Arrangement.spacedBy(9.dp),
    ) {
        item { ScreenTitle("Settings", "Account, server and this device.") }
        error?.let { item { ErrorLine(it) } }
        notice?.let { item { Muted(it) } }

        item { SectionLabel("Account") }
        if (me != null) {
            item {
                SettingCard {
                    SettingRow("Signed in as ${me.username}", me.email ?: "no email on file", icon = Lucide.User)
                    SettingDivider()
                    SettingRow("Account tools", "Email and password", icon = Lucide.Lock) {
                        GhostButton(if (showAccountTools) "Hide" else "Open") { showAccountTools = !showAccountTools }
                    }
                }
            }
            if (showAccountTools) {
                item {
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        McField(email, { email = it }, "Email", keyboard = KeyboardOptions(keyboardType = KeyboardType.Email))
                        GhostButton("Save email") {
                            scope.launch {
                                Api.setEmail(email.trim()).fold(
                                    onSuccess = { Account.refresh(); notice = "Email saved." },
                                    onFailure = { error = it.message ?: "could not save the email" },
                                )
                            }
                        }
                        McField(oldPassword, { oldPassword = it }, "Current password", password = true)
                        McField(newPassword, { newPassword = it }, "New password", password = true)
                        GhostButton("Change password") {
                            scope.launch {
                                Api.changePassword(oldPassword, newPassword).fold(
                                    onSuccess = {
                                        oldPassword = ""; newPassword = ""
                                        notice = "Password changed."
                                    },
                                    onFailure = { error = it.message ?: "could not change the password" },
                                )
                            }
                        }
                    }
                }
            }
            if (Account.isAdmin) {
                item {
                    SettingCard {
                        SettingRow("Admin", "Users, invites and the download queue", icon = Lucide.Server, onClick = onAdmin)
                    }
                }
            }
            item {
                SettingCard {
                    SettingRow(
                        "Sign out",
                        danger = true,
                        icon = Lucide.LogOut,
                        onClick = {
                            scope.launch {
                                Account.signOut()
                                onSignedOut()
                            }
                        },
                    )
                }
            }
        }

        item { SectionLabel("Server") }
        item {
            SettingCard {
                SettingRow(
                    "Server URL",
                    "Where streams, covers and API calls go",
                    icon = Lucide.Server,
                    value = Prefs.server,
                )
                SettingDivider()
                SettingRow(
                    "App version",
                    "This Android client",
                    icon = Lucide.Info,
                    value = "${BuildConfig.VERSION_NAME} (${BuildConfig.VERSION_CODE})",
                )
                SettingDivider()
                SettingRow(
                    "Self-hosting guide",
                    "Run mcmusic on your own server",
                    icon = Lucide.House,
                    onClick = {
                        runCatching {
                            context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(SELFHOST_GUIDE_URL)))
                        }
                    },
                )
            }
        }
        item {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                McField(server, { server = it }, "Server URL", keyboard = KeyboardOptions(keyboardType = KeyboardType.Uri))
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    GhostButton("Save server") {
                        Prefs.saveServer(server)
                        server = Prefs.server
                        notice = "Server saved. Restart the app if the session does not follow."
                    }
                    GhostButton("Reset default") {
                        Prefs.saveServer(Prefs.DEFAULT_SERVER)
                        server = Prefs.server
                    }
                }
                Muted("Streams, covers and the API all follow this address.")
            }
        }

        item { SectionLabel("Appearance") }
        item {
            SettingCard {
                SettingRow(
                    "Palette",
                    "Five families, System, and wallpaper on Android 12+",
                    icon = Lucide.Palette,
                    value = when (Prefs.palette) {
                        DynamicColour.WALLPAPER -> "Wallpaper"
                        Palettes.AUTO -> "System (${DynamicColour.resolve(Prefs.palette, isSystemInDarkTheme()).label})"
                        else -> DynamicColour.resolve(Prefs.palette, isSystemInDarkTheme()).label
                    },
                    onClick = { palettePicker = true },
                )
                SettingDivider()
                SwitchRow(
                    "Colour from cover",
                    "Tint the app with the playing artwork; real sleeves stay unchanged",
                    icon = Lucide.Image,
                    checked = Prefs.dynamicColour,
                    onChange = { Prefs.saveDynamicColour(it) },
                )
                SettingDivider()
                SettingRow(
                    "Icon width",
                    "Lucide outline thickness; filled icons are not available",
                    icon = Lucide.Pencil,
                    value = Prefs.iconStroke.label,
                    onClick = { iconStrokePicker = true },
                )
                SettingDivider()
                SettingRow(
                    "Design language",
                    "One shared layout in this build",
                    icon = Lucide.Compass,
                    value = DesignLanguage.from(Prefs.language).label,
                    onClick = { Prefs.saveLanguage(DesignLanguage.Flufi.id) },
                )
                SettingDivider()
                SwitchRow(
                    "Show song covers",
                    "Artwork in lists and tiles",
                    icon = Lucide.Image,
                    checked = Prefs.showCovers,
                    onChange = { Prefs.saveShowCovers(it) },
                )
                SettingDivider()
                SwitchRow(
                    "Hide explicit tracks",
                    "Filters tracks flagged explicit by the server",
                    icon = Lucide.EyeOff,
                    checked = Prefs.hideExplicit,
                    onChange = { Prefs.saveHideExplicit(it) },
                )
            }
        }
        item {
            if (palettePicker) {
                val activeId = Palettes.resolve(Prefs.palette, isSystemInDarkTheme()).id
                val activeFamily = Palettes.families.firstOrNull {
                    it.light.id == activeId || it.dark.id == activeId
                }?.id
                AlertDialog(
                    onDismissRequest = { palettePicker = false },
                    title = { Text("Palette") },
                    text = {
                        Column {
                            Palettes.families.forEach { option ->
                                TextButton(onClick = {
                                    Prefs.savePalette(option.id)
                                    Widgets.refresh(context)
                                    palettePicker = false
                                }) {
                                    Text(
                                        if (activeFamily == option.id) "${option.label} (selected)"
                                        else option.label
                                    )
                                }
                            }
                            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                                TextButton(onClick = {
                                    DynamicColour.refreshWallpaper(context)
                                    Prefs.savePalette(DynamicColour.WALLPAPER)
                                    Widgets.refresh(context)
                                    palettePicker = false
                                }) {
                                    Text(
                                        if (Prefs.palette == DynamicColour.WALLPAPER) "Wallpaper (selected)"
                                        else "Wallpaper"
                                    )
                                }
                            }
                            TextButton(onClick = {
                                Prefs.savePalette(Palettes.AUTO)
                                Widgets.refresh(context)
                                palettePicker = false
                            }) {
                                Text(if (Prefs.palette == Palettes.AUTO) "System (selected)" else "System")
                            }
                        }
                    },
                    confirmButton = { TextButton(onClick = { palettePicker = false }) { Text("Done") } },
                )
            }
            if (iconStrokePicker) {
                AlertDialog(
                    onDismissRequest = { iconStrokePicker = false },
                    title = { Text("Icon width") },
                    text = {
                        Column {
                            IconStroke.choices.forEach { option ->
                                TextButton(onClick = {
                                    Prefs.saveIconStroke(option)
                                    iconStrokePicker = false
                                }) {
                                    Text(
                                        if (Prefs.iconStroke == option) "${option.label} (selected)"
                                        else option.label
                                    )
                                }
                            }
                        }
                    },
                    confirmButton = { TextButton(onClick = { iconStrokePicker = false }) { Text("Done") } },
                )
            }
            if (addSource) {
                AddSourceDialog(
                    dismiss = { addSource = false },
                    add = { source ->
                        Prefs.saveDownloadSources(Prefs.downloadSources + source)
                        addSource = false
                        scope.launch { AutoDownload.runIfAllowed(force = true) }
                    },
                )
            }
        }

        item { SectionLabel("Social") }
        item {
            SettingCard {
                SwitchRow(
                    "Rotur activity",
                    "Share what you are listening to on Rotur",
                    icon = Lucide.Server,
                    checked = Prefs.roturActivity,
                    onChange = { enabled ->
                        Prefs.saveRoturActivity(enabled)
                        Playback.activitySettingChanged()
                    },
                )
                SettingDivider()
                SwitchRow(
                    "Discord activity",
                    "Share what you are listening to on Discord",
                    icon = Lucide.MessageCircle,
                    checked = Prefs.discordActivity,
                    onChange = { enabled ->
                        Prefs.saveDiscordActivity(enabled)
                        Playback.activitySettingChanged()
                    },
                )
                SettingDivider()
                SettingRow(
                    "Rotur account",
                    linkSubtitle(roturStatus),
                    icon = Lucide.Link,
                    trailing = {
                        GhostButton(
                            if (linking == "rotur") "Working…"
                            else if (roturStatus?.linked == true) "Unlink"
                            else "Connect",
                            danger = roturStatus?.linked == true,
                        ) {
                            if (roturStatus?.linked == true) finishUnlink("rotur") else beginLink("rotur")
                        }
                    },
                )
                SettingDivider()
                SettingRow(
                    "Discord account",
                    linkSubtitle(discordStatus),
                    icon = Lucide.Link,
                    trailing = {
                        GhostButton(
                            if (linking == "discord") "Working…"
                            else if (discordStatus?.linked == true) "Unlink"
                            else "Connect",
                            danger = discordStatus?.linked == true,
                        ) {
                            if (discordStatus?.linked == true) finishUnlink("discord") else beginLink("discord")
                        }
                    },
                )
                SettingDivider()
                SettingRow(
                    "Rotur on the web",
                    "rotur.dev",
                    icon = Lucide.Compass,
                    onClick = { openUrl("https://rotur.dev") },
                )
                SettingDivider()
                SettingRow(
                    "Discord on the web",
                    "discord.com",
                    icon = Lucide.MessageCircle,
                    onClick = { openUrl("https://discord.com") },
                )
            }
        }

        item { SectionLabel("Auto-download") }
        item {
            SettingCard {
                SwitchRow(
                    "Keep Faves offline",
                    "Saves the metrics-ranked top songs on this device",
                    icon = Lucide.Radio,
                    checked = Prefs.autoFaves,
                    onChange = {
                        Prefs.saveAutoFaves(it)
                        if (it) scope.launch { AutoDownload.runIfAllowed(force = true) }
                    },
                )
                SettingDivider()
                SettingRow(
                    "Faves connection",
                    "Wi-Fi only, stable connection, or any connection",
                    icon = Lucide.Wifi,
                    value = networkLabel(Prefs.autoFavesNetwork),
                    onClick = {
                        val next = when (Prefs.autoFavesNetwork) {
                            "wifi" -> "stable"
                            "stable" -> "any"
                            else -> "wifi"
                        }
                        Prefs.saveAutoFavesNetwork(next)
                    },
                )
                Prefs.downloadSources.forEachIndexed { index, source ->
                    SettingDivider()
                    SettingRow(
                        source.name,
                        "Tap to change the connection rule",
                        icon = Lucide.Download,
                        value = networkLabel(source.network),
                        onClick = {
                            val next = when (source.network) {
                                "wifi" -> "stable"
                                "stable" -> "any"
                                else -> "wifi"
                            }
                            Prefs.saveDownloadSources(
                                Prefs.downloadSources.toMutableList().also { it[index] = source.copy(network = next) },
                            )
                        },
                        trailing = {
                            IconButton(Lucide.Trash) {
                                Prefs.saveDownloadSources(Prefs.downloadSources.filterIndexed { i, _ -> i != index })
                            }
                        },
                    )
                }
                SettingDivider()
                SettingRow(
                    "Add a source",
                    "Keep a playlist, artist, album or Likes offline",
                    icon = Lucide.ListPlus,
                    onClick = { addSource = true },
                )
                if (Prefs.downloadSources.isNotEmpty()) {
                    SettingDivider()
                    SettingRow(
                        "Sync now",
                        "Respects each source's connection rule",
                        icon = Lucide.RefreshCw,
                        onClick = { scope.launch { AutoDownload.runIfAllowed(force = true) } },
                    )
                }
            }
        }

        item { SectionLabel("Playback and data") }
        item {
            SettingCard {
                SwitchRow(
                    "Playful motion",
                    "Springs, shape morphs and taps; system reduce-motion still wins",
                    icon = Lucide.RefreshCw,
                    checked = Prefs.playfulMotion,
                    onChange = { Prefs.savePlayfulMotion(it) },
                )
                SettingDivider()
                SwitchRow(
                    "Download over Wi-Fi only",
                    "Blocks downloads on mobile data.",
                    icon = Lucide.Wifi,
                    checked = Prefs.wifiOnly,
                    onChange = { Prefs.saveWifiOnly(it) },
                )
                SettingDivider()
                SettingRow(
                    "Downloads",
                    "${Downloads.items.size} tracks · ${formatBytes(Downloads.totalBytes())}",
                    icon = Lucide.HardDrive,
                )
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    SettingDivider()
                    SettingRow(
                        "Notifications",
                        "Keep music playing when the screen is off",
                        icon = Lucide.Info,
                        onClick = {
                            runCatching {
                                context.startActivity(
                                    Intent(AndroidSettings.ACTION_APP_NOTIFICATION_SETTINGS)
                                        .putExtra(AndroidSettings.EXTRA_APP_PACKAGE, context.packageName),
                                )
                            }
                        },
                    )
                }
            }
        }

        item { SectionLabel("Update") }
        item {
            SettingCard {
                SettingRow(
                    "Version",
                    if (checking) "checking the server…"
                    else update?.let { "Update available: ${it.version}" } ?: "You are on the newest build",
                    icon = Lucide.RefreshCw,
                    value = Updater.currentVersion,
                )
                SettingDivider()
                if (update != null && !downloading) {
                    SettingRow(
                        "Install update",
                        "Downloads the signed APK from this server",
                        icon = Lucide.Download,
                        onClick = { installUpdate() },
                    )
                } else {
                    SettingRow(
                        if (downloading) "Downloading $progress%" else "Check for updates",
                        "Uses the same build the website serves",
                        icon = Lucide.RefreshCw,
                        onClick = { if (!downloading) checkUpdate() },
                    )
                }
                if (downloading) {
                    LinearProgressIndicator(
                        progress = { progress / 100f },
                        modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 6.dp),
                        color = design.accent,
                        trackColor = design.hairline,
                    )
                }
                updateError?.let { ErrorLine(it) }
            }
        }

        item { SectionLabel("About") }
        item {
            SettingCard {
                SettingRow("mcmusic Android", "Native client for the mcmusic server", icon = Lucide.Info)
                SettingDivider()
                SettingRow("Server", Prefs.server.removePrefix("https://").removePrefix("http://"), icon = Lucide.Server)
                SettingDivider()
                SettingRow(
                    "Build",
                    "Compose · Media3",
                    icon = Lucide.Library,
                    value = BuildConfig.VERSION_NAME,
                )
            }
        }
        item {
            Text(
                "Playback continues in the notification shade. Cover art and catalogs come from the same API the web client uses.",
                color = design.dim,
                fontSize = 11.sp,
                lineHeight = 16.sp,
                fontWeight = FontWeight.Normal,
                modifier = Modifier.padding(top = 4.dp, bottom = 8.dp),
            )
        }
    }
}

private fun networkLabel(network: String): String = when (network) {
    "stable" -> "Stable"
    "any" -> "Any connection"
    else -> "Wi-Fi only"
}

/** Picker for the managed offline sources shown in the Auto-download card. */
@Composable
private fun AddSourceDialog(dismiss: () -> Unit, add: (DownloadSource) -> Unit) {
    var playlists by remember { mutableStateOf<List<dev.mcmusic.app.data.Playlist>>(emptyList()) }
    var artists by remember { mutableStateOf<List<dev.mcmusic.app.data.ArtistSummary>>(emptyList()) }
    var albums by remember { mutableStateOf<List<dev.mcmusic.app.data.AlbumSummary>>(emptyList()) }
    LaunchedEffect(Unit) {
        Api.playlists().onSuccess { playlists = it }
        Api.search("").onSuccess {
            artists = it.artists.take(20)
            albums = it.albums.take(20)
        }
    }
    AlertDialog(
        onDismissRequest = dismiss,
        title = { Text("Keep offline") },
        text = {
            Column {
                TextButton(onClick = { add(DownloadSource("likes", "likes", "Liked songs")) }) {
                    Text("Liked songs")
                }
                playlists.forEach { playlist ->
                    TextButton(onClick = {
                        add(DownloadSource("playlist", playlist.id.toString(), playlist.name))
                    }) { Text(playlist.name) }
                }
                artists.forEach { artist ->
                    TextButton(onClick = {
                        add(DownloadSource("artist", artist.artist, artist.artist))
                    }) { Text(artist.artist) }
                }
                albums.forEach { album ->
                    TextButton(onClick = {
                        add(DownloadSource("album", album.album, album.album))
                    }) { Text(album.album) }
                }
            }
        },
        confirmButton = { TextButton(onClick = dismiss) { Text("Done") } },
    )
}
```

### `gui/android/app/src/main/java/dev/mcmusic/app/ui/screens/SignIn.kt`

```kotlin
package dev.mcmusic.app.ui.screens

import android.content.Intent
import android.net.Uri
import androidx.activity.compose.BackHandler
import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Account
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.Prefs
import dev.mcmusic.app.data.SELFHOST_GUIDE_URL
import dev.mcmusic.app.ui.ErrorLine
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.LucideIcon
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface
import kotlinx.coroutines.launch

/** The brief flat screen while a saved token is verified on cold start. */
@Composable
fun AuthSplash() {
    val design = LocalDesign.current
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(18.dp),
        ) {
            Box(
                Modifier.size(44.dp).clip(RoundedCornerShape(design.tileRadius)).background(design.accent),
                Alignment.Center,
            ) {
                Text("m", color = design.onAccent, fontSize = 24.sp, fontWeight = FontWeight.Bold)
            }
            Text("mcmusic", color = design.fg, fontSize = 20.sp, fontWeight = FontWeight.SemiBold)
            LinearProgressIndicator(
                modifier = Modifier.width(120.dp).height(3.dp).clip(RoundedCornerShape(4.dp)),
                color = design.accentText,
                trackColor = design.hairline,
            )
        }
    }
}

/**
 * The sign-in gate. Nothing in the app is reachable until [Account.signIn] or
 * [Account.acceptRoturToken] publishes a verified account, so the shell below
 * this screen never has to guess whether a stored token still works.
 *
 * Styling follows flufimusic v3 exactly: flat ink surfaces, one 10dp radius,
 * hairline borders, and a single violet interaction colour.
 */
@Composable
fun SignInScreen() {
    val design = LocalDesign.current
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    // Back must not drop the user into a half-unlocked shell.
    BackHandler(enabled = true) {}

    var identifier by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var showServer by remember { mutableStateOf(false) }
    var server by remember { mutableStateOf(Prefs.server) }

    val appear = remember { Animatable(if (Prefs.motion) 0f else 1f) }
    LaunchedEffect(Unit) {
        if (Prefs.playfulMotion) appear.animateTo(1f, tween(320, easing = FastOutSlowInEasing))
    }

    fun submit() {
        if (identifier.isBlank() || password.isBlank() || busy) return
        busy = true
        error = null
        scope.launch {
            Account.signIn(identifier.trim(), password).fold(
                onSuccess = { password = "" },
                onFailure = { error = it.message ?: "could not sign in" },
            )
            busy = false
        }
    }

    fun openRotur() {
        val url = "${Prefs.server}/api/auth/rotur/authorize?app=1" +
            "&device_hash=${Uri.encode(Api.deviceHash)}"
        runCatching {
            context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
        }.onFailure { error = it.message ?: "no browser available" }
    }

    fun openSelfHostGuide() {
        runCatching {
            context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(SELFHOST_GUIDE_URL)))
        }.onFailure { error = it.message ?: "no browser available" }
    }

    Box(
        Modifier
            .fillMaxSize()
            .statusBarsPadding()
            .navigationBarsPadding()
            .imePadding(),
    ) {
        Column(
            Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .graphicsLayer {
                    alpha = appear.value
                    translationY = (1f - appear.value) * 18.dp.toPx()
                }
                .padding(horizontal = 24.dp, vertical = 26.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    Modifier.size(34.dp).clip(RoundedCornerShape(design.tileRadius)).background(design.accent),
                    Alignment.Center,
                ) {
                    Text("m", color = design.onAccent, fontSize = 19.sp, fontWeight = FontWeight.Bold)
                }
                Spacer(Modifier.width(10.dp))
                Column {
                    Text("mcmusic", color = design.fg, fontSize = 19.sp, fontWeight = FontWeight.SemiBold)
                    Text("your room, your rules", color = design.dim, fontSize = 10.sp)
                }
            }

            Box(Modifier.fillMaxWidth().height(1.dp).background(design.hairline))

            Column(verticalArrangement = Arrangement.spacedBy(5.dp)) {
                Text("Welcome back", color = design.fg, fontSize = 28.sp, fontWeight = FontWeight.Bold)
                Text(
                    "Sign in for your library, playlists and downloads.",
                    color = design.dim,
                    fontSize = 13.sp,
                )
            }

            Column(
                Modifier.fillMaxWidth().mcSurface().padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                AuthField(
                    icon = Lucide.Mail,
                    label = "Email or username",
                    value = identifier,
                    onChange = { identifier = it },
                    imeAction = ImeAction.Next,
                )
                AuthField(
                    icon = Lucide.Lock,
                    label = "Password",
                    value = password,
                    onChange = { password = it },
                    password = true,
                    imeAction = ImeAction.Done,
                    done = { submit() },
                )

                error?.let { ErrorLine(it) }
                Account.gateError?.let { reason ->
                    ErrorLine(reason)
                    Box(
                        Modifier
                            .clip(RoundedCornerShape(design.tileRadius))
                            .border(1.dp, design.hairline, RoundedCornerShape(design.tileRadius))
                            .clickable { scope.launch { Account.refresh() } }
                            .padding(horizontal = 14.dp, vertical = 9.dp),
                    ) {
                        Text("Retry connection", color = design.accentText, fontSize = 12.sp, fontWeight = FontWeight.Medium)
                    }
                }

                Box(
                    Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(design.tileRadius))
                        .background(if (busy) design.accentSoft else design.accent)
                        .clickable(enabled = !busy) { submit() }
                        .padding(vertical = 13.dp),
                    contentAlignment = Alignment.Center,
                ) {
                    if (busy) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(18.dp),
                            strokeWidth = 2.dp,
                            color = design.accentText,
                        )
                    } else {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            Text("Sign in", color = design.onAccent, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
                            LucideIcon(Lucide.ChevronRight, design.onAccent, size = 16.dp)
                        }
                    }
                }

                Row(
                    Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    Box(Modifier.weight(1f).height(1.dp).background(design.hairline))
                    Text("or", color = design.dim, fontSize = 11.sp)
                    Box(Modifier.weight(1f).height(1.dp).background(design.hairline))
                }

                Box(
                    Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(design.tileRadius))
                        .border(1.dp, design.hairline, RoundedCornerShape(design.tileRadius))
                        .background(design.accentWash)
                        .clickable { openRotur() }
                        .padding(vertical = 12.dp),
                    contentAlignment = Alignment.Center,
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        LucideIcon(Lucide.User, design.accentText, size = 16.dp)
                        Text("Continue with Rotur", color = design.fg, fontSize = 13.sp, fontWeight = FontWeight.Medium)
                    }
                }
            }

            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                FeatureChip(Lucide.Library, "Library")
                FeatureChip(Lucide.ListMusic, "Playlists")
                FeatureChip(Lucide.Download, "Offline")
            }

            Column {
                Row(
                    Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(design.tileRadius))
                        .clickable { showServer = !showServer }
                        .padding(vertical = 8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    LucideIcon(Lucide.Server, design.dim, size = 15.dp)
                    Text(
                        "Server: ${Prefs.server.removePrefix("https://").removePrefix("http://")}",
                        color = design.dim,
                        fontSize = 11.sp,
                        modifier = Modifier.weight(1f),
                    )
                    LucideIcon(Lucide.ChevronRight, design.dim, size = 14.dp)
                }
                if (showServer) {
                    AuthField(
                        icon = Lucide.Server,
                        label = "Server URL",
                        value = server,
                        onChange = { server = it },
                        imeAction = ImeAction.Done,
                        done = {
                            Prefs.saveServer(server)
                            server = Prefs.server
                        },
                    )
                    Spacer(Modifier.height(8.dp))
                    Box(
                        Modifier
                            .clip(RoundedCornerShape(design.tileRadius))
                            .border(1.dp, design.hairline, RoundedCornerShape(design.tileRadius))
                            .clickable {
                                Prefs.saveServer(server)
                                server = Prefs.server
                            }
                            .padding(horizontal = 14.dp, vertical = 9.dp),
                    ) {
                        Text("Use this server", color = design.accentText, fontSize = 12.sp, fontWeight = FontWeight.Medium)
                    }
                }
            }

            Spacer(Modifier.height(8.dp))
            Text(
                "New accounts need an invite from an admin.",
                color = design.dim,
                fontSize = 11.sp,
            )
            Row(
                Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(design.tileRadius))
                    .clickable { openSelfHostGuide() }
                    .padding(vertical = 6.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(7.dp),
            ) {
                LucideIcon(Lucide.Info, design.accentText, size = 14.dp)
                Column {
                    Text("Self-hosting guide", color = design.accentText, fontSize = 11.sp, fontWeight = FontWeight.Medium)
                    Text(
                        "Point this app at your own mcmusic server.",
                        color = design.dim,
                        fontSize = 10.sp,
                    )
                }
            }
        }
    }
}

@Composable
private fun AuthField(
    icon: Int,
    label: String,
    value: String,
    onChange: (String) -> Unit,
    password: Boolean = false,
    imeAction: ImeAction = ImeAction.Next,
    done: () -> Unit = {},
) {
    val design = LocalDesign.current
    OutlinedTextField(
        value = value,
        onValueChange = onChange,
        label = { Text(label, fontSize = 12.sp) },
        singleLine = true,
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(design.tileRadius),
        textStyle = TextStyle(color = design.fg, fontSize = 14.sp),
        visualTransformation = if (password) PasswordVisualTransformation() else VisualTransformation.None,
        leadingIcon = { LucideIcon(icon, design.dim, size = 17.dp) },
        keyboardOptions = KeyboardOptions(
            imeAction = imeAction,
            keyboardType = if (password) KeyboardType.Password else KeyboardType.Uri,
        ),
        keyboardActions = KeyboardActions(onDone = { done() }),
        colors = OutlinedTextFieldDefaults.colors(
            focusedTextColor = design.fg,
            unfocusedTextColor = design.fg,
            focusedBorderColor = design.accentText,
            unfocusedBorderColor = design.hairline,
            focusedLabelColor = design.accentText,
            unfocusedLabelColor = design.dim,
            focusedLeadingIconColor = design.accentText,
            unfocusedLeadingIconColor = design.dim,
            cursorColor = design.accentText,
            focusedContainerColor = design.accentWash,
            unfocusedContainerColor = design.accentWash,
        ),
    )
}

@Composable
private fun FeatureChip(icon: Int, label: String) {
    val design = LocalDesign.current
    Row(
        Modifier
            .clip(RoundedCornerShape(design.tileRadius))
            .border(1.dp, design.hairline, RoundedCornerShape(design.tileRadius))
            .background(design.accentWash)
            .padding(horizontal = 10.dp, vertical = 7.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        LucideIcon(icon, design.accentText, size = 14.dp)
        Text(label, color = design.dim, fontSize = 11.sp, fontWeight = FontWeight.Medium)
    }
}
```

### `gui/android/app/src/main/java/dev/mcmusic/app/ui/screens/Videos.kt`

```kotlin
package dev.mcmusic.app.ui.screens

import android.view.SurfaceView
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.datasource.DefaultHttpDataSource
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.exoplayer.source.DefaultMediaSourceFactory
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.VideoInfo
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.playback.checkedFactory
import dev.mcmusic.app.ui.Cover
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.ErrorLine
import dev.mcmusic.app.ui.IconButton
import dev.mcmusic.app.ui.Loading
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.Muted
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.SectionLabel
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface
import dev.mcmusic.app.ui.formatMillis
import dev.mcmusic.app.ui.trackCoverUrl
import kotlinx.coroutines.delay

/**
 * Videos imported with a request live on the server for four hours after the
 * last view. This pane plays that local file with ExoPlayer — no YouTube embed
 * and no second set of controls from a web view.
 */
@Composable
fun VideosScreen(
    ytId: String? = null,
    startMs: Long = 0L,
    onBack: () -> Unit,
    onPlay: (String, Long) -> Unit,
    onClosed: (Long?) -> Unit,
) {
    if (!ytId.isNullOrBlank()) {
        VideoPlaybackScreen(ytId, startMs, onBack, onClosed)
        return
    }
    val design = LocalDesign.current
    var videos by remember { mutableStateOf<List<VideoInfo>?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var reload by remember { mutableStateOf(0) }

    LaunchedEffect(reload) {
        Api.videos().fold(
            onSuccess = { videos = it; error = null },
            onFailure = { error = it.message ?: "could not load videos"; videos = emptyList() },
        )
    }

    LazyColumn(
        contentPadding = PaddingValues(design.screenPadding, 10.dp, design.screenPadding, 24.dp),
        verticalArrangement = Arrangement.spacedBy(9.dp),
    ) {
        item {
            ScreenTitle("Videos", "Music videos saved with your requests.")
        }
        error?.let { item { ErrorLine(it) } }
        item {
            SectionLabel("Cached for four hours after your last view") {
                IconButton(Lucide.RefreshCw, size = 16.dp) { reload++ }
            }
        }
        val list = videos.orEmpty()
        if (list.isEmpty()) {
            item {
                EmptyState(
                    icon = Lucide.Film,
                    title = "No videos yet",
                    body = "Import a YouTube link, then its video appears here alongside the music.",
                )
            }
        }
        items(list, key = { it.ytId }) { video ->
            Row(
                Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(design.cardRadius))
                    .mcSurface()
                    .clickable { onPlay(video.ytId, 0L) }
                    .padding(10.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(11.dp),
            ) {
                Cover(
                    url = video.trackId?.let { trackCoverUrl(it) }.orEmpty(),
                    shape = RoundedCornerShape(8.dp),
                    modifier = Modifier.size(58.dp),
                    fallback = design.accentSoft,
                )
                Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                    Text(
                        video.title.ifBlank { video.ytId },
                        color = design.fg,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.SemiBold,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                    Muted(video.artist.ifBlank { "Saved on this server" }, size = 11)
                    Muted("Expires ${formatExpiry(video.expires)}", size = 10)
                }
                IconButton(Lucide.Play, tint = design.accentText) { onPlay(video.ytId, 0L) }
            }
        }
        item {
            Muted(
                "Videos play from mcmusic's own cache. Watching one keeps it for another four hours.",
                size = 11,
            )
        }
    }
}

private fun formatExpiry(expires: Long): String {
    val minutes = ((expires - System.currentTimeMillis() / 1000) / 60).coerceAtLeast(0)
    return if (minutes >= 60) "${minutes / 60}h ${minutes % 60}m" else "${minutes}m"
}

/** Full-screen local video with controls and the current song's start position. */
@Composable
private fun VideoPlaybackScreen(
    ytId: String,
    startMs: Long,
    onBack: () -> Unit,
    onClosed: (Long?) -> Unit,
) {
    val context = LocalContext.current
    val design = LocalDesign.current
    var info by remember(ytId) { mutableStateOf<VideoInfo?>(null) }
    var error by remember(ytId) { mutableStateOf<String?>(null) }

    LaunchedEffect(ytId) {
        Playback.duckForVideo()
        while (true) {
            val result = Api.video(ytId, prepare = info == null)
            if (result.isSuccess) {
                val found = result.getOrThrow()
                info = found
                error = null
                if (found.state == "ready") break
            } else {
                error = result.exceptionOrNull()?.message ?: "could not reach the server"
            }
            delay(1_500)
        }
    }

    val url = info?.url
    if (url.isNullOrBlank()) {
        LazyColumn(
            Modifier.fillMaxSize(),
            contentPadding = PaddingValues(design.screenPadding),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            item { ScreenTitle("Video", info?.title ?: ytId) }
            error?.let { item { ErrorLine(it) } }
            item {
                Loading(
                    when (info?.state) {
                        "preparing" -> "Saving this video for offline playback…"
                        else -> "Looking for this video…"
                    },
                )
            }
            item { Muted("It will play as soon as the server finishes caching it.", size = 11) }
        }
        return
    }

    val player = remember(url) {
        val source = checkedFactory(DefaultHttpDataSource.Factory()
            .setUserAgent("mcmusic-android")
            .setDefaultRequestProperties(Api.authHeaders()))
        ExoPlayer.Builder(context)
            .setMediaSourceFactory(DefaultMediaSourceFactory(source))
            .build()
            .apply {
                setMediaItem(MediaItem.fromUri(Api.videoUrl(ytId)))
                prepare()
                if (startMs > 0) seekTo(startMs)
                playWhenReady = true
            }
    }
    var playing by remember(url) { mutableStateOf(true) }
    var position by remember(url) { mutableLongStateOf(startMs) }
    var duration by remember(url) { mutableLongStateOf(0L) }
    var scrub by remember(url) { mutableFloatStateOf(0f) }

    DisposableEffect(player) {
        val listener = object : Player.Listener {
            override fun onPlaybackStateChanged(state: Int) {
                duration = player.duration.coerceAtLeast(0)
            }

            override fun onIsPlayingChanged(value: Boolean) {
                playing = value
            }
        }
        player.addListener(listener)
        onDispose {
            val finalPosition = player.currentPosition
            player.removeListener(listener)
            player.release()
            Playback.unduckFromVideo(finalPosition)
            onClosed(finalPosition)
        }
    }

    LaunchedEffect(Unit) {
        while (true) {
            position = player.currentPosition
            if (duration <= 0) duration = player.duration.coerceAtLeast(0)
            delay(500)
        }
    }

    val fraction = if (duration > 0) scrub.takeIf { it != 0f } ?: (position.toFloat() / duration) else 0f
    Column(
        Modifier
            .fillMaxSize()
            .background(design.palette.bg)
            .padding(horizontal = 10.dp, vertical = 12.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            IconButton(Lucide.ChevronLeft) { onBack() }
            Column(Modifier.weight(1f)) {
                Text(
                    info?.title ?: ytId,
                    color = design.fg,
                    fontSize = 15.sp,
                    fontWeight = FontWeight.SemiBold,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                Muted(info?.artist.orEmpty(), size = 11)
            }
        }
        Box(
            Modifier
                .fillMaxWidth()
                .aspectRatio(16f / 9f)
                .clip(RoundedCornerShape(design.cardRadius))
                .background(design.palette.bg2),
        ) {
            AndroidView(
                factory = { ctx ->
                    SurfaceView(ctx).also { player.setVideoSurfaceView(it) }
                },
                modifier = Modifier.fillMaxSize(),
            )
        }
        Slider(
            value = fraction.coerceIn(0f, 1f),
            onValueChange = { scrub = it },
            onValueChangeFinished = {
                if (duration > 0) player.seekTo((duration * scrub).toLong())
                scrub = 0f
            },
            colors = SliderDefaults.colors(
                thumbColor = design.accentText,
                activeTrackColor = design.accentText,
                inactiveTrackColor = design.hairline,
            ),
        )
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Muted(formatMillis(position), size = 11)
            Muted(formatMillis(duration), size = 11)
        }
        Row(
            Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(Lucide.SkipBack, size = 20.dp) { player.seekToMaxToPrevious() }
            Box(
                Modifier
                    .size(54.dp)
                    .clip(RoundedCornerShape(50))
                    .background(design.accent)
                    .clickable {
                        if (playing) player.pause() else player.play()
                    },
                Alignment.Center,
            ) {
                dev.mcmusic.app.ui.LucideIcon(
                    if (playing) Lucide.Pause else Lucide.Play,
                    design.onAccent,
                    size = 20.dp,
                )
            }
            IconButton(Lucide.SkipForward, size = 20.dp) { player.seekTo(player.currentPosition + 10_000L) }
        }
        Muted("Audio follows the video; your music resumes where you left it when you go back.", size = 11)
    }
}

private fun ExoPlayer.seekToMaxToPrevious() = seekTo((currentPosition - 10_000L).coerceAtLeast(0L))
```

