package dev.mcmusic.app.play

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.media.MediaMetadata
import android.media.session.MediaSession
import android.media.session.PlaybackState
import android.os.Build
import android.os.IBinder
import androidx.core.content.ContextCompat
import dev.mcmusic.app.MainActivity
import dev.mcmusic.app.R

/**
 * The bridge between the notification/lock-screen/media widgets and the
 * in-app engine. PlaybackService owns the platform MediaSession, so Android
 * (and anything reading the media session: widgets, Bluetooth, Wear, the
 * media carousel) sees a real music player instead of a plain notification.
 */
object MediaControls {
    var onPlayPause: (() -> Unit)? = null
    var onNext: (() -> Unit)? = null
    var onPrev: (() -> Unit)? = null
    var onSeek: ((Double) -> Unit)? = null
}

class PlaybackService : Service() {

    companion object {
        private const val CHANNEL = "mcmusic_playback"
        private const val NOTIFY_ID = 4101
        private const val EXTRA_TITLE = "title"
        private const val EXTRA_SUB = "sub"
        private const val EXTRA_PLAYING = "playing"
        private const val EXTRA_POSITION = "position"
        private const val EXTRA_DURATION = "duration"
        private const val EXTRA_ART = "art"
        private const val EXTRA_COOKIE = "cookie"
        private const val ACTION_START = "dev.mcmusic.app.PLAYBACK_START"
        private const val ACTION_UPDATE = "dev.mcmusic.app.PLAYBACK_UPDATE"
        private const val ACTION_TOGGLE = "dev.mcmusic.app.TOGGLE"
        private const val ACTION_NEXT = "dev.mcmusic.app.NEXT"
        private const val ACTION_PREV = "dev.mcmusic.app.PREV"

        fun start(
            context: Context,
            title: String,
            sub: String,
            playing: Boolean = true,
            artUrl: String? = null,
            cookie: String = "",
        ) {
            send(context, ACTION_START, title, sub, playing, 0, 0, true, artUrl, cookie)
        }

        fun update(
            context: Context,
            title: String,
            sub: String,
            playing: Boolean,
            positionMs: Long,
            durationMs: Long,
            artUrl: String? = null,
            cookie: String = "",
        ) {
            send(context, ACTION_UPDATE, title, sub, playing, positionMs, durationMs, false, artUrl, cookie)
        }

        private fun send(
            context: Context,
            action: String,
            title: String,
            sub: String,
            playing: Boolean,
            positionMs: Long,
            durationMs: Long,
            foreground: Boolean,
            artUrl: String?,
            cookie: String,
        ) {
            val intent = Intent(context, PlaybackService::class.java)
                .setAction(action)
                .putExtra(EXTRA_TITLE, title)
                .putExtra(EXTRA_SUB, sub)
                .putExtra(EXTRA_PLAYING, playing)
                .putExtra(EXTRA_POSITION, positionMs)
                .putExtra(EXTRA_DURATION, durationMs)
                .putExtra(EXTRA_ART, artUrl)
                .putExtra(EXTRA_COOKIE, cookie)
            try {
                if (foreground) ContextCompat.startForegroundService(context, intent)
                else context.startService(intent)
            } catch (e: Exception) {
                /* a refused start must never break playback inside the app */
            }
        }

        fun stop(context: Context) {
            try {
                context.stopService(Intent(context, PlaybackService::class.java))
            } catch (e: Exception) {
                /* already gone */
            }
        }
    }

    private var session: MediaSession? = null
    private var receiver: BroadcastReceiver? = null

