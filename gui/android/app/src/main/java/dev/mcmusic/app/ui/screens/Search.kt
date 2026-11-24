package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Account
import dev.mcmusic.app.data.AlbumSummary
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.ArtistSummary
import dev.mcmusic.app.data.Listener
import dev.mcmusic.app.data.SearchResults
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.ui.Cover
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.ErrorLine
import dev.mcmusic.app.ui.Loading
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.McField
import dev.mcmusic.app.ui.Muted
import dev.mcmusic.app.ui.SectionLabel
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.TrackRow
import dev.mcmusic.app.ui.visibleTracks
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

/** Grouped search, the same three buckets `/api/search` returns to the site. */
@Composable
fun SearchScreen(onPlaylist: (Int) -> Unit, onOpenPlayer: () -> Unit) {
    val design = LocalDesign.current
    val uriHandler = LocalUriHandler.current
    var query by remember { mutableStateOf("") }
    var results by remember { mutableStateOf<SearchResults?>(null) }
    var people by remember { mutableStateOf<List<Listener>>(emptyList()) }
    var error by remember { mutableStateOf<String?>(null) }
    var searching by remember { mutableStateOf(false) }
    var album by remember { mutableStateOf<AlbumSummary?>(null) }
    var artist by remember { mutableStateOf<ArtistSummary?>(null) }
    var searchJob by remember { mutableStateOf<Job?>(null) }

    suspend fun runSearch(text: String) {
        if (text.isBlank()) {
            results = null
            people = emptyList()
            error = null
            searching = false
            return
        }
        searching = true
        // The public directory works before sign-in; the music index does not.
        Api.listening().fold(
            onSuccess = { all ->
                people = all.filter { it.username.contains(text.trim(), ignoreCase = true) }
            },
            onFailure = { people = emptyList() },
        )
        Api.now(text.trim()).fold(
            onSuccess = { exact ->
                if (exact != null && people.none { it.username.equals(exact.username, ignoreCase = true) }) {
                    people = listOf(exact) + people
                }
            },
            onFailure = {},
        )
        if (Account.me == null) {
            results = null
            searching = false
            return
        }
        Api.search(text).fold(
            onSuccess = { results = it; error = null },
            onFailure = { error = it.message ?: "search failed"; results = null },
        )
        searching = false
    }

    // Cancel the previous request so a slow earlier query cannot overwrite the
    // results of a newer one.
    LaunchedEffect(query, Account.me?.id) {
        searchJob?.cancel()
        searchJob = launch {
            delay(250)
            runSearch(query)
        }
    }

    LazyColumn(
        contentPadding = PaddingValues(start = design.screenPadding, end = design.screenPadding, top = 10.dp, bottom = 24.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        item { ScreenTitle("Search", "Tracks, albums, artists and people.") }
        item {
            McField(
                value = query,
                onValueChange = { query = it },
                label = "What do you want to hear?",
                keyboard = KeyboardOptions(imeAction = ImeAction.Search),
                actions = KeyboardActions(onSearch = { }),
            )
        }
        if (searching) item { Loading("Searching…") }
        error?.let { item { ErrorLine(it) } }

        val found = results
        if (!searching && found == null && query.isBlank()) {
            item {
                EmptyState(
                    icon = Lucide.Search,
                    title = "Find something to play",
                    body = "Search by song, album or artist. Results come from the same index the website uses.",
                )
            }
        }
        if (people.isNotEmpty()) {
            item { SectionLabel("People") }
            items(people, key = { "p-${it.username}" }) { person ->
                Row(
                    Modifier.fillMaxWidth().mcSurface(RoundedCornerShape(8.dp))
                        .clickable(enabled = person.profileUrl.isNotBlank()) {
                            runCatching { uriHandler.openUri(person.profileUrl) }
                        }
                        .padding(10.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    Cover(
                        url = person.coverUrl.ifBlank { person.profileUrl },
                        shape = CircleShape,
                        modifier = Modifier.size(40.dp),
                        fallback = design.accentSoft,
                    )
                    Column(Modifier.weight(1f)) {
                        Text(person.username, color = design.accent, fontSize = 14.sp, fontWeight = FontWeight.Medium)
                        Text(
                            person.track?.let { "${it.title} · ${it.artist}" }
                                ?: if (person.listening) "listening" else "offline",
                            color = design.dim,
                            fontSize = 11.sp,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                        )
                    }
                    dev.mcmusic.app.ui.LucideIcon(Lucide.User, design.dim, Modifier.size(16.dp))
                }
            }
        }
        if (found != null) {
            val shownTracks = found.tracks.visibleTracks()
            if (found.artists.isNotEmpty()) {
                item { SectionLabel("Artists") }
                items(found.artists, key = { "a-${it.artist}" }) { entry ->
                    Row(
                        Modifier.fillMaxWidth().mcSurface(RoundedCornerShape(8.dp))
                            .clickable { artist = entry }
                            .padding(10.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(10.dp),
                    ) {
                        Cover(
                            url = albumCoverUrl(entry.coverId),
                            shape = CircleShape,
                            modifier = Modifier.size(40.dp),
                            fallback = design.accentSoft,
                        )
                        Column(Modifier.weight(1f)) {
                            Text(entry.artist, color = design.fg, fontSize = 14.sp, fontWeight = FontWeight.Medium)
                            Text(
                                if (entry.albums > 0) "${entry.count} tracks · ${entry.albums} albums"
                                else "${entry.count} tracks",
                                color = design.dim,
                                fontSize = 11.sp,
                            )
                        }
                    }
                }
            }
            if (found.albums.isNotEmpty()) {
                item { SectionLabel("Albums") }
                items(found.albums, key = { "b-${it.album}" }) { entry ->
                    Row(
                        Modifier.fillMaxWidth().mcSurface(RoundedCornerShape(8.dp))
                            .clickable { album = entry }
                            .padding(10.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(10.dp),
                    ) {
                        Cover(
                            url = albumCoverUrl(entry.coverId),
                            shape = RoundedCornerShape(6.dp),
                            modifier = Modifier.size(40.dp),
                            fallback = design.accentSoft,
                        )
                        Column(Modifier.weight(1f)) {
                            Text(entry.album, color = design.fg, fontSize = 14.sp, fontWeight = FontWeight.Medium, maxLines = 1, overflow = TextOverflow.Ellipsis)
                            Text("${entry.artist} · ${entry.count} tracks", color = design.dim, fontSize = 11.sp, maxLines = 1)
                        }
                    }
                }
            }
            if (shownTracks.isNotEmpty()) {
                item { SectionLabel("Tracks") }
                items(shownTracks, key = { "t-${it.id}" }) { track ->
                    TrackRow(track, menu = true, onClick = {
                        Playback.play(shownTracks, shownTracks.indexOf(track))
                        onOpenPlayer()
                    })
                }
            }
            if (shownTracks.isEmpty() && found.albums.isEmpty() && found.artists.isEmpty() && people.isEmpty()) {
                item {
                    EmptyState(
                        icon = Lucide.Search,
                        title = "No matches",
                        body = "Nothing matched \"$query\". Try a shorter phrase.",
                    )
                }
            }
        }
    }

    album?.let {
        CollectionSheet(CollectionKind.Album, it.album, onDismiss = { album = null }, onOpenPlayer = onOpenPlayer)
    }
    artist?.let {
        CollectionSheet(CollectionKind.Artist, it.artist, onDismiss = { artist = null }, onOpenPlayer = onOpenPlayer)
    }
}
