package dev.mcmusic.app.data

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONArray
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit

data class UpdateInfo(
    val version: String,
    val url: String,
    val notes: String,
    val size: Long,
) {
    /** True only when [version] is newer than [current], never on a downgrade. */
    fun isNewerThan(current: String): Boolean {
        val a = parts(version)
        val b = parts(current)
        for (i in 0 until maxOf(a.size, b.size)) {
            val cmp = a.getOrElse(i) { 0 }.compareTo(b.getOrElse(i) { 0 })
            if (cmp != 0) return cmp > 0
        }
        return false
    }

    private fun parts(raw: String): List<Int> =
        raw.trim().removePrefix("v")
            .split('.', '-', '+')
            .map { it.takeWhile(Char::isDigit).toIntOrNull() ?: 0 }
}

/**
 * Reads the newest published GitHub release. The release carries the same APK
 * the web download page serves, so updating here keeps both installs in step.
 */
object UpdateChecker {

    const val REPO = "mc20000-01/mcmusic"

    val client: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .build()

    suspend fun latest(): UpdateInfo? = withContext(Dispatchers.IO) {
        val request = Request.Builder()
            .url("https://api.github.com/repos/$REPO/releases/latest")
            .header("Accept", "application/vnd.github+json")
            .header("User-Agent", "mcmusic-android")
            .build()

        client.newCall(request).execute().use { response ->
            if (response.code == 404) return@withContext null
            if (!response.isSuccessful) throw IOException("GitHub returned ${response.code}")
            val text = response.body?.string().orEmpty()
            val release = runCatching { JSONObject(text) }.getOrNull() ?: return@withContext null

            val assets: JSONArray = release.optJSONArray("assets") ?: JSONArray()
            var apk: JSONObject? = null
            for (i in 0 until assets.length()) {
                val asset = assets.optJSONObject(i) ?: continue
                if (asset.optString("name").endsWith(".apk", ignoreCase = true)) {
                    apk = asset
                    break
                }
            }
            val asset = apk ?: return@withContext null
            val name = asset.optString("name")
            val version = Regex("""mcmusic-([0-9][^/]*)\.apk""")
                .find(name)?.groupValues?.getOrNull(1)
                ?: release.optString("tag_name").removePrefix("v")

            UpdateInfo(
                version = version,
                url = asset.optString("browser_download_url"),
                notes = release.optString("body"),
                size = asset.optLong("size"),
            )
        }
    }
}