    private var title: String = "mcmusic"
    private var sub: String = ""
    private var playing: Boolean = false
    private var positionMs: Long = 0
    private var durationMs: Long = 0
    private var artUrl: String? = null
    private var artBitmap: android.graphics.Bitmap? = null

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        session = MediaSession(this, "mcmusic").apply {
            setCallback(object : MediaSession.Callback() {
                override fun onPlay() { MediaControls.onPlayPause?.invoke() }
                override fun onPause() { MediaControls.onPlayPause?.invoke() }
                override fun onSkipToNext() { MediaControls.onNext?.invoke() }
                override fun onSkipToPrevious() { MediaControls.onPrev?.invoke() }
                override fun onSeekTo(pos: Long) { MediaControls.onSeek?.invoke(pos / 1000.0) }
            })
            isActive = true
        }
        val filter = IntentFilter().apply {
            addAction(ACTION_TOGGLE)
            addAction(ACTION_NEXT)
            addAction(ACTION_PREV)
        }
        val recv = object : BroadcastReceiver() {
            override fun onReceive(ctx: Context?, intent: Intent?) {
                when (intent?.action) {
                    ACTION_TOGGLE -> MediaControls.onPlayPause?.invoke()
                    ACTION_NEXT -> MediaControls.onNext?.invoke()
                    ACTION_PREV -> MediaControls.onPrev?.invoke()
                }
            }
        }
        receiver = recv
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(recv, filter, Context.RECEIVER_NOT_EXPORTED)
        } else {
            @Suppress("UnspecifiedRegisterReceiverFlag")
            registerReceiver(recv, filter)
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        intent?.getStringExtra(EXTRA_TITLE)?.takeIf { it.isNotBlank() }?.let { title = it }
        intent?.getStringExtra(EXTRA_SUB)?.let { sub = it }
        intent?.getBooleanExtra(EXTRA_PLAYING, playing)?.let { playing = it }
        positionMs = intent?.getLongExtra(EXTRA_POSITION, positionMs) ?: positionMs
        durationMs = intent?.getLongExtra(EXTRA_DURATION, durationMs) ?: durationMs
        loadArt(
            intent?.getStringExtra(EXTRA_ART),
            intent?.getStringExtra(EXTRA_COOKIE).orEmpty(),
        )

        startForeground(NOTIFY_ID, buildNotification())
        publish()
        return START_STICKY
    }

    private fun channelId(): String {
        val nm = getSystemService(NotificationManager::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && nm.getNotificationChannel(CHANNEL) == null) {
            nm.createNotificationChannel(
                NotificationChannel(CHANNEL, "Playback", NotificationManager.IMPORTANCE_LOW).apply {
                    setShowBadge(false)
                    description = "What mcmusic is playing"
                }
            )
        }
        return CHANNEL
    }

    private fun loadArt(url: String?, cookie: String) {
        if (url.isNullOrBlank()) {
            artBitmap = null
            artUrl = null
            return
        }
        if (url == artUrl && artBitmap != null) return
        artUrl = url
        artBitmap = null
        Thread {
            val bmp = runCatching {
                val conn = (java.net.URL(url).openConnection() as java.net.HttpURLConnection)
                conn.connectTimeout = 8_000
                conn.readTimeout = 8_000
                if (cookie.isNotBlank()) conn.setRequestProperty("Cookie", cookie)
                conn.inputStream.use { android.graphics.BitmapFactory.decodeStream(it) }
            }.getOrNull()
            if (bmp != null && url == artUrl) {
                artBitmap = bmp
                android.os.Handler(mainLooper).post { runCatching { publish() } }
            }
        }.also { it.isDaemon = true }.start()
    }

    private fun durationText(): String? {
        if (durationMs <= 0) return null
        val total = durationMs / 1000
        return "%d:%02d".format(total / 60, total % 60)
    }

    private fun publish() {
        val token = session?.sessionToken ?: return
        val meta = MediaMetadata.Builder()
            .putString(MediaMetadata.METADATA_KEY_TITLE, title)
            .putString(MediaMetadata.METADATA_KEY_ARTIST, sub)
            .putString(MediaMetadata.METADATA_KEY_ALBUM_ARTIST, sub)
            .putLong(MediaMetadata.METADATA_KEY_DURATION, durationMs)
        artBitmap?.let {
            meta.putBitmap(MediaMetadata.METADATA_KEY_ALBUM_ART, it)
            meta.putBitmap(MediaMetadata.METADATA_KEY_ART, it)
        }
        session?.setMetadata(meta.build())
        session?.setPlaybackState(
            PlaybackState.Builder()
                .setActions(
                    PlaybackState.ACTION_PLAY or PlaybackState.ACTION_PAUSE or
                        PlaybackState.ACTION_PLAY_PAUSE or PlaybackState.ACTION_SKIP_TO_NEXT or
                        PlaybackState.ACTION_SKIP_TO_PREVIOUS or PlaybackState.ACTION_SEEK_TO
                )
                .setState(
                    if (playing) PlaybackState.STATE_PLAYING else PlaybackState.STATE_PAUSED,
                    positionMs,
                    if (playing) 1f else 0f,
                )
                .build()
        )
        val nm = getSystemService(NotificationManager::class.java)
        nm.notify(NOTIFY_ID, buildNotification())
    }

    private fun action(action: String, request: Int): PendingIntent =
        PendingIntent.getBroadcast(
            this,
            request,
            Intent(this, PlaybackService::class.java).setAction(action),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )

    private fun buildNotification(): Notification {
        val open = PendingIntent.getActivity(
            this,
            0,
            Intent(this, MainActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
            },
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        val toggleIcon = if (playing) android.R.drawable.ic_media_pause else android.R.drawable.ic_media_play
        val style = Notification.MediaStyle()
            .setMediaSession(session?.sessionToken)
            .setShowActionsInCompactView(0, 1, 2)

        return Notification.Builder(this, channelId())
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setContentTitle(title)
            .setContentText(sub)
            .setContentIntent(open)
            .setStyle(style)
            .setLargeIcon(artBitmap)
            .setSubText(durationText())
            .setProgress(
                if (durationMs > 0) 1000 else 0,
                if (durationMs > 0) ((positionMs * 1000) / durationMs).toInt().coerceIn(0, 1000) else 0,
                false,
            )
            .setOngoing(playing)
            .setOnlyAlertOnce(true)
            .setVisibility(Notification.VISIBILITY_PUBLIC)
            .setCategory(Notification.CATEGORY_TRANSPORT)
            .addAction(
                Notification.Action.Builder(
                    android.R.drawable.ic_media_previous, "Previous", action(ACTION_PREV, 1)
                ).build()
            )
            .addAction(
                Notification.Action.Builder(toggleIcon, if (playing) "Pause" else "Play", action(ACTION_TOGGLE, 2)).build()
            )
            .addAction(
                Notification.Action.Builder(
                    android.R.drawable.ic_media_next, "Next", action(ACTION_NEXT, 3)
                ).build()
            )
            .build()
    }

    override fun onDestroy() {
        receiver?.let { runCatching { unregisterReceiver(it) } }
        session?.isActive = false
        session?.release()
        session = null
        super.onDestroy()
    }
}
