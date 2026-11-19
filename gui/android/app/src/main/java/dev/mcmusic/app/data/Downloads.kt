package dev.mcmusic.app.data

import android.content.Context
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.URL

data class Download(
    val id: Int,
    val title: String,
    val artist: String,
    val album: String,
    val duration: Double,
    val bytes: Long,
)

/**
 * Offline copies of tracks, stored as opaque blobs in app storage with a JSON
 * index. The audio comes from the same authenticated stream endpoint, so the
 * session cookie is what makes a download possible; playback prefers the local
 * file whenever one exists.
 */
object Downloads {
    var items by mutableStateOf<List<Download>>(emptyList())
        private set

    var active by mutableStateOf<Set<Int>>(emptySet())
        private set

    private var dir: File? = null
    private var appContext: Context? = null

    fun init(context: Context) {
        if (dir != null) return
        appContext = context.applicationContext
        val d = File(context.filesDir, "downloads").apply { mkdirs() }
        dir = d
        items = readIndex(d)
    }

    fun totalBytes(): Long = items.sumOf { it.bytes }

    fun clearAll() {
        val d = dir ?: return
        d.listFiles()?.forEach { runCatching { it.delete() } }
        items = emptyList()
        writeIndex(d)
    }

    /** True when the phone is on Wi-Fi or ethernet, or the state is unknown. */
    private fun onWifi(): Boolean {
        val ctx = appContext ?: return true
        val cm = ctx.getSystemService(Context.CONNECTIVITY_SERVICE) as? android.net.ConnectivityManager
            ?: return true
        val caps = cm.getNetworkCapabilities(cm.activeNetwork) ?: return false
        return caps.hasTransport(android.net.NetworkCapabilities.TRANSPORT_WIFI) ||
            caps.hasTransport(android.net.NetworkCapabilities.TRANSPORT_ETHERNET)
    }

    fun file(id: Int): File? = dir?.let { File(it, "$id.audio") }?.takeIf { it.exists() && it.length() > 0 }

    fun isDownloaded(id: Int): Boolean = file(id) != null

    suspend fun download(track: Track): Result<Download> = withContext(Dispatchers.IO) {
        val d = dir ?: return@withContext Result.failure(IllegalStateException("downloads are not ready"))
        if (Prefs.wifiOnly && !onWifi()) {
            return@withContext Result.failure(
                IllegalStateException("Downloads are set to Wi-Fi only — connect to Wi-Fi to save this track."),
            )
        }
        active = active + track.id
        try {
            val tmp = File(d, "${track.id}.part")
            val conn = (URL(Api.streamUrl(track.id)).openConnection() as HttpURLConnection).apply {
                connectTimeout = 15_000
                readTimeout = 60_000
                setRequestProperty("Accept", "audio/*")
                Api.authHeaders().forEach { (name, value) -> setRequestProperty(name, value) }
            }
            try {
                if (conn.responseCode !in 200..299) {
                    throw ApiException(conn.responseCode, "server said ${conn.responseCode}")
                }
                conn.inputStream.use { input -> tmp.outputStream().use { out -> input.copyTo(out) } }
            } finally {
                conn.disconnect()
            }
            val target = File(d, "${track.id}.audio")
            if (target.exists()) target.delete()
            if (!tmp.renameTo(target)) throw IllegalStateException("could not store the file")
            val entry = Download(
                id = track.id,
                title = track.title,
                artist = track.artist,
                album = track.album,
                duration = track.duration,
                bytes = target.length(),
            )
            items = (items.filterNot { it.id == entry.id } + entry).sortedBy { it.title.lowercase() }
            writeIndex(d)
            Result.success(entry)
        } catch (e: Exception) {
            runCatching { File(d, "${track.id}.part").delete() }
            Result.failure(e)
        } finally {
            active = active - track.id
        }
    }

    fun remove(id: Int) {
        val d = dir ?: return
        file(id)?.delete()
        items = items.filterNot { it.id == id }
        writeIndex(d)
    }

    private fun readIndex(d: File): List<Download> = runCatching {
        val arr = JSONArray(File(d, "index.json").readText())
        buildList {
            for (i in 0 until arr.length()) {
                val o = arr.optJSONObject(i) ?: continue
                val id = o.optInt("id")
                add(
                    Download(
                        id = id,
                        title = o.optString("title"),
                        artist = o.optString("artist"),
                        album = o.optString("album"),
                        duration = o.optDouble("duration", 0.0),
                        bytes = o.optLong("bytes"),
                    ),
                )
            }
        }
    }.getOrDefault(emptyList()).filter { File(d, "${it.id}.audio").exists() }

    private fun writeIndex(d: File) {
        val arr = JSONArray()
        items.forEach { e ->
            arr.put(
                JSONObject()
                    .put("id", e.id)
                    .put("title", e.title)
                    .put("artist", e.artist)
                    .put("album", e.album)
                    .put("duration", e.duration)
                    .put("bytes", e.bytes),
            )
        }
        runCatching { File(d, "index.json").writeText(arr.toString()) }
    }
}
