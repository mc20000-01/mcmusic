package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectDragGesturesAfterLongPress
import androidx.compose.foundation.gestures.scrollBy
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyListState
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.Track
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.ui.Cover
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.McIcon
import dev.mcmusic.app.ui.Pill
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface
import dev.mcmusic.app.ui.timecode
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlin.math.abs

@Composable
fun PlayerScreen() {
    val design = LocalDesign.current
    val state = Playback.state
    var scrub by remember { mutableStateOf<Float?>(null) }
    val listState = rememberLazyListState()
    val scope = rememberCoroutineScope()
    // Drag-to-sort state: which queue row is being dragged, how far, and where it would land.
    var dragIndex by remember { mutableStateOf<Int?>(null) }
    var dragOffset by remember { mutableStateOf(0f) }
    var dragTarget by remember { mutableStateOf(0) }

    fun rowCenter(index: Int): Float? {
        val info = listState.layoutInfo.visibleItemsInfo.firstOrNull { it.key == "queue-$index" } ?: return null
        return info.offset + info.size / 2f
    }

    fun startDrag(index: Int) {
        dragIndex = index
        dragTarget = index
        dragOffset = 0f
    }

    fun dragBy(index: Int, dy: Float) {
        dragOffset += dy
        val center = rowCenter(index) ?: return
        val target = listState.nearestQueueIndex(center + dragOffset) ?: index
        dragTarget = target
        // Let a long queue be dragged past the visible rows.
        val info = listState.layoutInfo.visibleItemsInfo.firstOrNull { it.key == "queue-$index" } ?: return
        val top = info.offset + dragOffset
        val edge = info.size * 1.2f
        when {
            top < listState.layoutInfo.viewportStartOffset + edge -> scope.launch { listState.scrollBy(-info.size / 2f) }
            top + info.size > listState.layoutInfo.viewportEndOffset - edge -> scope.launch { listState.scrollBy(info.size / 2f) }
        }
    }

    fun endDrag() {
        val from = dragIndex
        val to = dragTarget
        dragIndex = null
        dragOffset = 0f
        if (from != null && from != to) Playback.move(from, to)
    }

    // The controller does not push position updates; poll while this page is open.
    LaunchedEffect(state.track?.id, state.playing) {
        while (true) {
            Playback.tick()
            delay(500)
        }
    }

    val displayPosition = scrub?.let { (it * state.duration).toLong() } ?: state.position
    val fraction = if (state.duration > 0) state.position.toFloat() / state.duration else 0f

    LazyColumn(
        state = listState,
        contentPadding = PaddingValues(
            start = design.screenPadding,
            end = design.screenPadding,
            top = 12.dp,
            bottom = 150.dp,
        ),
        verticalArrangement = Arrangement.spacedBy(design.gap),
    ) {
        item { ScreenTitle("Player", "Streaming from ${Api.server.removePrefix("https://").removePrefix("http://")}") }

        state.error?.let { message ->
            item {
                Row(
                    Modifier
                        .fillMaxWidth()
                        .mcSurface(RoundedCornerShape(16.dp), tint = design.accent.copy(alpha = 0.12f))
                        .padding(14.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    Column(Modifier.weight(1f)) {
                        Text("Playback stopped", color = design.fg, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
                        Text(message, color = design.dim, fontSize = 12.sp)
                    }
                    Text(
                        "Dismiss",
                        color = design.accent,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.SemiBold,
                        modifier = Modifier.clickable { Playback.clearError() },
                    )
                }
            }
        }

        item {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .mcSurface(RoundedCornerShape(design.cardRadius), tint = design.accent.copy(alpha = 0.08f))
                    .padding(horizontal = 20.dp, vertical = 24.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(16.dp),
            ) {
                Platter(
                    trackId = state.track?.id,
                    spinning = state.playing,
                )
                Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(5.dp)) {
                    Text(
                        text = state.track?.title ?: "Nothing queued",
                        color = design.fg,
                        fontSize = 21.sp,
                        fontWeight = FontWeight.SemiBold,
                        textAlign = TextAlign.Center,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis,
                    )
                    Text(
                        text = listOfNotNull(
                            state.track?.artist?.takeIf { it.isNotBlank() },
                            state.track?.album?.takeIf { it.isNotBlank() },
                        ).joinToString(" · ").ifBlank {
                            "Pick a track in Library and it plays here"
                        },
                        color = design.dim,
                        fontSize = 13.sp,
                        textAlign = TextAlign.Center,
                    )
                }

                Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                    Slider(
                        value = if (state.duration > 0) {
                            (scrub ?: fraction).coerceIn(0f, 1f)
                        } else 0f,
                        onValueChange = { scrub = it },
                        onValueChangeFinished = {
                            scrub?.let { Playback.seekFraction(it) }
                            scrub = null
                        },
                        enabled = state.duration > 0,
                        colors = SliderDefaults.colors(
                            thumbColor = design.accent,
                            activeTrackColor = design.accent,
                            inactiveTrackColor = design.palette.line.copy(alpha = 0.5f),
                        ),
                    )
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text(timecode(displayPosition / 1000.0), color = design.dim, fontSize = 11.sp)
                        Text(
                            if (state.duration > 0) timecode(state.duration / 1000.0) else "--:--",
                            color = design.dim,
                            fontSize = 11.sp,
                        )
                    }
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceEvenly,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    TransportButton(
                        label = if (state.shuffle) "shuffle on" else "shuffle",
                        active = state.shuffle,
                        onClick = { Playback.toggleShuffle() },
                    )
                    TransportButton(label = "prev", onClick = { Playback.previous() })
                    RoundControl(
                        playing = state.playing,
                        buffering = state.buffering,
                        onClick = { Playback.toggle() },
                    )
                    TransportButton(label = "next", onClick = { Playback.next() })
                    TransportButton(
                        label = if (state.repeat) "repeat on" else "repeat",
                        active = state.repeat,
                        onClick = { Playback.cycleRepeat() },
                    )
                }

                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    if (state.track != null) {
                        Pill(if (state.playing) "playing" else "paused", state.playing)
                        Text(
                            "track ${state.index + 1} of ${state.queue.size}",
                            color = design.dim,
                            fontSize = 12.sp,
                        )
                    }
                }
            }
        }

        if (state.queue.isEmpty()) {
            item {
                EmptyState(
                    icon = McIcon.Play,
                    title = "Nothing playing yet",
                    body = "Open Library and tap a track — it streams from your server, keeps playing in the background and shows up in the notification.",
                    actionLabel = null,
                    onAction = {},
                )
            }
        } else {
            item(key = "upnext") {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Text(
                        "Up next",
                        color = design.fg,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.SemiBold,
                        modifier = Modifier.weight(1f),
                    )
                    Text(
                        if (dragIndex != null) "move to ${dragTarget + 1}" else "hold ≡ to reorder",
                        color = if (dragIndex != null) design.accent else design.dim,
                        fontSize = 11.sp,
                    )
                }
            }
            itemsIndexed(state.queue, key = { index, _ -> "queue-$index" }) { index, track ->
                val lifted = dragIndex == index
                QueueRow(
                    track = track,
                    playing = index == state.index,
                    offsetY = if (lifted) dragOffset else 0f,
                    lifted = lifted,
                    onClick = { Playback.play(state.queue, index) },
                    handle = if (state.queue.size > 1) {
                        Modifier.pointerInput(index) {
                            detectDragGesturesAfterLongPress(
                                onDragStart = { startDrag(index) },
                                onDrag = { change, amount ->
                                    change.consume()
                                    dragIndex?.let { dragBy(it, amount.y) }
                                },
                                onDragEnd = { endDrag() },
                                onDragCancel = { endDrag() },
                            )
                        }
                    } else {
                        Modifier
                    },
                )
            }
        }
    }
}

