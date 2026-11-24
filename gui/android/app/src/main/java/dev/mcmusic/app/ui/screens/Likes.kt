package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.ArtistSummary
import dev.mcmusic.app.data.LibraryState
import dev.mcmusic.app.data.Track
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.ErrorLine
import dev.mcmusic.app.ui.GhostButton
import dev.mcmusic.app.ui.Loading
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.PrimaryButton
import dev.mcmusic.app.ui.ScreenBack
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.TrackRow
import dev.mcmusic.app.ui.visibleTracks
import dev.mcmusic.app.ui.design.LocalDesign

/**
 * The web client's /likes page: every liked track in newest-first order, with
 * one tap to play them all. Likes can change from any track row, so the shared
 * library revision refreshes this list too.
 */
@Composable
fun LikesScreen(onBack: () -> Unit, onOpenPlayer: () -> Unit) {
    val design = LocalDesign.current
    var tracks by remember { mutableStateOf<List<Track>?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var reload by remember { mutableIntStateOf(0) }
    var artist by remember { mutableStateOf<ArtistSummary?>(null) }

    LaunchedEffect(reload, LibraryState.revision) {
        Api.likes().fold(
            onSuccess = { tracks = it; error = null },
            onFailure = {
                error = it.message ?: "could not load liked songs"
                tracks = emptyList()
            },
        )
    }

    val shown = tracks.orEmpty().visibleTracks()

    LazyColumn(
        contentPadding = PaddingValues(design.screenPadding, 10.dp, design.screenPadding, 24.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        item { ScreenBack(onBack) }
        item {
            Row(
                Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                Column(Modifier.weight(1f)) {
                    ScreenTitle(
                        "Liked songs",
                        if (tracks == null) "Your saved tracks" else "${shown.size} saved · newest first",
                    )
                }
                PrimaryButton("Play all", enabled = shown.isNotEmpty()) {
                    Playback.play(shown, 0)
                    onOpenPlayer()
                }
            }
        }
        if (error != null) {
            item { ErrorLine(error!!) }
            item { GhostButton("Retry") { reload++ } }
        }
        if (tracks == null && error == null) item { Loading("Loading liked songs…") }
        if (tracks != null && shown.isEmpty() && error == null) {
            item {
                EmptyState(
                    icon = Lucide.Heart,
                    title = "Nothing liked yet",
                    body = "Tap the heart on a track, or swipe a track row right, to save it here.",
                )
            }
        }
        items(shown, key = { it.id }) { track ->
            TrackRow(
                track,
                menu = true,
                onClick = {
                    Playback.play(shown, shown.indexOf(track))
                    onOpenPlayer()
                },
                onOpenArtist = { name ->
                    artist = ArtistSummary(name, 0, 0, track.id)
                },
            )
        }
    }

    artist?.let {
        CollectionSheet(
            CollectionKind.Artist,
            it.artist,
            onDismiss = { artist = null },
            onOpenPlayer = onOpenPlayer,
        )
    }
}
