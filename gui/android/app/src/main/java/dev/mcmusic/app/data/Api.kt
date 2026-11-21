package dev.mcmusic.app.data

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.net.CookieHandler
import java.net.CookieManager
import java.net.CookiePolicy
import java.net.CookieStore
import java.net.HttpCookie
import java.net.HttpURLConnection
import java.net.URI
import java.net.URL

data class Track(
    val id: Int,
    val title: String,
    val artist: String,
    val album: String,
    val duration: Double,
)

data class Listener(
    val username: String,
    val listening: Boolean,
    val position: Double,
    val track: Track?,
    val coverUrl: String,
    val profileUrl: String,
    val updated: Long = 0,
)

data class Me(
    val id: Int,
    val username: String,
    val isAdmin: Boolean,
    val email: String? = null,
    val roturLinked: Boolean = false,
)

data class Playlist(
    val id: Int,
    val name: String,
    val count: Int,
    val coverId: Int?,
)

data class AlbumSummary(
    val album: String,
    val artist: String,
    val count: Int,
    val coverId: Int?,
)

data class ArtistSummary(
    val artist: String,
    val count: Int,
    val albums: Int,
    val coverId: Int?,
)

data class HomeSection(val title: String, val tracks: List<Track>)

data class HomeFeed(val sections: List<HomeSection>, val albums: List<AlbumSummary>)

data class SearchResults(
    val tracks: List<Track>,
    val albums: List<AlbumSummary>,
    val artists: List<ArtistSummary>,
)

data class AdminStats(
    val users: Int,
    val admins: Int,
    val tracks: Int,
    val albums: Int,
    val playlists: Int,
    val plays: Int,
    val pending: Int,
    val approved: Int,
    val running: Int,
    val failed: Int,
    val done: Int,
    val queue: Int,
    val rooms: Int,
    val musicBytes: Long,
    val diskFree: Long,
    val diskTotal: Long,
    val uptime: Long,
)

data class AdminUser(
    val id: Int,
    val username: String,
    val email: String?,
    val isAdmin: Boolean,
    val created: Long,
    val plays: Int,
    val likes: Int,
    val playlists: Int,
    val requests: Int,
)

data class InviteCode(
    val id: Int,
    val code: String,
    val uses: Int,
    val maxUses: Int,
    val expires: Long,
    val note: String,
    val forUser: String,
    val active: Boolean,
    val createdByName: String,
    val usedBy: List<String>,
)

data class DownloadRequest(
    val id: Int,
    val url: String,
    val status: String,
    val username: String,
    val running: Boolean,
    val elapsed: Long,
    val log: String,
)

/**
 * The whole HTTP side of the client. Session cookies are kept the way the web
 * app keeps them (Flask session cookie), so a signed-in phone can use the same
 * authed endpoints the site does.
 */
object Api {
    private lateinit var cookies: PersistentCookieStore
    private lateinit var appContext: Context

    val server: String get() = Prefs.server

    /** Stable identity used for both device pairing and playback heartbeats. */
    val deviceHash: String
        get() = "android-" + android.provider.Settings.Secure.getString(
            appContext.contentResolver,
            android.provider.Settings.Secure.ANDROID_ID,
        )

    val deviceName: String get() = android.os.Build.MODEL ?: "Android"

    fun init(context: Context) {
        if (::cookies.isInitialized) return
        appContext = context.applicationContext
        cookies = PersistentCookieStore(appContext)
        CookieHandler.setDefault(CookieManager(cookies, CookiePolicy.ACCEPT_ALL))
    }

    suspend fun listening(): Result<List<Listener>> = call {
        val body = get("/api/public/listening")
        val users = JSONObject(body).optJSONArray("users") ?: return@call emptyList()
        buildList {
            for (i in 0 until users.length()) {
                val u = users.optJSONObject(i) ?: continue
                add(listenerOf(u))
            }
        }
    }

    suspend fun now(username: String): Result<Listener?> = call {
        JSONObject(get("/api/public/now/${enc(username)}")).let { listenerOf(it) }
    }

