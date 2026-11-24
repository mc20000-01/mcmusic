package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.gestures.Orientation
import androidx.compose.foundation.gestures.detectHorizontalDragGestures
import androidx.compose.foundation.gestures.draggable
import androidx.compose.foundation.gestures.rememberDraggableState
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.SwipeToDismissBox
import androidx.compose.material3.SwipeToDismissBoxValue
import androidx.compose.material3.Text
import androidx.compose.material3.rememberSwipeToDismissBoxState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.Lyrics
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.ui.Cover
import dev.mcmusic.app.ui.Danger
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.ErrorLine
import dev.mcmusic.app.ui.GhostButton
import dev.mcmusic.app.ui.IconButton
import dev.mcmusic.app.ui.Loading
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.LucideIcon
import dev.mcmusic.app.ui.Muted
import dev.mcmusic.app.ui.ScreenBack
import dev.mcmusic.app.ui.SectionLabel
import dev.mcmusic.app.ui.SwitchRow
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface
import dev.mcmusic.app.ui.formatMillis
import dev.mcmusic.app.ui.formatDuration
import dev.mcmusic.app.ui.trackCoverUrl
import dev.mcmusic.app.data.Track
import kotlinx.coroutines.delay

/**
 * Now playing, with the same queue the service is playing. The scrubber writes
 * through to ExoPlayer, and the sleep timer is Playback's own (it pauses the
 * controller when the clock runs out).
 */
