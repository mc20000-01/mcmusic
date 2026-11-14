package dev.mcmusic.app.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import dev.mcmusic.app.AppViewModel
import dev.mcmusic.app.data.Track
import dev.mcmusic.app.ui.theme.LocalMc
import dev.mcmusic.app.ui.theme.McType

/** One timed line of an LRC file. `at` is milliseconds; plain lyrics get
 *  sequential indexes and never claim a time. */
data class LyricLine(val at: Long, val text: String)

private val STAMP = Regex("""\[(\d{1,2}):(\d{2})(?:[.:](\d{1,3}))?]""")

/** LRC in, lines out. Anything without stamps is treated as plain text, which
 *  is what most of the library is anyway. */
fun parseLyrics(raw: String): List<LyricLine> {
    if (raw.isBlank()) return emptyList()
    val timed = mutableListOf<LyricLine>()
    var sawStamp = false
    raw.lineSequence().forEach { line ->
        val stamps = STAMP.findAll(line).toList()
        val words = line.replace(STAMP, "").trim()
        if (stamps.isEmpty()) {
            if (words.isNotEmpty()) timed += LyricLine(-1, words)
            return@forEach
        }
        sawStamp = true
        if (words.isEmpty()) return@forEach
        stamps.forEach { m ->
            val min = m.groupValues[1].toLongOrNull() ?: 0
            val sec = m.groupValues[2].toLongOrNull() ?: 0
            val fracRaw = m.groupValues[3]
            val frac = when (fracRaw.length) {
                0 -> 0L
                1 -> fracRaw.toLong() * 100
                2 -> fracRaw.toLong() * 10
                else -> fracRaw.take(3).toLong()
            }
            timed += LyricLine((min * 60 + sec) * 1000 + frac, words)
        }
    }
    if (!sawStamp) {
        return raw.lines().map { it.trim() }
            .filter { it.isNotEmpty() }
            .mapIndexed { i, s -> LyricLine(-1, s) }
    }
    return timed.sortedBy { it.at }
}

/** Index of the line playing at `positionSeconds`, or -1 before the first. */
fun activeLine(lines: List<LyricLine>, positionSeconds: Double): Int {
    if (lines.isEmpty() || lines.first().at < 0) return -1
    val ms = (positionSeconds * 1000).toLong()
    var lo = 0
    var hi = lines.size - 1
    var found = -1
    while (lo <= hi) {
        val mid = (lo + hi) / 2
        if (lines[mid].at <= ms) {
            found = mid
            lo = mid + 1
        } else {
            hi = mid - 1
        }
    }
    return found
}

@Composable
fun LyricsSheet(vm: AppViewModel, track: Track, onDismiss: () -> Unit) {
    val mc = LocalMc.current
    var raw by remember(track.id) { mutableStateOf<String?>(null) }
    val lines = remember(raw) { parseLyrics(raw.orEmpty()) }

    LaunchedEffect(track.id) {
        raw = vm.lyrics(track.id)
    }

    McSheet(onDismiss = onDismiss, title = "Lyrics") {
        when {
            raw == null -> {
                Column(
                    Modifier.fillMaxWidth().height(180.dp),
                    verticalArrangement = Arrangement.Center,
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    Text("Looking for the words…", style = McType.bodySm, color = mc.dim)
                }
            }
            lines.isEmpty() -> {
                Column(
                    Modifier.fillMaxWidth().height(200.dp),
                    verticalArrangement = Arrangement.Center,
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    Text("No lyrics for this one yet", style = McType.bodySm, color = mc.fg)
                    Text(
                        "It may be instrumental, or nobody has written them down.",
                        style = McType.bodyXs,
                        color = mc.dim2,
                        textAlign = TextAlign.Center,
                        modifier = Modifier.padding(top = 6.dp, start = 24.dp, end = 24.dp),
                    )
                }
            }
            else -> {
                val state = rememberLazyListState()
                val synced = lines.first().at >= 0
                val current = if (synced) activeLine(lines, vm.engine.position) else -1
                LaunchedEffect(current) {
                    if (synced && current >= 0) {
                        state.animateScrollToItem((current - 2).coerceAtLeast(0))
                    }
                }
                Box(Modifier.fillMaxWidth()) {
                    LazyColumn(
                        state = state,
                        contentPadding = PaddingValues(vertical = 120.dp),
                        verticalArrangement = Arrangement.spacedBy(14.dp),
                    ) {
                        itemsIndexed(lines) { i, line ->
                            val active = synced && i == current
                            Text(
                                line.text,
                                style = if (active) McType.h3 else McType.bodySm.copy(
                                    fontWeight = FontWeight.Normal,
                                ),
                                color = when {
                                    !synced -> mc.fg
                                    active -> mc.accent
                                    i < current -> mc.dim2
                                    else -> mc.dim
                                },
                                modifier = Modifier.fillMaxWidth(),
                            )
                        }
                    }
                    // Soft edges so lines fade instead of being chopped off.
                    Box(
                        Modifier.fillMaxWidth().height(64.dp).align(Alignment.TopCenter)
                            .background(
                                Brush.verticalGradient(listOf(mc.bg2, mc.bg2.copy(alpha = 0f))),
                            ),
                    )
                    Box(
                        Modifier.fillMaxWidth().height(64.dp).align(Alignment.BottomCenter)
                            .background(
                                Brush.verticalGradient(listOf(mc.bg2.copy(alpha = 0f), mc.bg2)),
                            ),
                    )
                }
            }
        }
    }
}
