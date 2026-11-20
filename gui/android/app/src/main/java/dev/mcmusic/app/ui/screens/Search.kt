package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.Background
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.clickable
import androidx.compose.foundation.combinedClickable
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
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.PasswordFieldValue
import androidx.compose.ui.text.style.TextAlign
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
import dev.mcmusic.app.ui.timecode
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
            loadMusic(name)
        }
    }

    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = androidx.compose.foundation.Arrangement.spacedBy(12.dp),
    ) {
        SearchBar(query = query, onChange = { query = it }, onSubmit = { lookUp() })
        if (busy) {
            item { CircularProgressIndicator(modifier = Modifier.align(Alignment.CenterHorizontal)) }
        }
        if (message != null) {
            item { Text(message, color = design.dim, fontSize = 13.sp, align = androidx.compose.ui.Alignment.CenterHorizontally) }
        }
        if (results != null && results.tracks.isNotEmpty()) {
            SectionLabel("Search results")
            items(results.tracks, key = { it.id }) { track ->
                SongRow(track)
            }
        }
        if (results != null && results.albums.isNotEmpty()) {
            SectionLabel("Albums")
            items(results.albums, key = { it.album }) { album ->
                AlbumTile(album) {
                    scope.launch {
                        Api.albumTracks(album.album).onSuccess { tracks ->
                            if (tracks.isNotEmpty()) Playback.play(tracks, 0)
                        }
                    }
                }
            }
        }
        if (results != null && results.artists.isNotEmpty()) {
            SectionLabel("Artists")
            items(results.artists, key = { it.id }) { artist ->
                ArtistTile(artist) {
                    scope.launch {
                        Api.artistTracks(artist.id).onSuccess { tracks ->
                            if (tracks.isNotEmpty()) Playback.play(tracks, 0)
                        }
                    }
                }
            }
        }
        if (results == null || results.tracks.isEmpty()) {
            EmptyState(
                icon = dev.mcmusic.app.ui.Lucide.Search,
                title = "Nothing found",
                body = "Try a different search term or check your spelling.",
                actionLabel = "Search again",
                onAction = { reload++ },
            )
        }
    }
}

@Composable
fun SearchBar(
    query: String,
    onChange: (String) -> Unit,
    onSubmit: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val design = LocalDesign.current
    OutlinedTextField(
        value = query,
        onValueChange = onChange,
        keyboardOptions = KeyboardOptions(
            imeAction = ImeAction.search,
            keyboardType = KeyboardType.text,
        ),
        keyboardActions = KeyboardActions.onSearch { onSubmit },
        placeholder = { Text("Search for songs, albums, or artists", color = design.dim, fontSize = 13.sp) },
        modifier = modifier
            .fillMaxWidth()
            .mcSurface(RoundedCornerShape(16.dp))
            .padding(16.dp),
        textStyle = design.fg.copy(alpha = 0.9f),
        dividerColor = design.line,
        label = { Text("Search", color = design.dim) },
        trailingIcon = {
            if (query.isNotEmpty()) {
                Icon(
                    painter = androidx.compose.ui.graphics.painterResource(
                        dev.mcmusic.app.R.drawable.ic_lucide_close
                    ),
                    tint = design.dim,
                    modifier = Modifier.size(18.dp),
                    contentDescription = null,
                    onClick = { query = ""; onChange("") },
                )
            } else {
                Modifier.empty
            }
        },
    )
}

/** A library row used by the home feed, search results and collection pages. */
@Composable
fun SongRow(track: Track, modifier: Modifier = Modifier) {
    val design = LocalDesign.current
    Row(
        modifier = modifier
            .fillMaxWidth()
            .mcSurface(RoundedCornerShape(design.cardRadius))
            .clickable { Playback.play(Track.empty().copy(id = track.id, title = track.title, artist = track.artist), 0) }
            .padding(10.dp),
        verticalAlignment = androidx.compose.foundation.alignment.CenterVertically,
        horizontalArrangement = androidx.compose.foundation.Arrangement.spacedBy(10.dp),
    ) {
        Cover(
            url = "${Api.server}/api/tracks/${track.id}/cover",
            shape = RoundedCornerShape(10.dp),
            modifier = Modifier.size(42.dp),
            fallback = design.accentSoft,
        )
        Column(Modifier.weight(1f), verticalArrangement = androidx.compose.foundation.Arrangement.spacedBy(2.dp)) {
            Text(track.title, color = design.fg, fontSize = 14.sp, fontWeight = FontWeight.Medium, maxLines = 1)
            Text(
                text = listOf(track.artist, track.album).filter { it.isNotBlank() }.joinToString(" · "),
                color = design.dim,
                fontSize = 11.sp,
                maxLines = 1,
            )
        }
        if (track.duration > 0) {
            Text(timecode(track.duration), color = design.dim, fontSize = 11.sp)
        }
        LucideIcon(dev.mcmusic.app.ui.Lucide.Play, design.accent, Modifier.size(16.dp))
    }
}