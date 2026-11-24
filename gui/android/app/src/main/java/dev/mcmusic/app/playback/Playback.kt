package dev.mcmusic.app.playback

import android.app.PendingIntent
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.net.Uri
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
import dev.mcmusic.app.MainActivity
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.Downloads
import dev.mcmusic.app.data.Prefs
import dev.mcmusic.app.data.QueueSnapshot
import dev.mcmusic.app.data.Track
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import java.util.concurrent.Executor
import kotlin.math.abs

data class PlaybackState(
    val track: Track? = null,
    val queue: List<Track> = emptyList(),
    val index: Int = 0,
    val playing: Boolean = false,
    val buffering: Boolean = false,
    val position: Long = 0,
    val duration: Long = 0,
    val shuffle: Boolean = false,
    /** Shuffle decided by the model ordering rather than Media3's RNG. */
    val modelShuffle: Boolean = false,
    val repeat: Boolean = false,
    /** Media3 repeat mode: 0 off, 1 all, 2 one. */
    val repeatMode: Int = Player.REPEAT_MODE_OFF,
    /** Refill the queue from radio after the last track ends. */
    val autoplay: Boolean = true,
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
    private var reportedTrackKey: String? = null
    private var activitySignature: String? = null
    private var lastSavedPosition = 0L
    private var lastPositionSaveAt = 0L
    private var autoplayBusy = false
    private var modelShuffle = false
    private var videoPausedMusic = false
    private var autoplayDoneKey: String? = null
    private var suppressAutoplayKey: String? = null
    private val reportScope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    private val reportHandler = Handler(Looper.getMainLooper())
    private val reportRunnable: Runnable = object : Runnable {
        override fun run() {
            controller?.let { player ->
                position(player)
                checkSleep(player)
                checkAutoplay(player)
                if (state.track != null) report(player)
            }
            reportHandler.postDelayed(this, 5_000L)
        }
    }

    fun init(context: Context) {
        if (controller != null || future != null) return
        val app = context.applicationContext
        appContext = app
        state = state.copy(autoplay = Prefs.autoplay)
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
                    if (events.contains(Player.EVENT_PLAYBACK_STATE_CHANGED)) checkAutoplay(player)
                }

                override fun onMediaItemTransition(mediaItem: MediaItem?, reason: Int) {
                    // A new item is a fresh chance for radio at its natural end.
                    autoplayDoneKey = null
                    suppressAutoplayKey = null
                }

                override fun onPlayerError(error: androidx.media3.common.PlaybackException) {
                    state = state.copy(error = error.message ?: "playback failed", playing = false)
                }
            })
            // Only restore when the service really came back empty. A live
            // session in another activity or a notification restart must keep
            // the queue it already owns.
            if (queueTracks.isEmpty() && c.mediaItemCount == 0) restoreSavedQueue(c)
            state = state.copy(ready = true)
            publish(c)
            reportHandler.removeCallbacks(reportRunnable)
            reportHandler.post(reportRunnable)
        }, main)
    }

    /** Media ids carry the queue occurrence, so duplicate track ids stay distinct. */
    private fun mediaId(trackId: Int, index: Int): String = "$trackId@$index"

    private fun storedIndex(mediaId: String?): Int? {
        if (mediaId == null) return null
        val at = mediaId.lastIndexOf('@')
        if (at <= 0) return null
        val id = mediaId.substring(0, at).toIntOrNull() ?: return null
        val index = mediaId.substring(at + 1).toIntOrNull() ?: return null
        if (index !in queueTracks.indices || queueTracks[index].id != id) return null
        return index
    }

    private fun trackKey(index: Int, track: Track?): String = "$index:${track?.id}"

    /** Resolve the playing track by its stored queue index, never by a broad id search. */
    private fun currentTrack(player: Player): Pair<Track?, Int> {
        if (queueTracks.isEmpty()) return null to 0
        val index = storedIndex(player.currentMediaItem?.mediaId)
            ?: player.currentMediaItemIndex.coerceAtLeast(0)
        val safe = index.coerceIn(0, queueTracks.lastIndex)
        return queueTracks[safe] to safe
    }

    private fun itemsOf(tracks: List<Track>): List<MediaItem> = tracks.mapIndexed { index, track ->
        val local = Downloads.file(track.id)
        val item = MediaItem.Builder().setMediaId(mediaId(track.id, index))
        if (local != null) item.setUri(Uri.fromFile(local)) else item.setUri(Api.streamUrl(track.id))
        item.setMediaMetadata(
            MediaMetadata.Builder()
                .setTitle(track.title)
                .setArtist(track.artist)
                .setAlbumTitle(track.album)
                .build(),
        ).build()
    }

    private fun restoreSavedQueue(player: Player) {
        val saved = Prefs.savedQueue() ?: return
        queueTracks = saved.tracks
        reportedTrackKey = trackKey(saved.index, saved.tracks.getOrNull(saved.index))
        player.setMediaItems(itemsOf(saved.tracks), saved.index, saved.positionMs)
        player.shuffleModeEnabled = saved.shuffle
        player.repeatMode = saved.repeatMode
        Prefs.saveAutoplay(saved.autoplay)
        state = state.copy(autoplay = saved.autoplay)
        // Restoring is not a new play: don't double-count it as a stream.
        player.prepare()
        saveQueue(player, saved.positionMs)
    }

    private fun publish(player: Player) {
        val (track, index) = currentTrack(player)
        val wasPlaying = state.playing
        val key = trackKey(index, track)
        val trackChanged = key != reportedTrackKey
        // Home screen widgets follow the phone's queue while it owns it.
        val signature = "${track?.id}@$index:${player.isPlaying}"
        if (signature != widgetSignature) {
            widgetSignature = signature
            appContext?.let { ctx -> Thread { runCatching { dev.mcmusic.app.widget.Widgets.refresh(ctx) } }.start() }
        }

        val repeatMode = player.repeatMode
        state = state.copy(
            track = track,
            queue = queueTracks,
            index = index,
            playing = player.isPlaying,
            buffering = player.playbackState == Player.STATE_BUFFERING,
            duration = player.duration.takeIf { it > 0 } ?: ((track?.duration ?: 0.0) * 1000).toLong(),
            shuffle = player.shuffleModeEnabled || modelShuffle,
            modelShuffle = modelShuffle,
            repeat = repeatMode != Player.REPEAT_MODE_OFF,
            repeatMode = repeatMode,
            autoplay = Prefs.autoplay,
            error = null,
        )
        position(player)
        if (trackChanged && track != null) {
            reportedTrackKey = key
            autoplayDoneKey = null
            val id = track.id
            reportScope.launch { runCatching { Api.recordPlay(id) } }
        }
        if (track != null && (trackChanged || wasPlaying != state.playing)) {
            report(player)
            pushActivity(track, player.isPlaying, player.currentPosition)
        } else if (track == null || !player.isPlaying) {
            pushActivity(null, false, 0L)
        }
    }

    private fun position(player: Player) {
        val pos = player.currentPosition.coerceAtLeast(0)
        state = state.copy(position = pos)
        val now = System.currentTimeMillis()
        if (now - lastPositionSaveAt >= 3_000L || abs(pos - lastSavedPosition) >= 2_000L) {
            lastPositionSaveAt = now
            lastSavedPosition = pos
            saveQueue(player, pos)
        }
    }

    /** Snapshot everything needed to rebuild the exact queue after process death. */
    private fun saveQueue(player: Player, positionMs: Long) {
        if (queueTracks.isEmpty()) {
            Prefs.saveQueue(null)
            return
        }
        val (_, index) = currentTrack(player)
        Prefs.saveQueue(
            QueueSnapshot(
                tracks = queueTracks,
                index = index,
                positionMs = positionMs,
                repeatMode = player.repeatMode,
                shuffle = player.shuffleModeEnabled,
                autoplay = Prefs.autoplay,
            ),
        )
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

    /**
     * Radio only when the last item actually ended. Being near the end of the
     * queue is deliberately not enough, and manual Next is suppressed too.
     */
    private fun checkAutoplay(player: Player) {
        if (!Prefs.autoplay || autoplayBusy || queueTracks.isEmpty()) return
        if (player.repeatMode != Player.REPEAT_MODE_OFF) return
        if (player.playbackState != Player.STATE_ENDED) return
        val (track, index) = currentTrack(player)
        if (track == null || index != queueTracks.lastIndex) return
        val key = trackKey(index, track)
        if (key == autoplayDoneKey || key == suppressAutoplayKey) return
        autoplayBusy = true
        reportScope.launch {
            val suggestions = Api.radio(track.id).getOrElse { emptyList() }
            val existing = queueTracks.map { it.id }.toHashSet()
            val additions = suggestions
                .filter { it.id > 0 && it.id !in existing }
                .distinctBy { it.id }
                .take(5)
            if (additions.isNotEmpty()) play(queueTracks + additions, queueTracks.size)
            autoplayDoneKey = key
            autoplayBusy = false
        }
    }

    /** Push (or clear) Rotur/Discord activity when the playing state changes. */
    private fun pushActivity(track: Track?, playing: Boolean, positionMs: Long, force: Boolean = false) {
        val sinks = buildList {
            if (Prefs.roturActivity) add("rotur")
            if (Prefs.discordActivity) add("discord")
        }
        val key = "${track?.id}:$playing:${sinks.joinToString()}"
        if (!force && key == activitySignature) return
        activitySignature = key
        reportScope.launch {
            sinks.forEach { sink ->
                runCatching {
                    if (track != null && playing) Api.pushActivity(sink, track.id, positionMs, true)
                    else Api.pushActivity(sink, null, 0L, false)
                }
            }
        }
    }

    /** Call after an activity toggle in Settings so a stale activity is cleared. */
    fun activitySettingChanged() {
        val player = controller ?: return
        val (track, _) = currentTrack(player)
        pushActivity(track, player.isPlaying, player.currentPosition, force = true)
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

    private fun installQueue(player: Player, tracks: List<Track>, startIndex: Int, positionMs: Long = 0L) {
        if (tracks.isEmpty()) return
        queueTracks = tracks
        autoplayDoneKey = null
        suppressAutoplayKey = null
        player.setMediaItems(itemsOf(tracks), startIndex.coerceIn(0, tracks.lastIndex), positionMs)
        saveQueue(player, positionMs)
    }

    fun play(tracks: List<Track>, startIndex: Int = 0) {
        val c = controller ?: return
        if (tracks.isEmpty()) return
        installQueue(c, tracks, startIndex)
        c.prepare()
        c.play()
        publish(c)
    }

    /** Plays a single track without replacing the rest of the queue. */
    fun playNow(track: Track, queue: List<Track> = listOf(track)) {
        val index = queue.indexOfFirst { it.id == track.id }.coerceAtLeast(0)
        play(queue, index)
    }

    /**
     * Drop a track that was removed from the server library. The local queue
     * mirrors the server's queue, so leaving it in would try to stream a file
     * that no longer exists on the next track change.
     */
    fun removeTrack(id: Int) {
        val c = controller ?: return
        val removed = queueTracks.indexOfFirst { it.id == id }
        if (removed < 0) return
        val remaining = queueTracks.filterNot { it.id == id }
        if (remaining.isEmpty()) {
            queueTracks = emptyList()
            autoplayDoneKey = null
            suppressAutoplayKey = null
            c.stop()
            c.clearMediaItems()
            Prefs.saveQueue(null)
            state = PlaybackState(autoplay = Prefs.autoplay)
            return
        }
        val wasCurrent = state.track?.id == id
        val target = if (wasCurrent) {
            removed.coerceAtMost(remaining.lastIndex)
        } else {
            (c.currentMediaItemIndex - if (removed < c.currentMediaItemIndex) 1 else 0)
                .coerceIn(0, remaining.lastIndex)
        }
        val wasPlaying = c.isPlaying
        val position = if (wasCurrent) 0L else c.currentPosition
        installQueue(c, remaining, target, position)
        c.prepare()
        if (wasPlaying) c.play()
        publish(c)
    }

    /**
     * Remove one queue occurrence without touching the server library. Used by
     * the swipe-to-dismiss gesture in the Player queue.
     */
    fun removeFromQueue(index: Int) {
        val c = controller ?: return
        if (index !in queueTracks.indices) return
        val wasCurrent = index == state.index
        val remaining = queueTracks.filterIndexed { i, _ -> i != index }
        if (remaining.isEmpty()) {
            queueTracks = emptyList()
            autoplayDoneKey = null
            suppressAutoplayKey = null
            c.stop()
            c.clearMediaItems()
            Prefs.saveQueue(null)
            state = PlaybackState(autoplay = Prefs.autoplay)
            return
        }
        val target = if (wasCurrent) index.coerceAtMost(remaining.lastIndex)
        else (c.currentMediaItemIndex - if (index < c.currentMediaItemIndex) 1 else 0)
            .coerceIn(0, remaining.lastIndex)
        val wasPlaying = c.isPlaying
        val position = if (wasCurrent) 0L else c.currentPosition
        installQueue(c, remaining, target, position)
        c.prepare()
        if (wasPlaying) c.play()
        saveQueue(c, position)
        publish(c)
    }

    /** UI-facing progress pump; the service also refreshes on its own timer. */
    fun tick() {
        val c = controller ?: return
        position(c)
        checkSleep(c)
        checkAutoplay(c)
    }

    /** Pause music while a local video owns the speakers. */
    fun duckForVideo() {
        val c = controller ?: return
        if (!c.isPlaying) return
        videoPausedMusic = true
        c.pause()
        publish(c)
    }

    /** Resume music at the video's position after the video screen closes. */
    fun unduckFromVideo(positionMs: Long?) {
        val c = controller ?: return
        if (!videoPausedMusic) return
        videoPausedMusic = false
        if (positionMs != null && positionMs > 0) seekTo(positionMs)
        c.play()
        publish(c)
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
        val currentIndex = currentTrack(c).second
        val currentPosition = c.currentPosition
        queueTracks = queueTracks.toMutableList().also { it.add(to, it.removeAt(from)) }
        // Rebuild media ids so each occurrence keeps its position in the moved queue.
        installQueue(c, queueTracks, currentIndex, currentPosition)
        c.prepare()
        publish(c)
    }

    /** Manual Next never triggers radio, even when it happens on the last item. */
    fun next() {
        val c = controller ?: return
        val (track, index) = currentTrack(c)
        suppressAutoplayKey = trackKey(index, track)
        c.seekToNextMediaItem()
    }

    fun previous() { controller?.seekToPreviousMediaItem() }

    fun seekTo(ms: Long) {
        controller?.seekTo(ms.coerceAtLeast(0))
        controller?.let {
            position(it)
            saveQueue(it, ms.coerceAtLeast(0))
        }
    }

    fun seekFraction(fraction: Float) {
        val duration = state.duration
        if (duration > 0) seekTo((duration * fraction.coerceIn(0f, 1f)).toLong())
    }

    fun toggleShuffle() {
        val c = controller ?: return
        if (modelShuffle || c.shuffleModeEnabled) {
            modelShuffle = false
            c.shuffleModeEnabled = false
            saveQueue(c, c.currentPosition)
            publish(c)
            return
        }
        // With the 76% work-rate gate open, the server's MDL decides the order;
        // otherwise Media3's random shuffle is the fallback.
        modelShuffle = true
        state = state.copy(shuffle = true, modelShuffle = true)
        val currentId = state.track?.id ?: 0
        val ids = queueTracks.map { it.id }
        reportScope.launch {
            Api.modelRank(currentId, ids).fold(
                onSuccess = { ranked ->
                    if (modelShuffle && ranked.active && ranked.ids.size > 1) {
                        applyModelOrder(ranked.ids)
                    } else if (modelShuffle) {
                        c.shuffleModeEnabled = true
                        publish(c)
                    }
                },
                onFailure = {
                    if (modelShuffle) {
                        c.shuffleModeEnabled = true
                        publish(c)
                    }
                },
            )
        }
    }

    /** Rebuild the live queue in the order the MDL chose, keeping the current song. */
    private fun applyModelOrder(ids: List<Int>) {
        val c = controller ?: return
        val byId = queueTracks.associateBy { it.id }
        val ranked = ids.mapNotNull { byId[it] }
        if (ranked.size < 2) return
        val seen = ranked.map { it.id }.toSet()
        val ordered = ranked + queueTracks.filterNot { it.id in seen }
        val currentId = state.track?.id
        val index = ordered.indexOfFirst { it.id == currentId }.coerceAtLeast(0)
        val position = c.currentPosition
        val wasPlaying = c.isPlaying
        installQueue(c, ordered, index, position)
        c.prepare()
        if (wasPlaying) c.play()
        saveQueue(c, position)
        publish(c)
    }

    fun cycleRepeat() = setRepeatMode(
        when (state.repeatMode) {
            Player.REPEAT_MODE_OFF -> Player.REPEAT_MODE_ALL
            Player.REPEAT_MODE_ALL -> Player.REPEAT_MODE_ONE
            else -> Player.REPEAT_MODE_OFF
        },
    )

    /** Any repeat mode turns autoplay off; loop-one only repeats the current item. */
    fun setRepeatMode(mode: Int) {
        val c = controller ?: return
        c.repeatMode = mode
        if (mode != Player.REPEAT_MODE_OFF && Prefs.autoplay) Prefs.saveAutoplay(false)
        state = state.copy(autoplay = Prefs.autoplay)
        saveQueue(c, c.currentPosition)
        publish(c)
    }

    fun setAutoplay(enabled: Boolean) {
        val c = controller
        Prefs.saveAutoplay(enabled)
        if (enabled && c != null) c.repeatMode = Player.REPEAT_MODE_OFF
        state = state.copy(autoplay = enabled, repeatMode = c?.repeatMode ?: state.repeatMode)
        state = state.copy(repeat = state.repeatMode != Player.REPEAT_MODE_OFF)
        if (c != null) {
            saveQueue(c, c.currentPosition)
            publish(c)
        }
    }

    fun clearError() {
        state = state.copy(error = null)
    }

    fun stop() {
        controller?.let { report(it) }
        Prefs.saveSleepEndsAt(0L)
        reportedTrackKey = null
        autoplayDoneKey = null
        suppressAutoplayKey = null
        controller?.stop()
        controller?.clearMediaItems()
        queueTracks = emptyList()
        Prefs.saveQueue(null)
        pushActivity(null, false, 0L, force = true)
        state = PlaybackState(ready = controller != null, autoplay = Prefs.autoplay)
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
        // DefaultHttpDataSource cannot open file:// URIs. The delegate keeps the
        // auth headers for streams while DefaultDataSource handles local files.
        val sources = androidx.media3.datasource.DefaultDataSource.Factory(this, http)
        val player = androidx.media3.exoplayer.ExoPlayer.Builder(this)
            .setMediaSourceFactory(androidx.media3.exoplayer.source.DefaultMediaSourceFactory(sources))
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
