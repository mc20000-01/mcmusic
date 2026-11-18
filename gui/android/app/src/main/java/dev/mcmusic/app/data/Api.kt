package dev.mcmusic.app.data

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
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

data class Me(val id: Int, val username: String, val isAdmin: Boolean)

/**
 * The whole HTTP side of the client. Session cookies are kept the way the web
 * app keeps them (Flask session cookie), so a signed-in phone can use the same
 * authed endpoints the site does.
 */
object Api {
    private lateinit var cookies: PersistentCookieStore

    val server: String get() = Prefs.server

    fun init(context: Context) {
        if (::cookies.isInitialized) return
        cookies = PersistentCookieStore(context)
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

    suspend fun login(username: String, password: String): Result<Me> = call {
        val body = JSONObject()
            .put("username", username)
            .put("password", password)
            .toString()
        val json = JSONObject(post("/api/login", body))
        val me = meOf(json)
        Prefs.saveUsername(me.username)
        me
    }

    suspend fun logout() {
        runCatching { post("/api/logout", "{}") }
        cookies.clear()
        Prefs.saveUsername(null)
    }

    suspend fun me(): Me? = runCatching { meOf(JSONObject(get("/api/me"))) }.getOrNull()

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

    /** Where ExoPlayer reads audio; session cookies travel with the request. */
    fun streamUrl(id: Int): String = server + "/api/tracks/$id/stream"

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

    private fun meOf(j: JSONObject) = Me(
        id = j.optInt("id"),
        username = j.optString("username"),
        isAdmin = j.optBoolean("is_admin"),
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

/** Session cookies that survive a restart, so the app does not sign out on every cold start. */
private class PersistentCookieStore(context: Context) : CookieStore {
    private val sp = context.getSharedPreferences("cookies", Context.MODE_PRIVATE)
    private val jar = sp.all.mapNotNull { (k, v) -> runCatching { HttpCookie.parse(v as String).first() }.getOrNull() }.toMutableList()
    private val lock = Any()

    override fun add(uri: URI, cookie: HttpCookie) {
        synchronized(lock) {
            jar.removeAll { it.name == cookie.name && it.domain == cookie.domain && it.path == cookie.path }
            jar.add(cookie)
            sp.edit().putString(key(cookie), cookie.toString()).apply()
        }
    }

    override fun get(uri: URI): List<HttpCookie> = synchronized(lock) {
        jar.filter { it.domain == null || uri.host.orEmpty().endsWith(it.domain.trimStart('.')) }
    }

    override fun getCookies(): List<HttpCookie> = synchronized(lock) { jar.toList() }

    override fun getURIs(): List<URI> = synchronized(lock) {
        jar.mapNotNull { it.domain }.distinct().mapNotNull { d -> runCatching { URI("https://${d.trimStart('.')}") }.getOrNull() }
    }

    override fun remove(uri: URI, cookie: HttpCookie): Boolean = synchronized(lock) {
        sp.edit().remove(key(cookie)).apply()
        jar.removeAll { it.name == cookie.name && it.domain == cookie.domain }
    }

    override fun removeAll(): Boolean = synchronized(lock) {
        sp.edit().clear().apply()
        jar.clear()
        true
    }

    fun clear() = synchronized(lock) {
        jar.clear()
        sp.edit().clear().apply()
    }

    private fun key(c: HttpCookie) = "${c.domain}|${c.path}|${c.name}"
}
