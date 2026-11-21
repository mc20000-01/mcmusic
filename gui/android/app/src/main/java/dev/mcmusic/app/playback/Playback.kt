package dev.mcmusic.app.playback

import android.app.PendingIntent
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.os.Handler
import android.os.Looper
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.media3.common.AudioAttributes
import androidx.media3.common.C
import androidx.media3.common.MediaItem
import androidx.media3.common.MediaMetadata
import androidx.media3.common.Player
import androidx.media3.session.MediaController
import androidx.media3.session.MediaSession
import androidx.media3.session.MediaSessionService
import androidx.media3.session.SessionToken
import com.google.common.util.concurrent.ListenableFuture
import android.net.Uri
import dev.mcmusic.app.MainActivity
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.Downloads
import dev.mcmusic.app.data.Prefs
import dev.mcmusic.app.data.Track
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import java.util.concurrent.Executor

data class PlaybackState(
    val track: Track? = null,
    val queue: List<Track> = emptyList(),
    val index: Int = 0,
    val playing: Boolean = false,
    val buffering: Boolean = false,
    val position: Long = 0,
    val duration: Long = 0,
    val shuffle: Boolean = false,
    val repeat: Boolean = false,
    val ready: Boolean = false,
    val error: String? = null,
    /** Sleep timer length in minutes, 0 when off. */
    val sleepMinutes: Int = 0,
    /** Milliseconds left on the sleep timer, 0 when off. */
    val sleepRemaining: Long = 0,
)

/**
 * One playback session for the whole app: the service owns the ExoPlayer, this
 * object owns the controller and publishes state as Compose state. Streams come
 * from `/api/tracks/<id>/stream`, which is session-authenticated — ExoPlayer's
 * default HTTP stack shares the app's CookieHandler, so the same login works.
 */
object Playback {
    var state by mutableStateOf(PlaybackState())
        private set

    private var controller: MediaController? = null
    private var future: ListenableFuture<MediaController>? = null
    private var queueTracks: List<Track> = emptyList()
    private var appContext: Context? = null
    private var widgetSignature: String? = null
    private var reportedTrackId: Int? = null
    private val reportScope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    private val reportHandler = Handler(Looper.getMainLooper())
    private val reportRunnable = object : Runnable {
        override fun run() {
            controller?.let { player ->
                position(player)
                checkSleep(player)
                if (state.track != null) report(player)
            }
            reportHandler.postDelayed(this, 5_000L)
        }
    }

    fun init(context: Context) {
        if (controller != null || future != null) return
        val app = context.applicationContext
        appContext = app
        val savedSleep = Prefs.sleepEndsAt
        val now = System.currentTimeMillis()
        if (savedSleep > now) {
            state = state.copy(
                sleepMinutes = ((savedSleep - now + 59_999) / 60_000).toInt(),
                sleepRemaining = savedSleep - now,
            )
        } else if (savedSleep > 0) {
            Prefs.saveSleepEndsAt(0L)
        }
        val token = SessionToken(app, ComponentName(app, PlaybackService::class.java))
        val main = Executor { Handler(Looper.getMainLooper()).post(it) }
        val f = MediaController.Builder(app, token).buildAsync()
        future = f
        f.addListener({
            val c = runCatching { f.get() }.getOrNull() ?: return@addListener
            controller = c
            c.addListener(object : Player.Listener {
                override fun onEvents(player: Player, events: Player.Events) {
                    publish(player)
                }

                override fun onPlayerError(error: androidx.media3.common.PlaybackException) {
                    state = state.copy(error = error.message ?: "playback failed", playing = false)
                }
            })
            state = state.copy(ready = true)
            publish(c)
            reportHandler.removeCallbacks(reportRunnable)
            reportHandler.post(reportRunnable)
        }, main)
    }

