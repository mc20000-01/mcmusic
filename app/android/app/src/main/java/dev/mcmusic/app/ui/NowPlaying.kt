package dev.mcmusic.app.ui

import android.content.Intent
import android.net.Uri
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.systemBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import dev.mcmusic.app.AppViewModel
import dev.mcmusic.app.Route
import dev.mcmusic.app.ui.theme.D
import dev.mcmusic.app.ui.theme.LocalMc
import dev.mcmusic.app.ui.theme.McType
import kotlin.math.PI
import kotlin.math.sin

@OptIn(ExperimentalFoundationApi::class)
@Composable
fun PlayerOverlay(vm: AppViewModel) {
    val mc = LocalMc.current
    val engine = vm.engine
    val t = engine.current
    val haptics = LocalHapticFeedback.current
    // One short tick per press. It's the cheapest way to make a flat pane of
    // glass feel like hardware, and it stays out of the way of the audio.
    val tick: () -> Unit = { haptics.performHapticFeedback(HapticFeedbackType.LongPress) }
    var lyricsOpen by remember { mutableStateOf(false) }

    Box(
        Modifier.fillMaxSize().background(
            Brush.verticalGradient(
                listOf(
                    mc.accent.copy(alpha = 0.20f),
                    mc.bg.copy(alpha = 0.94f),
                    mc.bg,
                ),
            ),
        ),
    ) {
        Column(
            Modifier
                .fillMaxSize()
                .systemBarsPadding()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 18.dp, vertical = 8.dp),
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                IconBtn(AppIcons.ChevronDown, { vm.playerOpen = false }, contentDescription = "Close")
                Text(
                    "NOW PLAYING",
                    style = McType.kicker,
                    color = mc.accent,
                    modifier = Modifier.weight(1f),
                    textAlign = androidx.compose.ui.text.style.TextAlign.Center,
                )
                if (t != null) {
                    IconBtn(AppIcons.MoreVertical, { vm.openTrackMenu(t) }, contentDescription = "Track options")
                } else {
                    Spacer(Modifier.size(32.dp))
                }
            }

            if (t == null) {
                Spacer(Modifier.height(80.dp))
                EmptyState(
                    "Nothing playing right now",
                    "Pick a song from your library to get started.",
                    icon = AppIcons.Disc,
                    actionLabel = "Browse your library",
                    onAction = {
                        vm.playerOpen = false
                        vm.navigate(Route.Library, push = false)
                    },
                )
                return@Column
            }

            BoxWithConstraints(
                Modifier
                    .fillMaxWidth()
                    .padding(top = 14.dp)
                    .background(
                        Brush.radialGradient(
                            listOf(mc.accent.copy(alpha = 0.16f), Color.Transparent),
                        ),
                    ),
                contentAlignment = Alignment.Center,
            ) {
                val artSize = minOf(maxWidth * 0.72f, 300.dp)
                Art(
                    t.id,
                    artSize,
                    modifier = Modifier
                        .clip(RoundedCornerShape(D.r3))
                        .combinedClickable(
                            onClick = {},
                            onLongClickLabel = "Track options",
                            onLongClick = { tick(); vm.openTrackMenu(t) },
                        ),
                )
            }

            Spacer(Modifier.height(22.dp))
            Text(
                t.title,
                style = McType.h2,
                color = mc.fg,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
                textAlign = TextAlign.Center,
                modifier = Modifier.fillMaxWidth(),
            )
            Spacer(Modifier.height(4.dp))
            Row(
                Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.Center,
            ) {
                Text(t.artist, style = McType.bodySm, color = mc.dim)
                if (t.album.isNotBlank()) {
                    Text("  ·  ", style = McType.bodySm, color = mc.dim2)
                    Text(
                        t.album,
                        style = McType.bodySm,
                        color = mc.dim2,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                        modifier = Modifier.clickable { vm.navigate(Route.Album(t.album)) },
                    )
                }
            }

            Spacer(Modifier.height(18.dp))
            ProgressBar(
                position = engine.position,
                duration = if (engine.duration > 0) engine.duration else t.duration,
                onSeekFraction = { engine.seekFraction(it) },
            )

            Spacer(Modifier.height(18.dp))
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                IconBtn(
                    AppIcons.Shuffle,
                    { tick(); engine.toggleShuffle() },
                    size = 40.dp,
                    tint = if (engine.shuffle) mc.accent else mc.dim,
                    contentDescription = if (engine.shuffle) "Shuffle on" else "Shuffle off",
                )
                IconBtn(AppIcons.SkipBack, { tick(); engine.prev() }, size = 44.dp, tint = mc.fg,
                    contentDescription = "Previous track")
                Box(
                    Modifier
                        .size(56.dp)
                        .shadow(
                            12.dp,
                            CircleShape,
                            ambientColor = mc.accent.copy(alpha = 0.28f),
                            spotColor = mc.accent.copy(alpha = 0.28f),
                        )
                        .clip(CircleShape)
                        .background(mc.accent)
                        .clickable { tick(); engine.toggle() },
                    contentAlignment = Alignment.Center,
                ) {
                    Icon(
                        if (engine.playing) AppIcons.Pause else AppIcons.Play,
                        if (engine.playing) "Pause" else "Play",
                        Modifier.size(22.dp),
                        tint = mc.accentFg,
                    )
                }
                IconBtn(AppIcons.SkipForward, { tick(); engine.next() }, size = 44.dp, tint = mc.fg,
                    contentDescription = "Next track")
                IconBtn(
                    if (engine.repeat == "one") AppIcons.RepeatOne else AppIcons.Repeat,
                    { tick(); engine.cycleRepeat() },
                    size = 40.dp,
                    tint = if (engine.repeat != "off") mc.accent else mc.dim,
                    contentDescription = when (engine.repeat) {
                        "one" -> "Repeat one"
                        "all" -> "Repeat all"
                        else -> "Repeat off"
                    },
                )
            }

            Spacer(Modifier.height(16.dp))
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                IconBtn(
                    AppIcons.Heart,
                    { tick(); vm.toggleLike(t) },
                    size = 40.dp,
                    tint = if (t.liked) mc.accent else mc.dim,
                    contentDescription = if (t.liked) "Remove from likes" else "Add to likes",
                )
                McButton(
                    "Lyrics",
                    { tick(); lyricsOpen = true },
                    small = true,
                    ghost = true,
                    leading = AppIcons.Text,
                )
                McButton(
                    "Queue",
                    { tick(); vm.queueOpen = true },
                    small = true,
                    ghost = true,
                    leading = AppIcons.ListMusic,
                )
                IconBtn(
                    AppIcons.FolderPlus,
                    { tick(); vm.openAddToPlaylist(t) },
                    size = 40.dp,
                    contentDescription = "Add to playlist",
                )
            }

            Spacer(Modifier.height(24.dp))
        }

        if (lyricsOpen) {
            t?.let { LyricsSheet(vm, it, onDismiss = { lyricsOpen = false }) }
        }
    }
}

