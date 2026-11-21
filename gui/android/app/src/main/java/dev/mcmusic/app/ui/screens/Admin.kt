package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
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
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Account
import dev.mcmusic.app.data.AdminStats
import dev.mcmusic.app.data.AdminUser
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.DownloadRequest
import dev.mcmusic.app.data.InviteCode
import dev.mcmusic.app.ui.Danger
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.ErrorLine
import dev.mcmusic.app.ui.GhostButton
import dev.mcmusic.app.ui.Loading
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.Muted
import dev.mcmusic.app.ui.PrimaryButton
import dev.mcmusic.app.ui.ScreenBack
import dev.mcmusic.app.ui.SectionLabel
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface
import dev.mcmusic.app.ui.formatBytes
import kotlinx.coroutines.launch

/**
 * Admin parity with the web panel: server stats, user roles, invite codes and
 * the download request queue. Everything calls the same admin endpoints, so the
 * phone can do whatever the site can.
 */
@Composable
fun AdminScreen(onBack: () -> Unit) {
    val design = LocalDesign.current
    val scope = rememberCoroutineScope()
    var tab by remember { mutableIntStateOf(0) }
    var reload by remember { mutableIntStateOf(0) }
    var error by remember { mutableStateOf<String?>(null) }
    var notice by remember { mutableStateOf<String?>(null) }
    var stats by remember { mutableStateOf<AdminStats?>(null) }
    var users by remember { mutableStateOf<List<AdminUser>?>(null) }
    var invites by remember { mutableStateOf<List<InviteCode>?>(null) }
    var requests by remember { mutableStateOf<List<DownloadRequest>?>(null) }
    var inviteUses by remember { mutableStateOf("1") }
    var inviteHours by remember { mutableStateOf("24") }
    var inviteNote by remember { mutableStateOf("") }
    var lastCode by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(reload, tab) {
        when (tab) {
            0 -> Api.adminStats().fold(onSuccess = { stats = it }, onFailure = { error = it.message ?: "could not load stats" })
            1 -> Api.adminUsers().fold(onSuccess = { users = it }, onFailure = { error = it.message ?: "could not load users" })
            2 -> Api.adminInvites().fold(onSuccess = { invites = it }, onFailure = { error = it.message ?: "could not load invites" })
            3 -> Api.adminRequests().fold(onSuccess = { requests = it }, onFailure = { error = it.message ?: "could not load the queue" })
        }
    }

    LazyColumn(
        contentPadding = PaddingValues(design.screenPadding, 10.dp, design.screenPadding, 32.dp),
        verticalArrangement = Arrangement.spacedBy(9.dp),
    ) {
        item { ScreenBack(onBack = onBack) }
        item { ScreenTitle("Admin", Account.me?.username ?: "server") }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                listOf("Overview", "Users", "Invites", "Queue").forEachIndexed { index, label ->
                    val selected = tab == index
                    Box(
                        Modifier.clip(RoundedCornerShape(7.dp))
                            .then(if (selected) Modifier.mcSurface(RoundedCornerShape(7.dp)) else Modifier)
                            .clickable { tab = index; error = null }
                            .padding(horizontal = 10.dp, vertical = 7.dp),
                    ) {
                        Text(
                            label,
                            color = if (selected) design.fg else design.dim,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Medium,
                        )
                    }
                }
            }
        }
        error?.let { item { ErrorLine(it) } }
        notice?.let { item { Muted(notice!!) } }

        when (tab) {
            0 -> {
                val s = stats
                if (s == null) {
                    item { Loading("Loading stats…") }
                } else {
                    item { SectionLabel("Library") }
                    item { StatRow("Tracks", "${s.tracks}", "Albums", "${s.albums}") }
                    item { StatRow("Playlists", "${s.playlists}", "Plays", "${s.plays}") }
                    item { SectionLabel("People") }
                    item { StatRow("Users", "${s.users}", "Admins", "${s.admins}") }
                    item { StatRow("Rooms", "${s.rooms}", "Uptime", "${s.uptime / 3600}h") }
                    item { SectionLabel("Downloads") }
                    item { StatRow("Pending", "${s.pending}", "Running", "${s.running}") }
                    item { StatRow("Approved", "${s.approved}", "Done", "${s.done}") }
                    item { StatRow("Failed", "${s.failed}", "Queue", "${s.queue}") }
                    item { SectionLabel("Storage") }
                    item { StatRow("Music", formatBytes(s.musicBytes), "Free", formatBytes(s.diskFree)) }
                    item { Muted("Disk total ${formatBytes(s.diskTotal)}") }
                    item {
                        Row(Modifier.padding(top = 4.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            GhostButton("Rescan library") {
                                scope.launch {
                                    Api.adminScan().fold(
                                        onSuccess = { (t, a) ->
                                            notice = "Scanned $t tracks and $a albums."
                                            reload++
                                        },
                                        onFailure = { error = it.message ?: "scan failed" },
                                    )
                                }
                            }
                            GhostButton("Refresh") { reload++ }
                        }
                    }
                }
            }
            1 -> {
                val list = users
                if (list == null) {
                    item { Loading("Loading users…") }
                } else {
                    item { SectionLabel("Users", Modifier) { GhostButton("Refresh") { reload++ } } }
                    items(list, key = { it.id }) { user ->
                        Column(Modifier.fillMaxWidth().mcSurface(RoundedCornerShape(8.dp)).padding(11.dp)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Column(Modifier.weight(1f)) {
                                    Text(
                                        user.username + if (user.isAdmin) "  · admin" else "",
                                        color = if (user.isAdmin) design.accent else design.fg,
                                        fontSize = 14.sp,
                                        fontWeight = FontWeight.Medium,
                                        maxLines = 1,
                                        overflow = TextOverflow.Ellipsis,
                                    )
                                    Muted(
                                        "${user.plays} plays · ${user.likes} likes · ${user.playlists} playlists" +
                                            (user.email?.let { " · $it" } ?: ""),
                                        size = 10,
                                    )
                                }
                                if (user.id != Account.me?.id) {
                                    GhostButton(if (user.isAdmin) "Demote" else "Promote") {
                                        scope.launch {
                                            Api.adminSetRole(user.id, !user.isAdmin).fold(
                                                onSuccess = { reload++ },
                                                onFailure = { error = it.message ?: "could not change the role" },
                                            )
                                        }
                                    }
                                    Box(Modifier.padding(start = 6.dp)) {
                                        GhostButton("Delete", danger = true) {
                                            scope.launch {
                                                Api.adminDeleteUser(user.id).fold(
                                                    onSuccess = { reload++ },
                                                    onFailure = { error = it.message ?: "could not delete the user" },
                                                )
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            2 -> {
                item { SectionLabel("Create invite") }
                item {
                    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                            Box(Modifier.weight(1f)) {
                                dev.mcmusic.app.ui.McField(inviteUses, { inviteUses = it }, "Uses")
                            }
                            Box(Modifier.weight(1f)) {
                                dev.mcmusic.app.ui.McField(inviteHours, { inviteHours = it }, "Hours")
                            }
                        }
                        dev.mcmusic.app.ui.McField(inviteNote, { inviteNote = it }, "Note (optional)")
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            PrimaryButton("Create") {
                                scope.launch {
                                    Api.adminCreateInvite(
                                        inviteUses.toIntOrNull() ?: 1,
                                        inviteHours.toIntOrNull() ?: 24,
                                        inviteNote.trim(),
                                    ).fold(
                                        onSuccess = { lastCode = it; reload++ },
                                        onFailure = { error = it.message ?: "could not create the invite" },
                                    )
                                }
                            }
                            GhostButton("Refresh") { reload++ }
                        }
                        lastCode?.let { Muted("New code: $it", size = 12) }
                    }
                }
                val list = invites
                if (list == null) {
                    item { Loading("Loading invites…") }
                } else if (list.isEmpty()) {
                    item { EmptyState(Lucide.Lock, "No invite codes", "Create one above to let someone sign up.") }
                } else {
                    items(list, key = { it.id }) { code ->
                        Column(Modifier.fillMaxWidth().mcSurface(RoundedCornerShape(8.dp)).padding(11.dp)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Column(Modifier.weight(1f)) {
                                    Text(code.code, color = design.fg, fontSize = 14.sp, fontWeight = FontWeight.Medium)
                                    Muted(
                                        "${code.uses}/${code.maxUses} uses" +
                                            (code.note.takeIf { it.isNotBlank() }?.let { " · $it" } ?: "") +
                                            (code.usedBy.takeIf { it.isNotEmpty() }?.joinToString(", ")?.let { " · used by $it" } ?: ""),
                                        size = 10,
                                    )
                                }
                                GhostButton("Revoke", danger = true) {
                                    scope.launch {
                                        Api.adminRevokeInvite(code.id).fold(
                                            onSuccess = { reload++ },
                                            onFailure = { error = it.message ?: "could not revoke the code" },
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }
            else -> {
                item { SectionLabel("Download requests") { GhostButton("Refresh") { reload++ } } }
                val list = requests
                if (list == null) {
                    item { Loading("Loading queue…") }
                } else if (list.isEmpty()) {
                    item { EmptyState(Lucide.Download, "Queue is empty", "New requests appear here for approval.") }
                } else {
                    items(list, key = { it.id }) { request ->
                        Column(Modifier.fillMaxWidth().mcSurface(RoundedCornerShape(8.dp)).padding(11.dp)) {
                            Text(
                                request.url,
                                color = design.fg,
                                fontSize = 12.sp,
                                maxLines = 2,
                                overflow = TextOverflow.Ellipsis,
                            )
                            Muted(
                                "${request.username} · ${request.status}" +
                                    (if (request.running) " · running ${request.elapsed}s" else ""),
                                size = 10,
                            )
                            Row(
                                Modifier.padding(top = 6.dp),
                                horizontalArrangement = Arrangement.spacedBy(5.dp),
                            ) {
                                val actions = when (request.status) {
                                    "pending" -> listOf("approve", "reject")
                                    "approved" -> listOf("run", "reject")
                                    "running" -> listOf("cancel")
                                    "failed" -> listOf("retry", "delete")
                                    else -> listOf("delete")
                                }
                                actions.forEach { action ->
                                    GhostButton(action.replaceFirstChar { it.uppercase() }, danger = action == "delete" || action == "reject") {
                                        scope.launch {
                                            Api.adminRequestAction(request.id, action).fold(
                                                onSuccess = { reload++ },
                                                onFailure = { error = it.message ?: "could not $action the request" },
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun StatRow(left: String, leftValue: String, right: String, rightValue: String) {
    val design = LocalDesign.current
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        StatTile(left, leftValue, Modifier.weight(1f))
        StatTile(right, rightValue, Modifier.weight(1f))
    }
}

@Composable
private fun StatTile(label: String, value: String, modifier: Modifier = Modifier) {
    val design = LocalDesign.current
    Column(modifier.mcSurface(RoundedCornerShape(8.dp)).padding(11.dp)) {
        Text(label, color = design.dim, fontSize = 10.sp)
        Text(value, color = design.fg, fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
    }
}
