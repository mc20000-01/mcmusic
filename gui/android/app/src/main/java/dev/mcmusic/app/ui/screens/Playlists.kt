package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
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
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.Playlist
import dev.mcmusic.app.data.Track
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.McIcon
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.SectionLabel
import dev.mcmusic.app.ui.Segmented
import dev.mcmusic.app.ui.ScreenBack
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface
import dev.mcmusic.app.ui.timecode
import kotlinx.coroutines.launch

/**
 * Playlists live on the server (`/api/playlists`), so the phone shows the same
 * lists as the web: open one to see its tracks, play it as a queue, remove a
 * track, rename or delete the list. Creating a list is here too; adding tracks
 * from the phone is the Library row's long-press menu.
 */
@Composable
fun PlaylistBrowser(onTracksMode: () -> Unit) {
    val design = LocalDesign.current
    val scope = rememberCoroutineScope()
    var lists by remember { mutableStateOf<List<Playlist>?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var creating by remember { mutableStateOf(false) }
    var name by remember { mutableStateOf("") }
    var open by remember { mutableStateOf<Playlist?>(null) }
    var reload by remember { mutableStateOf(0) }

    LaunchedEffect(reload) {
        Api.playlists().fold(
            onSuccess = { lists = it; error = null },
            onFailure = { error = it.message ?: "could not load playlists" },
        )
    }

    open?.let { playlist ->
        PlaylistDetail(
            playlist = playlist,
            onBack = { open = null },
            onDeleted = {
                open = null
                reload++
            },
        )
        return
    }

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
                "Library",
                when {
                    lists == null && error == null -> "Loading your playlists…"
                    else -> "${lists?.size ?: 0} playlists on this server"
                },
            )
        }
        item {
            Segmented(listOf("Tracks", "Playlists"), 1, onSelect = { if (it == 0) onTracksMode() })
        }
        item {
            Row(
                Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(16.dp))
                    .background(design.accentSoft)
                    .clickable {
                        name = ""
                        creating = true
                    }
                    .padding(horizontal = 16.dp, vertical = 12.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                Text("+", color = design.accent, fontSize = 18.sp, fontWeight = FontWeight.Bold)
                Text("New playlist", color = design.accent, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
            }
        }

        error?.let { message ->
            item {
                EmptyState(
                    icon = McIcon.Library,
                    title = "Playlists didn't load",
                    body = message,
                    actionLabel = "Try again",
                    onAction = { reload++ },
                )
            }
        }

        val current = lists
        if (current != null && current.isEmpty()) {
            item {
                EmptyState(
                    icon = McIcon.Library,
                    title = "No playlists yet",
                    body = "Create one here or on the web — both read the same lists from your account.",
                )
            }
        }
        if (current != null && current.isNotEmpty()) {
            item { SectionLabel("Your playlists") }
            items(current, key = { it.id }) { playlist ->
                PlaylistRow(playlist = playlist, onOpen = { open = playlist })
            }
        }
    }

    if (creating) {
        Dialog(onDismissRequest = { creating = false }) {
            Column(
                Modifier
                    .fillMaxWidth()
                    .mcSurface(RoundedCornerShape(design.cardRadius), tint = design.palette.bg.copy(alpha = 0.35f))
                    .padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                Text("New playlist", color = design.fg, fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
                OutlinedTextField(
                    value = name,
                    onValueChange = { name = it },
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(14.dp),
                    placeholder = { Text("Playlist name", fontSize = 14.sp) },
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(imeAction = ImeAction.Done),
                    textStyle = androidx.compose.ui.text.TextStyle(fontSize = 15.sp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = design.accent,
                        unfocusedBorderColor = design.hairline,
                        focusedTextColor = design.fg,
                        unfocusedTextColor = design.fg,
                        cursorColor = design.accent,
                        focusedPlaceholderColor = design.dim,
                        unfocusedPlaceholderColor = design.dim,
                        focusedContainerColor = design.palette.bg2.copy(alpha = 0.35f),
                        unfocusedContainerColor = design.palette.bg2.copy(alpha = 0.35f),
                    ),
                )
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                    Box(Modifier.weight(1f))
                    Text(
                        "Cancel",
                        color = design.dim,
                        fontSize = 13.sp,
                        modifier = Modifier
                            .clip(RoundedCornerShape(50))
                            .clickable { creating = false }
                            .padding(horizontal = 14.dp, vertical = 9.dp),
                    )
                    Box(
                        Modifier
                            .height(38.dp)
                            .clip(RoundedCornerShape(50))
                            .background(if (name.isBlank()) design.palette.line else design.accent)
                            .clickable(enabled = name.isNotBlank()) {
                                val trimmed = name.trim()
                                creating = false
                                scope.launch {
                                    Api.createPlaylist(trimmed).fold(
                                        onSuccess = { reload++ },
                                        onFailure = { error = it.message ?: "could not create the playlist" },
                                    )
                                }
                            }
                            .padding(horizontal = 18.dp),
                        contentAlignment = Alignment.Center,
                    ) {
                        Text("Create", color = design.palette.bg2, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
                    }
                }
            }
        }
    }
}

