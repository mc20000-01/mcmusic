@file:OptIn(
    androidx.compose.material3.ExperimentalMaterial3Api::class,
    androidx.compose.foundation.ExperimentalFoundationApi::class,
)

package dev.mcmusic.app.ui

import android.content.Intent
import android.net.Uri
import androidx.activity.compose.BackHandler
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectDragGesturesAfterLongPress
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.SwipeToDismissBox
import androidx.compose.material3.SwipeToDismissBoxValue
import androidx.compose.material3.Text
import androidx.compose.material3.rememberSwipeToDismissBoxState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.em
import androidx.compose.ui.unit.sp
import androidx.compose.ui.zIndex
import dev.mcmusic.app.AppViewModel
import dev.mcmusic.app.BuildConfig
import dev.mcmusic.app.CollectionMenu
import dev.mcmusic.app.R
import dev.mcmusic.app.Route
import dev.mcmusic.app.data.Track
import dev.mcmusic.app.ui.theme.D
import dev.mcmusic.app.ui.theme.LocalMc
import dev.mcmusic.app.ui.theme.McType
import dev.mcmusic.app.ui.theme.glass
import kotlin.math.roundToInt

@Composable
fun AppRoot(vm: AppViewModel) {
    val mc = LocalMc.current

    BackHandler {
        when {
            vm.playerOpen -> vm.playerOpen = false
            vm.queueOpen -> vm.queueOpen = false
            vm.collectionMenu != null -> vm.closeCollectionMenu()
            vm.addToPlaylistTrack != null -> vm.closeAddToPlaylist()
            vm.infoTrack != null -> vm.closeInfo()
            vm.menuTrack != null -> vm.closeTrackMenu()
            vm.createPlaylistOpen -> vm.createPlaylistOpen = false
            vm.stack.isNotEmpty() -> vm.back()
            vm.route != Route.Home -> vm.navigate(Route.Home, push = false)
        }
    }

    Box(Modifier.fillMaxSize().background(mc.bg)) {
        when {
            !vm.checked -> Splash()
            vm.me == null -> LoginScreen(vm)
            else -> Shell(vm)
        }
        if (vm.me != null && vm.playerOpen) PlayerOverlay(vm)
        ToastHost(
            message = vm.toastText,
            onDismiss = vm::clearToast,
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .navigationBarsPadding()
                .padding(bottom = if (vm.me == null) 44.dp else 144.dp),
        )
    }
}

@Composable
private fun Splash() {
    val mc = LocalMc.current
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(14.dp)) {
            Icon(
                painterResource(R.drawable.ic_logo),
                contentDescription = null,
                modifier = Modifier.size(52.dp),
                tint = mc.accent,
            )
            Text("mcmusic", style = McType.h2, color = mc.fg)
            CircularProgressIndicator(Modifier.size(18.dp), color = mc.accent, strokeWidth = 2.dp)
        }
    }
}

@Composable
fun Shell(vm: AppViewModel) {
    val mc = LocalMc.current
    Box(Modifier.fillMaxSize()) {
        Column(
            Modifier
                .fillMaxSize()
                .background(
                    Brush.verticalGradient(
                        listOf(
                            mc.accent.copy(alpha = 0.18f),
                            mc.bg.copy(alpha = 0.92f),
                            mc.bg,
                        ),
                    ),
                )
                .statusBarsPadding()
                .navigationBarsPadding(),
        ) {
            TopBar(vm)
            RoomBanner(vm)
            Box(Modifier.weight(1f).padding(bottom = D.pageBottom)) {
                ArtistNav.go = { name -> vm.navigate(Route.Artist(name)) }
                CompositionLocalProvider(
                    LocalListPrefs provides ListPrefs(
                        covers = vm.settings.covers,
                        compact = vm.settings.density == "compact",
                    ),
                ) {
                AnimatedContent(
                    targetState = vm.route,
                    transitionSpec = {
                        (fadeIn(tween(220)) + slideInHorizontally(tween(240)) { it / 14 })
                            .togetherWith(fadeOut(tween(120)))
                    },
                    label = "screen",
                ) { r ->
                    when (r) {
                        Route.Home -> HomeScreen(vm)
                        Route.Search -> SearchScreen(vm)
                        Route.Library -> LibraryScreen(vm)
                        is Route.Album -> CollectionScreen(vm, r.name, "Album", false)
                        is Route.Artist -> CollectionScreen(vm, r.name, "Artist", true)
                        Route.Likes -> LikesScreen(vm)
                        Route.Playlists -> PlaylistsScreen(vm)
                        is Route.Playlist -> PlaylistScreen(vm, r.id)
                        Route.Requests -> RequestsScreen(vm)
                        Route.Downloads -> DownloadsScreen(vm)
                        Route.Settings -> SettingsScreen(vm)
                        Route.Admin -> AdminScreen(vm)
                        Route.NowPlaying -> NowPlayingScreen(vm)
                    }
                }
                }
            }
        }

        if (vm.engine.current != null) {
            Deck(
                vm,
                Modifier
                    .align(Alignment.BottomCenter)
                    .navigationBarsPadding()
                    .padding(start = 10.dp, end = 10.dp, bottom = 78.dp),
            )
        }
        NavBar(vm, Modifier.align(Alignment.BottomCenter))

        if (vm.queueOpen) QueueSheet(vm)
        if (vm.sleepOpen) SleepSheet(vm)
        vm.collectionMenu?.let { CollectionMenuSheet(vm, it) }
        if (vm.updateDialogOpen) UpdateDialog(vm)
        vm.menuTrack?.let { MenuSheet(vm, it) }
        vm.infoTrack?.let { InfoSheet(vm, it) }
        vm.addToPlaylistTrack?.let { AddToPlaylistSheet(vm, it) }
        if (vm.createPlaylistOpen) CreatePlaylistSheet(vm)
        if (vm.requestLog != null) RequestLogSheet(vm)
    }
}

