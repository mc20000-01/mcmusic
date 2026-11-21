package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Account
import dev.mcmusic.app.data.Download
import dev.mcmusic.app.data.Downloads
import dev.mcmusic.app.data.Track
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.GhostButton
import dev.mcmusic.app.ui.IconButton
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.Muted
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.SectionLabel
import dev.mcmusic.app.ui.TrackCover
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.formatBytes

/**
 * Offline copies. Downloads are per device and stored by [Downloads]; playback
 * already prefers the local file, so this page only shows, plays and removes.
 */
@Composable
fun DownloadsScreen(onOpenPlayer: () -> Unit) {
    val design = LocalDesign.current
    val items = Downloads.items
    var confirmClear by remember { mutableStateOf(false) }

    fun asTrack(d: Download) = Track(d.id, d.title, d.artist, d.album, d.duration)

    LazyColumn(
        contentPadding = PaddingValues(design.screenPadding, 10.dp, design.screenPadding, 24.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        item {
            ScreenTitle(
                "Downloads",
                if (items.isEmpty()) "Nothing saved on this device yet."
                else "${items.size} tracks · ${formatBytes(Downloads.totalBytes())}",
            )
        }
        if (Account.me == null) {
            item {
                EmptyState(
                    icon = Lucide.LogIn,
                    title = "Sign in to download",
                    body = "Audio comes from the authenticated stream endpoint, so downloads need an account.",
                )
            }
        }
        if (items.isNotEmpty()) {
            item {
                SectionLabel("On this device") {
                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        GhostButton(if (confirmClear) "Really clear?" else "Clear all", danger = true) {
                            if (confirmClear) {
                                Downloads.clearAll()
                                confirmClear = false
                            } else {
                                confirmClear = true
                            }
                        }
                    }
                }
            }
            items(items, key = { it.id }) { download ->
                val track = asTrack(download)
                Row(
                    Modifier.fillMaxWidth().padding(horizontal = 4.dp, vertical = 6.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(11.dp),
                ) {
                    TrackCover(track)
                    Column(Modifier.weight(1f)) {
                        Text(track.title, color = design.fg, fontSize = 14.sp, fontWeight = FontWeight.Medium)
                        Text(
                            "${track.artist} · ${formatBytes(download.bytes)}",
                            color = design.dim, fontSize = 11.sp,
                        )
                    }
                    IconButton(Lucide.Play, tint = design.accent) {
                        Playback.play(items.map(::asTrack), items.indexOf(download))
                        onOpenPlayer()
                    }
                    IconButton(Lucide.Trash) { Downloads.remove(download.id) }
                }
            }
        } else {
            item {
                EmptyState(
                    icon = Lucide.Download,
                    title = "No downloads",
                    body = "Saved tracks play offline and show up in the mini player like any other queue.",
                )
            }
        }
        item { Muted("Downloads are not synced between devices.") }
    }
}