    /**
     * Sign in with the password and keep the returned device token. Every later
     * request sends it as `Authorization: Bearer`, so nothing depends on a
     * cookie jar surviving the trip.
     */
    suspend fun login(username: String, password: String): Result<Me> = call {
        val body = JSONObject()
            .put("username", username)
            .put("password", password)
            .put("device", deviceName)
            .put("device_hash", deviceHash)
            .toString()
        val json = JSONObject(post("/api/auth/app/login", body))
        val token = json.optString("token")
        if (token.isBlank()) throw ApiException(500, "the server did not return a sign-in token")
        val previous = Prefs.token
        Prefs.saveToken(token)
        // The token only counts once the server accepts it as this account.
        val verified = runCatching { meOf(JSONObject(get("/api/me"))) }.getOrNull()
        if (verified == null) {
            Prefs.saveToken(previous)
            throw ApiException(401, "Signed in, but the server did not accept the new token.")
        }
        Prefs.saveUsername(verified.username)
        verified
    }

    suspend fun logout() {
        // Close presence while the token still resolves the user, then revoke it.
        runCatching { post("/api/logout", "{}") }
        runCatching { post("/api/auth/app/logout", "{}") }
        cookies.clear()
        Prefs.saveToken(null)
        Prefs.saveUsername(null)
    }

    suspend fun changePassword(old: String, new: String): Result<Unit> = call {
        val body = JSONObject().put("old", old).put("new", new).toString()
        request("/api/password", "POST", body)
        Unit
    }

    suspend fun setEmail(email: String): Result<Me> = call {
        val body = JSONObject().put("email", email).toString()
        meOf(JSONObject(post("/api/auth/email", body)))
    }

    suspend fun me(): Me? = runCatching { meOf(JSONObject(get("/api/me"))) }.getOrNull()

    /** Personalised feed: made-for-you sections plus recently added albums. */
    suspend fun home(): Result<HomeFeed> = call {
        val json = JSONObject(get("/api/home"))
        val sections = buildList {
            val arr = json.optJSONArray("sections")
            if (arr != null) {
                for (i in 0 until arr.length()) {
                    val section = arr.optJSONObject(i) ?: continue
                    val tracks = tracksOf(section.optJSONArray("tracks"))
                    if (tracks.isNotEmpty()) add(HomeSection(section.optString("title"), tracks))
                }
            }
        }
        HomeFeed(sections, albumsOf(json.optJSONArray("albums")))
    }

    /** The same grouped search the website uses: tracks, albums and artists. */
    suspend fun search(query: String): Result<SearchResults> = call {
        val json = JSONObject(get("/api/search?q=${enc(query)}"))
        SearchResults(
            tracks = tracksOf(json.optJSONArray("tracks")),
            albums = albumsOf(json.optJSONArray("albums")),
            artists = artistsOf(json.optJSONArray("artists")),
        )
    }

    suspend fun albumTracks(name: String): Result<List<Track>> = call {
        tracksOf(JSONObject(get("/api/album?name=${enc(name)}")).optJSONArray("tracks"))
    }

    suspend fun artistTracks(name: String): Result<List<Track>> = call {
        tracksOf(JSONObject(get("/api/artist?name=${enc(name)}")).optJSONArray("tracks"))
    }

    suspend fun toggleLike(id: Int): Result<Boolean> = call {
        JSONObject(post("/api/like/$id", "{}")).optBoolean("liked")
    }

    // --- playback presence ------------------------------------------------

    /** Count one play so the server's Faves and admin stats stay honest. */
    suspend fun recordPlay(trackId: Int, completed: Boolean = false): Result<Unit> = call {
        request(
            "/api/plays",
            "POST",
            JSONObject().put("track_id", trackId).put("completed", completed).toString(),
        )
        Unit
    }

    /** Keep this phone visible in Devices and public listening views. */
    suspend fun heartbeat(trackId: Int?, positionMs: Long, paused: Boolean): Result<Unit> = call {
        request(
            "/api/devices/heartbeat",
            "POST",
            JSONObject()
                .put("device_hash", deviceHash)
                .put("name", deviceName)
                .put("track_id", trackId)
                .put("position", positionMs / 1000.0)
                .put("paused", paused)
                .toString(),
        )
        Unit
    }

