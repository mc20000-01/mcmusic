package dev.mcmusic.app.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import dev.mcmusic.app.AppViewModel
import dev.mcmusic.app.Route
import dev.mcmusic.app.data.InviteCode
import dev.mcmusic.app.data.RequestRow
import dev.mcmusic.app.ui.theme.D
import dev.mcmusic.app.ui.theme.LocalMc
import dev.mcmusic.app.ui.theme.McThemes
import dev.mcmusic.app.ui.theme.McType
import dev.mcmusic.app.ui.theme.paletteFor

/* ── playlists ──────────────────────────────────────────────────────────── */

@Composable
fun PlaylistsScreen(vm: AppViewModel) {
    val mc = LocalMc.current
    Column(Modifier.fillMaxSize()) {
        Row(
            Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text("Playlists", style = McType.h1Small, color = mc.fg)
            Spacer(Modifier.weight(1f))
            McButton(
                "New playlist",
                { vm.createPlaylistOpen = true },
                small = true,
                solid = true,
                leading = AppIcons.Plus,
            )
        }
        if (vm.playlists.isEmpty()) {
            EmptyState(
                "No playlists yet",
                "Create one and add songs from any track menu.",
                icon = AppIcons.ListMusic,
                actionLabel = "New playlist",
                onAction = { vm.createPlaylistOpen = true },
            )
        } else {
            LazyColumn(
                Modifier.fillMaxSize(),
                contentPadding = PaddingValues(start = 14.dp, end = 14.dp, bottom = 24.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                items(vm.playlists.chunked(2)) { row ->
                    Row(
                        Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(10.dp),
                    ) {
                        row.forEach { p ->
                            Box(Modifier.weight(1f)) {
                                PlaylistTile(
                                    p,
                                    onClick = { vm.navigate(Route.Playlist(p.id, p.name)) },
                                    onPlay = { vm.playPlaylist(p.id) },
                                    fillWidth = true,
                                )
                            }
                        }
                        if (row.size == 1) Spacer(Modifier.weight(1f))
                    }
                }
            }
        }
    }
}

@Composable
fun PlaylistScreen(vm: AppViewModel, id: Int) {
    val mc = LocalMc.current
    var renaming by remember { mutableStateOf(false) }
    var deleting by remember { mutableStateOf(false) }
    val tracks = vm.playlistTracks
    val playable = if (vm.settings.hideExplicit) tracks.filter { !it.explicit } else tracks

    if (renaming) {
        var name by remember { mutableStateOf(vm.playlistName) }
        McSheet(onDismiss = { renaming = false }, title = "Rename playlist") {
            McField(name, { name = it }, "Playlist name")
            Spacer(Modifier.height(12.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                McButton("Save", {
                    vm.renamePlaylist(id, name)
                    renaming = false
                }, solid = true, enabled = name.isNotBlank())
                McButton("Cancel", { renaming = false }, ghost = true)
            }
        }
    }

    if (deleting) {
        AlertDialog(
            onDismissRequest = { deleting = false },
            containerColor = mc.bg2,
            title = { Text("Delete playlist?", style = McType.h3, color = mc.fg) },
            text = {
                Text(
                    "\"${vm.playlistName}\" will be removed. This can't be undone.",
                    style = McType.bodySm,
                    color = mc.dim,
                )
            },
            confirmButton = {
                McButton("Delete", {
                    deleting = false
                    vm.deletePlaylist(id)
                }, danger = true)
            },
            dismissButton = {
                McButton("Cancel", { deleting = false }, ghost = true)
            },
        )
    }

    if (tracks.isEmpty()) {
        Column(Modifier.fillMaxSize().padding(14.dp)) {
            Text(vm.playlistName.ifBlank { "Playlist" }, style = McType.h1Small, color = mc.fg)
            EmptyState(
                "Empty playlist",
                "Use \"Add to playlist\" from a track menu.",
                icon = AppIcons.ListMusic,
            )
        }
        return
    }

    LazyColumn(
        Modifier.fillMaxSize(),
        contentPadding = PaddingValues(start = 14.dp, end = 14.dp, top = 10.dp, bottom = 28.dp),
    ) {
        item {
            Hero(
                coverId = tracks.firstOrNull()?.id,
                kicker = "Playlist",
                title = vm.playlistName,
                subs = listOf("${tracks.size} tracks", fmtTotal(tracks.sumOf { it.duration })),
            ) {
                McButton("Play", { vm.playList(playable, 0) }, solid = true, leading = AppIcons.Play)
                McButton("Shuffle", { vm.shufflePlay(playable) }, leading = AppIcons.Shuffle)
                McButton(
                    "Download",
                    { vm.downloadAll(playable) },
                    small = true,
                    ghost = true,
                    leading = AppIcons.Download,
                )
                McButton(
                    "Queue on server",
                    { vm.queueServerDownloads(if (vm.playlistName == "Faves") "faves" else "playlist", id) },
                    small = true,
                    ghost = true,
                    leading = AppIcons.CloudDownload,
                )
                McButton("Rename", { renaming = true }, small = true, ghost = true)
                McButton("Delete", { deleting = true }, small = true, danger = true)
            }
        }
        itemsIndexed(playable, key = { _, t -> t.id }) { index, track ->
            TrackRow(
                track = track,
                number = index,
                isCurrent = track.id == vm.engine.current?.id,
                onClick = { vm.playList(playable, index) },
                onLike = { vm.toggleLike(track) },
                onMore = { vm.openTrackMenu(track, id) },
            )
        }
    }
}

/* ── requests ───────────────────────────────────────────────────────────── */

@Composable
fun RequestsScreen(vm: AppViewModel) {
    val mc = LocalMc.current
    var url by remember { mutableStateOf("") }
    Column(Modifier.fillMaxSize()) {
        Column(Modifier.padding(horizontal = 14.dp)) {
            Text(
                "Request songs",
                style = McType.h1Small,
                color = mc.fg,
                modifier = Modifier.padding(bottom = 12.dp),
            )
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                Box(Modifier.weight(1f)) {
                    McField(
                        url,
                        { url = it },
                        "Paste a YouTube video or playlist link",
                        leading = AppIcons.Download,
                    )
                }
                McButton("Send", {
                    if (vm.addRequest(url)) url = ""
                }, solid = true, enabled = url.isNotBlank())
            }
            Spacer(Modifier.height(12.dp))
        }

        if (vm.requests.isEmpty()) {
            EmptyState(
                "No requests yet",
                "Paste a link above.",
                icon = AppIcons.Download,
            )
        } else {
            LazyColumn(
                Modifier.fillMaxSize(),
                contentPadding = PaddingValues(start = 14.dp, end = 14.dp, bottom = 24.dp),
                verticalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                items(vm.requests, key = { it.id }) { request ->
                    RequestRowView(vm, request)
                }
            }
        }
    }
}

@Composable
private fun RequestRowView(vm: AppViewModel, request: RequestRow) {
    val mc = LocalMc.current
    val statusColor = when (request.status) {
        "done" -> mc.ok
        "failed", "rejected", "cancelled" -> mc.err
        "running", "approved" -> mc.accent
        "pending" -> mc.warn
        else -> mc.dim
    }
    Column(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(D.r2))
            .background(mc.bg2)
            .border(1.dp, mc.line, RoundedCornerShape(D.r2))
            .padding(10.dp),
        verticalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(
                request.url,
                style = McType.mono10,
                color = mc.fg,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                modifier = Modifier.weight(1f),
            )
            StatusChip(request.status, statusColor)
        }
        Text(
            listOfNotNull(
                request.username?.ifBlank { null },
                request.created.takeIf { it > 0 }?.let {
                    java.text.DateFormat.getDateTimeInstance(
                        java.text.DateFormat.SHORT,
                        java.text.DateFormat.SHORT,
                    ).format(java.util.Date((it * 1000).toLong()))
                },
            ).joinToString(" · "),
            style = McType.mono9,
            color = mc.dim2,
        )
        if (vm.requestsAdmin) {
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                when (request.status) {
                    "pending", "failed" -> {
                        McButton("Approve", { vm.actRequest(request.id, "approve") }, small = true)
                        McButton(
                            "Reject",
                            { vm.actRequest(request.id, "reject") },
                            small = true,
                            ghost = true,
                        )
                    }
                    "approved", "running" -> {
                        McButton(
                            "Cancel",
                            { vm.cancelRequest(request) },
                            small = true,
                            danger = true,
                        )
                    }
                }
                Spacer(Modifier.weight(1f))
                McButton("Log", { vm.openRequestLog(request) }, small = true, ghost = true)
                if (request.status in listOf("failed", "done", "cancelled", "rejected")) {
                    McButton("Retry", { vm.retryRequest(request) }, small = true, ghost = true)
                }
                IconBtn(
                    AppIcons.Trash,
                    { vm.deleteRequest(request) },
                    size = 30.dp,
                    tint = mc.err,
                    contentDescription = "Delete request",
                )
            }
        }
    }
}

