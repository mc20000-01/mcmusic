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
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import kotlinx.coroutines.launch
import dev.mcmusic.app.data.Api
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
fun LibraryScreen() {
    val design = LocalDesign.current
    var signedIn by remember { mutableStateOf<Boolean?>(null) }
    var tracks by remember { mutableStateOf<List<Track>>(emptyList()) }
    var error by remember { mutableStateOf<String?>(null) }
    var isAdmin by remember { mutableStateOf(false) }
    var pendingDelete by remember { mutableStateOf<Track?>(null) }
    val scope = rememberCoroutineScope()
    var query by rememberSaveable { mutableStateOf("") }
    var showLogin by remember { mutableStateOf(false) }
    var reload by remember { mutableStateOf(0) }

    LaunchedEffect(reload) {
        val me = Api.me()
        signedIn = me != null
        isAdmin = me?.isAdmin == true
        if (me != null) {
            Api.tracks().fold(
                onSuccess = { tracks = it; error = null },
                onFailure = { error = it.message ?: "could not load the library" },
            )
        }
    }

    val needle = query.trim().lowercase()
    val shown = if (needle.isEmpty()) tracks else tracks.filter {
        it.title.lowercase().contains(needle) ||
            it.artist.lowercase().contains(needle) ||
            it.album.lowercase().contains(needle)
    }

    LazyColumn(
        contentPadding = PaddingValues(
            start = design.screenPadding,
            end = design.screenPadding,
            top = 12.dp,
            bottom = 124.dp,
        ),
        verticalArrangement = Arrangement.spacedBy(design.gap),
    ) {
        item {
            ScreenTitle(
                "Library",
                if (tracks.isEmpty()) "Everything you own on this server" else "${tracks.size} tracks on this server",
            )
        }

        if (signedIn == false) {
            item {
                EmptyState(
                    icon = McIcon.Library,
                    title = "Your library is behind a sign-in",
                    body = "The library endpoints are per account, so the phone needs the same session the web app uses.",
                    actionLabel = "Sign in",
                    onAction = { showLogin = true },
                )
            }
        }

        if (signedIn == true) {
            item {
                OutlinedTextField(
                    value = query,
                    onValueChange = { query = it },
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(if (design.ios) 18.dp else 20.dp),
                    placeholder = { Text("Filter your library", fontSize = 14.sp) },
                    singleLine = true,
                    textStyle = androidx.compose.ui.text.TextStyle(fontSize = 15.sp),
                    keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search),
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
            }

            error?.let { message ->
                item {
                    EmptyState(
                        icon = McIcon.Library,
                        title = "Library didn't load",
                        body = message,
                        actionLabel = "Try again",
                        onAction = { reload++ },
                    )
                }
            }

            if (tracks.isEmpty() && error == null) {
                item {
                    EmptyState(
                        icon = McIcon.Library,
                        title = "Nothing in the library",
                        body = "Add music on the web and it appears here — the phone reads the same database.",
                    )
                }
            }

            if (shown.isNotEmpty()) {
                item { SectionLabel("${shown.size} tracks") }
            }

            item {
                if (shown.isNotEmpty()) {
                    Text(
                        "Tap a track to play it",
                        color = design.dim,
                        fontSize = 11.sp,
                    )
                }
            }

            items(shown, key = { it.id }) { track ->
                TrackRow(
                    track = track,
                    canDelete = isAdmin,
                    playing = Playback.state.track?.id == track.id && Playback.state.playing,
                    downloaded = Downloads.items.any { it.id == track.id },
                    downloading = Downloads.active.contains(track.id),
                    onPlay = {
                        val index = shown.indexOfFirst { it.id == track.id }.coerceAtLeast(0)
                        Playback.play(shown, index)
                    },
                    onDownload = {
                        scope.launch {
                            Downloads.download(track).fold(
                                onSuccess = { error = null },
                                onFailure = { error = "Could not download “${track.title}”: ${it.message}" },
                            )
                        }
                    },
                    onDelete = { pendingDelete = track },
                )
            }
        }
    }

    pendingDelete?.let { track ->
        Dialog(onDismissRequest = { pendingDelete = null }) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .mcSurface(RoundedCornerShape(design.cardRadius), tint = design.palette.bg.copy(alpha = 0.35f))
                    .padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                Text("Remove track", color = design.fg, fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
                Text(
                    text = "“${track.title}” will be deleted from the server and its file removed. This cannot be undone.",
                    color = design.dim,
                    fontSize = 13.sp,
                    lineHeight = 18.sp,
                )
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Box(Modifier.weight(1f))
                    Box(
                        Modifier
                            .clip(RoundedCornerShape(50))
                            .clickable { pendingDelete = null }
                            .padding(horizontal = 14.dp, vertical = 9.dp),
                    ) {
                        Text("Cancel", color = design.dim, fontSize = 13.sp)
                    }
                    Box(
                        Modifier
                            .height(38.dp)
                            .clip(RoundedCornerShape(50))
                            .background(Color(0xFFE5484D))
                            .clickable {
                                val id = track.id
                                pendingDelete = null
                                scope.launch {
                                    Api.deleteTrack(id).fold(
                                        onSuccess = {
                                            tracks = tracks.filterNot { it.id == id }
                                            error = null
                                        },
                                        onFailure = { error = it.message ?: "could not delete the track" },
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

    LoginDialog(
        visible = showLogin,
        onDismiss = { showLogin = false },
        onSignedIn = {
            showLogin = false
            reload++
        },
    )
}

@Composable
private fun TrackRow(
    track: Track,
    canDelete: Boolean,
    playing: Boolean,
    downloaded: Boolean,
    downloading: Boolean,
    onPlay: () -> Unit,
    onDownload: () -> Unit,
    onDelete: () -> Unit,
) {
    val design = LocalDesign.current
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .mcSurface(RoundedCornerShape(design.cardRadius), tint = if (playing) design.accent.copy(alpha = 0.1f) else androidx.compose.ui.graphics.Color.Transparent)
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
                text = if (playing) "▶" else track.title.take(1).uppercase().ifBlank { "?" },
                color = design.accent,
                fontSize = if (playing) 14.sp else 17.sp,
                fontWeight = FontWeight.SemiBold,
            )
        }
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Text(
                track.title,
                color = if (playing) design.accent else design.fg,
                fontSize = 14.sp,
                fontWeight = FontWeight.Medium,
                maxLines = 1,
            )
            Text(
                text = listOf(track.artist, track.album).filter { it.isNotBlank() }.joinToString(" · "),
                color = design.dim,
                fontSize = 12.sp,
                maxLines = 1,
            )
        }
        if (track.duration > 0) {
            Text(timecode(track.duration), color = design.dim, fontSize = 11.sp)
        }
        Box(
            modifier = Modifier
                .size(30.dp)
                .clip(RoundedCornerShape(50))
                .background(if (downloaded) design.accentSoft else design.palette.line.copy(alpha = 0.25f))
                .clickable(enabled = !downloading && !downloaded) { onDownload() },
            contentAlignment = Alignment.Center,
        ) {
            Text(
                when {
                    downloading -> "…"
                    downloaded -> "✓"
                    else -> "↓"
                },
                color = if (downloaded) design.accent else design.dim,
                fontSize = 13.sp,
                fontWeight = FontWeight.SemiBold,
            )
        }
        if (canDelete) {
            Box(
                modifier = Modifier
                    .clip(RoundedCornerShape(50))
                    .background(Color(0xFFE5484D).copy(alpha = 0.14f))
                    .clickable { onDelete() }
                    .padding(horizontal = 11.dp, vertical = 6.dp),
            ) {
                Text("Remove", color = Color(0xFFE5484D), fontSize = 11.sp, fontWeight = FontWeight.SemiBold, textAlign = TextAlign.Center)
            }
        }
    }
}
