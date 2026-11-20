package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.Background
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
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
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
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Account
import dev.mcmusic.app.data.AlbumSummary
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.ArtistSummary
import dev.mcmusic.app.data.HomeFeed
import dev.mcmusic.app.data.Listener
import dev.mcmusic.app.data.Prefs
import dev.mcmusic.app.data.Track
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.ui.Cover
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.LucideIcon
import dev.mcmusic.app.ui.Pill
import dev.mcmusic.app.ui.ScreenBack
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.SectionLabel
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface
import dev.mcmusic.app.ui.timecode
import kotlinx.coroutines.launch

sealed interface Feed {
    data object Loading : Feed
    data class Ready(val users: List<Listener>) : Feed
    data class Failed(val message: String) : Feed
}

/**
 * Signed in this is the website's own home feed (`/api/home`): made-for-you,
 * discover, top tracks and recently added. Signed out it falls back to the public
 * listening feed, which is all the server exposes without a session.
 */
@Composable
fun HomeScreen() {
    val design = LocalDesign.current
    val me = Account.me
    val scope = rememberCoroutineScope()
    var feed by remember { mutableStateOf<Feed>(Feed.Loading) }
    var home by remember { mutableStateOf<HomeFeed?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var reload by remember { mutableIntStateOf(0) }

    LaunchedEffect(reload, me != null) {
        error = null
        if (me != null) {
            Api.home().fold(
                onSuccess = { home = it },
                onFailure = { error = it.message ?: "could not load your feed" },
            )
        }
        feed = Api.listening().fold(
            onSuccess = { Feed.Ready(it) },
            onFailure = { Feed.Failed(it.message ?: "could not reach the server") },
        )
    }

    val users = (feed as? Feed.Ready)?.users.orEmpty()
    val live = users.count { it.listening }

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
                if (me != null) "Made for you on ${Prefs.server}" else "What mcmusic is playing right now",
            )
        }

        if (me != null) {
            val sections = home?.sections.orEmpty()
            if (sections.isEmpty() && error == null) {
                item { Text("Building your feed…", color = design.dim, fontSize = 13.sp) }
            }
            sections.forEach { section ->
                item(key = "section-${section.title}") {
                    SectionLabel(section.title, Modifier.padding(top = 4.dp))
                }
                items(section.tracks.take(5), key = { "s-${section.title}-${it.id}" }) { track ->
                    SongRow(track, queue = section.tracks)
                }
            }

            val albums = home?.albums.orEmpty()
            if (albums.isNotEmpty()) {
                item { SectionLabel("Albums", Modifier.padding(top = 4.dp)) }
                item {
                    LazyRow(horizontalArrangement = androidx.compose.foundation.Arrangement.spacedBy(design.gap)) {
                        items(albums, key = { "album-${it.album}" }) { album ->
                            AlbumTile(album) {
                                scope.launch {
                                    Api.albumTracks(album.album).onSuccess { tracks ->
                                        if (tracks.isNotEmpty()) Playback.play(tracks, 0)
                                    }
                                }
                            }
                        }
                    }
                }
            }

            error?.let { message ->
                item {
                    EmptyState(
                        icon = dev.mcmusic.app.ui.Lucide.Search,
                        title = "Couldn't load your feed",
                        body = message,
                        actionLabel = "Try again",
                        onAction = { reload++ },
                    )
                }
            }

            item { SectionLabel("Listening now", Modifier.padding(top = 4.dp)) }

            if (feed is Feed.Ready && users.isEmpty()) {
                item {
                    EmptyState(
                        icon = dev.mcmusic.app.ui.Lucide.Play,
                        title = "Nobody is listening",
                        body = "When someone starts a track it shows up here within a few seconds.",
                        actionLabel = "Refresh",
                        onAction = { reload++ },
                    )
                }
            }

            items(users, key = { it.username }) { listener -> ListenerCard(listener) }
        } else {
            item {
                HeroCard(
                    live = live,
                    total = users.size,
                    loading = feed is Feed.Loading,
                    onRefresh = { reload++ },
                )
            }

            if (feed is Feed.Failed) {
                item {
                    EmptyState(
                        icon = dev.mcmusic.app.ui.Lucide.Search,
                        title = "Can't reach the server",
                        body = (feed as Feed.Failed).message,
                        actionLabel = "Try again",
                        onAction = { reload++ },
                    )
                }
            }

            item { SectionLabel("Listening now", Modifier.padding(top = 4.dp)) }

            if (feed is Feed.Ready && users.isEmpty()) {
                item {
                    EmptyState(
                        icon = dev.mcmusic.app.ui.Lucide.Play,
                        title = "Nobody is listening",
                        body = "When someone starts a track it shows up here within a few seconds.",
                        actionLabel = "Refresh",
                        onAction = { reload++ },
                    )
                }
            }

            items(users, key = { it.username }) { listener -> ListenerCard(listener) }
        }
    }
}