    /** Publish the queue and transport state for bots, rooms and other devices. */
    suspend fun pushPlayback(
        trackId: Int?,
        positionMs: Long,
        durationMs: Long,
        playing: Boolean,
        queue: List<Int>,
    ): Result<Unit> = call {
        val ids = JSONArray()
        queue.take(200).forEach(ids::put)
        request(
            "/api/playback",
            "POST",
            JSONObject()
                .put("track_id", trackId)
                .put("position", positionMs / 1000.0)
                .put("duration", durationMs / 1000.0)
                .put("playing", playing)
                .put("queue", ids)
                .put("device", deviceHash)
                .toString(),
        )
        Unit
    }

    // --- admin ------------------------------------------------------------

    suspend fun adminStats(): Result<AdminStats> = call {
        val j = JSONObject(get("/api/admin/stats"))
        val req = j.optJSONObject("requests")
        fun count(key: String) = req?.optInt(key) ?: 0
        AdminStats(
            users = j.optInt("users"),
            admins = j.optInt("admins"),
            tracks = j.optInt("tracks"),
            albums = j.optInt("albums"),
            playlists = j.optInt("playlists"),
            plays = j.optInt("plays"),
            pending = count("pending"),
            approved = count("approved"),
            running = count("running"),
            failed = count("failed"),
            done = count("done"),
            queue = j.optInt("queue"),
            rooms = j.optInt("rooms"),
            musicBytes = j.optLong("music_bytes"),
            diskFree = j.optLong("disk_free"),
            diskTotal = j.optLong("disk_total"),
            uptime = j.optLong("uptime"),
        )
    }

    suspend fun adminUsers(): Result<List<AdminUser>> = call {
        val arr = JSONObject(get("/api/admin/users")).optJSONArray("users") ?: return@call emptyList()
        buildList {
            for (i in 0 until arr.length()) {
                val u = arr.optJSONObject(i) ?: continue
                add(
                    AdminUser(
                        id = u.optInt("id"),
                        username = u.optString("username"),
                        email = u.optString("email").takeIf { it.isNotBlank() },
                        isAdmin = u.optBoolean("is_admin"),
                        created = u.optLong("created"),
                        plays = u.optInt("plays"),
                        likes = u.optInt("likes"),
                        playlists = u.optInt("playlists"),
                        requests = u.optInt("requests"),
                    ),
                )
            }
        }
    }

    suspend fun adminSetRole(id: Int, admin: Boolean): Result<Unit> = call {
        request("/api/admin/users/$id/admin", "POST", JSONObject().put("is_admin", admin).toString())
        Unit
    }

    suspend fun adminDeleteUser(id: Int): Result<Unit> = call {
        request("/api/admin/users/$id", "DELETE", null)
        Unit
    }

    suspend fun adminInvites(): Result<List<InviteCode>> = call {
        val arr = JSONObject(get("/api/admin/invite-codes")).optJSONArray("codes") ?: return@call emptyList()
        buildList {
            for (i in 0 until arr.length()) {
                val c = arr.optJSONObject(i) ?: continue
                val used = buildList {
                    val ub = c.optJSONArray("used_by")
                    if (ub != null) for (x in 0 until ub.length()) {
                        ub.optJSONObject(x)?.optString("username")?.takeIf { it.isNotBlank() }?.let(::add)
                    }
                }
                add(
                    InviteCode(
                        id = c.optInt("id"),
                        code = c.optString("code"),
                        uses = c.optInt("uses"),
                        maxUses = c.optInt("max_uses", 1),
                        expires = c.optLong("expires"),
                        note = c.optString("note"),
                        forUser = c.optString("for_user"),
                        active = c.optBoolean("active", true),
                        createdByName = c.optString("created_by_name"),
                        usedBy = used,
                    ),
                )
            }
        }
    }

    suspend fun adminCreateInvite(uses: Int, hours: Int, note: String): Result<String> = call {
        val body = JSONObject().put("uses", uses).put("hours", hours).put("note", note).toString()
        JSONObject(post("/api/admin/invite-codes", body)).optString("code")
    }

    suspend fun adminRevokeInvite(id: Int): Result<Unit> = call {
        request("/api/admin/invite-codes/$id", "DELETE", null)
        Unit
    }

    suspend fun adminScan(): Result<Pair<Int, Int>> = call {
        val j = JSONObject(post("/api/admin/scan", "{}"))
        j.optInt("tracks") to j.optInt("albums")
    }

