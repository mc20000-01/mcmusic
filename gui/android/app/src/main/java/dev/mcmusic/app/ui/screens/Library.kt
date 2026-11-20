package dev.mcmusic.app.ui.screens

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
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Account
import dev.mcmusic.app.data.AlbumSummary
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.Downloads
import dev.mcmusic.app.data.Track
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.ui.Cover
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.LucideIcon
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.SectionLabel
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface
import kotlinx.coroutines.launch

@Composable
fun LibraryScreen() {
    val design = LocalDesign.current
    var signedIn by remember { mutableStateOf<Boolean?>(null) }
    var tracks by remember { mutableStateOf<List<Track>>(emptyList()) }
    var loading by remember { mutableStateOf(true) }
    var error by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(Unit) {
        if (me != null) {
            loading = true
            Api.library { it ->
                loading = false
                tracks = it
                error = null
            }.onFailure { loading = false; error = it.message ?: "could not load library" }
        } else {
            loading = false
        }
        signedIn = me != null
    }

    val me = Account.me

    LazyColumn(
        contentPadding = PaddingValues(
            start = design.screenPadding,
            end = design.screenPadding,
            top = 10.dp,
            bottom = design.gap,
        ),
        verticalArrangement = androidx.compose.foundation.Arrangement.spacedBy(design.gap),
    ) {
        item {
            ScreenTitle(
                if (me != null) "Your library" else "Add music to your library",
            )
        }

        if (me != null) {
            if (loading) {
                item { Text("Loading library…", color = design.dim, fontSize = 13.sp, align = androidx.compose.ui.Alignment.CenterHorizontally) }
            }
            if (error != null) {
                EmptyState(
                    icon = dev.mcmusic.app.ui.Lucide.Library,
                    title = "Couldn't load library",
                    body = error,
                    actionLabel = "Try again",
                    onAction = { /* reload */ },
                )
            }
            if (tracks.isNotEmpty()) {
                items(tracks, key = { it.id }) { track ->
                    SongRow(track)
                }
            }
            if (tracks.isEmpty()) {
                EmptyState(
                    icon = dev.mcmusic.app.ui.Lucide.Library,
                    title = "Your library is empty",
                    body = "Add music by requesting a YouTube video or playlist, and it'll show up here once it's ready.",
                    actionLabel = "Add some music",
                    onAction = { /* nav to requests */ },
                )
            }
        } else {
            if (!me!.value) {
                item {
                    ScreenBack(onBack = { }) {
                        /* sign in */
                    }
                    Text("Sign in to access your library", color = design.dim, fontSize = 14.sp, align = androidx.compose.ui.Alignment.CenterHorizontally)
                }
            }
            item {
                EmptyState(
                    icon = dev.mcmusic.app.ui.Lucide.Search,
                    title = "Add music to get started",
                    body = "Search for tracks, paste a YouTube link, or browse playlists.",
                    actionLabel = "Add music",
                    onAction = { /* nav to requests */ },
                )
            }
        }
    }
}