/* ── listen-along banner ────────────────────────────────────────────────── */

@Composable
private fun RoomBanner(vm: AppViewModel) {
    val role = vm.roomRole ?: return
    val mc = LocalMc.current
    val clipboard = LocalClipboardManager.current
    val st = vm.roomState
    val track = st?.track
    val detail = when {
        role == "host" -> "Sharing your playback · code ${vm.roomCode}"
        track != null -> "${track.title}${if (track.artist.isNotBlank()) " · ${track.artist}" else ""}"
        st?.hostAway == true -> "Host is away"
        else -> "Waiting for ${vm.roomHostName.ifBlank { "the host" }}"
    }
    Row(
        Modifier
            .fillMaxWidth()
            .padding(horizontal = 14.dp, vertical = 5.dp)
            .clip(RoundedCornerShape(D.r2))
            .background(mc.bg2)
            .border(1.dp, mc.line2, RoundedCornerShape(D.r2))
            .padding(horizontal = 10.dp, vertical = 7.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Icon(AppIcons.Users, null, Modifier.size(15.dp), tint = mc.accent)
        Column(Modifier.weight(1f)) {
            Text(
                if (role == "host") "Hosting listen-along" else "Listening with ${vm.roomHostName}",
                style = McType.labelSm,
                color = mc.fg,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            Text(
                detail,
                style = McType.mono9,
                color = mc.dim2,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        }
        if (role == "host") {
            IconBtn(
                AppIcons.Link,
                { clipboard.setText(AnnotatedString(vm.roomLink())) },
                size = 28.dp,
                contentDescription = "Copy room link",
            )
        }
        McButton(if (role == "host") "End" else "Leave", { vm.leaveRoom() }, small = true, ghost = true)
    }
}

/* ── download log (admin) ───────────────────────────────────────────────── */

@Composable
private fun RequestLogSheet(vm: AppViewModel) {
    val mc = LocalMc.current
    McSheet(onDismiss = vm::closeRequestLog, title = vm.requestLogTitle.ifBlank { "Request log" }) {
        Box(
            Modifier
                .fillMaxWidth()
                .height(320.dp)
                .clip(RoundedCornerShape(D.r2))
                .background(mc.bg)
                .border(1.dp, mc.line, RoundedCornerShape(D.r2))
                .padding(10.dp)
                .verticalScroll(rememberScrollState()),
        ) {
            Text(
                vm.requestLog.orEmpty(),
                style = McType.mono10,
                color = mc.dim,
            )
        }
    }
}

/* ── masthead ───────────────────────────────────────────────────────────── */

@Composable
private fun TopBar(vm: AppViewModel) {
    val mc = LocalMc.current
    val width = LocalConfiguration.current.screenWidthDp
    Row(
        Modifier
            .fillMaxWidth()
            .height(D.top)
            .padding(horizontal = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        if (vm.stack.isNotEmpty()) {
            IconBtn(AppIcons.ChevronLeft, { vm.back() }, contentDescription = "Back")
        }
        Box(Modifier.weight(1f)) {
            McField(
                value = vm.searchQuery,
                onValueChange = vm::onSearchChange,
                placeholder = "Search for songs, albums, or artists",
                leading = AppIcons.Search,
                trailing = if (vm.searchQuery.isNotEmpty()) {
                    { IconBtn(AppIcons.Close, { vm.onSearchChange("") }, size = 24.dp) }
                } else null,
            )
        }
        Row(
            Modifier
                .clip(RoundedCornerShape(D.r2))
                .clickable { vm.navigate(Route.Settings) }
                .padding(horizontal = 4.dp, vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(7.dp),
        ) {
            Box(
                Modifier.size(24.dp).clip(CircleShape).background(mc.accent),
                contentAlignment = Alignment.Center,
            ) {
                Text(
                    vm.me?.username?.take(1)?.uppercase() ?: "?",
                    style = McType.mono9.copy(fontWeight = FontWeight.Bold),
                    color = mc.accentFg,
                )
            }
            if (width >= 400) {
                Text(
                    vm.me?.username.orEmpty(),
                    style = McType.bodyXs,
                    color = mc.dim,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }
        }
    }
}

/* ── deck ───────────────────────────────────────────────────────────────── */

@Composable
private fun Deck(vm: AppViewModel, modifier: Modifier = Modifier) {
    val t = vm.engine.current ?: return
    val mc = LocalMc.current
    val error = vm.engine.error
    var moreOpen by remember(t.id) { mutableStateOf(false) }

    Box(
        modifier
            .fillMaxWidth()
            .height(D.deck)
            .glass(RoundedCornerShape(18.dp)),
    ) {
        Row(
            Modifier.fillMaxSize().padding(horizontal = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            SwipeToSkip(
                onPrevious = {
                    val i = vm.engine.index
                    if (i > 0) vm.engine.jumpTo(i - 1)
                },
                onNext = {
                    val i = vm.engine.index
                    if (i in 0 until vm.engine.queue.lastIndex) vm.engine.jumpTo(i + 1)
                },
                compact = true,
                modifier = Modifier.weight(1f).fillMaxHeight(),
            ) {
                Row(
                    Modifier
                        .fillMaxSize()
                        .clip(RoundedCornerShape(8.dp))
                        .clickable {
                            if (error != null) vm.engine.retry() else vm.playerOpen = true
                        }
                        .padding(horizontal = 2.dp, vertical = 4.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Art(t.id, 34.dp)
                    Column(Modifier.weight(1f)) {
                        Text(
                            t.title,
                            style = McType.bodySm.copy(fontSize = 13.sp, fontWeight = FontWeight.Medium),
                            color = mc.fg,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                        )
                        Text(
                            error ?: t.artist,
                            style = McType.mono9,
                            color = if (error != null) mc.err else mc.dim,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                        )
                    }
                }
            }

            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(0.dp),
            ) {
                IconBtn(
                    AppIcons.SkipBack,
                    { vm.engine.prev() },
                    size = 38.dp,
                    tint = mc.fg,
                    contentDescription = "Previous track",
                )
                Box(
                    Modifier
                        .size(38.dp)
                        .shadow(
                            10.dp,
                            CircleShape,
                            ambientColor = mc.accent.copy(alpha = 0.28f),
                            spotColor = mc.accent.copy(alpha = 0.28f),
                        )
                        .clip(CircleShape)
                        .background(mc.accent)
                        .clickable { vm.engine.toggle() },
                    contentAlignment = Alignment.Center,
                ) {
                    Icon(
                        if (vm.engine.playing) AppIcons.Pause else AppIcons.Play,
                        if (vm.engine.playing) "Pause" else "Play",
                        Modifier.size(21.dp),
                        tint = mc.accentFg,
                    )
                }
                IconBtn(
                    AppIcons.SkipForward,
                    { vm.engine.next() },
                    size = 38.dp,
                    tint = mc.fg,
                    contentDescription = "Next track",
                )
            }

            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(0.dp),
            ) {
                IconBtn(
                    AppIcons.ListMusic,
                    { vm.queueOpen = true },
                    size = 38.dp,
                    tint = mc.dim,
                    contentDescription = "Queue",
                )
                Box {
                    IconBtn(
                        AppIcons.MoreHorizontal,
                        { moreOpen = true },
                        size = 38.dp,
                        tint = mc.dim,
                        contentDescription = "More player actions",
                    )
                    DropdownMenu(
                        expanded = moreOpen,
                        onDismissRequest = { moreOpen = false },
                        containerColor = mc.bg2,
                    ) {
                        DropdownMenuItem(
                            text = { Text("Open player", style = McType.bodySm, color = mc.fg) },
                            leadingIcon = { Icon(AppIcons.ChevronRight, null, Modifier.size(18.dp), tint = mc.dim) },
                            onClick = { moreOpen = false; vm.playerOpen = true },
                        )
                        DropdownMenuItem(
                            text = { Text("Queue", style = McType.bodySm, color = mc.fg) },
                            leadingIcon = { Icon(AppIcons.ListMusic, null, Modifier.size(18.dp), tint = mc.dim) },
                            onClick = { moreOpen = false; vm.queueOpen = true },
                        )
                        DropdownMenuItem(
                            text = { Text("Sleep timer", style = McType.bodySm, color = mc.fg) },
                            leadingIcon = { Icon(AppIcons.Clock, null, Modifier.size(18.dp), tint = mc.dim) },
                            onClick = { moreOpen = false; vm.sleepOpen = true },
                        )
                        DropdownMenuItem(
                            text = { Text("Track info", style = McType.bodySm, color = mc.fg) },
                            leadingIcon = { Icon(AppIcons.Info, null, Modifier.size(18.dp), tint = mc.dim) },
                            onClick = { moreOpen = false; vm.openInfo(t) },
                        )
                    }
                }
            }
        }
    }
}

/* ── tab bar ────────────────────────────────────────────────────────────── */

private data class NavItem(val route: Route, val label: String, val icon: ImageVector)

@Composable
private fun NavBar(vm: AppViewModel, modifier: Modifier = Modifier) {
    val mc = LocalMc.current
    val items = listOf(
        NavItem(Route.Home, "Home", AppIcons.Home),
        NavItem(Route.Search, "Search", AppIcons.Search),
        NavItem(Route.Library, "Library", AppIcons.Library),
        NavItem(Route.Downloads, "Downloads", AppIcons.Download),
        NavItem(Route.Settings, "Settings", AppIcons.Settings),
    )

    Box(
        modifier
            .fillMaxWidth()
            .navigationBarsPadding()
            .padding(horizontal = 10.dp, vertical = 10.dp),
    ) {
        Row(
            Modifier
                .fillMaxWidth()
                .height(D.tab)
                .glass(RoundedCornerShape(29.dp))
                .padding(4.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            items.forEach { item ->
                val active = isActive(vm.route, item.route)
                val tint by animateColorAsState(
                    targetValue = if (active) mc.fg else mc.dim,
                    animationSpec = tween(220),
                    label = "nav tint",
                )
                Column(
                    Modifier
                        .weight(1f)
                        .fillMaxHeight()
                        .clip(RoundedCornerShape(22.dp))
                        .background(if (active) mc.accentSoft else Color.Transparent)
                        .clickable { vm.navigate(item.route, push = false) },
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center,
                ) {
                    Icon(item.icon, null, Modifier.size(20.dp), tint = tint)
                    Spacer(Modifier.height(2.dp))
                    Text(
                        item.label.uppercase(),
                        style = McType.mono9.copy(fontSize = 9.sp, letterSpacing = 0.06.em),
                        color = if (active) mc.accent else mc.dim2,
                        maxLines = 1,
                        overflow = TextOverflow.Clip,
                    )
                }
            }
        }
    }
}


private fun isActive(current: Route, item: Route): Boolean = when (item) {
    Route.Home -> current == Route.Home
    Route.Search -> current == Route.Search
    Route.Library -> current is Route.Library || current is Route.Album || current is Route.Artist
    Route.Likes -> current == Route.Likes
    Route.Downloads -> current == Route.Downloads
    Route.Playlists -> current == Route.Playlists || current is Route.Playlist
    Route.Requests -> current == Route.Requests
    Route.Settings -> current == Route.Settings
    Route.Admin -> current == Route.Admin
    else -> false
}

/* ── queue sheet ────────────────────────────────────────────────────────── */

@Composable
private fun QueueSheet(vm: AppViewModel) {
    val mc = LocalMc.current
    val engine = vm.engine
    val current = engine.current
    val upcoming = engine.queue.drop(engine.index + 1)
    val haptics = LocalHapticFeedback.current
    val density = LocalDensity.current
    val rowHeightPx = with(density) { 46.dp.toPx() }
    val listState = rememberLazyListState()

    var order by remember { mutableStateOf(upcoming) }
    var draggingIndex by remember { mutableStateOf<Int?>(null) }
    var dragOffset by remember { mutableStateOf(0f) }

    LaunchedEffect(upcoming.map { it.id }) {
        if (draggingIndex == null) order = upcoming
    }

    // Use queue positions, not track ids: the same track may appear twice.
    fun removeQueuedAt(upcomingIndex: Int) {
        engine.removeAt(engine.index + 1 + upcomingIndex)
    }

    fun jumpTo(upcomingIndex: Int) {
        engine.jumpTo(engine.index + 1 + upcomingIndex)
        vm.queueOpen = false
    }

    McSheet(onDismiss = { vm.queueOpen = false }, title = "Queue") {
        if (current == null) {
            Text("Queue is empty", style = McType.bodySm, color = mc.dim)
            return@McSheet
        }
        Text("NOW PLAYING", style = McType.mono9, color = mc.dim2)
        QueueRow(current) { vm.queueOpen = false; vm.playerOpen = true }

        Row(
            Modifier.fillMaxWidth().padding(top = 16.dp, bottom = 2.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text("Next up (${upcoming.size})", style = McType.mono9, color = mc.dim2)
            Spacer(Modifier.weight(1f))
            if (upcoming.isNotEmpty()) {
                McButton("Clear next", { engine.clearUpcoming() }, small = true, ghost = true)
            }
        }
        if (upcoming.isEmpty()) {
            Text(
                "Nothing queued — long-press a track to add more.",
                style = McType.bodyXs,
                color = mc.dim2,
                modifier = Modifier.padding(top = 6.dp),
            )
            return@McSheet
        }

        Text(
            "Swipe left to remove · hold and drag to reorder",
            style = McType.mono10,
            color = mc.dim2,
            modifier = Modifier.padding(bottom = 6.dp),
        )

        LazyColumn(
            state = listState,
            modifier = Modifier.fillMaxWidth().heightIn(max = 420.dp),
        ) {
            itemsIndexed(order, key = { i, t -> "${t.id}:$i" }) { i, track ->
                val isDragging = draggingIndex == i
                Box(
                    Modifier
                        .fillMaxWidth()
                        .zIndex(if (isDragging) 1f else 0f)
                        .graphicsLayer {
                            translationY = if (isDragging) dragOffset else 0f
                            shadowElevation = if (isDragging) 12f else 0f
                        }
                        .pointerInput(Unit) {
                            detectDragGesturesAfterLongPress(
                                onDragStart = {
                                    draggingIndex = i
                                    dragOffset = 0f
                                    haptics.performHapticFeedback(HapticFeedbackType.LongPress)
                                },
                                onDragCancel = {
                                    draggingIndex = null
                                    dragOffset = 0f
                                },
                                onDragEnd = {
                                    if (draggingIndex != null) engine.setUpcoming(order)
                                    draggingIndex = null
                                    dragOffset = 0f
                                },
                                onDrag = { change, amount ->
                                    change.consume()
                                    val from = draggingIndex ?: return@detectDragGesturesAfterLongPress
                                    dragOffset += amount.y
                                    val target = (from + (dragOffset / rowHeightPx).roundToInt())
                                        .coerceIn(0, order.lastIndex)
                                    if (target != from) {
                                        order = order.toMutableList().apply {
                                            add(target, removeAt(from))
                                        }
                                        draggingIndex = target
                                        dragOffset -= (target - from) * rowHeightPx
                                        haptics.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                                    }
                                },
                            )
                        },
                ) {
                    DismissibleQueueRow(
                        track = track,
                        onClick = { jumpTo(i) },
                        onRemove = { removeQueuedAt(i) },
                    )
                }
            }
        }
    }
}

@Composable
private fun DismissibleQueueRow(
    track: Track,
    onClick: () -> Unit,
    onRemove: () -> Unit,
) {
    val mc = LocalMc.current
    val dismissState = rememberSwipeToDismissBoxState(
        confirmValueChange = { value ->
            if (value == SwipeToDismissBoxValue.EndToStart) {
                onRemove()
                true
            } else {
                false
            }
        },
        positionalThreshold = { it * 0.35f },
    )
    SwipeToDismissBox(
        state = dismissState,
        enableDismissFromStartToEnd = false,
        backgroundContent = {
            Box(
                Modifier
                    .fillMaxSize()
                    .clip(RoundedCornerShape(D.r2))
                    .background(mc.err.copy(alpha = 0.16f))
                    .padding(horizontal = 14.dp),
                contentAlignment = Alignment.CenterEnd,
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                ) {
                    Text("Remove", style = McType.mono10, color = mc.err)
                    Icon(AppIcons.Trash, null, Modifier.size(15.dp), tint = mc.err)
                }
            }
        },
    ) {
        Box(Modifier.fillMaxWidth().background(mc.bg2)) {
            QueueRow(track, onClick)
        }
    }
}

@Composable
private fun QueueRow(t: Track, onClick: (() -> Unit)? = null) {
    val mc = LocalMc.current
    Row(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(D.r2))
            .then(if (onClick != null) Modifier.clickable(onClick = onClick) else Modifier)
            .padding(horizontal = 4.dp, vertical = 6.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Art(t.id, 34.dp)
        Column(Modifier.weight(1f)) {
            Text(t.title, style = McType.bodySm, color = mc.fg, maxLines = 1, overflow = TextOverflow.Ellipsis)
            ArtistCredits(t, McType.mono10, mc.dim)
        }
        Icon(AppIcons.ListMusic, null, Modifier.size(14.dp), tint = mc.dim2)
    }
}

/* ── collection (album / artist / playlist) long-press menu ─────────────── */

@Composable
private fun CollectionMenuSheet(vm: AppViewModel, menu: CollectionMenu) {
    val mc = LocalMc.current
    val kind = menu.kind.lowercase()
    McSheet(onDismiss = vm::closeCollectionMenu, title = menu.title) {
        Row(
            Modifier.fillMaxWidth().padding(bottom = 10.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Art(menu.coverId ?: menu.tracks.first().id, 56.dp)
            Column(Modifier.weight(1f)) {
                if (menu.subtitle.isNotBlank()) {
                    Text(menu.subtitle, style = McType.bodyXs, color = mc.dim, maxLines = 1, overflow = TextOverflow.Ellipsis)
                }
                Text(
                    "${menu.tracks.size} tracks · ${kind.replaceFirstChar { it.uppercase() }}",
                    style = McType.mono10,
                    color = mc.dim2,
                )
            }
        }
        Column(Modifier.heightIn(max = 420.dp).verticalScroll(rememberScrollState())) {
            MenuRow(AppIcons.Play, "Play") { vm.playCollection(menu.tracks) }
            MenuRow(AppIcons.Shuffle, "Shuffle play") { vm.shuffleCollection(menu.tracks) }
            MenuRow(AppIcons.ListMusic, "Play next") { vm.queueCollection(menu.tracks, next = true) }
            MenuRow(AppIcons.Plus, "Add to queue") { vm.queueCollection(menu.tracks, next = false) }
            MenuRow(AppIcons.Radio, "Start radio") {
                vm.closeCollectionMenu()
                vm.startRadio(menu.tracks.first())
            }
            MenuRow(AppIcons.Download, "Download for offline") {
                vm.downloadAll(menu.tracks)
                vm.closeCollectionMenu()
            }
            if (kind == "playlist" || kind == "likes") {
                MenuRow(AppIcons.CloudDownload, "Queue on server") {
                    vm.queueServerDownloads(kind, menu.playlistId)
                    vm.closeCollectionMenu()
                }
            }
            when (kind) {
                "album" -> MenuRow(AppIcons.Disc, "Go to album") {
                    vm.closeCollectionMenu()
                    vm.navigate(Route.Album(menu.title))
                }
                "artist" -> MenuRow(AppIcons.Users, "Go to artist") {
                    vm.closeCollectionMenu()
                    vm.navigate(Route.Artist(menu.title))
                }
                "playlist" -> menu.playlistId?.let { id ->
                    MenuRow(AppIcons.ListMusic, "Open playlist") {
                        vm.closeCollectionMenu()
                        vm.navigate(Route.Playlist(id))
                    }
                }
                "likes" -> MenuRow(AppIcons.Heart, "Open liked songs") {
                    vm.closeCollectionMenu()
                    vm.navigate(Route.Likes)
                }
            }
        }
    }
}

/* ── GitHub update ─────────────────────────────────────────────────────── */

@Composable
private fun UpdateDialog(vm: AppViewModel) {
    val mc = LocalMc.current
    val info = vm.updateInfo ?: return
    AlertDialog(
        onDismissRequest = vm::dismissUpdate,
        containerColor = mc.bg2,
        title = { Text("Update available", style = McType.h3, color = mc.fg) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(
                    "mcmusic ${info.version} is ready. You're on ${BuildConfig.VERSION_NAME}.",
                    style = McType.bodySm,
                    color = mc.dim,
                )
                if (info.notes.isNotBlank()) {
                    Text(
                        info.notes.trim().take(320),
                        style = McType.bodyXs,
                        color = mc.dim2,
                        maxLines = 6,
                        overflow = TextOverflow.Ellipsis,
                    )
                }
                if (vm.updateDownloading) {
                    Text(
                        if (vm.updateVerifying) "Download complete · verifying…"
                        else "Downloading from GitHub… ${vm.updateProgress}%",
                        style = McType.mono10,
                        color = mc.accent,
                    )
                    if (vm.updateVerifying) {
                        LinearProgressIndicator(
                            modifier = Modifier.fillMaxWidth().height(4.dp),
                            color = mc.accent,
                            trackColor = mc.line,
                        )
                    } else {
                        LinearProgressIndicator(
                            progress = { vm.updateProgress / 100f },
                            modifier = Modifier.fillMaxWidth().height(4.dp),
                            color = mc.accent,
                            trackColor = mc.line,
                        )
                    }
                } else if (info.size > 0) {
                    Text(fmtBytes(info.size), style = McType.mono10, color = mc.dim2)
                }
                Text(
                    "The download is checked against GitHub's SHA-256 and the mcmusic package before the installer opens.",
                    style = McType.bodyXs,
                    color = mc.dim2,
                )
            }
        },
        confirmButton = {
            McButton(
                if (vm.updateDownloading) "Downloading…" else "Update now",
                { vm.installUpdate() },
                solid = true,
                enabled = !vm.updateDownloading,
                leading = AppIcons.Download,
            )
        },
        dismissButton = {
            Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                McButton(
                    "Skip",
                    vm::skipUpdate,
                    ghost = true,
                    small = true,
                    enabled = !vm.updateDownloading,
                )
                McButton(
                    "Later",
                    vm::dismissUpdate,
                    ghost = true,
                    small = true,
                    enabled = !vm.updateDownloading,
                )
            }
        },
    )
}

/* ── sleep timer ────────────────────────────────────────────────────────── */

@Composable
private fun SleepSheet(vm: AppViewModel) {
    val mc = LocalMc.current
    val left = vm.engine.sleepLeft
    McSheet(onDismiss = { vm.sleepOpen = false }, title = "Sleep timer") {
        Text(
            if (left != null) "Playback pauses in $left minute${if (left == 1) "" else "s"}."
            else "Stop the music after a while, without reaching for the phone.",
            style = McType.bodySm,
            color = if (left != null) mc.accent else mc.dim,
        )
        Row(
            Modifier.fillMaxWidth().padding(top = 16.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            listOf(15, 30, 60).forEach { minutes ->
                McButton(
                    "${minutes}m",
                    { vm.engine.setSleep(minutes); vm.sleepOpen = false },
                    small = true,
                    ghost = true,
                )
            }
        }
        if (left != null) {
            Spacer(Modifier.height(10.dp))
            McButton(
                "Turn it off",
                { vm.engine.setSleep(0); vm.sleepOpen = false },
                small = true,
                ghost = true,
            )
        }
    }
}

/* ── track menu ─────────────────────────────────────────────────────────── */

@Composable
private fun MenuSheet(vm: AppViewModel, t: Track) {
    McSheet(onDismiss = vm::closeTrackMenu, title = t.title) {
        Column(Modifier.verticalScroll(rememberScrollState())) {
            MenuRow(AppIcons.ListMusic, "Play next") {
                vm.closeTrackMenu()
                vm.queueNext(t)
            }
            MenuRow(AppIcons.Plus, "Add to queue") {
                vm.closeTrackMenu()
                vm.queueAdd(t)
            }
            MenuRow(AppIcons.FolderPlus, "Add to playlist…") {
                vm.closeTrackMenu()
                vm.openAddToPlaylist(t)
            }
            MenuRow(AppIcons.Radio, "Start radio") {
                vm.closeTrackMenu()
                vm.startRadio(t)
            }
            MenuRow(
                AppIcons.Clock,
                vm.engine.sleepLeft?.let { "Sleep timer · ${it} min left" } ?: "Sleep timer",
            ) {
                vm.closeTrackMenu()
                vm.sleepOpen = true
            }
            if (t.album.isNotBlank()) {
                MenuRow(AppIcons.Disc, "Go to album") {
                    vm.closeTrackMenu()
                    vm.navigate(Route.Album(t.album))
                }
            }
            if (t.artist.isNotBlank()) {
                MenuRow(AppIcons.Users, "Go to artist") {
                    vm.closeTrackMenu()
                    vm.navigate(Route.Artist(t.artist))
                }
            }
            MenuRow(
                AppIcons.Heart,
                if (t.liked) "Remove from liked" else "Like",
            ) {
                vm.closeTrackMenu()
                vm.toggleLike(t)
            }
            MenuRow(AppIcons.Info, "Track info") {
                vm.closeTrackMenu()
                vm.openInfo(t)
            }
            if (vm.isDownloaded(t.id)) {
                MenuRow(AppIcons.Trash, "Remove download") {
                    vm.closeTrackMenu()
                    vm.removeDownload(t.id)
                }
            } else {
                MenuRow(AppIcons.Download, "Download for offline") {
                    vm.closeTrackMenu()
                    vm.downloadTrack(t)
                }
            }
            vm.menuPlaylistId?.let { pid ->
                MenuRow(AppIcons.Trash, "Remove from playlist", danger = true) {
                    vm.closeTrackMenu()
                    vm.removeFromPlaylist(pid, t)
                }
            }
            if (vm.me?.isAdmin == true) {
                MenuRow(
                    AppIcons.Alert,
                    if (t.explicit) "Mark as clean" else "Mark as explicit",
                ) {
                    vm.closeTrackMenu()
                    vm.toggleExplicit(t)
                }
            }
        }
    }
}

/* ── track info ─────────────────────────────────────────────────────────── */

@Composable
private fun InfoSheet(vm: AppViewModel, t: Track) {
    val mc = LocalMc.current
    val context = LocalContext.current
    McSheet(onDismiss = vm::closeInfo, title = "Track info") {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Art(t.id, 64.dp)
            Column {
                Text(t.title, style = McType.bodySm.copy(fontWeight = FontWeight.Medium), color = mc.fg)
                Text(
                    listOfNotNull(t.artist.ifBlank { null }, t.album.ifBlank { null }).joinToString(" · "),
                    style = McType.bodyXs,
                    color = mc.dim2,
                )
            }
        }
        Column(Modifier.padding(top = 16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            kv("Length", fmtTime(t.duration))
            kv("Track", if (t.trackNo > 0) t.trackNo.toString() else "—")
            kv("Year", t.year.ifBlank { "—" })
            kv("Genre", t.genre.ifBlank { "—" })
            kv("Explicit", if (t.explicit) "Yes" else "No")
            t.ytChannel?.let { kv("Channel", it) }
            t.ytLikes?.let { kv("YT likes", fmtCount(it)) }
            t.ytViews?.let { kv("YT views", fmtCount(it)) }
            t.ytDate?.let { kv("Uploaded", it) }
        }
        if (t.ytId != null) {
            Spacer(Modifier.height(14.dp))
            McButton(
                "Open on YouTube",
                {
                    runCatching {
                        context.startActivity(
                            Intent(Intent.ACTION_VIEW, Uri.parse("https://www.youtube.com/watch?v=${t.ytId}"))
                        )
                    }
                },
                small = true,
                leading = AppIcons.ArrowUpRight,
            )
        }
    }
}

@Composable
private fun kv(key: String, value: String) {
    val mc = LocalMc.current
    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        Text(key.uppercase(), style = McType.mono9, color = mc.dim2, modifier = Modifier.width(96.dp))
        Text(value, style = McType.bodySm, color = mc.fg)
    }
}

/* ── add to playlist / create playlist ──────────────────────────────────── */

@Composable
private fun AddToPlaylistSheet(vm: AppViewModel, t: Track) {
    val mc = LocalMc.current
    var name by remember { mutableStateOf("") }
    McSheet(onDismiss = vm::closeAddToPlaylist, title = "Add to playlist") {
        Column(Modifier.verticalScroll(rememberScrollState())) {
            vm.playlists.forEach { p ->
                Row(
                    Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(D.r2))
                        .clickable { vm.addToPlaylist(p.id, t) }
                        .padding(vertical = 6.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    Art(p.coverId, 34.dp)
                    Column(Modifier.weight(1f)) {
                        Text(p.name, style = McType.bodySm, color = mc.fg)
                        Text("${p.n} tracks", style = McType.mono10, color = mc.dim2)
                    }
                }
            }
            if (vm.playlists.isEmpty()) {
                Text("No playlists yet — name one below.", style = McType.bodyXs, color = mc.dim2)
            }
            Spacer(Modifier.height(14.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                Box(Modifier.weight(1f)) {
                    McField(name, { name = it }, "New playlist name")
                }
                McButton("Create", { vm.createPlaylist(name, t) }, small = true, enabled = name.isNotBlank())
            }
        }
    }
}

@Composable
private fun CreatePlaylistSheet(vm: AppViewModel) {
    var name by remember { mutableStateOf("") }
    McSheet(onDismiss = { vm.createPlaylistOpen = false }, title = "New playlist") {
        McField(name, { name = it }, "Playlist name")
        Spacer(Modifier.height(12.dp))
        McButton(
            "Create",
            { vm.createPlaylist(name) },
            solid = true,
            enabled = name.isNotBlank(),
        )
    }
}