/** Queue row under the nearest visible row centre, used to pick a drop slot. */
private fun LazyListState.nearestQueueIndex(centerY: Float): Int? =
    layoutInfo.visibleItemsInfo
        .filter { (it.key as? String)?.startsWith("queue-") == true }
        .minByOrNull { abs(it.offset + it.size / 2f - centerY) }
        ?.let { (it.key as String).removePrefix("queue-").toIntOrNull() }

@Composable
private fun QueueRow(
    track: Track,
    playing: Boolean,
    offsetY: Float = 0f,
    lifted: Boolean = false,
    onClick: () -> Unit,
    handle: Modifier = Modifier,
) {
    val design = LocalDesign.current
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .graphicsLayer {
                translationY = offsetY
                scaleX = if (lifted) 1.02f else 1f
                scaleY = if (lifted) 1.02f else 1f
            }
            .clip(RoundedCornerShape(16.dp))
            .clickable { onClick() }
            .background(
                when {
                    lifted -> design.accent.copy(alpha = 0.2f)
                    playing -> design.accent.copy(alpha = 0.1f)
                    else -> design.palette.bg2.copy(alpha = 0.25f)
                },
            )
            .padding(horizontal = 14.dp, vertical = 11.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text(
            if (playing) "▶" else "${track.id}",
            color = if (playing) design.accent else design.dim,
            fontSize = if (playing) 12.sp else 10.sp,
            modifier = Modifier.size(22.dp),
            textAlign = TextAlign.Center,
        )
        Column(Modifier.weight(1f)) {
            Text(
                track.title,
                color = if (playing) design.accent else design.fg,
                fontSize = 14.sp,
                fontWeight = if (playing) FontWeight.SemiBold else FontWeight.Normal,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            Text(track.artist.ifBlank { "unknown artist" }, color = design.dim, fontSize = 11.sp, maxLines = 1)
        }
        if (track.duration > 0) {
            Text(timecode(track.duration), color = design.dim, fontSize = 11.sp)
        }
        Box(
            modifier = Modifier
                .size(34.dp)
                .clip(RoundedCornerShape(10.dp))
                .background(if (lifted) design.accent.copy(alpha = 0.22f) else design.palette.bg2.copy(alpha = 0.35f))
                .then(handle),
            contentAlignment = Alignment.Center,
        ) {
            Text("≡", color = if (lifted) design.accent else design.dim, fontSize = 14.sp)
        }
    }
}

@Composable
private fun TransportButton(label: String, active: Boolean = false, onClick: () -> Unit) {
    val design = LocalDesign.current
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(50))
            .background(if (active) design.accent.copy(alpha = 0.18f) else design.palette.bg2.copy(alpha = 0.3f))
            .clickable { onClick() }
            .padding(horizontal = 12.dp, vertical = 9.dp),
        contentAlignment = Alignment.Center,
    ) {
        Text(
            label,
            color = if (active) design.accent else design.dim,
            fontSize = 10.sp,
            fontWeight = FontWeight.Medium,
        )
    }
}

