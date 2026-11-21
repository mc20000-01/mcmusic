package dev.mcmusic.app.widget

import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.os.Handler
import android.os.Looper
import androidx.media3.session.MediaController
import androidx.media3.session.SessionToken
import dev.mcmusic.app.playback.PlaybackService

/**
 * Widget taps cannot call into the app directly, so they land here: connect a
 * short-lived MediaController to the playback session, send one command, then
 * release it and repaint the widgets.
 */
class WidgetControlReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val action = intent.action ?: return
        val pending = goAsync()
        val app = context.applicationContext
        val token = SessionToken(app, ComponentName(app, PlaybackService::class.java))
        val future = MediaController.Builder(app, token).buildAsync()
        val main = Handler(Looper.getMainLooper())
        future.addListener({
            try {
                val controller = runCatching { future.get() }.getOrNull()
                if (controller != null) {
                    when (action) {
                        ACTION_TOGGLE -> if (controller.isPlaying) controller.pause() else controller.play()
                        ACTION_NEXT -> controller.seekToNextMediaItem()
                        ACTION_PREVIOUS -> controller.seekToPreviousMediaItem()
                    }
                    main.postDelayed({ runCatching { controller.release() } }, 600)
                }
                main.postDelayed({ runCatching { Widgets.refresh(app) } }, 900)
            } finally {
                pending.finish()
            }
        }, java.util.concurrent.Executor { runnable -> main.post(runnable) })
    }

    companion object {
        const val ACTION_TOGGLE = "dev.mcmusic.app.widget.TOGGLE"
        const val ACTION_NEXT = "dev.mcmusic.app.widget.NEXT"
        const val ACTION_PREVIOUS = "dev.mcmusic.app.widget.PREVIOUS"

        fun pending(context: Context, action: String, code: Int): PendingIntent {
            val intent = Intent(context, WidgetControlReceiver::class.java).setAction(action)
            return PendingIntent.getBroadcast(
                context,
                code,
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
            )
        }
    }
}