    private fun publish(player: Player) {
        val index = player.currentMediaItemIndex.coerceAtLeast(0)
        val track = queueTracks.getOrNull(index)
        val wasPlaying = state.playing
        val trackChanged = track?.id != reportedTrackId
        // Home screen widgets follow the phone's queue while it owns it.
        val signature = "${track?.id}:${player.isPlaying}"
        if (signature != widgetSignature) {
            widgetSignature = signature
            appContext?.let { ctx -> Thread { runCatching { dev.mcmusic.app.widget.Widgets.refresh(ctx) } }.start() }
        }

        state = state.copy(
            track = track,
            queue = queueTracks,
            index = index,
            playing = player.isPlaying,
            buffering = player.playbackState == Player.STATE_BUFFERING,
            duration = player.duration.takeIf { it > 0 } ?: ((track?.duration ?: 0.0) * 1000).toLong(),
            shuffle = player.shuffleModeEnabled,
            repeat = player.repeatMode != Player.REPEAT_MODE_OFF,
            error = null,
        )
        position(player)
        if (trackChanged && track != null) {
            reportedTrackId = track.id
            val id = track.id
            reportScope.launch { runCatching { Api.recordPlay(id) } }
        }
        if (track != null && (trackChanged || wasPlaying != state.playing)) report(player)
    }

    private fun position(player: Player) {
        state = state.copy(position = player.currentPosition.coerceAtLeast(0))
    }

    /** Called by the UI while it is visible so the scrubber moves. */
    fun tick() {
        val c = controller ?: return
        position(c)
        checkSleep(c)
    }

    private fun checkSleep(player: Player) {
        val end = Prefs.sleepEndsAt
        if (end in 1..System.currentTimeMillis()) {
            Prefs.saveSleepEndsAt(0L)
            player.pause()
            state = state.copy(sleepMinutes = 0, sleepRemaining = 0)
            report(player)
        } else if (end > 0) {
            state = state.copy(sleepRemaining = end - System.currentTimeMillis())
        }
    }

    /** Push the current track, position and queue to the server. */
    private fun report(player: Player) {
        val snapshot = state
        val track = snapshot.track ?: return
        reportScope.launch {
            runCatching { Api.heartbeat(track.id, snapshot.position, !snapshot.playing) }
            runCatching {
                Api.pushPlayback(
                    trackId = track.id,
                    positionMs = snapshot.position,
                    durationMs = snapshot.duration,
                    playing = snapshot.playing,
                    queue = snapshot.queue.map { it.id },
                )
            }
        }
    }

    /** 0 turns the sleep timer off; otherwise playback pauses after [minutes]. */
    fun setSleep(minutes: Int) {
        val end = if (minutes <= 0) 0L else System.currentTimeMillis() + minutes * 60_000L
        Prefs.saveSleepEndsAt(end)
        val remaining = if (end > 0) end - System.currentTimeMillis() else 0
        state = state.copy(sleepMinutes = minutes.coerceAtLeast(0), sleepRemaining = remaining)
    }

    fun play(tracks: List<Track>, startIndex: Int = 0) {
        val c = controller ?: return
        if (tracks.isEmpty()) return
        queueTracks = tracks
        val items = tracks.map { track ->
            val local = Downloads.file(track.id)
            val item = MediaItem.Builder().setMediaId(track.id.toString())
            if (local != null) item.setUri(Uri.fromFile(local)) else item.setUri(Api.streamUrl(track.id))
            item.setMediaMetadata(
                MediaMetadata.Builder()
                    .setTitle(track.title)
                    .setArtist(track.artist)
                    .setAlbumTitle(track.album)
                    .build(),
            ).build()
        }
        c.setMediaItems(items, startIndex.coerceIn(0, items.lastIndex), 0)
        c.prepare()
        c.play()
        publish(c)
    }

    /** Plays a single track without replacing the rest of the queue. */
    fun playNow(track: Track, queue: List<Track> = listOf(track)) {
        play(queue, queue.indexOfFirst { it.id == track.id }.coerceAtLeast(0))
    }