    suspend fun adminRequests(): Result<List<DownloadRequest>> = call {
        val arr = JSONObject(get("/api/admin/requests")).optJSONArray("requests") ?: return@call emptyList()
        buildList {
            for (i in 0 until arr.length()) {
                val r = arr.optJSONObject(i) ?: continue
                add(
                    DownloadRequest(
                        id = r.optInt("id"),
                        url = r.optString("url"),
                        status = r.optString("status"),
                        username = r.optString("username"),
                        running = r.optBoolean("running"),
                        elapsed = r.optLong("elapsed"),
                        log = r.optString("log"),
                    ),
                )
            }
        }
    }

    /** approve/reject live on the user endpoint; cancel/retry/delete are admin-only. */
    suspend fun adminRequestAction(id: Int, action: String): Result<Unit> = call {
        when (action) {
            "approve", "reject" -> post("/api/requests/$id/$action", "{}")
            "delete" -> request("/api/admin/requests/$id", "DELETE", null)
            else -> post("/api/admin/requests/$id/$action", "{}")
        }
        Unit
    }

    suspend fun tracks(query: String = "", limit: Int = 200): Result<List<Track>> = call {
        val q = if (query.isBlank()) "" else "&q=${enc(query)}"
        val arr = JSONObject(get("/api/tracks?limit=$limit$q")).optJSONArray("tracks")
            ?: return@call emptyList()
        buildList {
            for (i in 0 until arr.length()) {
                val t = arr.optJSONObject(i) ?: continue
                add(trackOf(t))
            }
        }
    }

    suspend fun playlists(): Result<List<Playlist>> = call {
        val arr = JSONObject(get("/api/playlists")).optJSONArray("playlists")
            ?: return@call emptyList()
        buildList {
            for (i in 0 until arr.length()) {
                val p = arr.optJSONObject(i) ?: continue
                add(
                    Playlist(
                        id = p.optInt("id"),
                        name = p.optString("name"),
                        count = p.optInt("n"),
                        coverId = p.optInt("cover_id").takeIf { !p.isNull("cover_id") && it > 0 },
                    ),
                )
            }
        }
    }

    suspend fun playlist(id: Int): Result<Pair<String, List<Track>>> = call {
        val json = JSONObject(get("/api/playlists/$id"))
        val tracks = buildList {
            val arr = json.optJSONArray("tracks")
            if (arr != null) {
                for (i in 0 until arr.length()) {
                    val t = arr.optJSONObject(i) ?: continue
                    add(trackOf(t))
                }
            }
        }
        json.optString("name") to tracks
    }

    suspend fun createPlaylist(name: String): Result<Int> = call {
        val body = JSONObject().put("name", name).toString()
        JSONObject(post("/api/playlists", body)).optInt("id")
    }

    suspend fun renamePlaylist(id: Int, name: String): Result<Unit> = call {
        request("/api/playlists/$id", "PATCH", JSONObject().put("name", name).toString())
        Unit
    }

    suspend fun deletePlaylist(id: Int): Result<Unit> = call {
        request("/api/playlists/$id", "DELETE", null)
        Unit
    }

    suspend fun addToPlaylist(playlistId: Int, trackId: Int): Result<Unit> = call {
        request("/api/playlists/$playlistId/tracks", "POST", JSONObject().put("track_id", trackId).toString())
        Unit
    }

    suspend fun removeFromPlaylist(playlistId: Int, trackId: Int): Result<Unit> = call {
        request("/api/playlists/$playlistId/tracks/$trackId", "DELETE", null)
        Unit
    }

    /** Where ExoPlayer reads audio; the token travels with the request. */
    fun streamUrl(id: Int): String = server + "/api/tracks/$id/stream"

    /** Headers every authenticated media/image request needs. */
    fun authHeaders(): Map<String, String> =
        Prefs.token?.let { mapOf("Authorization" to "Bearer $it") } ?: emptyMap()

    /** Admin only; the server answers 403 for everyone else. */
    suspend fun deleteTrack(id: Int): Result<Unit> = call {
        request("/api/tracks/$id", "DELETE", null)
        Unit
    }

