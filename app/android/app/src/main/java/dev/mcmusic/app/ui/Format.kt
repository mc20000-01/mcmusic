package dev.mcmusic.app.ui

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.LruCache
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import java.util.Locale
import kotlin.math.abs

/* ── URLs ───────────────────────────────────────────────────────────────── */

object MediaUrls {
    @Volatile
    var base: String = ""

    fun cover(trackId: Int): String = "$base/api/tracks/$trackId/cover"
    fun stream(trackId: Int): String = "$base/api/tracks/$trackId/stream"
}

/* ── artwork loader (cookie-authenticated, native bitmaps) ─────────────── */

object ArtLoader {

    var client: OkHttpClient? = null

    private val cache = object : LruCache<String, Bitmap>(64) {
        override fun sizeOf(key: String, value: Bitmap): Int = 1
    }

    suspend fun load(url: String): ImageBitmap? {
        cache.get(url)?.let { return it.asImageBitmap() }
        val http = client ?: return null
        return withContext(Dispatchers.IO) {
            runCatching {
                val req = Request.Builder().url(url).build()
                http.newCall(req).execute().use { res ->
                    if (!res.isSuccessful) return@use null
                    val bytes = res.body?.bytes() ?: return@use null
                    val bmp = BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
                    if (bmp != null) cache.put(url, bmp)
                    bmp?.asImageBitmap()
                }
            }.getOrNull()
        }
    }
}

@Composable
fun rememberArt(trackId: Int?): ImageBitmap? {
    val url = remember(trackId) { trackId?.let { MediaUrls.cover(it) } }
    var bmp by remember(url) { mutableStateOf<ImageBitmap?>(null) }
    LaunchedEffect(url) {
        if (url != null) bmp = ArtLoader.load(url)
    }
    return bmp
}

/* ── number / time formatting (mirrors ui.js) ──────────────────────────── */

fun fmtTime(seconds: Double): String {
    val s = seconds.coerceAtLeast(0.0).toInt()
    return "${s / 60}:${(s % 60).toString().padStart(2, '0')}"
}

fun fmtCount(n: Long?): String {
    if (n == null) return ""
    if (n >= 1_000_000_000L) return trimmed(n / 1_000_000_000.0) + "B"
    if (n >= 1_000_000L) return trimmed(n / 1_000_000.0) + "M"
    if (n >= 1_000L) return trimmed(n / 1_000.0) + "K"
    return n.toString()
}

private fun trimmed(v: Double): String {
    val s = String.format(Locale.US, "%.1f", v)
    return s.removeSuffix(".0")
}

fun fmtTotal(seconds: Double): String {
    val m = (seconds / 60).toInt()
    return if (m < 60) "$m min" else "${m / 60} hr ${m % 60} min"
}

fun fmtBytes(bytes: Long): String {
    if (bytes < 1024) return "$bytes B"
    val units = listOf("KB", "MB", "GB", "TB")
    var v = bytes / 1024.0
    var i = 0
    while (v >= 1024 && i < units.lastIndex) {
        v /= 1024.0
        i += 1
    }
    return String.format(Locale.US, if (v >= 10) "%.0f %s" else "%.1f %s", v, units[i])
}

fun fmtAgo(timestamp: Double): String {
    if (timestamp <= 0.0) return "never"
    val secs = (System.currentTimeMillis() / 1000.0 - timestamp).toLong().coerceAtLeast(0)
    return when {
        secs < 60 -> "${secs}s ago"
        secs < 3600 -> "${secs / 60}m ago"
        secs < 86400 -> "${secs / 3600}h ago"
        else -> "${secs / 86400}d ago"
    }
}

fun fmtUptime(seconds: Double): String {
    val total = abs(seconds).toLong()
    val d = total / 86400
    val h = (total % 86400) / 3600
    val m = (total % 3600) / 60
    return when {
        d > 0 -> "${d}d ${h}h"
        h > 0 -> "${h}h ${m}m"
        else -> "${m}m"
    }
}
