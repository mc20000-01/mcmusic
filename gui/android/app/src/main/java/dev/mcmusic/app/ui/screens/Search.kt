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
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Account
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.Listener
import dev.mcmusic.app.data.SearchResults
import dev.mcmusic.app.data.Track
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.LucideIcon
import dev.mcmusic.app.ui.ScreenBack
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.SectionLabel
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

private data class Collection(val title: String, val kind: String, val tracks: List<Track>)

@Composable
fun SearchScreen() {
    val design = LocalDesign.current
    val scope = rememberCoroutineScope()
    val me = Account.me
    var query by rememberSaveable { mutableStateOf("") }
    var results by remember { mutableStateOf<SearchResults?>(null) }
    var collection by remember { mutableStateOf<Collection?>(null) }
    var directory by remember { mutableStateOf<List<Listener>>(emptyList()) }
    var profile by remember { mutableStateOf<Listener?>(null) }
    var message by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }

    suspend fun loadMusic(q: String) {
        busy = true
        Api.search(q).fold(
            onSuccess = { results = it; message = null },
            onFailure = { message = it.message ?: "search failed" },
        )
        busy = false
    }

    fun lookUp() {
        val name = query.trim()
        if (name.isEmpty() || busy) return
        scope.launch {
            busy = true
            message = null
            Api.now(name).fold(
                onSuccess = { found ->
                    profile = found
                    if (found == null) message = "\"$name\" is not on this server"
                },
                onFailure = { message = it.message ?: "could not reach the server" },
            )
            busy = false
        }
    }

    fun open(kind: String, name: String) {
        scope.launch {
            busy = true
            val result = if (kind == "album") Api.albumTracks(name) else Api.artistTracks(name)
            result.fold(
                onSuccess = { tracks ->
                    if (tracks.isEmpty()) message = "Nothing found for \"$name\"" else collection = Collection(name, kind, tracks)
                },
                onFailure = { message = it.message },
            )
            busy = false
        }
    }

    LaunchedEffect(Unit) {
        directory = Api.listening().getOrDefault(emptyList())
    }
    LaunchedEffect(me, query) {
        if (me != null && query.isNotBlank()) {
            delay(300)
            loadMusic(query.trim())
        } else {
            results = null
        }
    }

    val needle = query.trim().lowercase()
    val matches = if (needle.isEmpty()) emptyList() else directory.filter { listener ->
        listener.username.lowercase().contains(needle) ||
            listener.track?.title?.lowercase()?.contains(needle) == true ||
            listener.track?.artist?.lowercase()?.contains(needle) == true
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
        item { ScreenTitle("Search", "Tracks, albums, artists and listeners") }

        item {
            OutlinedTextField(
                value = query,
                onValueChange = {
                    query = it
                    profile = null
                    message = null
                },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(if (design.ios) 18.dp else 20.dp),
                placeholder = { Text("track, album, artist or username", fontSize = 14.sp) },
                singleLine = true,
                textStyle = androidx.compose.ui.text.TextStyle(fontSize = 15.sp),
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search),
                keyboardActions = KeyboardActions(onSearch = { if (me == null) lookUp() }),
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

        if (busy) item { Text("Looking…", color = design.dim, fontSize = 13.sp) }

        message?.let { text ->
            item {
                EmptyState(icon = Lucide.Search, title = "Nothing found", body = text)
            }
        }

        val open = collection
        if (open != null) {
            item { ScreenBack({ collection = null }, "Search") }
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    Column(Modifier.weight(1f)) {
                        Text(open.title, color = design.fg, fontSize = 22.sp, fontWeight = FontWeight.Bold)
                        Text(
                            "${open.kind} · ${open.tracks.size} track${if (open.tracks.size == 1) "" else "s"}",
                            color = design.dim,
                            fontSize = 12.sp,
                        )
                    }
                    Box(
                        Modifier
                            .clip(RoundedCornerShape(50))
                            .mcSurface(RoundedCornerShape(50), tint = design.accent)
                            .clickable { Playback.play(open.tracks, 0) }
                            .padding(horizontal = 14.dp, vertical = 8.dp),
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                            LucideIcon(Lucide.Play, design.palette.bg2, Modifier.size(13.dp))
                            Text("Play all", color = design.palette.bg2, fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                        }
                    }
                }
            }
            items(open.tracks, key = { "c-${it.id}" }) { track -> SongRow(track, open.tracks) }
        } else {
            val found = results
            if (me != null && needle.isNotEmpty() && found != null) {
                if (found.albums.isNotEmpty()) {
                    item { SectionLabel("Albums") }
                    item {
                        LazyRow(horizontalArrangement = Arrangement.spacedBy(design.gap)) {
                            items(found.albums, key = { "a-${it.album}" }) { album ->
                                AlbumTile(album) { open("album", album.album) }
                            }
                        }
                    }
                }
                if (found.artists.isNotEmpty()) {
                    item { SectionLabel("Artists") }
                    item {
                        LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            items(found.artists, key = { "r-${it.artist}" }) { artist ->
                                ArtistTile(artist) { open("artist", artist.artist) }
                            }
                        }
                    }
                }
                if (found.tracks.isNotEmpty()) {
                    item { SectionLabel("Tracks") }
                    items(found.tracks.take(40), key = { "t-${it.id}" }) { track ->
                        SongRow(track, found.tracks)
                    }
                }
                if (found.tracks.isEmpty() && found.albums.isEmpty() && found.artists.isEmpty()) {
                    item {
                        EmptyState(
                            icon = Lucide.Search,
                            title = "No music matches",
                            body = "Nothing in the library matches \"${query.trim()}\".",
                        )
                    }
                }
            }

            if (me == null && needle.isNotEmpty()) {
                item {
                    EmptyState(
                        icon = Lucide.User,
                        title = "Sign in to search the library",
                        body = "Only account holders can search tracks, albums and artists. Listener lookups work signed out.",
                        actionLabel = "Look up \"${query.trim()}\"",
                        onAction = { lookUp() },
                    )
                }
            }

            profile?.let { found ->
                item { SectionLabel("Profile") }
                item { ListenerCard(found) }
            }

            if (needle.isNotEmpty()) {
                item { SectionLabel("Active listeners") }
                if (matches.isEmpty()) {
                    item {
                        EmptyState(
                            icon = Lucide.Search,
                            title = "No one matches",
                            body = "Listener search looks at the last three minutes. Search a full username to open a profile.",
                            actionLabel = "Look up \"${query.trim()}\"",
                            onAction = { lookUp() },
                        )
                    }
                }
                items(matches, key = { it.username }) { ListenerCard(it) }
            } else if (directory.isNotEmpty()) {
                item { SectionLabel("Listening now") }
                items(directory.take(10), key = { it.username }) { ListenerCard(it) }
            }
        }
    }
}