/** Long-press on a library track: choose one of the account's playlists. */
@Composable
fun AddToPlaylistDialog(track: Track, onDismiss: () -> Unit, onAdded: (Playlist) -> Unit) {
    val design = LocalDesign.current
    val scope = rememberCoroutineScope()
    var lists by remember { mutableStateOf<List<Playlist>?>(null) }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(track.id) {
        Api.playlists().fold(
            onSuccess = { lists = it },
            onFailure = { error = it.message ?: "could not load playlists" },
        )
    }

    Dialog(onDismissRequest = onDismiss) {
        Column(
            Modifier
                .fillMaxWidth()
                .mcSurface(RoundedCornerShape(design.cardRadius), tint = design.palette.bg.copy(alpha = 0.35f))
                .padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Text("Add to playlist", color = design.fg, fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
            Text(
                track.title,
                color = design.dim,
                fontSize = 12.sp,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            error?.let { Text(it, color = Color(0xFFE5484D), fontSize = 12.sp) }
            val available = lists
            when {
                available == null && error == null -> Text("Loading…", color = design.dim, fontSize = 13.sp)
                available != null && available.isEmpty() -> Text(
                    "You have no playlists yet. Create one in the Playlists tab first.",
                    color = design.dim,
                    fontSize = 13.sp,
                    lineHeight = 18.sp,
                )
                else -> available?.forEach { playlist ->
                    Row(
                        Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(14.dp))
                            .background(design.palette.bg2.copy(alpha = 0.35f))
                            .clickable(enabled = !busy) {
                                busy = true
                                scope.launch {
                                    Api.addToPlaylist(playlist.id, track.id).fold(
                                        onSuccess = { onAdded(playlist) },
                                        onFailure = {
                                            error = it.message ?: "could not add the track"
                                            busy = false
                                        },
                                    )
                                }
                            }
                            .padding(horizontal = 14.dp, vertical = 11.dp),
                        horizontalArrangement = Arrangement.spacedBy(10.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Text("≡", color = design.accent, fontSize = 15.sp)
                        Text(playlist.name, color = design.fg, fontSize = 13.sp, modifier = Modifier.weight(1f), maxLines = 1, overflow = TextOverflow.Ellipsis)
                        Text("${playlist.count}", color = design.dim, fontSize = 11.sp)
                    }
                }
            }
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
                Text(
                    "Close",
                    color = design.dim,
                    fontSize = 13.sp,
                    modifier = Modifier
                        .clip(RoundedCornerShape(50))
                        .clickable { onDismiss() }
                        .padding(horizontal = 14.dp, vertical = 8.dp),
                )
            }
        }
    }
}

@Composable
private fun PlaylistRow(playlist: Playlist, onOpen: () -> Unit) {
    val design = LocalDesign.current
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .mcSurface(RoundedCornerShape(design.cardRadius))
            .clickable { onOpen() }
            .padding(design.gap),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(design.gap),
    ) {
        Box(
            modifier = Modifier
                .size(46.dp)
                .clip(RoundedCornerShape(if (design.ios) 12.dp else 14.dp))
                .background(design.accentSoft),
            contentAlignment = Alignment.Center,
        ) {
            Text("≡", color = design.accent, fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
        }
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Text(playlist.name, color = design.fg, fontSize = 14.sp, fontWeight = FontWeight.Medium, maxLines = 1, overflow = TextOverflow.Ellipsis)
            Text(
                if (playlist.count == 1) "1 track" else "${playlist.count} tracks",
                color = design.dim,
                fontSize = 12.sp,
            )
        }
        Text("›", color = design.dim, fontSize = 18.sp)
    }
}

