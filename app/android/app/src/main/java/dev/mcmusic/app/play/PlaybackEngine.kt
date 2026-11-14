package dev.mcmusic.app.play

import android.net.Uri
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.media3.common.AudioAttributes
import androidx.media3.common.C
import androidx.media3.common.MediaItem
import androidx.media3.common.PlaybackException
import androidx.media3.common.Player
import androidx.media3.datasource.DefaultHttpDataSource
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.exoplayer.source.DefaultMediaSourceFactory
import dev.mcmusic.app.McMusicApp
import dev.mcmusic.app.data.Track
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

/**
 * Owns the single native audio player. The browser was the playback authority
 * in the web app; here it is ExoPlayer, publishing the same /api/playback
 * snapshot so bots and the sticky dashboards stay in sync.
 */
class PlaybackEngine(private val app: McMusicApp) {

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    private var publishJob: Job? = null

    val player: ExoPlayer = ExoPlayer.Builder(app).build().apply {
        setAudioAttributes(
            AudioAttributes.Builder()
                .setContentType(C.AUDIO_CONTENT_TYPE_MUSIC)
                .setUsage(C.USAGE_MEDIA)
                .build(),
            true,
        )
        setHandleAudioBecomingNoisy(true)
        setWakeMode(C.WAKE_MODE_NETWORK)
        repeatMode = Player.REPEAT_MODE_OFF
        volume = app.store.volume
    }

    var queue by mutableStateOf<List<Track>>(emptyList())
        private set
    var index by mutableStateOf(-1)
        private set
    var playing by mutableStateOf(false)
        private set
    var position by mutableStateOf(0.0)
        private set
    var duration by mutableStateOf(0.0)
        private set
    var shuffle by mutableStateOf(false)
        private set
    var repeat by mutableStateOf("off")
        private set
    var error by mutableStateOf<String?>(null)

    /** Minutes left on the sleep timer, or null when it's off. */
    var sleepLeft by mutableStateOf<Int?>(null)
        private set
    private var sleepJob: Job? = null

    fun setSleep(minutes: Int) {
        sleepJob?.cancel()
        if (minutes <= 0) {
            sleepLeft = null
            return
        }
        sleepLeft = minutes
        sleepJob = scope.launch {
            var left = minutes
            while (isActive && left > 0) {
                delay(60_000)
                left -= 1
                sleepLeft = left
            }
            if (isActive) {
                pause()
                sleepLeft = null
            }
        }
    }

    var onTrackChanged: ((Track?) -> Unit)? = null

    private var reported = false
    private var lastPublish = 0L
    var shufflePlay = false
        private set

    val current: Track? get() = queue.getOrNull(index)

    init {
        MediaControls.onPlayPause = { toggle() }
        MediaControls.onNext = { next() }
        MediaControls.onPrev = { prev() }
        MediaControls.onSeek = { seconds -> seekTo(seconds) }
        player.addListener(object : Player.Listener {
            override fun onIsPlayingChanged(isPlaying: Boolean) {
                playing = isPlaying
                val t = current
                if (t != null) {
                    // Foreground service + platform MediaSession: audio keeps
                    // running when unfocused, and widgets/lock screen see a
                    // real music session rather than a plain notification.
                    PlaybackService.update(
                        app, t.title, t.artist, isPlaying,
                        player.currentPosition.coerceAtLeast(0L),
                        player.duration.coerceAtLeast(0L),
                        dev.mcmusic.app.ui.MediaUrls.cover(t.id),
                        app.api.cookieHeader(),
                    )
                    if (isPlaying) {
                        PlaybackService.start(
                            app, t.title, t.artist, true,
                            dev.mcmusic.app.ui.MediaUrls.cover(t.id),
                            app.api.cookieHeader(),
                        )
                    }
                } else if (!player.playWhenReady) {
                    PlaybackService.stop(app)
                }
                publish(force = true)
            }

            override fun onPlaybackStateChanged(playbackState: Int) {
                when (playbackState) {
                    Player.STATE_READY -> {
                        duration = (player.duration.takeIf { it > 0 } ?: 0L) / 1000.0
                        publish(force = true)
                    }
                    Player.STATE_ENDED -> onEnded()
                }
            }

            override fun onPlayerError(err: PlaybackException) {
                error = when (err.errorCode) {
                    PlaybackException.ERROR_CODE_IO_NETWORK_CONNECTION_FAILED,
                    PlaybackException.ERROR_CODE_IO_NETWORK_CONNECTION_TIMEOUT,
                    -> "Network lost while streaming"
                    PlaybackException.ERROR_CODE_IO_BAD_HTTP_STATUS -> "Sign in again to stream"
                    else -> "Playback failed"
                }
                playing = false
            }
        })

        // UI ticker: position, buffering and periodic publishing.
        scope.launch {
            while (isActive) {
                if (player.isPlaying) {
                    position = player.currentPosition / 1000.0
                    duration = (player.duration.takeIf { it > 0 } ?: (duration * 1000).toLong()) / 1000.0
                    maybeReport()
                    if (System.currentTimeMillis() - lastPublish > 3000) publish(force = true)
                }
                delay(500)
            }
        }
    }

