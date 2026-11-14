package dev.mcmusic.app.data

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

data class DownloadEntry(
    val id: Int,
    val title: String,
    val artist: String,
    val album: String,
    val duration: Double,
    val bytes: Long,
    val added: Long,
) {
    companion object {
        fun from(o: JSONObject) = DownloadEntry(
            id = o.optInt("id"),
            title = o.optString("title", "Unknown"),
            artist = o.optString("artist", ""),
            album = o.optString("album", ""),
            duration = o.optDouble("duration", 0.0),
            bytes = o.optLong("bytes"),
            added = o.optLong("added"),
        )
    }
}

/**
 * Keeps the audio bytes on the phone so playback works with no network.
 * The JSON sidecar is the index: any entry whose file has vanished (cleared
 * cache, failed write) is dropped on read instead of showing a dead row.
 */
class DownloadStore(private val context: Context, private val api: Api) {

    private val dir: File
        get() = File(context.filesDir, "downloads").apply { mkdirs() }

    private val indexFile: File
        get() = File(context.filesDir, "downloads.json")

    fun fileFor(id: Int): File? =
        File(dir, "$id.audio").takeIf { it.isFile && it.length() > 0 }

    fun isDownloaded(id: Int): Boolean = fileFor(id) != null

    fun entries(): List<DownloadEntry> = readIndex().filter { fileFor(it.id) != null }

    fun bytes(): Long = entries().sumOf { fileFor(it.id)?.length() ?: 0L }

    suspend fun download(track: Track): Boolean = withContext(Dispatchers.IO) {
        val body = api.bytes("tracks/${track.id}/stream") ?: return@withContext false
        if (body.isEmpty()) return@withContext false
        val target = File(dir, "${track.id}.audio")
        val temp = File(dir, "${track.id}.part")
        val wrote = runCatching {
            temp.writeBytes(body)
            if (target.exists()) target.delete()
            temp.renameTo(target)
        }.getOrDefault(false)
        if (!wrote || fileFor(track.id) == null) return@withContext false

        val rest = readIndex().filterNot { it.id == track.id }
        writeIndex(
            listOf(
                DownloadEntry(
                    id = track.id,
                    title = track.title,
                    artist = track.artist,
                    album = track.album,
                    duration = track.duration,
                    bytes = target.length(),
                    added = System.currentTimeMillis() / 1000,
                )
            ) + rest
        )
        true
    }

    fun remove(id: Int): Boolean {
        File(dir, "$id.audio").delete()
        writeIndex(readIndex().filterNot { it.id == id })
        return true
    }

    fun clear(): Int {
        val n = entries().size
        dir.listFiles()?.forEach { it.delete() }
        writeIndex(emptyList())
        return n
    }

    private fun readIndex(): List<DownloadEntry> = runCatching {
        val text = indexFile.takeIf { it.isFile }?.readText().orEmpty()
        if (text.isBlank()) {
            emptyList()
        } else {
            val arr = JSONArray(text)
            (0 until arr.length()).mapNotNull { i -> arr.optJSONObject(i)?.let(DownloadEntry::from) }
        }
    }.getOrElse { emptyList() }

    private fun writeIndex(list: List<DownloadEntry>) {
        runCatching {
            val arr = JSONArray()
            list.forEach { e ->
                arr.put(
                    JSONObject()
                        .put("id", e.id)
                        .put("title", e.title)
                        .put("artist", e.artist)
                        .put("album", e.album)
                        .put("duration", e.duration)
                        .put("bytes", e.bytes)
                        .put("added", e.added)
                )
            }
            indexFile.writeText(arr.toString())
        }
    }
}
