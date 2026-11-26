package dev.mcmusic.app.ui.screens

import android.view.SurfaceView
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.datasource.DefaultHttpDataSource
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.exoplayer.source.DefaultMediaSourceFactory
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.VideoInfo
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.playback.checkedFactory
import dev.mcmusic.app.ui.Cover
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.ErrorLine
import dev.mcmusic.app.ui.IconButton
import dev.mcmusic.app.ui.Loading
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.Muted
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.SectionLabel
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface
import dev.mcmusic.app.ui.formatMillis
import dev.mcmusic.app.ui.trackCoverUrl
import kotlinx.coroutines.delay

/**
 * Videos imported with a request live on the server for four hours after the
 * last view. This pane plays that local file with ExoPlayer — no YouTube embed
 * and no second set of controls from a web view.
 */
@Composable
fun VideosScreen(
    ytId: String? = null,
    startMs: Long = 0L,
    onBack: () -> Unit,
    onPlay: (String, Long) -> Unit,
    onClosed: (Long?) -> Unit,
) {
    if (!ytId.isNullOrBlank()) {
        VideoPlaybackScreen(ytId, startMs, onBack, onClosed)
        return
    }
    val design = LocalDesign.current
    var videos by remember { mutableStateOf<List<VideoInfo>?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var reload by remember { mutableStateOf(0) }

    LaunchedEffect(reload) {
        Api.videos().fold(
            onSuccess = { videos = it; error = null },
            onFailure = { error = it.message ?: "could not load videos"; videos = emptyList() },
        )
    }

    LazyColumn(
        contentPadding = PaddingValues(design.screenPadding, 10.dp, design.screenPadding, 24.dp),
        verticalArrangement = Arrangement.spacedBy(9.dp),
    ) {
        item {
            ScreenTitle("Videos", "Music videos saved with your requests.")
        }
        error?.let { item { ErrorLine(it) } }
        item {
            SectionLabel("Cached for four hours after your last view") {
                IconButton(Lucide.RefreshCw, size = 16.dp) { reload++ }
            }
        }
        val list = videos.orEmpty()
        if (list.isEmpty()) {
            item {
                EmptyState(
                    icon = Lucide.Film,
                    title = "No videos yet",
                    body = "Import a YouTube link, then its video appears here alongside the music.",
                )
            }
        }
        items(list, key = { it.ytId }) { video ->
            Row(
                Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(design.cardRadius))
                    .mcSurface()
                    .clickable { onPlay(video.ytId, 0L) }
                    .padding(10.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(11.dp),
            ) {
                Cover(
                    url = video.trackId?.let { trackCoverUrl(it) }.orEmpty(),
                    shape = RoundedCornerShape(8.dp),
                    modifier = Modifier.size(58.dp),
                    fallback = design.accentSoft,
                )
                Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                    Text(
                        video.title.ifBlank { video.ytId },
                        color = design.fg,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.SemiBold,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                    Muted(video.artist.ifBlank { "Saved on this server" }, size = 11)
                    Muted("Expires ${formatExpiry(video.expires)}", size = 10)
                }
                IconButton(Lucide.Play, tint = design.accentText) { onPlay(video.ytId, 0L) }
            }
        }
        item {
            Muted(
                "Videos play from mcmusic's own cache. Watching one keeps it for another four hours.",
                size = 11,
            )
        }
    }
}

private fun formatExpiry(expires: Long): String {
    val minutes = ((expires - System.currentTimeMillis() / 1000) / 60).coerceAtLeast(0)
    return if (minutes >= 60) "${minutes / 60}h ${minutes % 60}m" else "${minutes}m"
}

/** Full-screen local video with controls and the current song's start position. */
@Composable
private fun VideoPlaybackScreen(
    ytId: String,
    startMs: Long,
    onBack: () -> Unit,
    onClosed: (Long?) -> Unit,
) {
    val context = LocalContext.current
    val design = LocalDesign.current
    var info by remember(ytId) { mutableStateOf<VideoInfo?>(null) }
    var error by remember(ytId) { mutableStateOf<String?>(null) }

    LaunchedEffect(ytId) {
        Playback.duckForVideo()
        while (true) {
            val result = Api.video(ytId, prepare = info == null)
            if (result.isSuccess) {
                val found = result.getOrThrow()
                info = found
                error = null
                if (found.state == "ready") break
            } else {
                error = result.exceptionOrNull()?.message ?: "could not reach the server"
            }
            delay(1_500)
        }
    }

    val url = info?.url
    if (url.isNullOrBlank()) {
        LazyColumn(
            Modifier.fillMaxSize(),
            contentPadding = PaddingValues(design.screenPadding),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            item { ScreenTitle("Video", info?.title ?: ytId) }
            error?.let { item { ErrorLine(it) } }
            item {
                Loading(
                    when (info?.state) {
                        "preparing" -> "Saving this video for offline playback…"
                        else -> "Looking for this video…"
                    },
                )
            }
            item { Muted("It will play as soon as the server finishes caching it.", size = 11) }
        }
        return
    }

    val player = remember(url) {
        val source = checkedFactory(DefaultHttpDataSource.Factory()
            .setUserAgent("mcmusic-android")
            .setDefaultRequestProperties(Api.authHeaders()))
        ExoPlayer.Builder(context)
            .setMediaSourceFactory(DefaultMediaSourceFactory(source))
            .build()
            .apply {
                setMediaItem(MediaItem.fromUri(Api.videoUrl(ytId)))
                prepare()
                if (startMs > 0) seekTo(startMs)
                playWhenReady = true
            }
    }
    var playing by remember(url) { mutableStateOf(true) }
    var position by remember(url) { mutableLongStateOf(startMs) }
    var duration by remember(url) { mutableLongStateOf(0L) }
    var scrub by remember(url) { mutableFloatStateOf(0f) }

    DisposableEffect(player) {
        val listener = object : Player.Listener {
            override fun onPlaybackStateChanged(state: Int) {
                duration = player.duration.coerceAtLeast(0)
            }

            override fun onIsPlayingChanged(value: Boolean) {
                playing = value
            }
        }
        player.addListener(listener)
        onDispose {
            val finalPosition = player.currentPosition
            player.removeListener(listener)
            player.release()
            Playback.unduckFromVideo(finalPosition)
            onClosed(finalPosition)
        }
    }

    LaunchedEffect(Unit) {
        while (true) {
            position = player.currentPosition
            if (duration <= 0) duration = player.duration.coerceAtLeast(0)
            delay(500)
        }
    }

    val fraction = if (duration > 0) scrub.takeIf { it != 0f } ?: (position.toFloat() / duration) else 0f
    Column(
        Modifier
            .fillMaxSize()
            .background(design.palette.bg)
            .padding(horizontal = 10.dp, vertical = 12.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            IconButton(Lucide.ChevronLeft) { onBack() }
            Column(Modifier.weight(1f)) {
                Text(
                    info?.title ?: ytId,
                    color = design.fg,
                    fontSize = 15.sp,
                    fontWeight = FontWeight.SemiBold,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                Muted(info?.artist.orEmpty(), size = 11)
            }
        }
        Box(
            Modifier
                .fillMaxWidth()
                .aspectRatio(16f / 9f)
                .clip(RoundedCornerShape(design.cardRadius))
                .background(design.palette.bg2),
        ) {
            AndroidView(
                factory = { ctx ->
                    SurfaceView(ctx).also { player.setVideoSurfaceView(it) }
                },
                modifier = Modifier.fillMaxSize(),
            )
        }
        Slider(
            value = fraction.coerceIn(0f, 1f),
            onValueChange = { scrub = it },
            onValueChangeFinished = {
                if (duration > 0) player.seekTo((duration * scrub).toLong())
                scrub = 0f
            },
            colors = SliderDefaults.colors(
                thumbColor = design.accentText,
                activeTrackColor = design.accentText,
                inactiveTrackColor = design.hairline,
            ),
        )
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Muted(formatMillis(position), size = 11)
            Muted(formatMillis(duration), size = 11)
        }
        Row(
            Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(Lucide.SkipBack, size = 20.dp) { player.seekToMaxToPrevious() }
            Box(
                Modifier
                    .size(54.dp)
                    .clip(RoundedCornerShape(50))
                    .background(design.accent)
                    .clickable {
                        if (playing) player.pause() else player.play()
                    },
                Alignment.Center,
            ) {
                dev.mcmusic.app.ui.LucideIcon(
                    if (playing) Lucide.Pause else Lucide.Play,
                    design.onAccent,
                    size = 20.dp,
                )
            }
            IconButton(Lucide.SkipForward, size = 20.dp) { player.seekTo(player.currentPosition + 10_000L) }
        }
        Muted("Audio follows the video; your music resumes where you left it when you go back.", size = 11)
    }
}

private fun ExoPlayer.seekToMaxToPrevious() = seekTo((currentPosition - 10_000L).coerceAtLeast(0L))
