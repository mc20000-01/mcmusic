package dev.mcmusic.app.widget

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.LinearGradient
import android.graphics.Paint
import android.graphics.RectF
import android.graphics.Shader
import android.view.View
import android.widget.RemoteViews
import androidx.compose.ui.graphics.toArgb
import dev.mcmusic.app.MainActivity
import dev.mcmusic.app.R
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.Downloads
import dev.mcmusic.app.data.Listener
import dev.mcmusic.app.data.Prefs
import dev.mcmusic.app.data.Track
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.ui.design.DesignLanguage
import dev.mcmusic.app.ui.design.McPalette
import dev.mcmusic.app.ui.design.Palettes
import kotlinx.coroutines.runBlocking
import kotlin.math.roundToInt

/**
 * Home screen widgets, ported from the web embeds but aware of the phone: when
 * the app's player has a track loaded the widget mirrors that (and its buttons
 * control it), otherwise it falls back to the public "now" endpoint, the same
 * source the embeds use. RemoteViews cannot host Backdrop glass, so the surface
 * is a palette gradient with the selected language's radius.
 */
object Widgets {

    fun user(context: Context, id: Int? = null): String? {
        Prefs.init(context)
        val perWidget = id?.let { Prefs.widgetUserFor(it) }
        return perWidget ?: Prefs.widgetUser ?: Prefs.username
    }

    private fun palette(context: Context): McPalette {
        Prefs.init(context)
        val night = (context.resources.configuration.uiMode and
            android.content.res.Configuration.UI_MODE_NIGHT_MASK) ==
            android.content.res.Configuration.UI_MODE_NIGHT_YES
        return Palettes.resolve(Prefs.palette, night)
    }

    private fun cornerDp(context: Context): Float {
        Prefs.init(context)
        return 18f
    }

    /** Rewrites every placed widget of both sizes. */
    fun refresh(context: Context) {
        Prefs.init(context)
        Api.init(context)
        Downloads.init(context)
        val manager = AppWidgetManager.getInstance(context)
        refreshKind(context, manager, NowWidgetProvider::class.java, manager.getAppWidgetIds(ComponentName(context, NowWidgetProvider::class.java)), true)
        refreshKind(context, manager, BarWidgetProvider::class.java, manager.getAppWidgetIds(ComponentName(context, BarWidgetProvider::class.java)), false)
    }

    fun refreshKind(
        context: Context,
        manager: AppWidgetManager,
        provider: Class<out AppWidgetProvider>,
        ids: IntArray,
        tall: Boolean,
    ) {
        if (ids.isEmpty()) return
        val users = ids.associateWith { user(context, it) }
        val local = Playback.state
        Thread {
            val track = local.track
            val names = users.values.filterNotNull().distinct()
            val byUser = names.associateWith { name ->
                runCatching { runBlocking { Api.now(name) }.getOrNull() }.getOrNull()
            }
            ids.forEach { id ->
                val name = users[id]
                if (name == null && track == null) {
                    manager.updateAppWidget(id, signedOut(context, manager, id, tall))
                    return@forEach
                }
                val server: Listener? = if (track == null) name?.let { byUser[it] } else null
                val cover = when {
                    track != null -> coverForLocal(track)
                    server?.coverUrl?.isNotBlank() == true -> runCatching {
                        runBlocking { Api.cover(server.coverUrl) }?.let { bytes ->
                            BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
                        }
                    }.getOrNull()
                    else -> null
                }
                val views = if (tall) {
                    nowViews(context, manager, id, name, server, track, local.playing, cover)
                } else {
                    barViews(context, manager, id, name, server, track, local.playing, cover)
                }
                manager.updateAppWidget(id, views)
            }
        }.start()
    }

    private fun coverForLocal(track: Track): Bitmap? {
        Downloads.file(track.id)?.let { file ->
            val opts = BitmapFactory.Options().apply { inSampleSize = 2 }
            BitmapFactory.decodeFile(file.absolutePath, opts)?.let { return it }
        }
        return runCatching {
            runBlocking { Api.cover("${Api.server}/api/tracks/${track.id}/cover") }?.let { bytes ->
                BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
            }
        }.getOrNull()
    }

