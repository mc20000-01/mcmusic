package dev.mcmusic.app.data

import android.content.Context
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import android.net.NetworkCallback
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * Keeps the automatic collections on the device. Each target carries its own
 * connection rule so "Faves on Wi-Fi" and "an album on any connection" can
 * coexist. No WorkManager dependency: a default-network callback starts a
 * single coroutine when a usable connection appears, and every run is throttled
 * and guarded against overlap.
 */
object AutoDownload {
    private var callback: NetworkCallback? = null
    private var running = false
    private var lastRunAt = 0L
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    /** wifi: unmetered local network. stable: validated and not cellular-metered. */
    fun networkAllows(rule: String): Boolean {
        val ctx = Downloads.context() ?: return false
        val cm = ctx.getSystemService(Context.CONNECTIVITY_SERVICE) as? ConnectivityManager ?: return false
        val network = cm.activeNetwork ?: return false
        val caps = cm.getNetworkCapabilities(network) ?: return false
        if (!caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)) return false
        val cellular = caps.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)
        return when (rule) {
            "any" -> true
            "stable" -> caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED) &&
                (!cellular || caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_NOT_METERED))
            else -> !cellular && (
                caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) ||
                    caps.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET)
                )
        }
    }

    fun register(context: Context) {
        if (callback != null) return
        val cm = context.applicationContext.getSystemService(Context.CONNECTIVITY_SERVICE)
            as? ConnectivityManager ?: return
        val cb = object : NetworkCallback() {
            override fun onAvailable(network: Network) {
                scope.launch { runIfAllowed() }
            }
        }
        runCatching { cm.registerDefaultNetworkCallback(cb) }
        callback = cb
    }

    suspend fun runIfAllowed(force: Boolean = false) = withContext(Dispatchers.IO) {
        if (running || Prefs.token.isNullOrBlank()) return@withContext
        if (!force && System.currentTimeMillis() - lastRunAt < 60_000L) return@withContext
        if (!Prefs.autoFaves && Prefs.downloadSources.isEmpty()) return@withContext
        running = true
        lastRunAt = System.currentTimeMillis()
        try {
            var saved = 0
            if (Prefs.autoFaves && networkAllows(Prefs.autoFavesNetwork)) {
                val faves = Api.playlists().getOrNull()?.firstOrNull {
                    it.name.equals("faves", ignoreCase = true)
                }
                if (faves != null) saved += saveAll(Api.playlist(faves.id).getOrNull()?.second)
            }
            for (source in Prefs.downloadSources) {
                if (!networkAllows(source.network)) continue
                saved += saveAll(tracksFor(source))
                delay(200L)
            }
            if (saved > 0) Downloads.refreshFromDisk()
        } finally {
            running = false
        }
    }

    private suspend fun tracksFor(source: DownloadSource): List<Track> = when (source.kind) {
        "playlist" -> source.ref.toIntOrNull()?.let { Api.playlist(it).getOrNull()?.second }
        "artist" -> Api.artistTracks(source.ref).getOrNull()
        "album" -> Api.albumTracks(source.ref).getOrNull()
        "likes" -> Api.likes().getOrNull()
        else -> null
    }.orEmpty()

    private suspend fun saveAll(tracks: List<Track>?): Int {
        if (tracks.isNullOrEmpty()) return 0
        var saved = 0
        for (track in tracks.take(60)) {
            if (Downloads.isDownloaded(track.id)) continue
            if (Downloads.download(track).isSuccess) saved++
            delay(120L)
        }
        return saved
    }
}
