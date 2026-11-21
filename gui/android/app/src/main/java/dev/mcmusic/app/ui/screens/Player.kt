package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.ui.Cover
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.IconButton
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.Muted
import dev.mcmusic.app.ui.ScreenBack
import dev.mcmusic.app.ui.SectionLabel
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.formatMillis
import dev.mcmusic.app.ui.formatDuration
import dev.mcmusic.app.ui.trackCoverUrl
import kotlinx.coroutines.delay

/**
 * Now playing, with the same queue the service is playing. The scrubber writes
 * through to ExoPlayer, and the sleep timer is Playback's own (it pauses the
 * controller when the clock runs out).
 */
@Composable
fun PlayerScreen(onBack: () -> Unit) {
    val design = LocalDesign.current
    val state = Playback.state
    var scrub by remember { mutableStateOf<Float?>(null) }

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
                Cover(
                    url = trackCoverUrl(track.id),
                    shape = RoundedCornerShape(10.dp),
                    modifier = Modifier.size(248.dp),
                    fallback = design.accentSoft,
                )
            }
        }
        item {
            Column(
                Modifier.fillMaxWidth().padding(top = 6.dp),
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
                if (state.error != null) {
                    Text(state.error!!, color = dev.mcmusic.app.ui.Danger, fontSize = 11.sp, textAlign = TextAlign.Center)
                }
            }
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
            }
        }
        item {
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    when {
                        state.sleepMinutes == 0 -> "Sleep timer off"
                        state.sleepRemaining > 0 -> "Sleeping in ${((state.sleepRemaining / 60000) + 1)} min"
                        else -> "Sleep timer"
                    },
                    color = design.dim,
                    fontSize = 11.sp,
                )
                Spacer(Modifier.width(8.dp))
                listOf(0, 15, 30, 60).forEach { minutes ->
                    val selected = state.sleepMinutes == minutes
                    Box(
                        Modifier
                            .padding(horizontal = 2.dp)
                            .clip(RoundedCornerShape(6.dp))
                            .background(if (selected) design.accentSoft else design.palette.bg2)
                            .clickable { Playback.setSleep(minutes) }
                            .padding(horizontal = 8.dp, vertical = 5.dp),
                    ) {
                        Text(
                            if (minutes == 0) "Off" else "${minutes}m",
                            color = if (selected) design.accent else design.dim,
                            fontSize = 10.sp,
                        )
                    }
                }
            }
        }
        item { SectionLabel("Queue") }
        if (state.queue.isEmpty()) {
            item { Muted("The queue is empty.") }
        }
        items(state.queue, key = { it.id }) { item ->
            val current = item.id == track.id
            Row(
                Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(7.dp))
                    .background(if (current) design.accentSoft else design.palette.bg)
                    .clickable { Playback.play(state.queue, state.queue.indexOf(item)) }
                    .padding(horizontal = 8.dp, vertical = 8.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(9.dp),
            ) {
                Text(
                    if (current) "▶" else "${state.queue.indexOf(item) + 1}",
                    color = if (current) design.accent else design.dim,
                    fontSize = 11.sp,
                    modifier = Modifier.width(18.dp),
                )
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
            }
        }
    }
}
