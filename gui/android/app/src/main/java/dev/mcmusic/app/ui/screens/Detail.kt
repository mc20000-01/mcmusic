package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.Track
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.ErrorLine
import dev.mcmusic.app.ui.Loading
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.ScreenBack
import dev.mcmusic.app.ui.TrackRow
import dev.mcmusic.app.ui.visibleTracks
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface

enum class CollectionKind { Album, Artist, Playlist }

/**
 * Album/artist/playlist contents in a sheet. The web client routes these to
 * `/set/<album>` and `/artist/<name>`; a phone-width sheet is the same page
 * without losing the list you came from.
 */
@Composable
fun CollectionSheet(
    kind: CollectionKind,
    name: String,
    onDismiss: () -> Unit,
    onOpenPlayer: () -> Unit,
) {
    val design = LocalDesign.current
    var tracks by remember(name, kind) { mutableStateOf<List<Track>?>(null) }
    var error by remember(name, kind) { mutableStateOf<String?>(null) }
    val shown = tracks.orEmpty().visibleTracks()

    LaunchedEffect(name, kind) {
        val result = when (kind) {
            CollectionKind.Album -> Api.albumTracks(name)
            CollectionKind.Artist -> Api.artistTracks(name)
            CollectionKind.Playlist -> null
        }
        result?.fold(
            onSuccess = { tracks = it },
            onFailure = { error = it.message ?: "could not load $name" },
        )
    }

    Dialog(onDismissRequest = onDismiss) {
        Column(
            Modifier
                .fillMaxWidth()
                .heightIn(max = 560.dp)
                .mcSurface(RoundedCornerShape(12.dp))
                .padding(14.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            ScreenBack(onBack = onDismiss)
            Text(name, color = design.fg, fontSize = 20.sp, fontWeight = FontWeight.SemiBold)
            Text(
                when (kind) {
                    CollectionKind.Album -> "Album"
                    CollectionKind.Artist -> "Artist"
                    CollectionKind.Playlist -> "Playlist"
                },
                color = design.dim,
                fontSize = 12.sp,
            )
            Box(Modifier.weight(1f, fill = false)) {
                when {
                    error != null -> ErrorLine(error!!)
                    tracks == null -> Loading()
                    shown.isEmpty() -> EmptyState(
                        icon = Lucide.ListMusic,
                        title = "Nothing here",
                        body = "No tracks matched this $name.",
                    )
                    else -> LazyColumn {
                        items(shown, key = { it.id }) { track ->
                            TrackRow(track, menu = true, onClick = {
                                Playback.play(shown, shown.indexOf(track))
                                onDismiss()
                                onOpenPlayer()
                            })
                        }
                    }
                }
            }
        }
    }
}