@Composable
fun HeroCard(live: Int, total: Int, loading: Boolean, onRefresh: () -> Unit) {
    val design = LocalDesign.current
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .mcSurface(RoundedCornerShape(design.cardRadius), tint = design.accent.copy(alpha = 0.08f))
            .padding(20.dp),
        verticalArrangement = androidx.compose.foundation.Arrangement.spacedBy(14.dp),
    ) {
        Row(verticalAlignment = androidx.compose.foundation.alignment.Alignment.CenterVertically) {
            dev.mcmusic.app.ui.LiveDot(live > 0, 9.dp)
            androidx.compose.foundation.Spacer(Modifier.size(8.dp))
            Text(
                text = if (live > 0) "$live listening now" else "Quiet right now",
                color = design.fg,
                fontSize = 18.sp,
                fontWeight = androidx.compose.runtime.FontWeight.SemiBold,
            )
        }
        Text(
            text = if (loading) "Looking for listeners…"
            else if (total > 0) "$total account${if (total == 1) "" else "s"} active in the last 3 minutes"
            else "Nobody has played anything in the last 3 minutes",
            color = design.dim,
            fontSize = 13.sp,
            lineHeight = 18.sp,
        )
        Box(
            modifier = Modifier
                .clip(RoundedCornerShape(50))
                .clickable { onRefresh() }
                .mcSurface(RoundedCornerShape(50))
                .padding(horizontal = 14.dp, vertical = 7.dp),
            contentAlignment = androidx.compose.ui.Alignment.Center,
        ) {
            Text("Refresh", color = design.fg, fontSize = 12.sp, fontWeight = androidx.compose.runtime.FontWeight.Medium)
        }
    }
}