@Composable
fun PlayerScreen(onBack: () -> Unit, onVideo: (String?, Long) -> Unit = { _, _ -> }) {
    val design = LocalDesign.current
    val state = Playback.state
    var scrub by remember { mutableStateOf<Float?>(null) }
    var lyricsOpen by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        while (true) {
            Playback.tick()
            delay(500)
        }
    }

    val track = state.track
    if (track == null) {
        LazyColumn(contentPadding = PaddingValues(design.screenPadding)) {
            item { ScreenBack(onBack) }
            item {
                EmptyState(
                    icon = Lucide.Play,
                    title = "Nothing playing",
                    body = "Pick a track from Home, Search or the Library and it will start here.",
                )
            }
        }
        return
    }

    val fraction = if (state.duration > 0) {
        scrub ?: (state.position.toFloat() / state.duration).coerceIn(0f, 1f)
    } else 0f

    LazyColumn(
        contentPadding = PaddingValues(design.screenPadding, 10.dp, design.screenPadding, 24.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        item { ScreenBack(onBack) }
        item {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Center) {
                Box(
                    Modifier
                        .size(264.dp)
                        .clip(RoundedCornerShape(34.dp))
                        .background(design.accentSoft)
                        .skipOnSwipe(track.id),
                    Alignment.Center,
                ) {
                    Cover(
                        url = trackCoverUrl(track.id),
                        shape = RoundedCornerShape(26.dp),
                        modifier = Modifier.size(244.dp),
                        fallback = design.accentWash,
                    )
                }
            }
        }
        item {
            Column(
                Modifier.fillMaxWidth().padding(top = 6.dp).skipOnSwipe(track.id),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(3.dp),
            ) {
                Text(
                    track.title,
                    color = design.fg,
                    fontSize = 20.sp,
                    fontWeight = FontWeight.SemiBold,
                    textAlign = TextAlign.Center,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                )
                Text(
                    "${track.artist} · ${track.album}",
                    color = design.dim,
                    fontSize = 12.sp,
                    textAlign = TextAlign.Center,
                )
                Muted("Swipe artwork to skip · swipe a queue row left to remove", size = 10)
                state.error?.let { message ->
                    Text(message, color = dev.mcmusic.app.ui.Danger, fontSize = 11.sp, textAlign = TextAlign.Center)
                }
            }
        }
        if (!lyricsOpen && track.id > 0) {
            item { NowLyric(track.id) { lyricsOpen = true } }
        }
        item {
            Slider(
                value = fraction,
                onValueChange = { scrub = it },
                onValueChangeFinished = {
                    scrub?.let { Playback.seekFraction(it) }
                    scrub = null
                },
                colors = SliderDefaults.colors(
                    thumbColor = design.accent,
                    activeTrackColor = design.accent,
                    inactiveTrackColor = design.hairline,
                ),
            )
        }
        item {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Muted(formatMillis((fraction * state.duration).toLong()), size = 11)
                Muted(formatMillis(state.duration), size = 11)
            }
        }
        item {
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                IconButton(Lucide.Shuffle, size = 20.dp, tint = if (state.shuffle) design.accent else design.dim) {
                    Playback.toggleShuffle()
                }
                IconButton(Lucide.SkipBack, size = 26.dp) { Playback.previous() }
                Box(
                    Modifier.size(58.dp).clip(CircleShape).background(design.accent).clickable { Playback.toggle() },
                    Alignment.Center,
                ) {
                    dev.mcmusic.app.ui.LucideIcon(
                        if (state.playing) Lucide.Pause else Lucide.Play,
                        design.palette.bg,
                        Modifier.size(22.dp),
                    )
                }
                IconButton(Lucide.SkipForward, size = 26.dp) { Playback.next() }
                IconButton(Lucide.Repeat, size = 20.dp, tint = if (state.repeat) design.accent else design.dim) {
                    Playback.cycleRepeat()
                }
                IconButton(
                    Lucide.ListMusic,
                    size = 20.dp,
                    tint = if (lyricsOpen) design.accent else design.dim,
                ) { lyricsOpen = !lyricsOpen }
            }
        }
        if (lyricsOpen && track.id > 0) item { LyricsPanel(track.id) }
        if (!track.ytId.isNullOrBlank()) {
            item {
                Row(
                    Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.Center,
                ) {
                    GhostButton("Watch video") { onVideo(track.ytId, state.position) }
                }
            }
        }
        item {
            Column(
                Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(8.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                ) {
                    LucideIcon(Lucide.Clock, design.dim, Modifier.size(14.dp))
                    Text(
                        when {
                            state.sleepMinutes == 0 -> "Sleep timer off"
                            state.sleepRemaining > 0 -> "Sleeping in ${((state.sleepRemaining / 60000) + 1)} min"
                            else -> "Sleep timer"
                        },
                        color = design.dim,
                        fontSize = 12.sp,
                    )
                }
                FlowRow(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.Center,
                    verticalArrangement = Arrangement.spacedBy(6.dp),
                ) {
                    listOf(0, 15, 30, 60).forEach { minutes ->
                        val selected = state.sleepMinutes == minutes
                        Box(
                            Modifier
                                .padding(horizontal = 3.dp)
                                .clip(RoundedCornerShape(50))
                                .background(if (selected) design.accent else design.accentWash)
                                .clickable { Playback.setSleep(minutes) }
                                .padding(horizontal = 14.dp, vertical = 7.dp),
                        ) {
                            Text(
                                if (minutes == 0) "Off" else "${minutes}m",
                                color = if (selected) design.palette.bg else design.dim,
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Medium,
                            )
                        }
                    }
                }
            }
        }
        item { SectionLabel("Queue") }
        if (state.queue.isEmpty()) {
            item { Muted("The queue is empty.") }
        }
        itemsIndexed(state.queue, key = { index, item -> "${item.id}@$index" }) { index, item ->
            QueueRow(index, item, state)
        }
        item {
            SwitchRow(
                title = "Autoplay",
                subtitle = "When the last song ends, add up to 5 similar tracks",
                icon = Lucide.Radio,
                checked = state.autoplay,
                onChange = { Playback.setAutoplay(it) },
            )
        }
    }
}

/** Swipe the artwork or title: right = previous song, left = next song. */
@Composable
private fun Modifier.skipOnSwipe(trackId: Int): Modifier {
    var total by remember(trackId) { mutableFloatStateOf(0f) }
    return pointerInput(trackId) {
        detectHorizontalDragGestures(
            onDragEnd = {
                if (total > 48) Playback.previous()
                else if (total < -48) Playback.next()
                total = 0f
            },
        ) { _, amount -> total += amount }
    }
}

