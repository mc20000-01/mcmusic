package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Download
import dev.mcmusic.app.data.Downloads
import dev.mcmusic.app.data.Track
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.McIcon
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.SectionLabel
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface
import dev.mcmusic.app.ui.timecode

@Composable
fun DownloadsScreen() {
    val design = LocalDesign.current
    val items = Downloads.items
    val playing = Playback.state.track?.id

    LazyColumn(
        contentPadding = PaddingValues(
            start = design.screenPadding,
            end = design.screenPadding,
            top = 12.dp,
            bottom = 150.dp,
        ),
        verticalArrangement = Arrangement.spacedBy(design.gap),
    ) {
        item {
            ScreenTitle(
                "Downloads",
                if (items.isEmpty()) "Music kept on this phone"
                else "${items.size} tracks · ${megabytes(items.sumOf { it.bytes })}",
            )
        }

        if (items.isEmpty()) {
            item {
                EmptyState(
                    icon = McIcon.Download,
                    title = "Nothing offline yet",
                    body = "Open Library and tap the arrow on a track to keep a copy here. Downloads play without the network and appear in the same player as streams.",
                )
            }
        } else {
            item { SectionLabel("On this device") }
            items(items, key = { it.id }) { entry ->
                DownloadRow(
                    entry = entry,
                    playing = playing == entry.id && Playback.state.playing,
                    onPlay = {
                        Playback.play(
                            items.map {
                                Track(it.id, it.title, it.artist, it.album, it.duration)
                            },
                            items.indexOfFirst { it.id == entry.id }.coerceAtLeast(0),
                        )
                    },
                    onRemove = { Downloads.remove(entry.id) },
                )
            }
        }
    }
}

@Composable
private fun DownloadRow(entry: Download, playing: Boolean, onPlay: () -> Unit, onRemove: () -> Unit) {
    val design = LocalDesign.current
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .mcSurface(RoundedCornerShape(design.cardRadius), tint = if (playing) design.accent.copy(alpha = 0.1f) else Color.Transparent)
            .clickable { onPlay() }
            .padding(design.gap),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(design.gap),
    ) {
        Box(
            modifier = Modifier
                .size(44.dp)
                .clip(RoundedCornerShape(if (design.ios) 12.dp else 14.dp))
                .background(design.accentSoft),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                if (playing) "▶" else entry.title.take(1).uppercase().ifBlank { "?" },
                color = design.accent,
                fontSize = if (playing) 14.sp else 17.sp,
                fontWeight = FontWeight.SemiBold,
            )
        }
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Text(
                entry.title,
                color = if (playing) design.accent else design.fg,
                fontSize = 14.sp,
                fontWeight = FontWeight.Medium,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            Text(
                listOf(entry.artist, megabytes(entry.bytes)).filter { it.isNotBlank() }.joinToString(" · "),
                color = design.dim,
                fontSize = 11.sp,
                maxLines = 1,
            )
        }
        if (entry.duration > 0) Text(timecode(entry.duration), color = design.dim, fontSize = 11.sp)
        Box(
            modifier = Modifier
                .clip(RoundedCornerShape(50))
                .background(Color(0xFFE5484D).copy(alpha = 0.14f))
                .clickable { onRemove() }
                .padding(horizontal = 10.dp, vertical = 6.dp),
        ) {
            Text("Remove", color = Color(0xFFE5484D), fontSize = 11.sp, fontWeight = FontWeight.SemiBold)
        }
    }
}

private fun megabytes(bytes: Long): String = when {
    bytes >= 1_048_576 -> "%.1f MB".format(bytes / 1_048_576.0)
    bytes > 0 -> "${bytes / 1024} KB"
    else -> ""
}