    /* ── queue ──────────────────────────────────────────────────────────── */

    fun play(list: List<Track>, start: Int = 0, shuffleStart: Boolean = false) {
        if (list.isEmpty()) return
        val safeStart = start.coerceIn(0, list.lastIndex)
        val picked = list[safeStart]
        if (shuffleStart) {
            shuffle = true
            val rest = list.filterIndexed { i, _ -> i != safeStart }.shuffled()
            queue = listOf(picked) + rest
            index = 0
            shufflePlay = true
        } else {
            queue = list
            index = safeStart
        }
        loadCurrent()
    }

    fun add(track: Track, next: Boolean = false) {
        if (queue.isEmpty()) {
            play(listOf(track), 0)
            return
        }
        val at = if (next) (index + 1).coerceIn(0, queue.size) else queue.size
        queue = queue.toMutableList().apply { add(at, track) }
        if (at <= index) index += 1
        publish(force = true)
    }

    fun removeAt(at: Int): Boolean {
        if (at !in queue.indices) return false
        val list = queue.toMutableList()
        list.removeAt(at)
        if (at < index) index -= 1
        queue = list
        if (at == index) {
            if (queue.isNotEmpty()) {
                index = index.coerceIn(0, queue.lastIndex)
                loadCurrent()
            } else {
                index = -1
                player.stop()
            }
        }
        publish(force = true)
        return true
    }

    fun clearUpcoming() {
        if (index < 0) return
        queue = queue.take(index + 1)
        publish(force = true)
    }

    /** Move a queued track, keeping the playing item selected. Used by drag-reorder. */
    fun move(from: Int, to: Int): Boolean {
        if (from !in queue.indices || to !in queue.indices || from == to) return false
        val list = queue.toMutableList()
        val item = list.removeAt(from)
        list.add(to, item)
        queue = list
        index = when {
            index == from -> to
            from < index && to >= index -> index - 1
            from > index && to <= index -> index + 1
            else -> index
        }
        publish(force = true)
        return true
    }

    /** Append a whole album, artist or playlist. */
    fun addAll(tracks: List<Track>, next: Boolean = false) {
        if (tracks.isEmpty()) return
        if (queue.isEmpty()) {
            play(tracks, 0)
            return
        }
        val at = if (next) (index + 1).coerceIn(0, queue.size) else queue.size
        queue = queue.toMutableList().apply { addAll(at, tracks) }
        publish(force = true)
    }

    /** Replace everything after the current track, e.g. after drag-reorder. */
    fun setUpcoming(tracks: List<Track>) {
        if (index < 0) return
        queue = queue.take(index + 1) + tracks
        publish(force = true)
    }

    /** Jump to an existing queue entry without rebuilding the queue. */
    fun jumpTo(at: Int) {
        if (at !in queue.indices || at == index) return
        index = at
        loadCurrent()
    }

    /* ── transport ──────────────────────────────────────────────────────── */

    private fun loadCurrent() {
        val t = current ?: return
        error = null
        reported = false
        position = 0.0
        duration = t.duration

        val cookie = app.api.cookieHeader()
        val factory = DefaultHttpDataSource.Factory()
            .setUserAgent("mcmusic-android/1.0")
            .setAllowCrossProtocolRedirects(true)
            .setConnectTimeoutMs(15_000)
            .setReadTimeoutMs(30_000)
        if (cookie.isNotBlank()) factory.setDefaultRequestProperties(mapOf("Cookie" to cookie))

        // A downloaded copy wins: playback then needs no network at all.
        val local = app.downloads.fileFor(t.id)
        val uri = local?.let { Uri.fromFile(it) } ?: Uri.parse(app.api.streamUrl(t.id))
        val source = DefaultMediaSourceFactory(factory).createMediaSource(MediaItem.fromUri(uri))

        player.setMediaSource(source)
        player.prepare()
        player.playWhenReady = true
        onTrackChanged?.invoke(t)
        publish(force = true)
    }