/* ── settings ───────────────────────────────────────────────────────────── */

@Composable
fun SettingsScreen(vm: AppViewModel) {
    val mc = LocalMc.current
    var passwordOpen by remember { mutableStateOf(false) }
    var emailOpen by remember { mutableStateOf(false) }
    var emailValue by remember { mutableStateOf("") }

    if (emailOpen) {
        McSheet(onDismiss = { emailOpen = false }, title = "Account email") {
            Text(
                "One-time password reset links are mailed here. It is never shown to other accounts.",
                style = McType.bodyXs,
                color = mc.dim2,
            )
            Spacer(Modifier.height(10.dp))
            McField(
                emailValue,
                { emailValue = it },
                "you@example.com",
                keyboardType = KeyboardType.Email,
            )
            Spacer(Modifier.height(12.dp))
            McButton(
                "Save",
                { vm.setEmail(emailValue) { emailOpen = false } },
                solid = true,
                enabled = emailValue.contains("@") && emailValue.contains("."),
            )
        }
    }

    if (passwordOpen) {
        var old by remember { mutableStateOf("") }
        var fresh by remember { mutableStateOf("") }
        McSheet(onDismiss = { passwordOpen = false }, title = "Change password") {
            McField(old, { old = it }, "Current password", password = true)
            Spacer(Modifier.height(8.dp))
            McField(fresh, { fresh = it }, "New password (6+ characters)", password = true)
            Spacer(Modifier.height(12.dp))
            McButton("Save", {
                vm.changePassword(old, fresh) { passwordOpen = false }
            }, solid = true, enabled = old.isNotBlank() && fresh.length >= 6)
        }
    }

    LazyColumn(
        Modifier.fillMaxSize(),
        contentPadding = PaddingValues(start = 14.dp, end = 14.dp, top = 10.dp, bottom = 30.dp),
    ) {
        item {
            Text(
                "Settings",
                style = McType.h1Small,
                color = mc.fg,
                modifier = Modifier.padding(bottom = 16.dp),
            )
        }

        /* appearance */
        item {
            Panel("Appearance") {
                Text(
                    "Theme",
                    style = McType.mono9,
                    color = mc.dim2,
                    modifier = Modifier.padding(start = 16.dp, top = 12.dp),
                )
                LazyRow(
                    Modifier.padding(horizontal = 16.dp, vertical = 10.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    items(McThemes) { key ->
                        val palette = paletteFor(key)
                        val selected = vm.settings.theme == key
                        Column(
                            Modifier
                                .width(74.dp)
                                .clip(RoundedCornerShape(D.r2))
                                .border(
                                    1.dp,
                                    if (selected) mc.accent else mc.line2,
                                    RoundedCornerShape(D.r2),
                                )
                                .clickable { vm.setSetting { it.copy(theme = key) } },
                        ) {
                            Box(
                                Modifier
                                    .fillMaxWidth()
                                    .height(36.dp)
                                    .background(palette.bg),
                            ) {
                                Box(
                                    Modifier
                                        .align(Alignment.BottomStart)
                                        .fillMaxWidth()
                                        .height(4.dp)
                                        .background(palette.accent),
                                )
                            }
                            Text(
                                key.replaceFirstChar { it.uppercase() },
                                style = McType.mono9,
                                color = if (selected) mc.fg else mc.dim,
                                textAlign = TextAlign.Center,
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .background(mc.bg)
                                    .padding(vertical = 4.dp),
                            )
                        }
                    }
                }
                Box(Modifier.fillMaxWidth().height(1.dp).background(mc.line))
                Text(
                    "Accent colour",
                    style = McType.mono9,
                    color = mc.dim2,
                    modifier = Modifier.padding(start = 16.dp, top = 12.dp),
                )
                Row(
                    Modifier
                        .fillMaxWidth()
                        .horizontalScroll(rememberScrollState())
                        .padding(horizontal = 16.dp, vertical = 10.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    listOf(
                        "#6366f1", "#3b82f6", "#8b5cf6", "#ec4899",
                        "#f97316", "#eab308", "#14b8a6", "#ef4444",
                    ).forEach { hex ->
                        val selected = vm.settings.accent.equals(hex, ignoreCase = true)
                        Box(
                            Modifier
                                .size(24.dp)
                                .clip(CircleShape)
                                .background(Color(android.graphics.Color.parseColor(hex)))
                                .border(
                                    2.dp,
                                    if (selected) mc.fg else Color.Transparent,
                                    CircleShape,
                                )
                                .clickable { vm.setSetting { it.copy(accent = hex) } },
                        )
                    }
                }
                Box(Modifier.fillMaxWidth().height(1.dp).background(mc.line))
                SettingRow(
                    "Density",
                    "Compact rows in song lists",
                ) {
                    Seg(
                        options = listOf("comfy" to "Comfy", "compact" to "Compact"),
                        selected = vm.settings.density,
                        onSelect = { value -> vm.setSetting { it.copy(density = value) } },
                    )
                }
                SettingRow("Show cover art", last = true) {
                    SwitchPill(vm.settings.covers) { value ->
                        vm.setSetting { it.copy(covers = value) }
                    }
                }
            }
        }

        /* playback */
        item {
            Panel("Playback") {
                SettingRow("Autoplay", "Keep playing similar songs when the queue runs out") {
                    SwitchPill(vm.settings.autoplay) { value ->
                        vm.setSetting { it.copy(autoplay = value) }
                    }
                }
                SettingRow("Hide explicit songs", "Uses the server's explicit flag") {
                    SwitchPill(vm.settings.hideExplicit) { value ->
                        vm.setSetting { it.copy(hideExplicit = value) }
                    }
                }
                SettingRow("Remember volume", last = true) {
                    SwitchPill(vm.settings.rememberVolume) { value ->
                        vm.setSetting { it.copy(rememberVolume = value) }
                    }
                }
            }
        }

        /* privacy */
        item {
            Panel("Privacy") {
                SettingRow(
                    "Private session",
                    "Plays are not recorded, so recommendations stay untouched",
                ) {
                    SwitchPill(vm.settings.privateSession) { value ->
                        vm.setSetting { it.copy(privateSession = value) }
                    }
                }
                SettingRow("Show YouTube stats", "Like counts next to songs", last = true) {
                    SwitchPill(vm.settings.ytStats) { value ->
                        vm.setSetting { it.copy(ytStats = value) }
                    }
                }
            }
        }

        /* listen along */
        item {
            val role = vm.roomRole
            val clipboard = androidx.compose.ui.platform.LocalClipboardManager.current
            Panel("Listen along") {
                if (role == null) {
                    SettingRow(
                        "Start a room",
                        "Share what you're playing; guests hear the same track and you keep control",
                    ) {
                        McButton(
                            "Start",
                            { vm.startRoom() },
                            small = true,
                            solid = true,
                            leading = AppIcons.Users,
                        )
                    }
                    Box(Modifier.padding(horizontal = 16.dp)) {
                        McField(
                            vm.roomJoinCode,
                            vm::onRoomJoinCodeChange,
                            "Room code or invite link",
                        )
                    }
                    Row(Modifier.padding(horizontal = 16.dp, vertical = 10.dp)) {
                        McButton(
                            "Join a room",
                            { vm.joinRoom() },
                            small = true,
                            enabled = vm.roomJoinCode.isNotBlank(),
                        )
                    }
                } else {
                    val st = vm.roomState
                    SettingRow(
                        if (role == "host") "Hosting · ${vm.roomCode}" else "Listening with ${vm.roomHostName}",
                        when {
                            st?.track != null -> "${st.track.title} · ${st.track.artist}"
                            st?.hostAway == true -> "Host is away"
                            role == "host" -> "Share the link so friends can follow"
                            else -> "Waiting for the first track"
                        },
                    ) {
                        McButton(
                            "Copy link",
                            { clipboard.setText(AnnotatedString(vm.roomLink())) },
                            small = true,
                            ghost = true,
                            leading = AppIcons.Link,
                        )
                    }
                    Row(
                        Modifier.padding(horizontal = 16.dp, vertical = 10.dp),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        McButton(
                            if (role == "host") "End room" else "Leave",
                            { vm.leaveRoom() },
                            small = true,
                            danger = true,
                        )
                        if (role == "host") {
                            McButton(
                                "Copy link",
                                { clipboard.setText(AnnotatedString(vm.roomLink())) },
                                small = true,
                                ghost = true,
                            )
                        }
                    }
                }
            }
        }

        /* rotur */
        item {
            val status = vm.roturStatus
            val linked = status?.optBoolean("linked") ?: false
            val configured = status?.optBoolean("configured") ?: false
            val roturName = status?.optString("rotur_username").orEmpty()
                .ifBlank { status?.optString("rotur_id").orEmpty() }
            if (vm.devices.isNotEmpty()) {
                val other = vm.devices.firstOrNull { it.active && !vm.isThisDevice(it) }
                val me = vm.devices.firstOrNull { vm.isThisDevice(it) }
                Panel("Devices") {
                    if (other != null) {
                        SettingRow(
                            "Playing on ${other.name}",
                            listOfNotNull(other.trackTitle, other.trackArtist)
                                .joinToString(" — ").ifBlank { "No track reported yet" },
                        ) {
                            if (me != null) {
                                McButton(
                                    "Play on this phone",
                                    { vm.activateDevice(me) },
                                    small = true,
                                    solid = true,
                                )
                            }
                        }
                    }
                    vm.devices.forEachIndexed { i, d ->
                        val mine = vm.isThisDevice(d)
                        SettingRow(
                            d.name,
                            when {
                                d.active && mine -> "This device · playing here"
                                d.active -> "Playing here"
                                mine -> "This device · not the active player"
                                d.paused -> "Paused"
                                else -> "Idle"
                            },
                            last = i == vm.devices.lastIndex,
                        ) {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(8.dp),
                            ) {
                                Box(
                                    Modifier
                                        .size(8.dp)
                                        .background(
                                            if (d.active) mc.accent else mc.dim2,
                                            androidx.compose.foundation.shape.CircleShape,
                                        )
                                )
                                if (mine && !d.active) {
                                    McButton("Play here", { vm.activateDevice(d) }, small = true, ghost = true)
                                }
                            }
                        }
                    }
                }
            }
            Panel("Rotur account") {
                SettingRow(
                    "RoturLink",
                    when {
                        !configured -> "RoturLink is not configured on this server"
                        linked -> "Linked as ${roturName.ifBlank { "your Rotur account" }}"
                        else -> "Not linked — sign in with Rotur on the web app"
                    },
                ) {
                    if (linked) {
                        McButton("Unlink", { vm.unlinkRotur() }, small = true, ghost = true)
                    } else {
                        StatusChip("web only", mc.dim2)
                    }
                }
                SettingRow(
                    "Share as Rotur activity",
                    "Puts what you're playing in your Rotur status",
                ) {
                    SwitchPill(vm.settings.roturActivity) { vm.setRoturActivity(it) }
                }
                SettingRow(
                    "Show room link in status",
                    "Adds the listen-along link to your Rotur status",
                    last = true,
                ) {
                    SwitchPill(vm.settings.showRoomUrl) { vm.setShowRoomUrl(it) }
                }
            }
        }

        /* account */
        item {
            Panel("Account") {
                SettingRow(
                    vm.me?.username ?: "User",
                    if (vm.me?.isAdmin == true) "Admin" else "Member",
                ) {
                    McButton("Change password", { passwordOpen = true }, small = true, ghost = true)
                }
                SettingRow(
                    "Email",
                    vm.me?.email ?: "Not set — needed for password resets",
                ) {
                    McButton(
                        if (vm.me?.email != null) "Change" else "Add",
                        {
                            emailValue = vm.me?.email.orEmpty()
                            emailOpen = true
                        },
                        small = true,
                        ghost = true,
                    )
                }
                SettingRow("Session", "Signed in with the mcmusic session cookie") {
                    McButton("Log out", { vm.logout() }, small = true, danger = true)
                }
                SettingRow("Server", vm.api.baseUrl, last = true) {
                    StatusChip("active", mc.ok)
                }
            }
        }

        /* admin */
        if (vm.me?.isAdmin == true) {
            item {
                Panel("Admin") {
                    SettingRow("Rescan library", "Pick up files added outside of requests") {
                        McButton("Rescan", { vm.rescan() }, small = true)
                    }
                    SettingRow("Manage users", "Stats and admin roles", last = true) {
                        McButton("Open", { vm.navigate(Route.Admin) }, small = true, ghost = true)
                    }
                }
            }
        }

        item {
            Panel("About") {
                SettingRow("mcmusic for Android", "Native client · no WebView") {
                    Text(
                        dev.mcmusic.app.BuildConfig.VERSION_NAME,
                        style = McType.mono9,
                        color = mc.dim2,
                    )
                }
                SettingRow("API", vm.api.baseUrl, last = true) {
                    Text(vm.api.baseUrl, style = McType.mono9, color = mc.dim2, maxLines = 1)
                }
            }
        }
    }
}

/* ── admin ──────────────────────────────────────────────────────────────── */

@Composable
fun AdminScreen(vm: AppViewModel) {
    val mc = LocalMc.current
    val stats = vm.adminStats
    var invUses by remember { mutableStateOf("1") }
    var invHours by remember { mutableStateOf("0") }
    var invNote by remember { mutableStateOf("") }
    LazyColumn(
        Modifier.fillMaxSize(),
        contentPadding = PaddingValues(start = 14.dp, end = 14.dp, top = 10.dp, bottom = 30.dp),
    ) {
        item {
            Row(
                Modifier.fillMaxWidth().padding(bottom = 14.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text("Admin", style = McType.h1Small, color = mc.fg)
                Spacer(Modifier.weight(1f))
                McButton("Rescan", { vm.rescan() }, small = true, leading = AppIcons.Refresh)
            }
        }
        if (stats != null) {
            item {
                val cells = listOf(
                    "Users" to stats.users.toString(),
                    "Admins" to stats.admins.toString(),
                    "Tracks" to stats.tracks.toString(),
                    "Albums" to stats.albums.toString(),
                    "Playlists" to stats.playlists.toString(),
                    "Plays" to stats.plays.toString(),
                    "Queue" to stats.queue.toString(),
                    "Rooms" to stats.rooms.toString(),
                    "Uptime" to fmtUptime(stats.uptime),
                    "Library" to fmtBytes(stats.musicBytes),
                    "Free disk" to fmtBytes(stats.diskFree),
                    "Disk size" to fmtBytes(stats.diskTotal),
                )
                Column(verticalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.padding(bottom = 18.dp)) {
                    cells.chunked(2).forEach { row ->
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            row.forEach { (label, value) ->
                                Column(
                                    Modifier
                                        .weight(1f)
                                        .clip(RoundedCornerShape(D.r2))
                                        .background(mc.bg2)
                                        .border(1.dp, mc.line, RoundedCornerShape(D.r2))
                                        .padding(horizontal = 12.dp, vertical = 10.dp),
                                ) {
                                    Text(value, style = McType.h3, color = mc.fg)
                                    Text(label.uppercase(), style = McType.mono9, color = mc.dim2)
                                }
                            }
                            if (row.size == 1) Spacer(Modifier.weight(1f))
                        }
                    }
                }
            }
        }
        item {
            Panel("Friend codes") {
                Row(
                    Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 10.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Box(Modifier.weight(1f)) {
                        McField(invUses, { v -> invUses = v.filter(Char::isDigit) }, "Uses")
                    }
                    Box(Modifier.weight(1f)) {
                        McField(invHours, { v -> invHours = v.filter(Char::isDigit) }, "Hours (0 = never)")
                    }
                }
                Box(Modifier.fillMaxWidth().padding(horizontal = 14.dp)) {
                    McField(invNote, { invNote = it }, "Note (optional)")
                }
                Row(Modifier.padding(14.dp)) {
                    McButton(
                        "Generate",
                        {
                            vm.createInvite(
                                invUses.toIntOrNull() ?: 1,
                                invHours.toIntOrNull() ?: 0,
                                invNote,
                            ) { invNote = "" }
                        },
                        small = true,
                        solid = true,
                        leading = AppIcons.Plus,
                    )
                }
            }
        }
        if (vm.adminInvites.isNotEmpty()) {
            item {
                Text(
                    "CODES",
                    style = McType.mono9,
                    color = mc.dim2,
                    modifier = Modifier.padding(top = 8.dp, bottom = 6.dp),
                )
            }
            items(vm.adminInvites, key = { "invite-${it.id}" }) { invite ->
                Row(
                    Modifier.fillMaxWidth().padding(vertical = 7.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Column(Modifier.weight(1f)) {
                        Text(invite.code, style = McType.bodySm, color = mc.fg)
                        Text(
                            listOfNotNull(
                                "${invite.uses}/${invite.maxUses} used",
                                when {
                                    invite.expires <= 0.0 -> "no expiry"
                                    invite.expired -> "expired"
                                    else -> "until " + java.text.DateFormat.getDateInstance(
                                        java.text.DateFormat.SHORT,
                                    ).format(java.util.Date((invite.expires * 1000).toLong()))
                                },
                                invite.note.ifBlank { null },
                                invite.usedBy.takeIf { it.isNotEmpty() }?.let { "used by ${it.joinToString(", ")}" },
                            ).joinToString(" · "),
                            style = McType.mono9,
                            color = mc.dim2,
                        )
                    }
                    if (invite.active) {
                        McButton("Revoke", { vm.revokeInvite(invite) }, small = true, ghost = true)
                    } else {
                        StatusChip("revoked", mc.dim2)
                    }
                }
                Box(Modifier.fillMaxWidth().height(1.dp).background(mc.line))
            }
        }
        item {
            Text("USERS", style = McType.mono9, color = mc.dim2, modifier = Modifier.padding(top = 14.dp, bottom = 8.dp))
        }
        items(vm.adminUsers, key = { "user-${it.id}" }) { user ->
            Row(
                Modifier
                    .fillMaxWidth()
                    .padding(vertical = 7.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                Box(
                    Modifier.size(30.dp).clip(CircleShape).background(mc.accent),
                    contentAlignment = Alignment.Center,
                ) {
                    Text(
                        user.username.take(1).uppercase(),
                        style = McType.mono9,
                        color = mc.accentFg,
                    )
                }
                Column(Modifier.weight(1f)) {
                    Text(user.username, style = McType.bodySm, color = mc.fg)
                    Text(
                        "${user.plays} plays · ${user.likes} likes · ${user.playlists} playlists",
                        style = McType.mono9,
                        color = mc.dim2,
                    )
                }
                if (user.isAdmin) StatusChip("admin", mc.accent)
                McButton(
                    if (user.isAdmin) "Demote" else "Promote",
                    { vm.toggleAdmin(user) },
                    small = true,
                    ghost = true,
                )
                if (user.id != vm.me?.id) {
                    IconBtn(
                        AppIcons.Trash,
                        { vm.deleteUser(user) },
                        size = 30.dp,
                        tint = mc.err,
                        contentDescription = "Delete ${user.username}",
                    )
                }
            }
            Box(Modifier.fillMaxWidth().height(1.dp).background(mc.line))
        }
        item {
            Text(
                "ROOMS",
                style = McType.mono9,
                color = mc.dim2,
                modifier = Modifier.padding(top = 20.dp, bottom = 8.dp),
            )
        }
        if (vm.adminRooms.isEmpty()) {
            item {
                Text("No live listen-along rooms.", style = McType.bodyXs, color = mc.dim2)
            }
        }
        items(vm.adminRooms, key = { "room-${it.code}" }) { room ->
            Row(
                Modifier.fillMaxWidth().padding(vertical = 7.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                Column(Modifier.weight(1f)) {
                    Text("${room.host} · ${room.code}", style = McType.bodySm, color = mc.fg)
                    Text(
                        listOfNotNull(
                            room.trackTitle?.let { title ->
                                room.trackArtist?.let { "$title · $it" } ?: title
                            },
                            if (room.playing) "playing" else "paused",
                            "${room.idle.toInt()}s idle",
                            if (room.away) "away" else null,
                        ).joinToString(" · "),
                        style = McType.mono9,
                        color = mc.dim2,
                    )
                }
                McButton("End", { vm.closeRoom(room) }, small = true, ghost = true)
            }
        }
    }
}
