package dev.mcmusic.app.ui

import androidx.activity.compose.BackHandler
import androidx.annotation.DrawableRes
import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Account
import dev.mcmusic.app.data.Prefs
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface
import dev.mcmusic.app.ui.screens.AdminScreen
import dev.mcmusic.app.ui.screens.DownloadsScreen
import dev.mcmusic.app.ui.screens.HomeScreen
import dev.mcmusic.app.ui.screens.LikesScreen
import dev.mcmusic.app.ui.screens.LibraryScreen
import dev.mcmusic.app.ui.screens.PlaylistsScreen
import dev.mcmusic.app.ui.screens.PlayerScreen
import dev.mcmusic.app.ui.screens.SearchScreen
import dev.mcmusic.app.ui.screens.AuthSplash
import dev.mcmusic.app.ui.screens.SignInScreen
import dev.mcmusic.app.ui.screens.SettingsScreen
import dev.mcmusic.app.ui.screens.VideosScreen

enum class Tab(val label: String, @param:DrawableRes val icon: Int) {
    Home("Home", Lucide.House),
    Search("Search", Lucide.Search),
    Library("Library", Lucide.Library),
    Downloads("Downloads", Lucide.Download),
    Videos("Videos", Lucide.Film),
    Settings("Settings", Lucide.Settings),
    Playlists("Playlists", Lucide.ListMusic),
    Likes("Likes", Lucide.Heart),
    Player("Player", Lucide.Play),
    Admin("Admin", Lucide.User);

    val inBar: Boolean get() = this in listOf(Home, Search, Library, Downloads, Settings)
    val fullScreen: Boolean get() = this == Player || this == Admin || this == Likes || this == Videos
}

