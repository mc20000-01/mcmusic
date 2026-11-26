package dev.mcmusic.app.ui.screens

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
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Account
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.ArtistSummary
import dev.mcmusic.app.data.LibraryState
import dev.mcmusic.app.data.Playlist
import dev.mcmusic.app.data.Track
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.ui.Cover
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.ErrorLine
import dev.mcmusic.app.ui.GhostButton
import dev.mcmusic.app.ui.IconButton
import dev.mcmusic.app.ui.Loading
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.McField
import dev.mcmusic.app.ui.Muted
import dev.mcmusic.app.ui.PrimaryButton
import dev.mcmusic.app.ui.ScreenBack
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.SectionLabel
import dev.mcmusic.app.ui.TrackRow
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface
import kotlinx.coroutines.launch

/**
 * Playlists, the one library feature that needs an account. When [playlistId]
 * is null this is the index; otherwise it is one playlist with rename, delete
 * and remove-track controls, mirroring the web's `/playlists` pages.
 */
@Composable
fun PlaylistsScreen(playlistId: Int?, onOpenPlaylist: (Int) -> Unit, onOpenPlayer: () -> Unit, onBack: () -> Unit) {
    if (playlistId == null) {
        PlaylistIndex(onOpenPlaylist)
    } else {
        PlaylistDetail(playlistId, onOpenPlayer, onBack)
    }
}

@Composable
private fun PlaylistIndex(onOpenPlaylist: (Int) -> Unit) {
    val design = LocalDesign.current
    val scope = rememberCoroutineScope()
    var playlists by remember { mutableStateOf<List<Playlist>?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var newName by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var reload by remember { mutableIntStateOf(0) }

    LaunchedEffect(reload, LibraryState.revision) {
        Api.playlists().fold(
            onSuccess = { playlists = it; error = null },
            onFailure = { error = it.message ?: "could not load playlists"; playlists = emptyList() },
        )
    }

    LazyColumn(
        contentPadding = PaddingValues(design.screenPadding, 10.dp, design.screenPadding, 24.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        item { ScreenTitle("Playlists", "Everything you have saved, in order.") }
        if (Account.me == null) {
            item {
                EmptyState(
                    icon = Lucide.LogIn,
                    title = "Sign in for playlists",
                    body = "Playlists belong to an account. Sign in from Settings and they appear here.",
                )
            }
            return@LazyColumn
        }
        error?.let { item { ErrorLine(it) } }
        item {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Box(Modifier.weight(1f)) {
                    McField(newName, { newName = it }, "New playlist")
                }
                PrimaryButton(if (busy) "…" else "Create", enabled = newName.isNotBlank() && !busy) {
                    busy = true
                    scope.launch {
                        Api.createPlaylist(newName.trim()).fold(
                            onSuccess = { newName = ""; reload++ },
                            onFailure = { error = it.message ?: "could not create the playlist" },
                        )
                        busy = false
                    }
                }
            }
        }
        when {
            playlists == null -> item { Loading("Loading playlists…") }
            playlists!!.isEmpty() -> item {
                EmptyState(
                    icon = Lucide.ListMusic,
                    title = "No playlists yet",
                    body = "Create one above, then add tracks from any album or search result.",
                )
            }
            else -> items(playlists!!, key = { it.id }) { playlist ->
                Row(
                    Modifier.fillMaxWidth().mcSurface(RoundedCornerShape(design.cardRadius))
                        .clickable { onOpenPlaylist(playlist.id) }
                        .padding(10.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    Cover(
                        url = albumCoverUrl(playlist.coverId),
                        shape = RoundedCornerShape(20.dp),
                        modifier = Modifier.size(42.dp),
                        fallback = design.accentSoft,
                    )
                    Column(Modifier.weight(1f)) {
                        Text(playlist.name, color = design.fg, fontSize = 14.sp, fontWeight = FontWeight.Medium, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        Text("${playlist.count} tracks", color = design.dim, fontSize = 11.sp)
                    }
                    dev.mcmusic.app.ui.LucideIcon(Lucide.ChevronRight, design.dim, size = 16.dp)
                }
            }
        }
    }
}

@Composable
private fun PlaylistDetail(id: Int, onOpenPlayer: () -> Unit, onBack: () -> Unit) {
    val design = LocalDesign.current
    val scope = rememberCoroutineScope()
    var name by remember(id) { mutableStateOf("") }
    var tracks by remember(id) { mutableStateOf<List<Track>?>(null) }
    var error by remember(id) { mutableStateOf<String?>(null) }
    var renaming by remember(id) { mutableStateOf(false) }
    var draft by remember(id) { mutableStateOf("") }
    var reload by remember(id) { mutableIntStateOf(0) }
    var artist by remember(id) { mutableStateOf<ArtistSummary?>(null) }

    LaunchedEffect(id, reload, LibraryState.revision) {
        Api.playlist(id).fold(
            onSuccess = { (title, list) ->
                name = title
                tracks = list
                draft = title
                error = null
            },
            onFailure = { error = it.message ?: "could not load this playlist" },
        )
    }

    LazyColumn(
        contentPadding = PaddingValues(design.screenPadding, 10.dp, design.screenPadding, 24.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        item { ScreenBack(onBack = onBack) }
        item {
            ScreenTitle(
                name.ifBlank { "Playlist" },
                "${tracks?.size ?: 0} tracks",
            )
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                GhostButton(if (renaming) "Cancel" else "Rename", onClick = { renaming = !renaming })
                GhostButton("Delete", danger = true) {
                    scope.launch {
                        Api.deletePlaylist(id).onSuccess { tracks = emptyList(); name = "Deleted" }
                            .onFailure { error = it.message ?: "could not delete the playlist" }
                    }
                }
                if (!tracks.isNullOrEmpty()) {
                    PrimaryButton("Play all") {
                        Playback.play(tracks!!, 0)
                        onOpenPlayer()
                    }
                }
            }
        }
        if (renaming) {
            item {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Box(Modifier.weight(1f)) { McField(draft, { draft = it }, "Playlist name") }
                    PrimaryButton("Save", enabled = draft.isNotBlank()) {
                        scope.launch {
                            Api.renamePlaylist(id, draft.trim()).fold(
                                onSuccess = { name = draft.trim(); renaming = false },
                                onFailure = { error = it.message ?: "could not rename the playlist" },
                            )
                        }
                    }
                }
            }
        }
        error?.let { item { ErrorLine(it) } }
        when {
            tracks == null -> item { Loading("Loading playlist…") }
            tracks!!.isEmpty() -> item {
                EmptyState(
                    icon = Lucide.ListMusic,
                    title = "Empty playlist",
                    body = "Add tracks from an album or a search result.",
                )
            }
            else -> items(tracks!!, key = { it.id }) { track ->
                TrackRow(
                    track,
                    menu = true,
                    onClick = {
                        Playback.play(tracks!!, tracks!!.indexOf(track))
                        onOpenPlayer()
                    },
                    trailing = {
                        IconButton(Lucide.Trash) {
                            scope.launch {
                                Api.removeFromPlaylist(id, track.id).fold(
                                    onSuccess = { reload++ },
                                    onFailure = { error = it.message ?: "could not remove the track" },
                                )
                            }
                        }
                    },
                    onOpenArtist = { name ->
                        artist = ArtistSummary(name, 0, 0, track.id)
                    },
                )
            }
        }
        if (tracks != null) {
            item { Muted("Tracks can also be added from the web client; this list is the same data.", Modifier.padding(top = 6.dp)) }
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
