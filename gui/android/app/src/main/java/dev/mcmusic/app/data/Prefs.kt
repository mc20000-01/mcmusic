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
