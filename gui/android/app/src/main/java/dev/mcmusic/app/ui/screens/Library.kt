package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.GridItemSpan
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.AlbumSummary
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.ArtistSummary
import dev.mcmusic.app.data.Track
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.ui.Cover
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.ErrorLine
import dev.mcmusic.app.ui.GhostButton
import dev.mcmusic.app.ui.Loading
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.MediaCard
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.TrackRow
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface

/**
 * Everything the server has, grouped the way the website groups it: albums,
 * artists and a flat track list. The library is derived from `/api/tracks`, so
 * it needs no extra endpoint and stays consistent with search results.
 */
@Composable
fun LibraryScreen(onOpenPlaylists: () -> Unit, onOpenPlayer: () -> Unit) {
    val design = LocalDesign.current
    var tab by remember { mutableIntStateOf(0) }
    var tracks by remember { mutableStateOf<List<Track>?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var album by remember { mutableStateOf<AlbumSummary?>(null) }
    var artist by remember { mutableStateOf<ArtistSummary?>(null) }
    var reload by remember { mutableIntStateOf(0) }

    LaunchedEffect(reload) {
        Api.tracks(limit = 1000).fold(
            onSuccess = { tracks = it; error = null },
            onFailure = { error = it.message ?: "could not load the library" },
        )
    }

    val all = tracks.orEmpty()
    val albums = remember(all) {
        all.groupBy { it.album.ifBlank { it.title } }
            .map { (name, list) ->
                AlbumSummary(
                    album = name,
                    artist = list.first().artist,
                    count = list.size,
                    coverId = list.firstOrNull()?.id,
                )
            }
            .sortedBy { it.album.lowercase() }
    }
    val artists = remember(all) {
        all.groupBy { it.artist.ifBlank { "Unknown artist" } }
            .map { (name, list) ->
                ArtistSummary(
                    artist = name,
                    count = list.size,
                    albums = list.map { it.album.ifBlank { it.title } }.distinct().size,
                    coverId = list.firstOrNull()?.id,
                )
            }
            .sortedBy { it.artist.lowercase() }
    }

    Column(Modifier.fillMaxSize()) {
        Column(
            Modifier.fillMaxWidth().padding(start = design.screenPadding, end = design.screenPadding, top = 10.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            ScreenTitle("Library", "${all.size} tracks · ${albums.size} albums · ${artists.size} artists")
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                listOf("Albums", "Artists", "Tracks").forEachIndexed { index, label ->
                    val selected = tab == index
                    Box(
                        Modifier
                            .clip(RoundedCornerShape(design.tileRadius))
                            .background(if (selected) design.accentSoft else Color.Transparent)
                            .clickable { tab = index }
                            .padding(horizontal = 14.dp, vertical = 9.dp),
                    ) {
                        Text(
                            label,
                            color = if (selected) design.fg else design.dim,
                            fontSize = 12.sp,
                            fontWeight = if (selected) FontWeight.SemiBold else FontWeight.Medium,
                        )
                    }
                }
                Box(Modifier.weight(1f))
                GhostButton("Playlists", onClick = onOpenPlaylists)
            }
        }

        Box(Modifier.weight(1f)) {
            when {
                error != null -> Column(Modifier.padding(design.screenPadding).fillMaxSize()) {
                    ErrorLine(error!!)
                    GhostButton("Retry", Modifier.padding(top = 8.dp), onClick = { reload++ })
                }
                tracks == null -> Loading("Loading the library…")
                else -> when (tab) {
                    0 -> LazyVerticalGrid(
                        columns = GridCells.Adaptive(minSize = 140.dp),
                        modifier = Modifier.fillMaxSize(),
                        contentPadding = PaddingValues(design.screenPadding, 12.dp, design.screenPadding, 24.dp),
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                        verticalArrangement = Arrangement.spacedBy(14.dp),
                    ) {
                        items(albums, key = { it.album }) { entry ->
                            MediaCard(
                                title = entry.album,
                                subtitle = "${entry.artist} · ${entry.count}",
                                coverUrl = albumCoverUrl(entry.coverId),
                                width = 150.dp,
                                onClick = { album = entry },
                            )
                        }
                        if (albums.isEmpty()) {
                            item(span = { GridItemSpan(maxLineSpan) }) {
                                EmptyState(
                                    icon = Lucide.Library,
                                    title = "No albums",
                                    body = "The library is empty on this server.",
                                )
                            }
                        }
                    }
                    1 -> LazyColumn(
                        modifier = Modifier.fillMaxSize(),
                        contentPadding = PaddingValues(design.screenPadding, 12.dp, design.screenPadding, 24.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        items(artists, key = { it.artist }) { entry ->
                            Row(
                                Modifier.fillMaxWidth().mcSurface()
                                    .clickable { artist = entry }
                                    .padding(12.dp),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(12.dp),
                            ) {
                                Cover(
                                    url = albumCoverUrl(entry.coverId),
                                    shape = CircleShape,
                                    modifier = Modifier.size(46.dp),
                                    fallback = design.accentSoft,
                                )
                                Column(Modifier.weight(1f)) {
                                    Text(entry.artist, color = design.fg, fontSize = 15.sp, fontWeight = FontWeight.Medium, maxLines = 1, overflow = TextOverflow.Ellipsis)
                                    Text("${entry.count} tracks · ${entry.albums} albums", color = design.dim, fontSize = 12.sp)
                                }
                            }
                        }
                    }
                    else -> LazyColumn(
                        modifier = Modifier.fillMaxSize(),
                        contentPadding = PaddingValues(design.screenPadding, 8.dp, design.screenPadding, 24.dp),
                        verticalArrangement = Arrangement.spacedBy(6.dp),
                    ) {
                        items(all, key = { it.id }) { track ->
                            TrackRow(track, onClick = {
                                Playback.play(all, all.indexOf(track))
                                onOpenPlayer()
                            })
                        }
                    }
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