/** Brand mark plus account, kept above the scroll area like the site header. */
@Composable
private fun TopBar(onAccount: () -> Unit) {
    val design = LocalDesign.current
    val me = Account.me
    Row(
        Modifier
            .fillMaxWidth()
            .statusBarsPadding()
            .padding(start = 18.dp, end = 12.dp, top = 10.dp, bottom = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Box(
            Modifier.size(34.dp).clip(CircleShape).background(design.accent),
            Alignment.Center,
        ) {
            Text("m", color = design.onAccent, fontSize = 18.sp, fontWeight = FontWeight.Black)
        }
        Column(verticalArrangement = Arrangement.spacedBy(1.dp)) {
            Text("mcmusic", color = design.fg, fontSize = 16.sp, fontWeight = FontWeight.Bold)
            Text(
                Account.status ?: "your room, your rules",
                color = if (Account.status != null) design.accentText else design.dim,
                fontSize = 10.sp,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        }
        Box(Modifier.weight(1f))
        Box(
            Modifier
                .clip(RoundedCornerShape(50))
                .background(design.accentWash)
                .clickable { onAccount() }
                .padding(horizontal = 10.dp, vertical = 6.dp),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                if (me != null) "@${me.username}" else "Sign in",
                color = design.accentText,
                fontSize = 11.sp,
                fontWeight = FontWeight.SemiBold,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        }
    }
}

/** Floating now-playing card: artwork, title, transport and a hairline progress. */
@Composable
private fun MiniPlayer(onOpen: () -> Unit) {
    val state = Playback.state
    val track = state.track ?: return
    val design = LocalDesign.current
    val fraction = if (state.duration > 0) {
        (state.position.toFloat() / state.duration).coerceIn(0f, 1f)
    } else 0f
    val shape = RoundedCornerShape(18.dp)
    Column(
        Modifier
            .fillMaxWidth()
            .padding(horizontal = 12.dp, vertical = 6.dp)
            .mcSurface(shape),
    ) {
        Row(
            Modifier
                .fillMaxWidth()
                .clickable { onOpen() }
                .padding(start = 8.dp, end = 8.dp, top = 8.dp, bottom = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(11.dp),
        ) {
            TrackCover(track, 42.dp, 12.dp)
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Text(
                    track.title,
                    color = design.fg,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.SemiBold,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                Text(
                    if (state.buffering) "buffering…" else track.artist.ifBlank { "unknown artist" },
                    color = design.dim,
                    fontSize = 11.sp,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }
            IconButton(Lucide.SkipForward, size = 18.dp) { Playback.next() }
            Box(
                Modifier.size(38.dp).clip(CircleShape).background(design.accent).clickable { Playback.toggle() },
                Alignment.Center,
            ) {
                LucideIcon(
                    if (state.playing) Lucide.Pause else Lucide.Play,
                    design.onAccent,
                    size = 15.dp,
                )
            }
        }
        Box(Modifier.fillMaxWidth().height(2.dp).background(design.hairline)) {
            Box(Modifier.fillMaxWidth(fraction).height(2.dp).background(design.accent))
        }
    }
}

/** Flat tab dock, grouped into one pill. */
@Composable
private fun BottomBar(tab: Tab, onTab: (Tab) -> Unit) {
    val design = LocalDesign.current
    Row(
        Modifier
            .fillMaxWidth()
            .navigationBarsPadding()
            .padding(horizontal = 12.dp, vertical = 8.dp)
            .mcSurface(RoundedCornerShape(26.dp))
            .padding(horizontal = 6.dp, vertical = 6.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Tab.entries.filter { it.inBar }.forEach { entry ->
            val selected = entry == tab
            Column(
                Modifier
                    .weight(1f)
                    .clip(RoundedCornerShape(20.dp))
                    .background(if (selected) design.accentSoft else Color.Transparent)
                    .clickable { onTab(entry) }
                    .padding(vertical = 8.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(3.dp),
            ) {
                LucideIcon(
                    entry.icon,
                    if (selected) design.accentText else design.dim,
                    size = 20.dp,
                )
                Text(
                    entry.label,
                    color = if (selected) design.accentText else design.dim,
                    fontSize = 10.sp,
                    fontWeight = if (selected) FontWeight.SemiBold else FontWeight.Medium,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }
        }
    }
}

@Composable
private fun TabContent(
    tab: Tab,
    onTab: (Tab) -> Unit,
    onPlaylist: (Int) -> Unit,
    playlistId: Int?,
    videoId: String?,
    videoStartMs: Long,
    onBack: () -> Unit,
    onVideo: (String?, Long) -> Unit,
    onVideoClosed: (Long?) -> Unit,
) {
    val motion = Prefs.motion
    val appear = remember(tab) { Animatable(if (motion) 0f else 1f) }
    LaunchedEffect(tab) {
        if (motion) appear.animateTo(1f, tween(220, easing = FastOutSlowInEasing))
    }
    Box(
        Modifier
            .fillMaxSize()
            .graphicsLayer {
                alpha = appear.value
                translationY = (1f - appear.value) * 12.dp.toPx()
            },
    ) {
        when (tab) {
            Tab.Home -> HomeScreen(onOpenSearch = { onTab(Tab.Search) }, onOpenPlayer = { onTab(Tab.Player) })
            Tab.Search -> SearchScreen(onPlaylist = onPlaylist, onOpenPlayer = { onTab(Tab.Player) })
            Tab.Library -> LibraryScreen(
                onOpenPlaylist = onPlaylist,
                onOpenLikes = { onTab(Tab.Likes) },
                onOpenPlayer = { onTab(Tab.Player) },
            )
            Tab.Likes -> LikesScreen(onBack = onBack, onOpenPlayer = { onTab(Tab.Player) })
            Tab.Playlists -> PlaylistsScreen(
                playlistId = playlistId,
                onOpenPlaylist = onPlaylist,
                onOpenPlayer = { onTab(Tab.Player) },
                onBack = onBack,
            )
            Tab.Downloads -> DownloadsScreen(
                onOpenPlayer = { onTab(Tab.Player) },
                onOpenVideos = { onVideo(null, 0L) },
            )
            Tab.Settings -> SettingsScreen(onAdmin = { onTab(Tab.Admin) }, onSignedOut = { onTab(Tab.Home) })
            Tab.Player -> PlayerScreen(onBack = onBack, onVideo = onVideo)
            Tab.Videos -> VideosScreen(
                ytId = videoId,
                startMs = videoStartMs,
                onBack = onBack,
                onPlay = { id, start -> onVideo(id, start) },
                onClosed = onVideoClosed,
            )
            Tab.Admin -> AdminScreen(onBack = onBack)
        }
    }
}

/**
 * App shell: brand header, current page, floating player and tab dock. The
 * player and admin pages take over the screen and return to where they opened.
 */
@Composable
fun McShell() {
    // Verify the saved token before any screen can render. A cold start shows
    // a short splash; a missing or rejected token shows only the sign-in gate.
    LaunchedEffect(Unit) { Account.refresh() }
    if (!Account.loaded) {
        AuthSplash()
        return
    }
    if (!Account.signedIn) {
        SignInScreen()
        return
    }

    var tab by rememberSaveable { mutableStateOf(Tab.Home) }
    var previous by rememberSaveable { mutableStateOf(Tab.Home) }
    var playlistId by rememberSaveable { mutableStateOf<Int?>(null) }
    var videoId by rememberSaveable { mutableStateOf<String?>(null) }
    var videoStartMs by rememberSaveable { mutableStateOf(0L) }

    LaunchedEffect(Account.isAdmin) {
        if (!Account.isAdmin && tab == Tab.Admin) tab = Tab.Home
    }

    val open: (Tab) -> Unit = { next ->
        if (next != tab) previous = tab
        tab = next
    }

    // A detail pane is one level deep: Back closes it before leaving Playlists.
    val back: () -> Unit = {
        if (playlistId != null) {
            playlistId = null
        } else if (tab.fullScreen) {
            tab = previous
        } else {
            tab = Tab.Home
        }
    }
    BackHandler(enabled = tab.fullScreen || playlistId != null, onBack = back)

    val openPlaylist: (Int) -> Unit = { id ->
        playlistId = id
        open(Tab.Playlists)
    }

    val openVideo: (String?, Long) -> Unit = { id, start ->
        if (id != null) {
            videoStartMs = start
            videoId = id
            tab = Tab.Videos
        }
    }
    val closeVideo: (Long?) -> Unit = { _ ->
        videoId = null
        videoStartMs = 0L
        back()
    }

    Box(Modifier.fillMaxSize()) {
        if (tab.fullScreen) {
            Box(Modifier.fillMaxSize().statusBarsPadding().navigationBarsPadding()) {
                TabContent(
                    tab = tab,
                    onTab = open,
                    onPlaylist = openPlaylist,
                    playlistId = playlistId,
                    videoId = videoId,
                    videoStartMs = videoStartMs,
                    onBack = if (videoId != null) { { closeVideo(null) } } else back,
                    onVideo = openVideo,
                    onVideoClosed = closeVideo,
                )
            }
        } else {
            Column(Modifier.fillMaxSize()) {
                TopBar(onAccount = { open(Tab.Settings) })
                Box(Modifier.weight(1f)) {
                    TabContent(
                        tab = tab,
                        onTab = open,
                        onPlaylist = openPlaylist,
                        playlistId = playlistId,
                        videoId = videoId,
                        videoStartMs = videoStartMs,
                        onBack = if (videoId != null) { { closeVideo(null) } } else back,
                        onVideo = openVideo,
                        onVideoClosed = closeVideo,
                    )
                }
                MiniPlayer(onOpen = { open(Tab.Player) })
                BottomBar(tab = tab, onTab = open)
            }
        }
    }
}