    suspend fun cover(url: String): ByteArray? = withContext(Dispatchers.IO) {
        if (url.isBlank()) return@withContext null
        runCatching {
            val conn = URL(url).openConnection() as HttpURLConnection
            conn.connectTimeout = 8000
            conn.readTimeout = 12000
            conn.setRequestProperty("Accept", "image/*")
            authHeaders().forEach { (name, value) -> conn.setRequestProperty(name, value) }
            conn.inputStream.use { it.readBytes() }
        }.getOrNull()
    }

    // --- plumbing ---------------------------------------------------------

    private fun listenerOf(u: JSONObject): Listener {
        val track = u.optJSONObject("track")?.let(::trackOf)
        val user = u.optJSONObject("user")
        return Listener(
            username = user?.optString("username").orEmpty().ifEmpty { u.optString("username") },
            listening = u.optBoolean("listening"),
            position = u.optDouble("position", 0.0),
            track = track,
            coverUrl = u.optString("cover_url"),
            profileUrl = u.optString("profile_url"),
            updated = u.optLong("updated"),
        )
    }

    private fun trackOf(t: JSONObject) = Track(
        id = t.optInt("id"),
        title = t.optString("title").ifEmpty { "Unknown track" },
        artist = t.optString("artist"),
        album = t.optString("album"),
        duration = t.optDouble("duration", 0.0),
    )

    private fun tracksOf(arr: JSONArray?): List<Track> {
        if (arr == null) return emptyList()
        return buildList {
            for (i in 0 until arr.length()) arr.optJSONObject(i)?.let { add(trackOf(it)) }
        }
    }

    private fun albumsOf(arr: JSONArray?): List<AlbumSummary> {
        if (arr == null) return emptyList()
        return buildList {
            for (i in 0 until arr.length()) {
                val a = arr.optJSONObject(i) ?: continue
                add(
                    AlbumSummary(
                        album = a.optString("album"),
                        artist = a.optString("artist"),
                        count = a.optInt("n"),
                        coverId = a.optInt("cover_id").takeIf { it > 0 },
                    ),
                )
            }
        }
    }

    private fun artistsOf(arr: JSONArray?): List<ArtistSummary> {
        if (arr == null) return emptyList()
        return buildList {
            for (i in 0 until arr.length()) {
                val a = arr.optJSONObject(i) ?: continue
                add(
                    ArtistSummary(
                        artist = a.optString("artist"),
                        count = a.optInt("n"),
                        albums = a.optInt("albums"),
                        coverId = a.optInt("cover_id").takeIf { it > 0 },
                    ),
                )
            }
        }
    }

    private fun meOf(j: JSONObject) = Me(
        id = j.optInt("id"),
        username = j.optString("username"),
        isAdmin = j.optBoolean("is_admin"),
        email = j.optString("email").takeIf { it.isNotBlank() },
        roturLinked = j.optBoolean("rotur_linked"),
    )

    private suspend fun <T> call(block: suspend () -> T): Result<T> =
        withContext(Dispatchers.IO) { runCatching { block() } }

    private fun get(path: String): String = request(path, "GET", null)

    private fun post(path: String, body: String): String = request(path, "POST", body)

    private fun request(path: String, method: String, body: String?): String {
        val conn = (URL(server + path).openConnection() as HttpURLConnection).apply {
            requestMethod = method
            connectTimeout = 10_000
            readTimeout = 15_000
            setRequestProperty("Accept", "application/json")
            Prefs.token?.let { setRequestProperty("Authorization", "Bearer $it") }
            if (body != null) {
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
            }
        }
        try {
            if (body != null) conn.outputStream.use { it.write(body.toByteArray()) }
            val code = conn.responseCode
            val text = (if (code in 200..299) conn.inputStream else conn.errorStream)
                ?.bufferedReader()?.use { it.readText() }.orEmpty()
            if (code !in 200..299) throw ApiException(code, errorMessage(text, code))
            return text
        } finally {
            conn.disconnect()
        }
    }

    private fun errorMessage(text: String, code: Int): String =
        runCatching { JSONObject(text).optString("error") }.getOrNull()
            ?.takeIf { it.isNotBlank() }
            ?: when (code) {
                401 -> "not signed in"
                404 -> "not found"
                else -> "server error $code"
            }

