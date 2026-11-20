package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Background
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
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
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
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.LucideIcon
import dev.mcmusic.app.ui.Pill
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface
import dev.mcmusic.app.ui.timecode
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

    fun dragRow(index: Int, x: Float) {
        if (dragIndex == null) return
        val delta = x - rowCenter(dragIndex)
        val newIndex = dragIndex + roundSign(delta / design.gap)
        dragTarget = newIndex.coerceAtLeast(0).coerceAtMost(queue.size - 1)
        dragOffset = delta
    }

    fun endDrag(x: Float) {
        if (dragIndex == null) return
        val targetX = x - (design.screenPadding + 10.dp)
        val nearest = queue?.indices?.firstOrNull { i -> i >= dragTarget - 1 && i <= dragTarget + 1 } ?: dragTarget
        Playback.reorderQueue(dragIndex, nearest)
        dragIndex = null
        dragTarget = 0
        dragOffset = 0f
    }

    // Signed helpers
    fun roundSign(x: Float): Int = if (x > 0.5f) 1 else if (x < -0.5f) -1 else 0

    // Queue — the rows you can drag
    val queue = state.queue?.mapNotNull { it } ?: emptyList()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(design.palette.bg),
    ) {
        // Header: track cover + title + time + seek bar
        Cover(
            url = "${Api.server}/api/tracks/${state.track?.id}/cover",
            shape = RoundedCornerShape(design.tileRadius),
            modifier = Modifier
                .fillMaxWidth()
                .height(200.dp),
            fallback = design.accentSoft,
        )
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp, 20.dp),
            verticalArrangement = androidx.compose.foundation.Arrangement.spacedBy(12.dp),
        ) {
            Row(horizontalAlignment = androidx.compose.foundation.alignment.Start) {
                Text(
                    state.track?.title ?: "Nothing playing",
                    color = design.fg,
                    fontSize = 24.sp,
                    fontWeight = FontWeight.ExtraBold,
                    overflow = TextOverflow.Ellipsis,
                    maxLines = 1,
                )
                Spacer(Modifier.width(8.dp))
                Text(
                    state.track?.artist ?: "unknown artist",
                    color = design.dim,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Medium,
                    overflow = TextOverflow.Ellipsis,
                    maxLines = 1,
                )
            }
            Row(horizontalAlignment = androidx.compose.foundation.alignment.Start) {
                if (state.track?.duration > 0) {
                    Text(
                        timecode(state.position),
                        color = design.dim,
                        fontSize = 12.sp,
                    )
                    Spacer(Modifier.width(4.dp))
                    Text(
                        timecode(state.duration - state.position),
                        color = design.dim,
                        fontSize = 12.sp,
                    )
                }
            }
            // Seek bar
            if (state.duration > 0) {
                Slider(
                    value = if (state.duration > 0) (state.position.toFloat() / state.duration).coerceIn(0f, 1f) else 0f,
                    onValueChange = scrub = it,
                    // thumbColor = design.accent,
                    // trackColor = design.accent,
                    colors = SliderDefaults.colors(
                        thumbColor = design.accent,
                        trackColor = design.accent.copy(alpha = 0.3f),
                    ),
                    modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp),
                )
            }
            // Queue viewer
            if (queue.isNotEmpty()) {
                SectionLabel("Queue")
                LazyColumn(
                    state = listState,
                    modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp),
                    contentPadding = androidx.compose.foundation.Arrangement.space(design.gap),
                    verticalArrangement = androidx.compose.foundation.Arrangement.spacedBy(design.gap),
                ) { index ->
                    val qtrack = queue[index]
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(if (listState.firstVisibleItemIndex <= index && index <= listState.lastVisibleItemItemIndex) design.accentSoft else Color.Transparent)
                            .clickable { Playback.play(queue, index) }
                            .padding(vertical = 6.dp, horizontal = 12.dp),
                        verticalAlignment = androidx.compose.foundation.alignment.CenterVertically,
                        horizontalArrangement = androidx.compose.foundation.Arrangement.start,
                    ) {
                        Cover(
                            url = "${Api.server}/api/tracks/${qtrack.id}/cover",
                            shape = RoundedCornerShape(8.dp),
                            modifier = Modifier.size(36.dp),
                            fallback = design.accentSoft,
                        )
                        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(1.dp)) {
                            Text(qtrack.title, color = design.fg, fontSize = 12.sp, fontWeight = FontWeight.Medium, maxLines = 1)
                            Text(
                                text = qtrack.artist.ifBlank { "unknown" },
                                color = design.dim,
                                fontSize = 10.sp,
                                maxLines = 1,
                            )
                        }
                        if (index == state.queue?.indexOfFirst { it.id == state.track?.id }) {
                            LucideIcon(Lucide.Check, design.accent, Modifier.size(14.dp))
                                .align(Alignment.End)
                        }
                    }
                }
            }
        }

        // Mini controls at bottom: prev, play/pause, next
        MiniPlayer(onOpen = { }) {
            Cover(
                url = "${Api.server}/api/tracks/${state.track?.id}/cover",
                shape = RoundedCornerShape(if (design.ios) 10.dp else 8.dp),
                modifier = Modifier.size(44.dp),
                fallback = design.accentSoft,
            )
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(1.dp)) {
                Text(
                    state.track?.title ?: "Nothing playing",
                    color = design.fg,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Medium,
                    maxLines = 1,
                )
                Text(
                    if (state.buffering) "buffering…" else state.track?.artist.ifBlank { "unknown artist" } ?: "",
                    color = design.dim,
                    fontSize = 11.sp,
                    maxLines = 1,
                )
            }
            Row(
                modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spaceBetween,
            ) {
                Box(
                    modifier = Modifier
                        .size(32.dp)
                        .clip(CircleShape)
                        .background(design.palette.bg)
                        .clickable { Playback.prev() },
                    contentAlignment = Alignment.Center,
                ) {
                    LucideIcon(Lucide.SkipBack, design.dim, Modifier.size(16.dp))
                }
                Box(
                    modifier = Modifier
                        .size(44.dp)
                        .clip(CircleShape)
                        .background(design.accent)
                        .clickable { Playback.toggle() },
                    contentAlignment = Alignment.Center,
                ) {
                    LucideIcon(
                        icon = if (state.playing) Lucide.Pause else Lucide.Play,
                        tint = design.palette.bg2,
                        modifier = Modifier.size(20.dp),
                    )
                }
                Box(
                    modifier = Modifier
                        .size(32.dp)
                        .clip(CircleShape)
                        .background(design.palette.bg)
                        .clickable { Playback.next() },
                    contentAlignment = Alignment.Center,
                ) {
                    LucideIcon(Lucide.SkipForward, design.dim, Modifier.size(16.dp))
                }
            }
        }
    }
}