/**
 * The same player rendered as a routed screen (used by deep links from the deck
 * when the user navigates to the "now" view).
 */
@Composable
fun NowPlayingScreen(vm: AppViewModel) {
    val mc = LocalMc.current
    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(D.gutter),
    ) {
        val t = vm.engine.current
        if (t == null) {
            EmptyState(
                "Nothing playing right now",
                "Pick a song from your library and it’ll show up here.",
                icon = AppIcons.Disc,
                actionLabel = "Browse your library",
                onAction = { vm.navigate(Route.Library, push = false) },
            )
            return@Column
        }
        val ctx = LocalContext.current
        var showLyrics by remember { mutableStateOf(false) }
        var lyricText by remember { mutableStateOf("") }
        LaunchedEffect(t.id, showLyrics) {
            if (showLyrics) lyricText = vm.lyrics(t.id)
        }
        Text("NOW PLAYING", style = McType.kicker, color = mc.accent)
        Spacer(Modifier.height(10.dp))
        Art(t.id, 260.dp)
        Spacer(Modifier.height(16.dp))
        Text(t.title, style = McType.h2, color = mc.fg)
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            t.artists.ifEmpty { listOf(t.artist) }.forEach { name ->
                Text(
                    name,
                    style = McType.bodySm,
                    color = mc.dim,
                    modifier = Modifier
                        .clickable { vm.navigate(Route.Artist(name)) }
                        .padding(horizontal = 1.dp),
                )
            }
        }
        Spacer(Modifier.height(14.dp))
        ProgressBar(
            vm.engine.position,
            if (vm.engine.duration > 0) vm.engine.duration else t.duration,
            { vm.engine.seekFraction(it) },
        )
        Spacer(Modifier.height(14.dp))
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            IconBtn(AppIcons.SkipBack, { vm.engine.prev() }, size = 44.dp)
            IconBtn(
                if (vm.engine.playing) AppIcons.Pause else AppIcons.Play,
                { vm.engine.toggle() },
                size = 52.dp,
                tint = mc.fg,
            )
            IconBtn(AppIcons.SkipForward, { vm.engine.next() }, size = 44.dp)
            Spacer(Modifier.weight(1f))
            IconBtn(
                AppIcons.Heart,
                { vm.toggleLike(t) },
                tint = if (t.liked) mc.accent else mc.dim,
            )
        }
        Spacer(Modifier.height(14.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            McButton(
                if (showLyrics) "Hide lyrics" else "Lyrics",
                { showLyrics = !showLyrics },
                small = true,
                ghost = true,
            )
            McButton(
                "Video",
                {
                    val yt = t.ytId
                    val url = if (!yt.isNullOrBlank()) {
                        "https://www.youtube.com/watch?v=$yt"
                    } else {
                        "https://www.youtube.com/results?search_query=" +
                            Uri.encode("${t.title} ${t.artist}")
                    }
                    ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                },
                small = true,
                ghost = true,
            )
        }
        if (showLyrics) {
            Spacer(Modifier.height(10.dp))
            Text(
                if (lyricText.isBlank()) "No lyrics found for this track." else lyricText,
                style = McType.bodySm,
                color = mc.dim,
            )
        }
        Spacer(Modifier.height(16.dp))
        Text(
            "Open the full player from the deck for queue and radio.",
            style = McType.bodyXs,
            color = mc.dim2,
        )
    }
}

