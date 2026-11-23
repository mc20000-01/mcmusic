package dev.mcmusic.app.data

import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.core.content.FileProvider
import dev.mcmusic.app.BuildConfig
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.net.HttpURLConnection
import java.net.URL

/** The Android entry in the server's build registry. */
data class AppUpdate(
    val version: String,
    val path: String,
    val bytes: Long,
    val note: String,
) {
    val url: String get() = Prefs.server.trimEnd('/') + path
}

/**
 * In-app updates use the same registry the website downloads from, so the APK
 * offered here is byte-for-byte the one on the GitHub `latest` release. The
 * file is downloaded to the app's cache and handed to the system installer
 * through a FileProvider; the existing signing key makes it an update, not a
 * conflicting install.
 */
object Updater {
    val currentVersion: String get() = BuildConfig.VERSION_NAME

    private fun parts(version: String): List<Int> =
        version.split('.').map { it.filter(Char::isDigit).toIntOrNull() ?: 0 }

    private fun isNewer(remote: String): Boolean {
        val here = parts(currentVersion)
        val there = parts(remote)
        for (i in 0 until maxOf(here.size, there.size)) {
            val a = there.getOrElse(i) { 0 }
            val b = here.getOrElse(i) { 0 }
            if (a != b) return a > b
        }
        return false
    }

    suspend fun check(): Result<AppUpdate?> = withContext(Dispatchers.IO) {
        runCatching {
            val conn = (URL(Prefs.server.trimEnd('/') + "/api/builds").openConnection() as HttpURLConnection).apply {
                connectTimeout = 10_000
                readTimeout = 15_000
                setRequestProperty("Accept", "application/json")
            }
            val text = try {
                conn.inputStream.bufferedReader().use { it.readText() }
            } finally {
                conn.disconnect()
            }
            val builds = JSONObject(text).optJSONArray("builds") ?: return@runCatching null
            var newest: AppUpdate? = null
            for (i in 0 until builds.length()) {
                val entry = builds.optJSONObject(i) ?: continue
                if (!entry.optString("file", "").endsWith(".apk")) continue
                val version = entry.optString("version")
                val path = entry.optString("url")
                if (version.isBlank() || path.isBlank() || !isNewer(version)) continue
                val candidate = AppUpdate(
                    version = version,
                    path = path,
                    bytes = entry.optLong("bytes"),
                    note = entry.optString("note"),
                )
                if (newest == null || isNewer(candidate.version, newest.version)) newest = candidate
            }
            newest
        }
    }

    private fun isNewer(a: String, b: String): Boolean {
        val left = parts(a)
        val right = parts(b)
        for (i in 0 until maxOf(left.size, right.size)) {
            val x = left.getOrElse(i) { 0 }
            val y = right.getOrElse(i) { 0 }
            if (x != y) return x > y
        }
        return false
    }

    suspend fun download(
        context: Context,
        update: AppUpdate,
        onProgress: (Int) -> Unit,
    ): Result<File> = withContext(Dispatchers.IO) {
        runCatching {
            val dir = File(context.cacheDir, "updates").apply { mkdirs() }
            val file = File(dir, "mcmusic-${update.version}.apk")
            val conn = (URL(update.url).openConnection() as HttpURLConnection).apply {
                connectTimeout = 15_000
                readTimeout = 60_000
                setRequestProperty("Accept", "application/vnd.android.package-archive")
                instanceFollowRedirects = true
            }
            val total = try {
                val length = conn.contentLength
                conn.inputStream.use { input ->
                    FileOutputStream(file).use { out ->
                        val buffer = ByteArray(64 * 1024)
                        var done = 0L
                        while (true) {
                            val read = input.read(buffer)
                            if (read < 0) break
                            out.write(buffer, 0, read)
                            done += read
                            if (length > 0) {
                                val percent = (done * 100 / length).toInt().coerceIn(0, 100)
                                withContext(Dispatchers.Main) { onProgress(percent) }
                            }
                        }
                    }
                }
                length
            } finally {
                conn.disconnect()
            }
            if (total > 0 && file.length() != total.toLong()) {
                file.delete()
                error("download was incomplete — try again")
            }
            file
        }
    }

    @Suppress("DEPRECATION")
    fun install(context: Context, file: File) {
        val uri: Uri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file)
        val intent = Intent(Intent.ACTION_INSTALL_PACKAGE).apply {
            data = uri
            flags = Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_ACTIVITY_NEW_TASK
            putExtra(Intent.EXTRA_NOT_UNKNOWN_SOURCE, true)
        }
        context.startActivity(intent)
    }
}