@Composable
private fun RoundControl(playing: Boolean, buffering: Boolean, onClick: () -> Unit) {
    val design = LocalDesign.current
    Box(
        modifier = Modifier
            .size(64.dp)
            .clip(CircleShape)
            .background(design.accent)
            .clickable { onClick() },
        contentAlignment = Alignment.Center,
    ) {
        Text(
            when {
                buffering -> "···"
                playing -> "❚❚"
                else -> "▶"
            },
            color = design.palette.bg2,
            fontSize = if (buffering) 18.sp else 20.sp,
            fontWeight = FontWeight.Bold,
        )
    }
}

/** A record: palette-tinted sleeve, cover as the label, grooves drawn as rings. */
@Composable
private fun Platter(trackId: Int?, spinning: Boolean) {
    val design = LocalDesign.current
    val coverUrl = trackId?.let { "${Api.server}/api/tracks/$it/cover" }.orEmpty()
    Box(
        modifier = Modifier
            .size(196.dp)
            .clip(CircleShape),
        contentAlignment = Alignment.Center,
    ) {
        Canvas(Modifier.size(196.dp)) {
            drawCircle(design.palette.bg2)
            val rings = 14
            for (i in 1..rings) {
                val r = size.minDimension / 2f * (i / (rings + 1f))
                drawCircle(
                    color = design.palette.line.copy(alpha = 0.45f),
                    radius = r,
                    style = Stroke(width = 1.dp.toPx()),
                )
            }
            drawCircle(
                color = design.accent.copy(alpha = 0.18f),
                radius = size.minDimension / 2f,
                style = Stroke(width = 2.dp.toPx()),
            )
            drawCircle(color = design.palette.bg2, radius = 6.dp.toPx(), center = center)
            drawCircle(
                color = design.dim.copy(alpha = 0.6f),
                radius = 2.dp.toPx(),
                center = Offset(center.x, center.y),
            )
        }
        Cover(
            url = coverUrl,
            shape = CircleShape,
            modifier = Modifier.size(104.dp),
            fallback = design.palette.bg2,
        )
        if (spinning) {
            Box(
                Modifier
                    .size(20.dp)
                    .clip(CircleShape)
                    .background(design.accent.copy(alpha = 0.9f)),
            )
        }
    }
}