    private fun enc(s: String) = java.net.URLEncoder.encode(s, "UTF-8")
}

class ApiException(val code: Int, override val message: String) : Exception(message)

/**
 * Session cookies that survive a restart, so the app does not sign out on every
 * cold start. The whole cookie is stored, not just `name=value`: a restored
 * cookie has to keep its domain and path, or the next request never gets it and
 * the session looks lost right after signing in.
 */
private class PersistentCookieStore(context: Context) : CookieStore {
    private val sp = context.getSharedPreferences("cookies", Context.MODE_PRIVATE)
    private val lock = Any()
    private val jar = mutableListOf<HttpCookie>()

    init {
        // Older builds stored only "name=value", losing domain and path. Drop
        // that format once instead of restoring a half-broken session.
        if (sp.getInt(VERSION_KEY, 0) != VERSION) {
            sp.edit().clear().putInt(VERSION_KEY, VERSION).apply()
        } else {
            sp.all.values.forEach { raw ->
                if (raw is String) runCatching { decode(raw) }.getOrNull()?.let { jar.add(it) }
            }
        }
    }

    override fun add(uri: URI, cookie: HttpCookie) {
        synchronized(lock) {
            if (cookie.domain == null) cookie.domain = uri.host
            if (cookie.path.isNullOrEmpty()) cookie.path = "/"
            jar.removeAll { it.name == cookie.name && it.domain == cookie.domain && it.path == cookie.path }
            jar.add(cookie)
            sp.edit().putString(key(cookie), encode(cookie)).apply()
        }
    }

    override fun get(uri: URI): List<HttpCookie> = synchronized(lock) {
        val host = uri.host.orEmpty().lowercase()
        val path = uri.path.orEmpty().ifEmpty { "/" }
        val https = uri.scheme.equals("https", ignoreCase = true)
        jar.filter { c ->
            val domain = c.domain?.lowercase()
            val domainOk = domain == null || host == domain || host.endsWith(".$domain")
            val cookiePath = c.path.orEmpty().ifEmpty { "/" }
            val pathOk = path == cookiePath || path.startsWith(cookiePath.trimEnd('/') + "/")
            domainOk && pathOk && (https || !c.secure) && c.maxAge != 0L
        }
    }

    override fun getCookies(): List<HttpCookie> = synchronized(lock) { jar.toList() }

    override fun getURIs(): List<URI> = synchronized(lock) {
        jar.mapNotNull { it.domain }.distinct()
            .mapNotNull { d -> runCatching { URI("https://${d.trimStart('.')}") }.getOrNull() }
    }

    override fun remove(uri: URI, cookie: HttpCookie): Boolean = synchronized(lock) {
        sp.edit().remove(key(cookie)).apply()
        jar.removeAll { it.name == cookie.name && it.domain == cookie.domain && it.path == cookie.path }
        true
    }

    override fun removeAll(): Boolean = synchronized(lock) {
        jar.clear()
        sp.edit().clear().putInt(VERSION_KEY, VERSION).apply()
        true
    }

    fun clear() = synchronized(lock) {
        jar.clear()
        sp.edit().clear().putInt(VERSION_KEY, VERSION).apply()
    }

    private fun key(c: HttpCookie) = "${c.domain}|${c.path}|${c.name}"

    private fun encode(c: HttpCookie): String = JSONObject()
        .put("name", c.name)
        .put("value", c.value)
        .put("domain", c.domain.orEmpty())
        .put("path", c.path.orEmpty())
        .put("secure", c.secure)
        .put("httpOnly", c.isHttpOnly)
        .put("maxAge", c.maxAge)
        .toString()

    private fun decode(raw: String): HttpCookie {
        val o = JSONObject(raw)
        return HttpCookie(o.getString("name"), o.getString("value")).apply {
            o.optString("domain").takeIf { it.isNotBlank() }?.let { domain = it }
            o.optString("path").takeIf { it.isNotBlank() }?.let { path = it }
            secure = o.optBoolean("secure")
            isHttpOnly = o.optBoolean("httpOnly")
            maxAge = o.optLong("maxAge", -1L)
        }
    }

    private companion object {
        const val VERSION_KEY = "store_version"
        const val VERSION = 2
    }
}
