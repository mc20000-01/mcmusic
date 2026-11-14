package dev.mcmusic.app.data

import android.content.Context
import dev.mcmusic.app.BuildConfig
import okhttp3.Cookie
import okhttp3.CookieJar
import okhttp3.HttpUrl

/**
 * Persists the mcmusic session cookie. The server authenticates every request
 * with the signed `mcmusic_session` cookie, exactly like the web client.
 */
class PrefsCookieJar(context: Context) : CookieJar {

    private val prefs = context.getSharedPreferences("mcmusic_cookies", Context.MODE_PRIVATE)

    override fun saveFromResponse(url: HttpUrl, cookies: List<Cookie>) {
        if (cookies.isEmpty()) return
        val edit = prefs.edit()
        for (c in cookies) edit.putString(c.name, c.value)
        edit.apply()
    }

    override fun loadForRequest(url: HttpUrl): List<Cookie> {
        val out = ArrayList<Cookie>()
        for ((name, value) in prefs.all) {
            if (value !is String || value.isEmpty()) continue
            out.add(
                Cookie.Builder()
                    .name(name)
                    .value(value)
                    .domain(url.host)
                    .path("/")
                    .build()
            )
        }
        return out
    }

    fun header(): String =
        prefs.all.entries
            .filter { it.value is String && (it.value as String).isNotEmpty() }
            .joinToString("; ") { "${it.key}=${it.value}" }

    fun hasSession(): Boolean = prefs.all.values.any { it is String && it.isNotEmpty() }

    fun clear() = prefs.edit().clear().apply()
}

class SessionStore(context: Context) {

    private val prefs = context.getSharedPreferences("mcmusic", Context.MODE_PRIVATE)
    val cookieJar = PrefsCookieJar(context)

    var baseUrl: String
        // `base_url_v2` is the post-migration key: anything saved before the
        // switch to mcmusic.sdisk.us is ignored once, and a server the user
        // enters from now on is honoured.
        get() = prefs.getString("base_url_v2", BuildConfig.DEFAULT_SERVER)
            ?: BuildConfig.DEFAULT_SERVER
        set(value) {
            prefs.edit().putString("base_url_v2", value).apply()
        }

    var cachedMe: String?
        get() = prefs.getString("me", null)
        set(value) {
            prefs.edit().putString("me", value).apply()
        }

    var settingsJson: String?
        get() = prefs.getString("settings", null)
        set(value) {
            prefs.edit().putString("settings", value).apply()
        }

    var theme: String
        get() = prefs.getString("theme", "ink") ?: "ink"
        set(value) {
            prefs.edit().putString("theme", value).apply()
        }

    var accent: String
        get() = prefs.getString("accent", "#a06bff") ?: "#a06bff"
        set(value) {
            prefs.edit().putString("accent", value).apply()
        }

    /** True once the listener picks a theme in-app, so server defaults can't override it. */
    var themeChosen: Boolean
        get() = prefs.getBoolean("theme_chosen", false)
        set(value) {
            prefs.edit().putBoolean("theme_chosen", value).apply()
        }

    var volume: Float
        get() = prefs.getFloat("volume", 0.8f)
        set(value) {
            prefs.edit().putFloat("volume", value).apply()
        }

    var deviceHash: String?
        get() = prefs.getString("device_hash", null)
        set(value) {
            prefs.edit().putString("device_hash", value).apply()
        }

    fun clearSession() {
        cookieJar.clear()
        cachedMe = null
    }
}