/** One queue entry, keyed by occurrence so duplicate track ids stay visible. */
@OptIn(ExperimentalFoundationApi::class, ExperimentalMaterial3Api::class)
@Composable
private fun QueueRow(index: Int, item: Track, state: dev.mcmusic.app.playback.PlaybackState) {
    val design = LocalDesign.current
    val density = LocalDensity.current
    val rowHeight = with(density) { 56.dp.toPx() }
    var dragged by remember { mutableFloatStateOf(0f) }
    val dragState = rememberDraggableState { delta ->
        dragged += delta
        val steps = (dragged / rowHeight).toInt()
        if (steps != 0) {
            val target = (index + steps).coerceIn(0, state.queue.lastIndex)
            if (target != index) {
                Playback.move(index, target)
                dragged -= steps * rowHeight
            }
        }
    }
    val current = index == state.index
    val dismissState = rememberSwipeToDismissBoxState(
        confirmValueChange = { value ->
            if (value == SwipeToDismissBoxValue.EndToStart) {
                Playback.removeFromQueue(index)
                true
            } else false
        },
    )
    SwipeToDismissBox(
        state = dismissState,
        enableDismissFromStartToEnd = false,
        backgroundContent = {
            Row(
                Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(7.dp))
                    .background(Danger.copy(alpha = 0.16f))
                    .padding(horizontal = 14.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.End,
            ) {
                Text("Remove from queue", color = Danger, fontSize = 12.sp)
            }
        },
        content = {
    Row(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(7.dp))
            .background(if (current) design.accentSoft else design.palette.bg)
            .clickable { Playback.play(state.queue, index) }
            .padding(horizontal = 8.dp, vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(9.dp),
    ) {
        Box(Modifier.width(20.dp), Alignment.Center) {
            if (current) {
                LucideIcon(
                    Lucide.Play,
                    design.accent,
                    Modifier.size(14.dp),
                    contentDescription = "Now playing",
                )
            } else {
                Text("${index + 1}", color = design.dim, fontSize = 12.sp)
            }
        }
        Column(Modifier.weight(1f)) {
            Text(
                item.title,
                color = if (current) design.accent else design.fg,
                fontSize = 13.sp,
                fontWeight = FontWeight.Medium,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            Text(item.artist, color = design.dim, fontSize = 10.sp, maxLines = 1)
        }
        Muted(formatDuration(item.duration), size = 10)
        LucideIcon(
            Lucide.GripVertical,
            design.dim,
            Modifier.size(16.dp).draggable(
                state = dragState,
                orientation = Orientation.Vertical,
                onDragStopped = { dragged = 0f },
            ),
            contentDescription = "Drag to reorder",
        )
    }
        },
    )
}

private data class LyricLine(val time: Double, val text: String)

/** LRC timestamps plus plain text, honouring `[offset:]` and word stamps. */
private fun parseLyrics(text: String): List<LyricLine> {
    val stamps = Regex("\\[(\\d{1,2}):(\\d{2})(?:[.:](\\d{1,3}))?\\]")
    val metadata = Regex("^\\[(?:ar|ti|al|by|re|ue|length):", RegexOption.IGNORE_CASE)
    val offsetLine = Regex("^\\[offset:([+-]?\\d+)\\]", RegexOption.IGNORE_CASE)
    val inlineWords = Regex("<[^>]+>")
    var offsetMs = 0
    return buildList {
        for (raw in text.lineSequence()) {
            val line = raw.trim()
            if (line.isEmpty()) continue
            offsetLine.find(line)?.let { offsetMs = it.groupValues[1].toIntOrNull() ?: 0 }
            if (metadata.containsMatchIn(line) || offsetLine.containsMatchIn(line)) continue
            val times = mutableListOf<Double>()
            var lastEnd = 0
            for (match in stamps.findAll(line)) {
                val fraction = match.groupValues[3]
                val fractionSeconds = if (fraction.isEmpty()) 0.0 else "0.$fraction".toDouble()
                times += match.groupValues[1].toDouble() * 60 + match.groupValues[2].toDouble() + fractionSeconds
                lastEnd = match.range.last + 1
            }
            val words = inlineWords.replace(line.substring(lastEnd).trim(), "").trim()
            if (words.isEmpty()) continue
            if (times.isEmpty()) {
                add(LyricLine(-1.0, words))
            } else {
                val shift = offsetMs / 1000.0
                times.forEach { add(LyricLine((it - shift).coerceAtLeast(0.0), words)) }
            }
        }
    }.sortedBy { it.time }
}

/**
 * Lyrics panel, only composed while the Player toggle is on. The fetch is
 * keyed to the visible track (and a retry counter), so opening the panel is
 * the only thing that makes a lyrics request and switching tracks refetches.
 */
@Composable
private fun LyricsPanel(trackId: Int) {
    val design = LocalDesign.current
    var lyrics by remember(trackId) { mutableStateOf<Lyrics?>(null) }
    var error by remember(trackId) { mutableStateOf<String?>(null) }
    var loading by remember(trackId) { mutableStateOf(true) }
    var reload by remember(trackId) { mutableIntStateOf(0) }
    var visualizerMode by remember(trackId) { mutableStateOf(LyricVisualizerMode.Bars) }
    val listState = rememberLazyListState()

    LaunchedEffect(trackId, reload) {
        loading = true
        error = null
        lyrics = null
        Api.lyrics(trackId).fold(
            onSuccess = { lyrics = it; loading = false },
            onFailure = { error = it.message ?: "could not load lyrics"; loading = false },
        )
    }

    val lines = remember(lyrics?.text) { parseLyrics(lyrics?.text.orEmpty()) }
    val positionSeconds = Playback.state.position / 1000.0
    var activeIndex = -1
    for (index in lines.indices) {
        val time = lines[index].time
        if (time < 0) continue
        if (time <= positionSeconds) activeIndex = index else break
    }
    LaunchedEffect(activeIndex) {
        if (activeIndex >= 0) listState.animateScrollToItem(activeIndex)
    }

    val source = lyrics?.source.orEmpty()
    val via = when {
        source.contains("lrclib", ignoreCase = true) -> " · via LRCLIB"
        source.isNotBlank() -> " · $source"
        else -> ""
    }
    val kind = (if (lines.any { it.time >= 0 }) "Synced" else "Plain") + via

    Column(
        Modifier.fillMaxWidth().mcSurface(RoundedCornerShape(12.dp)).padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(7.dp)) {
            LucideIcon(Lucide.ListMusic, design.accent, Modifier.size(15.dp))
            Text("Lyrics", color = design.fg, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
            Box(Modifier.weight(1f))
            Muted(kind, size = 11)
        }
        LyricVisualizer(
            mode = visualizerMode,
            positionMs = Playback.state.position,
            activeLine = activeIndex,
            playing = Playback.state.playing,
            onCycle = { visualizerMode = visualizerMode.next() },
        )
        Muted("Visualizer: ${visualizerMode.label} · tap to change", size = 10)
        when {
            loading -> Loading("Loading lyrics…")
            error != null -> {
                ErrorLine(error!!)
                GhostButton("Retry") { reload++ }
            }
            lines.isEmpty() -> Muted("No lyrics found for this track yet.")
            else -> LazyColumn(
                modifier = Modifier.fillMaxWidth().heightIn(max = 280.dp),
                state = listState,
                verticalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                itemsIndexed(lines) { index, line ->
                    val active = index == activeIndex
                    Text(
                        line.text,
                        color = if (active) design.accent else design.dim,
                        fontSize = if (active) 15.sp else 13.sp,
                        fontWeight = if (active) FontWeight.SemiBold else FontWeight.Normal,
                        modifier = Modifier.clickable(enabled = line.time >= 0) {
                            Playback.seekTo((line.time * 1000).toLong())
                        },
                    )
                }
            }
        }
    }
}

/** A single live lyric line above the scrubber; tap it to open the full pane. */
@Composable
private fun NowLyric(trackId: Int, onOpen: () -> Unit) {
    val design = LocalDesign.current
    var raw by remember(trackId) { mutableStateOf<String?>(null) }
    LaunchedEffect(trackId) {
        raw = Api.lyrics(trackId).getOrNull()?.text
    }
    val lines = remember(raw) { parseLyrics(raw.orEmpty()) }
    val position = Playback.state.position / 1000.0
    val current = lines.lastOrNull { it.time >= 0 && it.time <= position }?.text
        ?: lines.firstOrNull { it.time < 0 }?.text
    if (current.isNullOrBlank()) return
    Row(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(design.accentSoft)
            .clickable(onClick = onOpen)
            .padding(horizontal = 12.dp, vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        LucideIcon(Lucide.ListMusic, design.accent, Modifier.size(14.dp))
        Text(
            current,
            color = design.accent,
            fontSize = 12.sp,
            fontWeight = FontWeight.Medium,
            maxLines = 2,
            overflow = TextOverflow.Ellipsis,
        )
    }
}