    fun retry() {
        if (current == null) return
        loadCurrent()
    }

    fun toggle() {
        if (current == null) return
        if (player.isPlaying) player.pause() else player.play()
    }

    fun pause() {
        if (player.isPlaying) player.pause()
    }

    /** Pause without publishing to /api/playback - used when another device takes over. */
    fun silentPause() {
        if (player.isPlaying) player.pause()
    }

    fun next(auto: Boolean = false) {
        if (queue.isEmpty()) return
        if (repeat == "one" && auto) {
            player.seekTo(0)
            reported = false
            player.play()
            return
        }
        when {
            index < queue.lastIndex -> {
                index += 1
                loadCurrent()
            }
            repeat == "all" -> {
                index = 0
                loadCurrent()
            }
            auto -> autoplayRadio()
            else -> {
                player.pause()
                player.seekTo(0)
            }
        }
    }

    fun prev() {
        if (current == null) return
        if (position > 3 || index <= 0) {
            player.seekTo(0)
            return
        }
        index -= 1
        loadCurrent()
    }

    private fun onEnded() {
        maybeReport(completed = true)
        next(auto = true)
    }

    fun seekTo(seconds: Double) {
        val max = (player.duration.takeIf { it > 0 } ?: 0L) / 1000.0
        val target = seconds.coerceIn(0.0, if (max > 0) max - 0.05 else 0.0)
        player.seekTo((target * 1000).toLong())
        position = target
        publish(force = true)
    }

    fun seekFraction(fraction: Float) {
        val d = if (duration > 0) duration else (player.duration / 1000.0)
        if (d <= 0) return
        seekTo(d * fraction.coerceIn(0f, 1f))
    }

    fun setVolume(v: Float) {
        val vol = v.coerceIn(0f, 1f)
        player.volume = vol
        if (app.settings.value.rememberVolume) {
            app.store.volume = vol
            app.viewModel?.setSetting { it.copy(volume = vol) }
        }
    }

    fun toggleShuffle(): Boolean {
        shuffle = !shuffle
        if (shuffle && queue.size > 1) {
            val head = queue.take(index + 1)
            val tail = queue.drop(index + 1).shuffled()
            queue = head + tail
        }
        return shuffle
    }

    fun cycleRepeat(): String {
        repeat = when (repeat) {
            "off" -> "all"
            "all" -> "one"
            else -> "off"
        }
        return repeat
    }

    fun markLiked(trackId: Int, liked: Boolean) {
        queue = queue.map { if (it.id == trackId) it.copy(liked = liked) else it }
    }

    fun markExplicit(trackId: Int, explicit: Boolean) {
        queue = queue.map { if (it.id == trackId) it.copy(explicit = explicit) else it }
    }

    /* ── autoplay radio ─────────────────────────────────────────────────── */

    private fun autoplayRadio() {
        if (!app.settings.value.autoplay) return
        val seed = current ?: return
        scope.launch {
            val extra = runCatching { app.repo.radio(seed.id) }.getOrNull() ?: return@launch
            val have = queue.map { it.id }.toSet()
            val add = extra.filter { it.id !in have }.take(20)
            if (add.isEmpty()) return@launch
            queue = queue + add
            index += 1
            loadCurrent()
        }
    }

    /* ── publishing ─────────────────────────────────────────────────────── */

    private fun maybeReport(completed: Boolean = false) {
        val t = current ?: return
        if (app.settings.value.privateSession) return
        if (reported && !completed) return
        val d = if (duration > 0) duration else player.duration / 1000.0
        val enough = completed || position > 20 || (d > 0 && position / d > 0.4)
        if (!enough) return
        reported = true
        scope.launch {
            runCatching { app.repo.reportPlay(t.id, completed || (d > 0 && position / d > 0.8)) }
        }
    }

    private fun publish(force: Boolean = false) {
        val t = current ?: return
        if (!force && System.currentTimeMillis() - lastPublish < 3000) return
        lastPublish = System.currentTimeMillis()
        val snapshotPos = position
        val snapshotDur = if (duration > 0) duration else 0.0
        val upcoming = queue.drop(index + 1).map { it.id }
        val playingNow = player.isPlaying
        scope.launch {
            runCatching {
                app.repo.publishPlayback(t.id, snapshotPos, snapshotDur, playingNow, upcoming)
            }
        }
    }

    fun release() {
        publishJob?.cancel()
        player.release()
        PlaybackService.stop(app)
    }
}
