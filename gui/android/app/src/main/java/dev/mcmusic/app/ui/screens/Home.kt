package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Account
import dev.mcmusic.app.data.AlbumSummary
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.HomeFeed
import dev.mcmusic.app.data.Listener
import dev.mcmusic.app.data.Track
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.ui.Cover
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.ErrorLine
import dev.mcmusic.app.ui.GhostButton
import dev.mcmusic.app.ui.Loading
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.MediaCard
import dev.mcmusic.app.ui.Muted
import dev.mcmusic.app.ui.Pill
import dev.mcmusic.app.ui.SectionLabel
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.TrackRow
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface
import dev.mcmusic.app.ui.formatDuration

/**
 * The signed-in feed the website shows, plus the public "listening now" row that
 * works without an account. Recently added and all-tracks sections fall back to
 * public endpoints, so a fresh install is useful before signing in.
 */
@Composable
fun HomeScreen(onOpenSearch: () -> Unit, onOpenPlayer: () -> Unit) {
    val design = LocalDesign.current
    val me = Account.me
    var feed by remember { mutableStateOf<HomeFeed?>(null) }
    var listeners by remember { mutableStateOf<List<Listener>>(emptyList()) }
    var recent by remember { mutableStateOf<List<Track>>(emptyList()) }
    var errors by remember { mutableStateOf<List<String>>(emptyList()) }
    var loading by remember { mutableStateOf(true) }
    var reload by remember { mutableIntStateOf(0) }
    var album by remember { mutableStateOf<AlbumSummary?>(null) }

    LaunchedEffect(reload, me != null) {
        loading = true
        val failures = mutableListOf<String>()
        Api.listening().fold(
            onSuccess = { listeners = it },
            onFailure = { failures += "Listening now: ${it.message ?: "unavailable"}" },
        )
        Api.tracks(limit = 60).fold(
            onSuccess = { recent = it },
            onFailure = { failures += "Library: ${it.message ?: "unavailable"}" },
        )
        if (me != null) {
            Api.home().fold(
                onSuccess = { feed = it },
                onFailure = { failures += "Your mix: ${it.message ?: "unavailable"}" },
            )
        } else {
            feed = null
        }
        errors = failures
        loading = false
    }

    LazyColumn(
        contentPadding = PaddingValues(
            start = design.screenPadding,
            end = design.screenPadding,
            top = 10.dp,
            bottom = 24.dp,
        ),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            ScreenTitle(
                if (me != null) "Made for ${me.username}" else "mcmusic",
                subtitle = if (me != null) "Your mix, the live room and what just landed."
                else "Sign in from Settings for a personalised mix.",
            )
        }

        if (loading) item { Loading("Building your feed…") }
        errors.forEach { message -> item { ErrorLine(message) } }

        if (listeners.isNotEmpty()) {
            item {
                SectionLabel("Listening now") {
                    Pill("${listeners.count { it.listening }} live")
                }
            }
            item {
                LazyRow(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    items(listeners, key = { it.username }) { listener ->
                        ListenerCard(listener)
                    }
                }
            }
        }

        feed?.sections?.forEach { section ->
            item { SectionLabel(section.title) }
            item {
                LazyRow(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    items(section.tracks, key = { it.id }) { track ->
                        TrackCard(track, onPlay = {
                            Playback.play(section.tracks, section.tracks.indexOf(track))
                            onOpenPlayer()
                        })
                    }
                }
            }
        }

        if (!feed?.albums.isNullOrEmpty()) {
            item { SectionLabel("Recently added") }
            item {
                LazyRow(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    items(feed!!.albums, key = { it.album }) { entry ->
                        MediaCard(
                            title = entry.album,
                            subtitle = entry.artist,
                            coverUrl = albumCoverUrl(entry.coverId),
                            onClick = { album = entry },
                        )
                    }
                }
            }
        }

        if (me == null) {
            item {
                Column(
                    Modifier.fillMaxWidth().mcSurface().padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Text("Get your own mix", color = design.fg, fontSize = 15.sp, fontWeight = FontWeight.SemiBold)
                    Muted("Signing in unlocks made-for-you sections, likes, playlists and downloads. Listening now stays public.")
                    GhostButton("Search the library", onClick = onOpenSearch)
                }
            }
        }

        item { SectionLabel("All tracks") }
        if (recent.isEmpty() && !loading) {
            item {
                EmptyState(
                    icon = Lucide.Library,
                    title = "No tracks yet",
                    body = "The server has not returned any tracks.",
                    actionLabel = "Retry",
                    onAction = { reload++ },
                )
            }
        }
        items(recent, key = { it.id }) { track ->
            TrackRow(track, onClick = {
                Playback.play(recent, recent.indexOf(track))
                onOpenPlayer()
            })
        }
    }

    album?.let { entry ->
        CollectionSheet(
            kind = CollectionKind.Album,
            name = entry.album,
            onDismiss = { album = null },
            onOpenPlayer = onOpenPlayer,
        )
    }
}

@Composable
private fun ListenerCard(listener: Listener) {
    val design = LocalDesign.current
    Row(
        Modifier
            .width(210.dp)
            .mcSurface(RoundedCornerShape(8.dp))
            .padding(8.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(9.dp),
    ) {
        Cover(
            url = listener.profileUrl,
            shape = CircleShape,
            modifier = Modifier.size(38.dp),
            fallback = design.accentSoft,
        )
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(5.dp)) {
                Text(listener.username, color = design.fg, fontSize = 12.sp, fontWeight = FontWeight.Medium, maxLines = 1)
                dev.mcmusic.app.ui.LiveDot(listener.listening, 5.dp)
            }
            Text(
                listener.track?.let { "${it.title} · ${it.artist}" }
                    ?: if (listener.listening) "listening" else "offline",
                color = design.dim,
                fontSize = 10.sp,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        }
    }
}

@Composable
private fun TrackCard(track: Track, onPlay: () -> Unit) {
    val design = LocalDesign.current
    Column(
        Modifier.width(132.dp).clip(RoundedCornerShape(8.dp)).clickable { onPlay() },
        verticalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        Box {
            Cover(
                url = dev.mcmusic.app.ui.trackCoverUrl(track.id),
                shape = RoundedCornerShape(6.dp),
                modifier = Modifier.size(132.dp),
                fallback = design.accentSoft,
            )
            Box(
                Modifier.align(Alignment.BottomEnd).padding(6.dp).size(24.dp).clip(CircleShape)
                    .background(design.accent),
                Alignment.Center,
            ) {
                dev.mcmusic.app.ui.LucideIcon(Lucide.Play, design.palette.bg, Modifier.size(11.dp))
            }
        }
        Text(track.title, color = design.fg, fontSize = 12.sp, fontWeight = FontWeight.Medium, maxLines = 1, overflow = TextOverflow.Ellipsis)
        Text(
            "${track.artist} · ${formatDuration(track.duration)}",
            color = design.dim, fontSize = 10.sp, maxLines = 1, overflow = TextOverflow.Ellipsis,
        )
    }
}

fun albumCoverUrl(coverId: Int?): String = coverId?.let { "${Api.server}/api/tracks/$it/cover" } ?: ""