@Composable
fun PlaylistDetail(playlist: Playlist, onBack: () -> Unit, onDeleted: () -> Unit) {
    val design = LocalDesign.current
    val scope = rememberCoroutineScope()
    var tracks by remember { mutableStateOf<List<Track>?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var name by remember { mutableStateOf(playlist.name) }
    var renaming by remember { mutableStateOf(false) }
    var confirmingDelete by remember { mutableStateOf(false) }
    var reload by remember { mutableStateOf(0) }

    LaunchedEffect(reload) {
        Api.playlist(playlist.id).fold(
            onSuccess = { (serverName, list) ->
                name = serverName
                tracks = list
                error = null
            },
            onFailure = { error = it.message ?: "could not load the playlist" },
        )
    }

    LazyColumn(
        contentPadding = PaddingValues(
            start = design.screenPadding,
            end = design.screenPadding,
            top = 12.dp,
            bottom = 150.dp,
        ),
        verticalArrangement = Arrangement.spacedBy(design.gap),
    ) {
        item { ScreenBack(onBack = onBack, label = "Playlists") }
        item {
            ScreenTitle(
                name,
                when (val list = tracks) {
                    null -> "Loading…"
                    else -> if (list.isEmpty()) "Empty playlist" else "${list.size} tracks"
                },
            )
        }

        error?.let { message ->
            item {
                EmptyState(
                    icon = McIcon.Library,
                    title = "That playlist didn't load",
                    body = message,
                    actionLabel = "Try again",
                    onAction = { reload++ },
                )
            }
        }

        val list = tracks
        if (list != null && list.isNotEmpty()) {
            item {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Box(
                        Modifier
                            .weight(1f)
                            .height(42.dp)
                            .clip(RoundedCornerShape(50))
                            .background(design.accent)
                            .clickable { Playback.play(list, 0) },
                        contentAlignment = Alignment.Center,
                    ) {
                        Text("Play all", color = design.palette.bg2, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
                    }
                    Box(
                        Modifier
                            .height(42.dp)
                            .clip(RoundedCornerShape(50))
                            .background(design.palette.bg2.copy(alpha = 0.5f))
                            .clickable { Playback.play(list.shuffled(), 0) }
                            .padding(horizontal = 16.dp),
                        contentAlignment = Alignment.Center,
                    ) {
                        Text("Shuffle", color = design.fg, fontSize = 13.sp)
                    }
                }
            }
            items(list, key = { it.id }) { track ->
                PlaylistTrackRow(
                    track = track,
                    playing = Playback.state.track?.id == track.id && Playback.state.playing,
                    onPlay = {
                        Playback.play(list, list.indexOfFirst { it.id == track.id }.coerceAtLeast(0))
                    },
                    onRemove = {
                        scope.launch {
                            Api.removeFromPlaylist(playlist.id, track.id).fold(
                                onSuccess = { tracks = list.filterNot { it.id == track.id } },
                                onFailure = { error = it.message ?: "could not remove the track" },
                            )
                        }
                    },
                )
            }
        }

        item {
            SectionLabel("Playlist")
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Box(
                    Modifier
                        .weight(1f)
                        .clip(RoundedCornerShape(50))
                        .background(design.palette.bg2.copy(alpha = 0.5f))
                        .clickable { renaming = true }
                        .padding(vertical = 11.dp),
                    contentAlignment = Alignment.Center,
                ) {
                    Text("Rename", color = design.fg, fontSize = 12.sp)
                }
                Box(
                    Modifier
                        .weight(1f)
                        .clip(RoundedCornerShape(50))
                        .background(Color(0xFFE5484D).copy(alpha = 0.14f))
                        .clickable { confirmingDelete = true }
                        .padding(vertical = 11.dp),
                    contentAlignment = Alignment.Center,
                ) {
                    Text("Delete playlist", color = Color(0xFFE5484D), fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                }
            }
        }
    }

    if (renaming) {
        Dialog(onDismissRequest = { renaming = false }) {
            var draft by remember { mutableStateOf(name) }
            Column(
                Modifier
                    .fillMaxWidth()
                    .mcSurface(RoundedCornerShape(design.cardRadius), tint = design.palette.bg.copy(alpha = 0.35f))
                    .padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                Text("Rename playlist", color = design.fg, fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
                OutlinedTextField(
                    value = draft,
                    onValueChange = { draft = it },
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(14.dp),
                    singleLine = true,
                    textStyle = androidx.compose.ui.text.TextStyle(fontSize = 15.sp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = design.accent,
                        unfocusedBorderColor = design.hairline,
                        focusedTextColor = design.fg,
                        unfocusedTextColor = design.fg,
                        cursorColor = design.accent,
                        focusedContainerColor = design.palette.bg2.copy(alpha = 0.35f),
                        unfocusedContainerColor = design.palette.bg2.copy(alpha = 0.35f),
                    ),
                )
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                    Box(Modifier.weight(1f))
                    Text(
                        "Cancel",
                        color = design.dim,
                        fontSize = 13.sp,
                        modifier = Modifier
                            .clip(RoundedCornerShape(50))
                            .clickable { renaming = false }
                            .padding(horizontal = 14.dp, vertical = 9.dp),
                    )
                    Box(
                        Modifier
                            .height(38.dp)
                            .clip(RoundedCornerShape(50))
                            .background(if (draft.isBlank()) design.palette.line else design.accent)
                            .clickable(enabled = draft.isNotBlank()) {
                                val trimmed = draft.trim()
                                renaming = false
                                scope.launch {
                                    Api.renamePlaylist(playlist.id, trimmed).fold(
                                        onSuccess = { name = trimmed },
                                        onFailure = { error = it.message ?: "could not rename the playlist" },
                                    )
                                }
                            }
                            .padding(horizontal = 18.dp),
                        contentAlignment = Alignment.Center,
                    ) {
                        Text("Save", color = design.palette.bg2, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
                    }
                }
            }
        }
    }

    if (confirmingDelete) {
        Dialog(onDismissRequest = { confirmingDelete = false }) {
            Column(
                Modifier
                    .fillMaxWidth()
                    .mcSurface(RoundedCornerShape(design.cardRadius), tint = design.palette.bg.copy(alpha = 0.35f))
                    .padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                Text("Delete “$name”?", color = design.fg, fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
                Text(
                    "The playlist is removed; its tracks stay in your library.",
                    color = design.dim,
                    fontSize = 13.sp,
                    lineHeight = 18.sp,
                )
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                    Box(Modifier.weight(1f))
                    Text(
                        "Cancel",
                        color = design.dim,
                        fontSize = 13.sp,
                        modifier = Modifier
                            .clip(RoundedCornerShape(50))
                            .clickable { confirmingDelete = false }
                            .padding(horizontal = 14.dp, vertical = 9.dp),
                    )
                    Box(
                        Modifier
                            .height(38.dp)
                            .clip(RoundedCornerShape(50))
                            .background(Color(0xFFE5484D))
                            .clickable {
                                confirmingDelete = false
                                scope.launch {
                                    Api.deletePlaylist(playlist.id).fold(
                                        onSuccess = { onDeleted() },
                                        onFailure = { error = it.message ?: "could not delete the playlist" },
                                    )
                                }
                            }
                            .padding(horizontal = 18.dp),
                        contentAlignment = Alignment.Center,
                    ) {
                        Text("Delete", color = Color.White, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
                    }
                }
            }
        }
    }
}

@Composable
private fun PlaylistTrackRow(track: Track, playing: Boolean, onPlay: () -> Unit, onRemove: () -> Unit) {
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
                .size(42.dp)
                .clip(RoundedCornerShape(if (design.ios) 12.dp else 14.dp))
                .background(design.accentSoft),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                if (playing) "▶" else track.title.take(1).uppercase().ifBlank { "?" },
                color = design.accent,
                fontSize = if (playing) 13.sp else 16.sp,
                fontWeight = FontWeight.SemiBold,
            )
        }
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Text(track.title, color = if (playing) design.accent else design.fg, fontSize = 14.sp, fontWeight = FontWeight.Medium, maxLines = 1, overflow = TextOverflow.Ellipsis)
            Text(track.artist.ifBlank { "unknown artist" }, color = design.dim, fontSize = 12.sp, maxLines = 1)
        }
        if (track.duration > 0) Text(timecode(track.duration), color = design.dim, fontSize = 11.sp)
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