    fun toggle() {
        val c = controller ?: return
        if (c.isPlaying) c.pause() else {
            if (c.playbackState == Player.STATE_IDLE) c.prepare()
            c.play()
        }
        publish(c)
    }

    /**
     * Moves an item inside the live queue. MediaItem indices follow the item, so
     * the playing track keeps playing even when the user drags it elsewhere.
     */
    fun move(from: Int, to: Int) {
        val c = controller ?: return
        if (from == to) return
        if (from !in queueTracks.indices || to !in queueTracks.indices) return
        queueTracks = queueTracks.toMutableList().also { it.add(to, it.removeAt(from)) }
        c.moveMediaItem(from, to)
        publish(c)
    }

    fun next() { controller?.seekToNextMediaItem() }
    fun previous() { controller?.seekToPreviousMediaItem() }

    fun seekTo(ms: Long) {
        controller?.seekTo(ms.coerceAtLeast(0))
        controller?.let { position(it) }
    }

    fun seekFraction(fraction: Float) {
        val duration = state.duration
        if (duration > 0) seekTo((duration * fraction.coerceIn(0f, 1f)).toLong())
    }

    fun toggleShuffle() {
        val c = controller ?: return
        c.shuffleModeEnabled = !c.shuffleModeEnabled
        publish(c)
    }

    fun cycleRepeat() {
        val c = controller ?: return
        c.repeatMode = when (c.repeatMode) {
            Player.REPEAT_MODE_OFF -> Player.REPEAT_MODE_ALL
            Player.REPEAT_MODE_ALL -> Player.REPEAT_MODE_ONE
            else -> Player.REPEAT_MODE_OFF
        }
        publish(c)
    }

    fun clearError() {
        state = state.copy(error = null)
    }

    fun stop() {
        controller?.let { report(it) }
        Prefs.saveSleepEndsAt(0L)
        reportedTrackId = null
        controller?.stop()
        controller?.clearMediaItems()
        queueTracks = emptyList()
        state = PlaybackState(ready = controller != null)
    }
}

class PlaybackService : MediaSessionService() {
    private var session: MediaSession? = null

    override fun onCreate() {
        super.onCreate()
        // Streams are bearer-authenticated; ExoPlayer must send the same token
        // the API client uses, or playback 401s while browsing works.
        // Read the token for every request: the service may start before login,
        // and logout/login can swap the token without recreating ExoPlayer.
        val baseHttp = androidx.media3.datasource.DefaultHttpDataSource.Factory()
        val http = object : androidx.media3.datasource.DataSource.Factory {
            override fun createDataSource(): androidx.media3.datasource.DataSource =
                baseHttp.createDataSource().apply {
                    val httpSource = this as androidx.media3.datasource.HttpDataSource
                    Api.authHeaders().forEach { (name, value) -> httpSource.setRequestProperty(name, value) }
                }
        }
        val player = androidx.media3.exoplayer.ExoPlayer.Builder(this)
            .setMediaSourceFactory(androidx.media3.exoplayer.source.DefaultMediaSourceFactory(http))
            .setAudioAttributes(
                AudioAttributes.Builder()
                    .setUsage(C.USAGE_MEDIA)
                    .setContentType(C.AUDIO_CONTENT_TYPE_MUSIC)
                    .build(),
                true,
            )
            .setHandleAudioBecomingNoisy(true)
            .build()
        val openApp = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val pending = PendingIntent.getActivity(
            this,
            0,
            openApp,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
        )
        session = MediaSession.Builder(this, player).setSessionActivity(pending).build()
    }

    override fun onGetSession(controllerInfo: MediaSession.ControllerInfo): MediaSession? = session

    override fun onTaskRemoved(rootIntent: android.content.Intent?) {
        val player = session?.player
        if (player == null || !player.playWhenReady || player.mediaItemCount == 0) stopSelf()
    }

    override fun onDestroy() {
        session?.run {
            player.release()
            release()
        }
        session = null
        super.onDestroy()
    }
}