    private fun signedOut(context: Context, manager: AppWidgetManager, id: Int, tall: Boolean): RemoteViews {
        val views = RemoteViews(context.packageName, if (tall) R.layout.widget_now else R.layout.widget_bar)
        val palette = palette(context)
        views.setImageViewBitmap(R.id.widget_bg, background(context, manager, id, tall, palette))
        views.setViewVisibility(R.id.widget_toggle, View.GONE)
        views.setViewVisibility(R.id.widget_next, View.GONE)
        if (tall) {
            views.setViewVisibility(R.id.widget_cover, View.INVISIBLE)
            views.setTextViewText(R.id.widget_kicker, "mcmusic")
            views.setTextViewText(R.id.widget_title, "No account yet")
            views.setTextViewText(R.id.widget_sub, "Open mcmusic and sign in")
            views.setTextViewText(R.id.widget_state, "")
            views.setTextColor(R.id.widget_kicker, palette.accentText.toArgb())
            views.setTextColor(R.id.widget_title, palette.fg.toArgb())
            views.setTextColor(R.id.widget_sub, palette.dim.toArgb())
            views.setTextColor(R.id.widget_state, palette.dim.toArgb())
        } else {
            views.setViewVisibility(R.id.widget_cover, View.GONE)
            views.setTextViewText(R.id.widget_title, "mcmusic")
            views.setTextViewText(R.id.widget_sub, "Open the app and sign in")
            views.setInt(R.id.widget_dot, "setBackgroundColor", palette.dim.toArgb())
            views.setTextColor(R.id.widget_title, palette.fg.toArgb())
            views.setTextColor(R.id.widget_sub, palette.dim.toArgb())
        }
        views.setOnClickPendingIntent(R.id.widget_root, openApp(context))
        return views
    }

    private fun nowViews(
        context: Context,
        manager: AppWidgetManager,
        id: Int,
        user: String?,
        server: Listener?,
        local: Track?,
        localPlaying: Boolean,
        cover: Bitmap?,
    ): RemoteViews {
        val views = RemoteViews(context.packageName, R.layout.widget_now)
        val palette = palette(context)
        views.setImageViewBitmap(R.id.widget_bg, background(context, manager, id, true, palette))

        val track = local ?: server?.track
        val listening = local?.let { localPlaying } ?: (server?.listening == true)
        val title = track?.title?.takeIf { it.isNotBlank() } ?: "Nothing playing"
        val sub = listOfNotNull(
            track?.artist?.takeIf { it.isNotBlank() },
            track?.album?.takeIf { it.isNotBlank() },
        ).joinToString(" · ").ifBlank { "quiet right now" }
        val who = local?.let { "this phone" } ?: server?.username ?: user.orEmpty()
        val state = when {
            local != null -> "${if (localPlaying) "playing" else "paused"} · $who"
            server == null -> "not found on this server"
            listening && track != null -> "listening · $who"
            !listening && track != null -> "paused · $who"
            else -> "quiet · $who"
        }

        if (cover != null) views.setImageViewBitmap(R.id.widget_cover, cover) else views.setViewVisibility(R.id.widget_cover, View.INVISIBLE)
        views.setTextViewText(R.id.widget_kicker, local?.let { user ?: "mcmusic" } ?: (server?.username ?: user.orEmpty()))
        views.setTextViewText(R.id.widget_title, title)
        views.setTextViewText(R.id.widget_sub, sub)
        views.setTextViewText(R.id.widget_state, state)
        views.setTextColor(R.id.widget_kicker, palette.accentText.toArgb())
        views.setTextColor(R.id.widget_title, palette.fg.toArgb())
        views.setTextColor(R.id.widget_sub, palette.dim.toArgb())
        views.setTextColor(R.id.widget_state, if (listening) palette.accentText.toArgb() else palette.dim.toArgb())

        controls(views, context, palette, local != null, localPlaying)
        views.setOnClickPendingIntent(R.id.widget_root, openApp(context))
        return views
    }

    private fun barViews(
        context: Context,
        manager: AppWidgetManager,
        id: Int,
        user: String?,
        server: Listener?,
        local: Track?,
        localPlaying: Boolean,
        cover: Bitmap?,
    ): RemoteViews {
        val views = RemoteViews(context.packageName, R.layout.widget_bar)
        val palette = palette(context)
        views.setImageViewBitmap(R.id.widget_bg, background(context, manager, id, false, palette))

        val track = local ?: server?.track
        val listening = local?.let { localPlaying } ?: (server?.listening == true)
        val title = track?.title?.takeIf { it.isNotBlank() }
            ?: (server?.username ?: user)?.let { "$it is quiet" }
            ?: "mcmusic"
        val sub = track?.artist?.takeIf { it.isNotBlank() } ?: "mcmusic"

        if (cover != null) views.setImageViewBitmap(R.id.widget_cover, cover) else views.setViewVisibility(R.id.widget_cover, View.GONE)
        views.setInt(R.id.widget_dot, "setBackgroundColor",
            (if (listening) palette.accentText else palette.dim).toArgb())
        views.setTextViewText(R.id.widget_title, title)
        views.setTextViewText(R.id.widget_sub, sub)
        views.setTextColor(R.id.widget_title, palette.fg.toArgb())
        views.setTextColor(R.id.widget_sub, palette.dim.toArgb())

        controls(views, context, palette, local != null, localPlaying)
        views.setOnClickPendingIntent(R.id.widget_root, openApp(context))
        return views
    }