/* ── small pieces of the player ─────────────────────────────────────────── */

/**
 * A breathing bar strip. It is decorative on purpose — one animation drives
 * every bar, so it costs almost nothing and never touches the audio thread.
 * Paused, the bars settle low instead of vanishing, which reads as "held"
 * rather than "broken".
 */
@Composable
fun Equalizer(
    playing: Boolean,
    tint: Color,
    modifier: Modifier = Modifier,
    bars: Int = 27,
    height: Dp = 22.dp,
) {
    val transition = rememberInfiniteTransition(label = "eq")
    val phase by transition.animateFloat(
        initialValue = 0f,
        targetValue = (2f * PI).toFloat(),
        animationSpec = infiniteRepeatable(tween(2400, easing = LinearEasing)),
        label = "phase",
    )
    val still = remember { List(bars) { i -> 0.22f + 0.5f * ((sin(i * 0.9f) + 1f) / 2f) } }

    Row(
        modifier.height(height),
        verticalAlignment = Alignment.Bottom,
        horizontalArrangement = Arrangement.spacedBy(3.dp),
    ) {
        repeat(bars) { i ->
            val wave = if (playing) {
                val wobble = sin(phase + i * 0.62f)
                0.16f + 0.84f * ((wobble + 1f) / 2f)
            } else {
                still[i]
            }
            Box(
                Modifier
                    .width(3.dp)
                    .fillMaxHeight(wave.coerceIn(0.1f, 1f))
                    .clip(RoundedCornerShape(2.dp))
                    .background(tint.copy(alpha = if (playing) 0.8f else 0.22f)),
            )
        }
    }
}

/** One quiet line that says what the transport is doing, so the icons alone
 *  don't have to carry it. Empty state collapses to nothing. */
@Composable
fun ModeStrip(shuffle: Boolean, repeat: String, sleepLeft: Int? = null) {
    val mc = LocalMc.current
    val labels = buildList {
        if (shuffle) add("Shuffle on")
        when (repeat) {
            "one" -> add("Repeat one")
            "all" -> add("Repeat all")
        }
        if (sleepLeft != null) add("Sleep $sleepLeft min")
    }
    if (labels.isEmpty()) return
    Row(
        Modifier.fillMaxWidth().padding(top = 10.dp),
        horizontalArrangement = Arrangement.Center,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        labels.forEachIndexed { i, label ->
            if (i > 0) {
                Text("  ·  ", style = McType.mono10, color = mc.dim2)
            }
            Text(
                label.uppercase(),
                style = McType.mono9,
                color = mc.accent.copy(alpha = 0.9f),
            )
        }
    }
}