/** A library row used by the home feed, search results and collection pages. */
@Composable
fun SongRow(track: Track, queue: List<Track>, modifier: Modifier = Modifier) {
    val design = LocalDesign.current
    Row(
        modifier = modifier
            .fillMaxWidth()
            .mcSurface(RoundedCornerShape(design.cardRadius))
            .clickable { Playback.play(queue, queue.indexOfFirst { it.id == track.id }.coerceAtLeast(0)) }
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

@Composable
fun AlbumTile(album: AlbumSummary, modifier: Modifier = Modifier, onClick: () -> Unit) {
    val design = LocalDesign.current
    Column(
        modifier = modifier
            .width(132.dp)
            .clip(RoundedCornerShape(design.tileRadius))
            .clickable { onClick() },
        verticalArrangement = androidx.compose.foundation.Arrangement.spacedBy(6.dp),
    ) {
        Cover(
            url = album.coverId?.let { "${Api.server}/api/tracks/$it/cover" }.orEmpty(),
            shape = RoundedCornerShape(design.tileRadius),
            modifier = Modifier.size(132.dp),
            fallback = design.accentSoft,
        )
        Text(album.album, color = design.fg, fontSize = 12.sp, fontWeight = FontWeight.SemiBold, maxLines = 1)
        Text(
            text = listOfNotNull(album.artist.takeIf { it.isNotBlank() }, "${album.count} tracks").joinToString(" · "),
            color = design.dim,
            fontSize = 10.sp,
            maxLines = 1,
        )
    }
}

@Composable
fun ArtistTile(artist: ArtistSummary, modifier: Modifier = Modifier, onClick: () -> Unit) {
    val design = LocalDesign.current
    Row(
        modifier = modifier
            .clip(RoundedCornerShape(50))
            .mcSurface(RoundedCornerShape(50), tint = design.accentSoft)
            .clickable { onClick() }
            .padding(horizontal = 12.dp, vertical = 8.dp),
        verticalAlignment = androidx.compose.foundation.alignment.CenterVertically,
        horizontalArrangement = androidx.compose.foundation.Arrangement.spacedBy(8.dp),
    ) {
        Cover(
            url = artist.coverId?.let { "${Api.server}/api/tracks/$it/cover" }.orEmpty(),
            shape = RoundedCornerShape(50),
            modifier = Modifier.size(26.dp),
            fallback = design.accentSoft,
        )
        Column {
            Text(artist.artist, color = design.fg, fontSize = 12.sp, fontWeight = FontWeight.SemiBold, maxLines = 1)
            Text("${artist.albums} albums · ${artist.count} tracks", color = design.dim, fontSize = 10.sp, maxLines = 1)
        }
    }
}

@Composable
fun ListenerCard(listener: Listener, modifier: Modifier = Modifier) {
    val design = LocalDesign.current
    val uriHandler = LocalUriHandler.current
    val track: Track? = listener.track

    Row(
        modifier = modifier
            .fillMaxWidth()
            .mcSurface(RoundedCornerShape(design.cardRadius))
            .clickable(enabled = listener.profileUrl.isNotBlank()) {
                runCatching { uriHandler.openUri(listener.profileUrl) }
            }
            .padding(design.gap),
        verticalAlignment = androidx.compose.foundation.alignment.CenterVertically,
        horizontalArrangement = androidx.compose.foundation.Arrangement.spacedBy(design.gap),
    ) {
        Cover(
            url = listener.coverUrl,
            shape = RoundedCornerShape(design.tileRadius),
            modifier = Modifier.size(58.dp),
        )
        Column(Modifier.weight(1f), verticalArrangement = androidx.compose.foundation.Arrangement.spacedBy(3.dp)) {
            Text(
                text = listener.username.ifBlank { "someone" },
                color = design.accent,
                fontSize = 11.sp,
                fontWeight = FontWeight.SemiBold,
                letterSpacing = 0.4.sp,
            )
            Text(
                text = track?.title ?: "Nothing playing",
                color = design.fg,
                fontSize = 15.sp,
                fontWeight = FontWeight.SemiBold,
                maxLines = 1,
            )
            Text(
                text = listOfNotNull(track?.artist?.takeIf { it.isNotBlank() }, track?.album?.takeIf { it.isNotBlank() })
                    .joinToString(" · ")
                    .ifBlank { "quiet" },
                color = design.dim,
                fontSize = 12.sp,
                maxLines = 1,
            )
            Row(
                modifier = Modifier.padding(top = 3.dp),
                verticalAlignment = androidx.compose.foundation.alignment.CenterVertically,
                horizontalArrangement = androidx.compose.foundation.Arrangement.spacedBy(8.dp),
            ) {
                Pill(if (listener.listening) "listening" else "paused", listener.listening)
                val duration = track?.duration ?: 0.0
                if (duration > 0) {
                    Text(
                        text = "${timecode(listener.position)} / ${timecode(duration)}",
                        color = design.dim,
                        fontSize = 11.sp,
                    )
                }
            }
        }
    }
}

/** Small helper so both languages get the same empty colour behind covers. */
@Composable
fun coverFallback(): Color = LocalDesign.current.palette.bg2