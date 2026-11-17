package dev.mcmusic.app.ui

import android.content.Intent
import android.net.Uri
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
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
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.PagerState
import androidx.compose.foundation.pager.rememberPagerState
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
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.Alignment
import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.blur
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.layout.ContentScale
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
import dev.mcmusic.app.ui.theme.LocalGfxLevel
import dev.mcmusic.app.ui.theme.LocalMaterial
import dev.mcmusic.app.ui.theme.LocalMc
import dev.mcmusic.app.ui.theme.McType
import kotlinx.coroutines.flow.distinctUntilChanged
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

    // The whole queue is the tape, so the pager lives here: the title block
    // can follow the centred card while the finger is still previewing.
    val queue = engine.queue
    val pager = rememberPagerState(
        initialPage = engine.index.coerceIn(0, (queue.size - 1).coerceAtLeast(0)),
        pageCount = { queue.size },
    )

    Box(Modifier.fillMaxSize()) {
        PlayerBackdrop(t?.id)
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

            Spacer(Modifier.height(14.dp))
            TrackTape(vm, pager, tick)

            Spacer(Modifier.height(18.dp))
            val shown = queue.getOrNull(pager.currentPage) ?: t
            Column(Modifier.fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    shown.title,
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
                    Text(shown.artist, style = McType.bodySm, color = mc.dim)
                    if (shown.album.isNotBlank()) {
                        Text("  ·  ", style = McType.bodySm, color = mc.dim2)
                        Text(
                            shown.album,
                            style = McType.bodySm,
                            color = mc.dim2,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                            modifier = Modifier.clickable { vm.navigate(Route.Album(shown.album)) },
                        )
                    }
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
 * The whole play queue as one long horizontal tape.
 *
 * Every card — already played, playing, and still upcoming — lives on the
 * same strip, so a swipe reveals the next cover with a small 20 dp peek past
 * the current one and a long, continuous drag can travel back through the
 * history or forward to any queued track. The track only changes when the
 * pager settles on a card, which keeps the gesture a true preview: let go
 * halfway through and playback stays put.
 */
@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun TrackTape(
    vm: AppViewModel,
    pager: PagerState,
    tick: () -> Unit,
    maxArt: Dp = 300.dp,
) {
    val engine = vm.engine
    val queue = engine.queue
    if (queue.isEmpty()) return

    // Settling on a card is the commit point. Jumping to it reuses the engine's
    // own queue move, so history, autoplay and the published now-playing
    // snapshot all stay in sync.
    LaunchedEffect(pager) {
        snapshotFlow { pager.settledPage }
            .distinctUntilChanged()
            .collect { page ->
                if (page != engine.index) {
                    tick()
                    engine.jumpTo(page)
                }
            }
    }

    // One quiet tick each time the drag crosses onto another card, so the tape
    // feels detented without interrupting the finger.
    LaunchedEffect(pager) {
        snapshotFlow { pager.currentPage }
            .distinctUntilChanged()
            .collect { page -> if (page != engine.index) tick() }
    }

    // Keep the tape centred when the track changes from a button, autoplay or
    // the lock screen rather than from a swipe.
    LaunchedEffect(engine.index, queue.size) {
        if (engine.index in queue.indices && pager.currentPage != engine.index) {
            pager.animateScrollToPage(engine.index)
        }
    }

    BoxWithConstraints(Modifier.fillMaxWidth()) {
        // Leave room for the neighbours: half the leftover space on each side,
        // minus the 20 dp gap, is the sliver of the next cover that peeks in.
        val artSize = minOf(maxWidth - 84.dp, maxArt)
        val side = (maxWidth - artSize) / 2
        HorizontalPager(
            state = pager,
            contentPadding = PaddingValues(horizontal = side),
            pageSpacing = 20.dp,
            modifier = Modifier.fillMaxWidth(),
        ) { page ->
            val track = queue.getOrNull(page) ?: return@HorizontalPager
            val centered = page == pager.currentPage
            Art(
                track.id,
                artSize,
                modifier = Modifier
                    .graphicsLayer {
                        // The centred card is the one being previewed, so it
                        // stays bright even before the swipe commits; the rest
                        // of the tape sits back.
                        alpha = if (centered) 1f else 0.48f
                        val s = if (centered) 1f else 0.93f
                        scaleX = s
                        scaleY = s
                    }
                    .clip(RoundedCornerShape(D.r3))
                    .combinedClickable(
                        onClick = {
                            if (page != engine.index) {
                                tick()
                                engine.jumpTo(page)
                            }
                        },
                        onLongClickLabel = "Track options",
                        onLongClick = { tick(); vm.openTrackMenu(track) },
                    ),
            )
        }
    }
}

private data class BackdropStyle(
    val blur: Dp,
    val artAlpha: Float,
    val topScrim: Float,
    val bottomScrim: Float,
    val wash: Float,
)

/**
 * A full-screen backdrop built from the current artwork.
 *
 * The art is blurred and pushed well back, then each material gets its own
 * finish: glass gets a soft accent bloom, metal a diagonal sheen, plane and
 * solid stay quiet and flat so the type carries the screen. Low graphics
 * levels skip the blur entirely instead of dropping frames on old hardware.
 */
@Composable
private fun PlayerBackdrop(trackId: Int?) {
    val mc = LocalMc.current
    val material = LocalMaterial.current
    val gfx = LocalGfxLevel.current
    val art = rememberArt(trackId)

    val style = when (material) {
        "plane" -> BackdropStyle(72.dp, 0.20f, 0.74f, 0.99f, 0.10f)
        "solid" -> BackdropStyle(52.dp, 0.14f, 0.80f, 0.99f, 0.07f)
        "metal" -> BackdropStyle(38.dp, 0.40f, 0.62f, 0.97f, 0.14f)
        else -> BackdropStyle(30.dp, 0.46f, 0.66f, 0.96f, 0.20f) // glass
    }

    Box(Modifier.fillMaxSize().background(mc.bg)) {
        if (art != null) {
            Image(
                art,
                contentDescription = null,
                contentScale = ContentScale.Crop,
                modifier = Modifier
                    .fillMaxSize()
                    .graphicsLayer {
                        // A little overscan hides the softened edge a blur
                        // leaves behind.
                        scaleX = 1.18f
                        scaleY = 1.18f
                    }
                    .then(if (gfx >= 2) Modifier.blur(style.blur) else Modifier)
                    .alpha(style.artAlpha),
            )
        }

        Box(
            Modifier.fillMaxSize().background(
                when (material) {
                    "metal" -> Brush.linearGradient(
                        listOf(
                            mc.fg.copy(alpha = 0.10f),
                            Color.Transparent,
                            mc.fg.copy(alpha = 0.05f),
                        ),
                    )

                    "plane", "solid" -> Brush.verticalGradient(
                        listOf(
                            mc.accent.copy(alpha = style.wash),
                            Color.Transparent,
                            mc.bg.copy(alpha = 0.22f),
                        ),
                    )

                    else -> Brush.verticalGradient(
                        listOf(
                            mc.glassHighlight.copy(alpha = 0.10f),
                            mc.accent.copy(alpha = style.wash),
                            Color.Transparent,
                        ),
                    )
                },
            ),
        )

        Box(
            Modifier.fillMaxSize().background(
                Brush.verticalGradient(
                    listOf(
                        mc.bg.copy(alpha = style.topScrim),
                        mc.bg.copy(alpha = (style.topScrim + style.bottomScrim) / 2f),
                        mc.bg.copy(alpha = style.bottomScrim),
                    ),
                ),
            ),
        )
    }
}

/**
 * The same player rendered as a routed screen (used by deep links from the deck
 * when the user navigates to the "now" view).
 */
@OptIn(ExperimentalFoundationApi::class)
@Composable
fun NowPlayingScreen(vm: AppViewModel) {
    val mc = LocalMc.current
    val queue = vm.engine.queue
    val pager = rememberPagerState(
        initialPage = vm.engine.index.coerceIn(0, (queue.size - 1).coerceAtLeast(0)),
        pageCount = { queue.size },
    )
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
        TrackTape(vm, pager, tick = {}, maxArt = 260.dp)
        Spacer(Modifier.height(16.dp))
        val shown = queue.getOrNull(pager.currentPage) ?: t
        Text(shown.title, style = McType.h2, color = mc.fg)
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            shown.artists.ifEmpty { listOf(shown.artist) }.forEach { name ->
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
