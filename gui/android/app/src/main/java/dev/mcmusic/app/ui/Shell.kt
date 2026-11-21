package dev.mcmusic.app.ui

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
import androidx.compose.foundation.layout.width
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
import dev.mcmusic.app.ui.screens.LibraryScreen
import dev.mcmusic.app.ui.screens.PlaylistsScreen
import dev.mcmusic.app.ui.screens.PlayerScreen
import dev.mcmusic.app.ui.screens.SearchScreen
import dev.mcmusic.app.ui.screens.SettingsScreen

enum class Tab(val label: String, @param:DrawableRes val icon: Int) {
    Home("Home", Lucide.House),
    Search("Search", Lucide.Search),
    Library("Library", Lucide.Library),
    Downloads("Downloads", Lucide.Download),
    Settings("Settings", Lucide.Settings),
    Playlists("Playlists", Lucide.ListMusic),
    Player("Player", Lucide.Play),
    Admin("Admin", Lucide.User);

    val inBar: Boolean get() = this in listOf(Home, Search, Library, Downloads, Settings)
}

/**
 * The compact top bar the web client has: wordmark on the left, account on the
 * right. It stays out of the scroll area, like the site's header.
 */
@Composable
private fun TopBar(onAccount: () -> Unit) {
    val design = LocalDesign.current
    Row(
        Modifier
            .fillMaxWidth()
            .background(design.palette.bg)
            .statusBarsPadding()
            .padding(start = 16.dp, end = 8.dp, top = 8.dp, bottom = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text("mcmusic", color = design.fg, fontSize = 15.sp, fontWeight = FontWeight.Bold)
        Box(Modifier.weight(1f))
        Text(
            Prefs.server.removePrefix("https://").removePrefix("http://"),
            color = design.dim,
            fontSize = 10.sp,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
        )
        Box(
            Modifier
                .size(30.dp)
                .clip(CircleShape)
                .background(design.accentSoft)
                .clickable { onAccount() },
            Alignment.Center,
        ) {
            LucideIcon(
                if (Account.me != null) Lucide.User else Lucide.LogIn,
                design.accent,
                Modifier.size(15.dp),
            )
        }
    }
}

@Composable
private fun MiniPlayer(onOpen: () -> Unit) {
    val state = Playback.state
    val track = state.track ?: return
    val design = LocalDesign.current
    val fraction = if (state.duration > 0) (state.position.toFloat() / state.duration).coerceIn(0f, 1f) else 0f
    Column(
        Modifier
            .fillMaxWidth()
            .padding(horizontal = 8.dp, vertical = 4.dp)
            .mcSurface(RoundedCornerShape(8.dp)),
    ) {
        Row(
            Modifier.fillMaxWidth().clickable { onOpen() }.padding(start = 8.dp, end = 4.dp, top = 7.dp, bottom = 7.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            TrackCover(track, 36.dp)
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(1.dp)) {
                Text(track.title, color = design.fg, fontSize = 12.sp, fontWeight = FontWeight.Medium, maxLines = 1, overflow = TextOverflow.Ellipsis)
                Text(
                    if (state.buffering) "buffering…" else track.artist.ifBlank { "unknown artist" },
                    color = design.dim, fontSize = 10.sp, maxLines = 1, overflow = TextOverflow.Ellipsis,
                )
            }
            IconButton(Lucide.SkipForward, onClick = { Playback.next() })
            Box(
                Modifier.size(32.dp).clip(CircleShape).background(design.accent).clickable { Playback.toggle() },
                Alignment.Center,
            ) {
                LucideIcon(if (state.playing) Lucide.Pause else Lucide.Play, design.palette.bg, Modifier.size(13.dp))
            }
        }
        Box(Modifier.fillMaxWidth().height(2.dp).background(design.hairline)) {
            Box(Modifier.fillMaxWidth(fraction).height(2.dp).background(design.accent))
        }
    }
}

@Composable
private fun BottomBar(tab: Tab, onTab: (Tab) -> Unit) {
    val design = LocalDesign.current
    Row(
        Modifier
            .fillMaxWidth()
            .background(design.palette.bg)
            .navigationBarsPadding()
            .padding(horizontal = 4.dp, vertical = 5.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Tab.entries.filter { it.inBar }.forEach { entry ->
            val selected = entry == tab
            Column(
                Modifier
                    .weight(1f)
                    .clip(RoundedCornerShape(8.dp))
                    .clickable { onTab(entry) }
                    .padding(vertical = 4.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(3.dp),
            ) {
                LucideIcon(
                    entry.icon,
                    if (selected) design.accent else design.dim,
                    Modifier.size(20.dp),
                )
                Text(
                    entry.label,
                    color = if (selected) design.accent else design.dim,
                    fontSize = 9.sp,
                    fontWeight = if (selected) FontWeight.SemiBold else FontWeight.Normal,
                    maxLines = 1,
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
    onBack: () -> Unit,
) {
    val design = LocalDesign.current
    val motion = Prefs.motion
    val appear = remember(tab) { Animatable(if (motion) 0f else 1f) }
    LaunchedEffect(tab) {
        if (motion) appear.animateTo(1f, tween(160, easing = FastOutSlowInEasing))
    }
    Box(
        Modifier
            .fillMaxSize()
            .graphicsLayer {
                alpha = appear.value
                translationY = (1f - appear.value) * 8.dp.toPx()
            },
    ) {
        when (tab) {
            Tab.Home -> HomeScreen(onOpenSearch = { onTab(Tab.Search) }, onOpenPlayer = { onTab(Tab.Player) })
            Tab.Search -> SearchScreen(onPlaylist = onPlaylist, onOpenPlayer = { onTab(Tab.Player) })
            Tab.Library -> LibraryScreen(onOpenPlaylists = { onTab(Tab.Playlists) }, onOpenPlayer = { onTab(Tab.Player) })
            Tab.Playlists -> PlaylistsScreen(
                playlistId = playlistId,
                onOpenPlaylist = onPlaylist,
                onOpenPlayer = { onTab(Tab.Player) },
                onBack = onBack,
            )
            Tab.Downloads -> DownloadsScreen(onOpenPlayer = { onTab(Tab.Player) })
            Tab.Settings -> SettingsScreen(onAdmin = { onTab(Tab.Admin) }, onSignedOut = { onTab(Tab.Home) })
            Tab.Player -> PlayerScreen(onBack = onBack)
            Tab.Admin -> AdminScreen(onBack = onBack)
        }
    }
}

/**
 * The app shell: fixed top bar, the current page, a mini player when something
 * is playing, and the bottom tab strip. The player and admin pages are pushed
 * over the shell and return to where they were opened from.
 */
@Composable
fun McShell() {
    val design = LocalDesign.current
    var tab by rememberSaveable { mutableStateOf(Tab.Home) }
    var previous by rememberSaveable { mutableStateOf(Tab.Home) }
    var playlistId by rememberSaveable { mutableStateOf<Int?>(null) }

    LaunchedEffect(Unit) { Account.refresh() }
    LaunchedEffect(Account.isAdmin) {
        if (!Account.isAdmin && tab == Tab.Admin) tab = Tab.Home
    }

    val open: (Tab) -> Unit = { next ->
        if (next != Tab.Player && next != Tab.Admin && next != Tab.Playlists) previous = tab
        tab = next
    }

    Box(Modifier.fillMaxSize().background(design.palette.bg)) {
        Column(Modifier.fillMaxSize()) {
            TopBar(onAccount = { open(Tab.Settings) })
            Box(Modifier.weight(1f)) {
                TabContent(
                    tab = tab,
                    onTab = open,
                    onPlaylist = { id -> playlistId = id; open(Tab.Playlists) },
                    playlistId = playlistId,
                    onBack = { tab = previous },
                )
            }
            if (tab != Tab.Player) MiniPlayer(onOpen = { open(Tab.Player) })
            BottomBar(tab = tab, onTab = open)
        }
    }
}