    /** Play/pause and skip, only when this widget is showing the phone's queue. */
    private fun controls(
        views: RemoteViews,
        context: Context,
        palette: McPalette,
        canControl: Boolean,
        playing: Boolean,
    ) {
        if (!canControl) {
            views.setViewVisibility(R.id.widget_toggle, View.GONE)
            views.setViewVisibility(R.id.widget_next, View.GONE)
            return
        }
        views.setViewVisibility(R.id.widget_toggle, View.VISIBLE)
        views.setViewVisibility(R.id.widget_next, View.VISIBLE)
        views.setImageViewResource(
            R.id.widget_toggle,
            if (playing) R.drawable.ic_lucide_pause else R.drawable.ic_lucide_play,
        )
        views.setInt(R.id.widget_toggle, "setColorFilter", palette.accentText.toArgb())
        views.setImageViewResource(R.id.widget_next, R.drawable.ic_lucide_skip_forward)
        views.setInt(R.id.widget_next, "setColorFilter", palette.dim.toArgb())
        views.setOnClickPendingIntent(
            R.id.widget_toggle,
            WidgetControlReceiver.pending(context, WidgetControlReceiver.ACTION_TOGGLE, 1),
        )
        views.setOnClickPendingIntent(
            R.id.widget_next,
            WidgetControlReceiver.pending(context, WidgetControlReceiver.ACTION_NEXT, 2),
        )
    }

    /** Palette gradient with the accent glow the embeds put in the top corner. */
    private fun background(context: Context, manager: AppWidgetManager, id: Int, tall: Boolean, palette: McPalette): Bitmap {
        val options = manager.getAppWidgetOptions(id)
        val widthDp = options.getInt(AppWidgetManager.OPTION_APPWIDGET_MIN_WIDTH).takeIf { it > 0 } ?: if (tall) 250 else 180
        val heightDp = options.getInt(AppWidgetManager.OPTION_APPWIDGET_MIN_HEIGHT).takeIf { it > 0 } ?: if (tall) 70 else 40
        val density = context.resources.displayMetrics.density
        val w = (widthDp * density).roundToInt().coerceAtLeast(1)
        val h = (heightDp * density).roundToInt().coerceAtLeast(1)

        val bitmap = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(bitmap)
        val radius = cornerDp(context) * density
        val rect = RectF(0f, 0f, w.toFloat(), h.toFloat())
        val paint = Paint(Paint.ANTI_ALIAS_FLAG)

        paint.shader = LinearGradient(0f, 0f, 0f, h.toFloat(), palette.bg.toArgb(), palette.bg2.toArgb(), Shader.TileMode.CLAMP)
        canvas.drawRoundRect(rect, radius, radius, paint)
        paint.shader = null

        paint.color = palette.accent.copy(alpha = 0.16f).toArgb()
        canvas.drawCircle(w * 0.08f, 0f, h * 1.4f, paint)

        paint.style = Paint.Style.STROKE
        paint.strokeWidth = 1f * density
        paint.color = palette.line.copy(alpha = 0.75f).toArgb()
        canvas.drawRoundRect(RectF(0.5f, 0.5f, w - 0.5f, h - 0.5f), radius, radius, paint)
        return bitmap
    }

    private fun openApp(context: Context): PendingIntent {
        val intent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        return PendingIntent.getActivity(
            context,
            0,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
    }

    /** Small helper for tests and debugging. */
    fun describe(listener: Listener?): String = when {
        listener == null -> "not found"
        listener.listening -> "listening"
        listener.track != null -> "paused"
        else -> "quiet"
    }
}

class NowWidgetProvider : AppWidgetProvider() {
    override fun onUpdate(context: Context, appWidgetManager: AppWidgetManager, appWidgetIds: IntArray) {
        Prefs.init(context)
        Api.init(context)
        Widgets.refreshKind(context, appWidgetManager, NowWidgetProvider::class.java, appWidgetIds, true)
    }
}

class BarWidgetProvider : AppWidgetProvider() {
    override fun onUpdate(context: Context, appWidgetManager: AppWidgetManager, appWidgetIds: IntArray) {
        Prefs.init(context)
        Api.init(context)
        Widgets.refreshKind(context, appWidgetManager, BarWidgetProvider::class.java, appWidgetIds, false)
    }
}
