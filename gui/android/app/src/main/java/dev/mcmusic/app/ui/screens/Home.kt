package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
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
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.Listener
import dev.mcmusic.app.data.Track
import dev.mcmusic.app.ui.Cover
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.LiveDot
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.Pill
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.SectionLabel
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface
import dev.mcmusic.app.ui.timecode

sealed interface Feed {
    data object Loading : Feed
    data class Ready(val users: List<Listener>) : Feed
    data class Failed(val message: String) : Feed
}

@Composable
fun HomeScreen() {
    val design = LocalDesign.current
    var feed by remember { mutableStateOf<Feed>(Feed.Loading) }
    var reload by remember { mutableIntStateOf(0) }

    LaunchedEffect(reload) {
        if (feed !is Feed.Ready) feed = Feed.Loading
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
            top = 12.dp,
            bottom = 124.dp,
        ),
        verticalArrangement = Arrangement.spacedBy(design.gap),
    ) {
        item {
            ScreenTitle("Home", "What mcmusic is playing right now")
        }

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
                    icon = Lucide.Search,
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
                    icon = Lucide.Play,
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

@Composable
private fun HeroCard(live: Int, total: Int, loading: Boolean, onRefresh: () -> Unit) {
    val design = LocalDesign.current
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .mcSurface(RoundedCornerShape(design.cardRadius), tint = design.accent.copy(alpha = 0.10f))
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            LiveDot(live > 0, 9.dp)
            Spacer(Modifier.size(8.dp))
            Text(
                text = if (live > 0) "$live listening now" else "Quiet right now",
                color = design.fg,
                fontSize = 18.sp,
                fontWeight = FontWeight.SemiBold,
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
            Modifier
                .clip(RoundedCornerShape(50))
                .clickable { onRefresh() }
                .mcSurface(RoundedCornerShape(50))
                .padding(horizontal = 14.dp, vertical = 7.dp),
        ) {
            Text("Refresh", color = design.fg, fontSize = 12.sp, fontWeight = FontWeight.Medium)
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
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(design.gap),
    ) {
        Cover(
            url = listener.coverUrl,
            shape = RoundedCornerShape(design.tileRadius),
            modifier = Modifier.size(58.dp),
        )
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
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
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp),
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

/** Shared by Home and Search. */
@Composable
fun ListenerList(users: List<Listener>, modifier: Modifier = Modifier) {
    Column(modifier, verticalArrangement = Arrangement.spacedBy(LocalDesign.current.gap)) {
        users.forEach { ListenerCard(it) }
    }
}

/** Small helper so both languages get the same empty colour behind covers. */
@Composable
fun coverFallback(): Color = LocalDesign.current.palette.bg2
