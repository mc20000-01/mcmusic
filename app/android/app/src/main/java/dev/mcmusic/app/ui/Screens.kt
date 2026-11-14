@file:OptIn(androidx.compose.foundation.ExperimentalFoundationApi::class)

package dev.mcmusic.app.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import dev.mcmusic.app.AppViewModel
import dev.mcmusic.app.Route
import dev.mcmusic.app.data.AlbumRef
import dev.mcmusic.app.data.Track
import dev.mcmusic.app.ui.theme.D
import dev.mcmusic.app.ui.theme.LocalMc
import dev.mcmusic.app.ui.theme.McType
import java.util.Calendar

@Composable
fun Loading() {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        CircularProgressIndicator(
            Modifier.size(20.dp),
            color = LocalMc.current.accent,
            strokeWidth = 2.dp,
        )
    }
}

/* ── home ───────────────────────────────────────────────────────────────── */

@Composable
fun HomeScreen(vm: AppViewModel) {
    val mc = LocalMc.current
    val home = vm.home
    if (home == null) {
        Loading()
        return
    }
    if (home.sections.isEmpty() && home.albums.isEmpty()) {
        EmptyState(
            "Your library is empty",
            "Request a YouTube playlist and the tracks will land here.",
            icon = AppIcons.Library,
            actionLabel = "Request music",
            onAction = { vm.navigate(Route.Requests) },
        )
        return
    }

    val hour = remember { Calendar.getInstance().get(Calendar.HOUR_OF_DAY) }
    val greeting = when {
        hour < 5 -> "Still awake"
        hour < 12 -> "Good morning"
        hour < 18 -> "Good afternoon"
        else -> "Good evening"
    }

    val allTracks = remember(home) {
        val seen = LinkedHashMap<Int, Track>()
        home.sections.forEach { section -> section.tracks.forEach { seen[it.id] = it } }
        seen.values.toList()
    }
    val shelf = buildString {
        append(allTracks.size)
        append(if (allTracks.size == 1) " track" else " tracks")
        if (home.albums.isNotEmpty()) {
            append(" · ")
            append(home.albums.size)
            append(if (home.albums.size == 1) " album" else " albums")
        }
        append(" on your shelf.")
    }

    LazyColumn(
        Modifier.fillMaxSize(),
        contentPadding = PaddingValues(start = D.gutter, end = D.gutter, top = 10.dp, bottom = 24.dp),
    ) {
        item {
            Row(
                Modifier
                    .fillMaxWidth()
                    .padding(bottom = 18.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                verticalAlignment = Alignment.Bottom,
            ) {
                Column(Modifier.weight(1f)) {
                    Text(
                        "$greeting, ${vm.me?.username ?: "listener"}",
                        style = McType.h1Small,
                        color = mc.fg,
                    )
                    Text(
                        shelf,
                        style = McType.bodyXs,
                        color = mc.dim2,
                        modifier = Modifier.padding(top = 3.dp),
                    )
                }
                if (allTracks.isNotEmpty()) {
                    McButton(
                        "Shuffle",
                        { vm.shufflePlay(allTracks) },
                        small = true,
                        ghost = true,
                        leading = AppIcons.Shuffle,
                    )
                }
            }
        }

        val picks = home.sections.firstOrNull { it.tracks.isNotEmpty() }?.tracks?.take(6).orEmpty()
        if (picks.isNotEmpty()) {
            item {
                Text(
                    "JUMP BACK IN",
                    style = McType.mono9,
                    color = mc.dim2,
                    modifier = Modifier.padding(bottom = 8.dp),
                )
                QuickPicks(vm, picks)
                Spacer(Modifier.height(22.dp))
            }
        }

        home.sections.forEach { section ->
            val list = if (vm.settings.hideExplicit) {
                section.tracks.filter { !it.explicit }
            } else {
                section.tracks
            }
            if (list.isEmpty()) return@forEach
            item(key = "section-${section.title}") {
                Shelf(section.title, meta = "${list.size}") {
                    LazyRow(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        items(list, key = { "${section.title}-${it.id}" }) { track ->
                            Tile(
                                title = track.title,
                                subtitle = track.artist,
                                coverId = track.id,
                                onClick = { vm.playList(list, list.indexOf(track)) },
                                onPlay = { vm.playList(list, list.indexOf(track)) },
                                onLongPress = { vm.openTrackMenu(track) },
                            )
                        }
                    }
                }
            }
        }

        if (home.albums.isNotEmpty()) {
            item {
                Shelf("Recent albums") {
                    LazyRow(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        items(home.albums, key = { it.album }) { album ->
                            AlbumTile(
                                album,
                                onClick = { vm.navigate(Route.Album(album.album)) },
                                onPlay = { vm.playAlbum(album.album) },
                                onLongPress = {
                                    vm.openCollectionMenu("album", album.album, album.artist, album.coverId)
                                },
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun QuickPicks(vm: AppViewModel, picks: List<Track>) {
    val mc = LocalMc.current
    val haptics = LocalHapticFeedback.current
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        picks.forEach { track ->
            Row(
                Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(D.r2))
                    .background(mc.glass)
                    .border(1.dp, mc.glassBorder, RoundedCornerShape(D.r2))
                    .combinedClickable(
                        onClick = { vm.playList(picks, picks.indexOf(track)) },
                        onLongClickLabel = "Track options",
                        onLongClick = {
                            haptics.performHapticFeedback(HapticFeedbackType.LongPress)
                            vm.openTrackMenu(track)
                        },
                    )
                    .padding(7.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(9.dp),
            ) {
                Art(track.id, 36.dp)
                Column(Modifier.weight(1f)) {
                    Text(
                        track.title,
                        style = McType.bodySm.copy(fontWeight = androidx.compose.ui.text.font.FontWeight.Medium),
                        color = mc.fg,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                    Text(
                        track.artist,
                        style = McType.mono9,
                        color = mc.dim,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                }
                Icon(AppIcons.Play, null, Modifier.size(16.dp), tint = mc.accent)
            }
        }
    }
}

/* ── search ─────────────────────────────────────────────────────────────── */

@Composable
fun SearchScreen(vm: AppViewModel) {
    val mc = LocalMc.current
    val data = vm.searchData

    when {
        vm.searchQuery.isBlank() -> EmptyState(
            "Search your library",
            "Songs, albums and artists.",
            icon = AppIcons.Search,
        )
        data == null -> Loading()
        data.tracks.isEmpty() && data.albums.isEmpty() && data.artists.isEmpty() -> EmptyState(
            "Nothing found",
            "No results for \"${vm.searchQuery}\".",
            icon = AppIcons.Search,
        )
        else -> {
            val tracks = if (vm.settings.hideExplicit) data.tracks.filter { !it.explicit } else data.tracks
            LazyColumn(
                Modifier.fillMaxSize(),
                contentPadding = PaddingValues(start = D.gutter, end = D.gutter, top = 8.dp, bottom = 24.dp),
            ) {
                if (data.artists.isNotEmpty()) {
                    item {
                        Shelf("Artists") {
                            LazyRow(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                                items(data.artists, key = { it.artist }) { artist ->
                                    ArtistTile(
                                        artist,
                                        onClick = { vm.navigate(Route.Artist(artist.artist)) },
                                        onPlay = { vm.playArtist(artist.artist) },
                                        onLongPress = {
                                            vm.openCollectionMenu("artist", artist.artist, "${artist.n} tracks", artist.coverId)
                                        },
                                    )
                                }
                            }
                        }
                    }
                }
                if (data.albums.isNotEmpty()) {
                    item {
                        Shelf("Albums") {
                            LazyRow(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                                items(data.albums, key = { it.album }) { album ->
                                    AlbumTile(
                                        album,
                                        onClick = { vm.navigate(Route.Album(album.album)) },
                                        onPlay = { vm.playAlbum(album.album) },
                                        onLongPress = {
                                            vm.openCollectionMenu("album", album.album, album.artist, album.coverId)
                                        },
                                    )
                                }
                            }
                        }
                    }
                }
                if (tracks.isNotEmpty()) {
                    item {
                        Text(
                            "Songs",
                            style = McType.h3,
                            color = mc.fg,
                            modifier = Modifier.padding(bottom = 8.dp),
                        )
                    }
                    itemsIndexed(tracks, key = { _, t -> t.id }) { index, track ->
                        TrackRow(
                            track = track,
                            number = index,
                            isCurrent = track.id == vm.engine.current?.id,
                            onClick = { vm.playList(tracks, index) },
                            onLike = { vm.toggleLike(track) },
                            onMore = { vm.openTrackMenu(track) },
                        )
                    }
                }
            }
        }
    }
}

/* ── library ────────────────────────────────────────────────────────────── */

@Composable
fun LibraryScreen(vm: AppViewModel) {
    val mc = LocalMc.current
    Column(Modifier.fillMaxSize()) {
        Column(Modifier.padding(horizontal = D.gutter)) {
            Row(
                Modifier.fillMaxWidth().padding(bottom = 12.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text("Your library", style = McType.h1Small, color = mc.fg)
                Spacer(Modifier.weight(1f))
                IconBtn(AppIcons.Refresh, { vm.refresh() }, contentDescription = "Refresh")
            }
            Row(
                Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
            ) {
                Seg(
                    options = listOf(
                        "songs" to "Songs",
                        "albums" to "Albums",
                        "artists" to "Artists",
                        "playlists" to "Playlists",
                        "liked" to "Liked",
                    ),
                    selected = vm.libraryTab,
                    onSelect = { vm.selectLibraryTab(it) },
                )
            }
            if (vm.libraryTab == "songs") {
                Row(
                    Modifier.fillMaxWidth().padding(top = 10.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text("${vm.tracks.size} songs", style = McType.mono9, color = mc.dim2)
                    Spacer(Modifier.weight(1f))
                    Seg(
                        options = listOf(
                            "artist" to "Artist",
                            "title" to "Title",
                            "recent" to "Recent",
                            "popular" to "Likes",
                        ),
                        selected = vm.sort,
                        onSelect = { vm.applySort(it) },
                    )
                }
            }
            Spacer(Modifier.height(10.dp))
        }

        when (vm.libraryTab) {
            "albums" -> GridList(values = vm.albums) { album ->
                AlbumTile(
                    album,
                    onClick = { vm.navigate(Route.Album(album.album)) },
                    onPlay = { vm.playAlbum(album.album) },
                    onLongPress = {
                        vm.openCollectionMenu("album", album.album, album.artist, album.coverId)
                    },
                    fillWidth = true,
                )
            }
            "artists" -> GridList(values = vm.artists) { artist ->
                ArtistTile(
                    artist,
                    onClick = { vm.navigate(Route.Artist(artist.artist)) },
                    onPlay = { vm.playArtist(artist.artist) },
                    onLongPress = {
                        vm.openCollectionMenu("artist", artist.artist, "${artist.n} tracks", artist.coverId)
                    },
                    fillWidth = true,
                )
            }
            "playlists" -> GridList(values = vm.playlists) { playlist ->
                PlaylistTile(
                    playlist,
                    onClick = { vm.navigate(Route.Playlist(playlist.id, playlist.name)) },
                    onPlay = { vm.playPlaylist(playlist.id) },
                    onLongPress = {
                        vm.openCollectionMenu(
                            "playlist", playlist.name, "${playlist.n} tracks",
                            playlist.coverId, playlist.id,
                        )
                    },
                    fillWidth = true,
                )
            }
            "liked" -> {
                val list = if (vm.settings.hideExplicit) vm.likes.filter { !it.explicit } else vm.likes
                if (list.isEmpty()) {
                    EmptyState(
                        "Nothing liked yet",
                        "Tap the heart on any song.",
                        icon = AppIcons.Heart,
                    )
                } else {
                    LazyColumn(
                        Modifier.fillMaxSize(),
                        contentPadding = PaddingValues(start = D.gutter, end = D.gutter, bottom = 24.dp),
                    ) {
                        itemsIndexed(list, key = { _, t -> t.id }) { index, track ->
                            TrackRow(
                                track = track,
                                number = index,
                                isCurrent = track.id == vm.engine.current?.id,
                                onClick = { vm.playList(list, index) },
                                onLike = { vm.toggleLike(track) },
                                onMore = { vm.openTrackMenu(track) },
                                showStats = vm.settings.ytStats,
                            )
                        }
                    }
                }
            }
            else -> {
                val sorted = remember(vm.tracks, vm.sort) { sortTracks(vm.tracks, vm.sort) }
                if (sorted.isEmpty()) {
                    EmptyState(
                        "No songs yet",
                        "Request a playlist to get started.",
                        icon = AppIcons.Music,
                    )
                } else {
                    LazyColumn(
                        Modifier.fillMaxSize(),
                        contentPadding = PaddingValues(start = D.gutter, end = D.gutter, bottom = 24.dp),
                    ) {
                        itemsIndexed(sorted, key = { _, t -> t.id }) { index, track ->
                            TrackRow(
                                track = track,
                                number = index,
                                isCurrent = track.id == vm.engine.current?.id,
                                onClick = { vm.playList(sorted, index) },
                                onLike = { vm.toggleLike(track) },
                                onMore = { vm.openTrackMenu(track) },
                                showStats = vm.settings.ytStats,
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun <T> GridList(
    values: List<T>,
    item: @Composable (T) -> Unit,
) {
    if (values.isEmpty()) {
        EmptyState("Nothing here yet", "Your library is still empty.", icon = AppIcons.Disc)
        return
    }
    LazyColumn(
        Modifier.fillMaxSize(),
        contentPadding = PaddingValues(start = D.gutter, end = D.gutter, bottom = 24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        items(values.chunked(2)) { row ->
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                row.forEach { value ->
                    Box(Modifier.weight(1f)) { item(value) }
                }
                if (row.size == 1) Spacer(Modifier.weight(1f))
            }
        }
    }
}

private fun sortTracks(tracks: List<Track>, sort: String): List<Track> = when (sort) {
    "title" -> tracks.sortedBy { it.title.lowercase() }
    "recent" -> tracks.sortedByDescending { it.added }
    "popular" -> tracks.sortedByDescending { it.ytLikes ?: 0L }
    else -> tracks.sortedWith(compareBy({ it.artist.lowercase() }, { it.album.lowercase() }))
}

/* ── album / artist ─────────────────────────────────────────────────────── */

@Composable
fun CollectionScreen(
    vm: AppViewModel,
    name: String,
    kicker: String,
    round: Boolean,
) {
    val mc = LocalMc.current
    val tracks = vm.collectionTracks
    val playable = if (vm.settings.hideExplicit) tracks.filter { !it.explicit } else tracks
    val albums = if (round) {
        tracks.groupBy { it.album }.map { (album, list) ->
            AlbumRef(
                album = album,
                artist = list.first().artist,
                n = list.size,
                coverId = list.first().id,
            )
        }.sortedBy { it.album.lowercase() }
    } else {
        emptyList()
    }

    if (tracks.isEmpty() && vm.collectionTitle == name) {
        Column(Modifier.fillMaxSize().padding(D.gutter)) {
            Text(name, style = McType.h1Small, color = mc.fg)
            EmptyState("No tracks here", "This $kicker has no playable tracks.", icon = AppIcons.Disc)
        }
        return
    }
    if (vm.collectionTitle != name) {
        Loading()
        return
    }

    LazyColumn(
        Modifier.fillMaxSize(),
        contentPadding = PaddingValues(start = D.gutter, end = D.gutter, top = 10.dp, bottom = 24.dp),
    ) {
        item {
            Hero(
                coverId = tracks.firstOrNull()?.id,
                kicker = kicker,
                title = name,
                subs = listOfNotNull(
                    "${tracks.size} tracks",
                    fmtTotal(tracks.sumOf { it.duration }),
                    if (round) "${albums.size} album${if (albums.size == 1) "" else "s"}"
                    else tracks.firstOrNull()?.genre?.ifBlank { null },
                ),
                round = round,
            ) {
                McButton(
                    "Play",
                    { vm.playList(playable, 0) },
                    solid = true,
                    leading = AppIcons.Play,
                )
                McButton(
                    "Shuffle",
                    { vm.shufflePlay(playable) },
                    leading = AppIcons.Shuffle,
                )
                McButton(
                    "Download",
                    { vm.downloadAll(playable) },
                    small = true,
                    ghost = true,
                    leading = AppIcons.Download,
                )
            }
        }
        if (albums.size > 1) {
            item(key = "artist-albums") {
                Shelf("Albums", meta = "${albums.size}") {
                    LazyRow(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        items(albums, key = { it.album }) { album ->
                            AlbumTile(
                                album,
                                onClick = { vm.navigate(Route.Album(album.album)) },
                                onPlay = { vm.playAlbum(album.album) },
                                onLongPress = {
                                    vm.openCollectionMenu("album", album.album, album.artist, album.coverId)
                                },
                            )
                        }
                    }
                }
            }
        }
        itemsIndexed(playable, key = { _, t -> t.id }) { index, track ->
            TrackRow(
                track = track,
                number = index,
                isCurrent = track.id == vm.engine.current?.id,
                onClick = { vm.playList(playable, index) },
                onLike = { vm.toggleLike(track) },
                onMore = { vm.openTrackMenu(track) },
            )
        }
    }
}

@Composable
fun LikesScreen(vm: AppViewModel) {
    val tracks = vm.likes
    val playable = if (vm.settings.hideExplicit) tracks.filter { !it.explicit } else tracks
    LazyColumn(
        Modifier.fillMaxSize(),
        contentPadding = PaddingValues(start = D.gutter, end = D.gutter, top = 10.dp, bottom = 24.dp),
    ) {
        item {
            Hero(
                coverId = tracks.firstOrNull()?.id,
                kicker = "Collection",
                title = "Liked songs",
                subs = listOf("${tracks.size} tracks", fmtTotal(tracks.sumOf { it.duration })),
            ) {
                McButton(
                    "Play",
                    { vm.playList(playable, 0) },
                    solid = true,
                    leading = AppIcons.Play,
                )
                McButton(
                    "Shuffle",
                    { vm.shufflePlay(playable) },
                    leading = AppIcons.Shuffle,
                )
                McButton(
                    "Download",
                    { vm.downloadAll(playable) },
                    small = true,
                    ghost = true,
                    leading = AppIcons.Download,
                )
                McButton(
                    "Queue on server",
                    { vm.queueServerDownloads("likes") },
                    small = true,
                    ghost = true,
                    leading = AppIcons.CloudDownload,
                )
            }
        }
        if (playable.isEmpty()) {
            item {
                EmptyState(
                    "Nothing liked yet",
                    "Tap the heart on any song.",
                    icon = AppIcons.Heart,
                )
            }
        } else {
            itemsIndexed(playable, key = { _, t -> t.id }) { index, track ->
                TrackRow(
                    track = track,
                    number = index,
                    isCurrent = track.id == vm.engine.current?.id,
                    onClick = { vm.playList(playable, index) },
                    onLike = { vm.toggleLike(track) },
                    onMore = { vm.openTrackMenu(track) },
                )
            }
        }
    }
}
