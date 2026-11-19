package dev.mcmusic.app.ui.screens

import android.content.ClipData
import android.content.ClipboardManager
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import dev.mcmusic.app.data.Account
import dev.mcmusic.app.data.AdminStats
import dev.mcmusic.app.data.AdminUser
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.DownloadRequest
import dev.mcmusic.app.data.InviteCode
import dev.mcmusic.app.data.Prefs
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.LucideIcon
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.SectionLabel
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

private data class Pending(
    val title: String,
    val body: String,
    val label: String,
    val run: suspend () -> Result<Unit>,
)

@Composable
fun AdminScreen() {
    val design = LocalDesign.current
    val scope = rememberCoroutineScope()
    val context = LocalContext.current
    val me = Account.me

    var stats by remember { mutableStateOf<AdminStats?>(null) }
    var users by remember { mutableStateOf<List<AdminUser>>(emptyList()) }
    var invites by remember { mutableStateOf<List<InviteCode>>(emptyList()) }
    var requests by remember { mutableStateOf<List<DownloadRequest>>(emptyList()) }
    var message by remember { mutableStateOf<String?>(null) }
    var reload by remember { mutableIntStateOf(0) }
    var scanning by remember { mutableStateOf(false) }
    var pending by remember { mutableStateOf<Pending?>(null) }
    var uses by remember { mutableStateOf("1") }
    var hours by remember { mutableStateOf("0") }
    var note by remember { mutableStateOf("") }

    suspend fun loadAll() {
        stats = Api.adminStats().getOrNull()
        users = Api.adminUsers().getOrDefault(users)
        invites = Api.adminInvites().getOrDefault(invites)
        requests = Api.adminRequests().getOrDefault(requests)
    }

    LaunchedEffect(reload) { loadAll() }
    LaunchedEffect(Unit) {
        while (true) {
            delay(5000)
            requests = Api.adminRequests().getOrDefault(requests)
        }
    }

    fun act(label: String, run: suspend () -> Result<Unit>) {
        scope.launch {
            run().fold(
                onSuccess = { message = "$label done" },
                onFailure = { message = it.message ?: "$label failed" },
            )
            reload++
        }
    }

    if (me?.isAdmin != true) {
        Column(
            modifier = Modifier.fillMaxWidth().padding(design.screenPadding),
            verticalArrangement = Arrangement.spacedBy(design.gap),
        ) {
            ScreenTitle("Admin", "Server state and controls")
            EmptyState(
                icon = Lucide.User,
                title = "Admins only",
                body = "Sign in with an admin account to see the server controls.",
            )
        }
        return
    }

    LazyColumn(
        contentPadding = PaddingValues(
            start = design.screenPadding,
            end = design.screenPadding,
            top = 12.dp,
            bottom = 124.dp,
        ),
        verticalArrangement = Arrangement.spacedBy(design.gap),
    ) {
        item { ScreenTitle("Admin", "Server state, accounts and the download queue") }

        message?.let { text ->
            item { Text(text, color = design.accent, fontSize = 12.sp, fontWeight = FontWeight.Medium) }
        }

        item { SectionLabel("Overview", Modifier.padding(top = 4.dp), Lucide.Server) }
        item {
            val s = stats
            if (s == null) {
                Text("Loading…", color = design.dim, fontSize = 13.sp)
            } else {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Stat("Users", s.users.toString(), Modifier.weight(1f))
                        Stat("Admins", s.admins.toString(), Modifier.weight(1f))
                        Stat("Tracks", s.tracks.toString(), Modifier.weight(1f))
                    }
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Stat("Albums", s.albums.toString(), Modifier.weight(1f))
                        Stat("Plays", s.plays.toString(), Modifier.weight(1f))
                        Stat("Queue", s.queue.toString(), Modifier.weight(1f))
                    }
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Stat("Pending", s.pending.toString(), Modifier.weight(1f))
                        Stat("Running", s.running.toString(), Modifier.weight(1f))
                        Stat("Rooms", s.rooms.toString(), Modifier.weight(1f))
                    }
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Stat("Library", bytes(s.musicBytes), Modifier.weight(1f))
                        Stat("Free disk", bytes(s.diskFree), Modifier.weight(1f))
                        Stat("Uptime", uptime(s.uptime), Modifier.weight(1f))
                    }
                }
            }
        }

        item {
            AdminCard {
                Row(
                    modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    LucideIcon(Lucide.RefreshCw, design.accent, Modifier.size(18.dp))
                    Column(Modifier.weight(1f)) {
                        Text("Rescan the library", color = design.fg, fontSize = 14.sp, fontWeight = FontWeight.Medium)
                        Text("Pick up files added to the music folder", color = design.dim, fontSize = 11.sp)
                    }
                    PillButton(if (scanning) "Scanning…" else "Scan") {
                        if (!scanning) {
                            scanning = true
                            scope.launch {
                                Api.adminScan().fold(
                                    onSuccess = { (tracks, albums) -> message = "Library: $tracks tracks in $albums albums" },
                                    onFailure = { message = it.message },
                                )
                                scanning = false
                                reload++
                            }
                        }
                    }
                }
            }
        }

        item { SectionLabel("Friend codes", Modifier.padding(top = 4.dp), Lucide.Plus) }
        item {
            AdminCard {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    NumberField("Uses", uses, Modifier.weight(1f)) { uses = it }
                    NumberField("Hours", hours, Modifier.weight(1f)) { hours = it }
                }
                OutlinedTextField(
                    value = note,
                    onValueChange = { note = it },
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(14.dp),
                    label = { Text("Note (optional)", fontSize = 11.sp) },
                    singleLine = true,
                    textStyle = androidx.compose.ui.text.TextStyle(fontSize = 13.sp),
                    keyboardOptions = KeyboardOptions(imeAction = ImeAction.Done),
                    colors = fieldColors(),
                )
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.End,
                ) {
                    PillButton("Generate") {
                        scope.launch {
                            Api.adminCreateInvite(
                                uses = uses.toIntOrNull()?.coerceIn(1, 100) ?: 1,
                                hours = hours.toIntOrNull()?.coerceAtLeast(0) ?: 0,
                                note = note.trim(),
                            ).fold(
                                onSuccess = {
                                    message = "Code $it created"
                                    note = ""
                                    reload++
                                },
                                onFailure = { message = it.message },
                            )
                        }
                    }
                }
                if (invites.isEmpty()) {
                    Text("No codes yet — generate one above.", color = design.dim, fontSize = 12.sp)
                }
                invites.forEach { code ->
                    Row(
                        modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        Column(Modifier.weight(1f)) {
                            Text(code.code, color = design.fg, fontSize = 14.sp, fontFamily = FontFamily.Monospace)
                            Text(
                                buildString {
                                    append("${code.uses}/${code.maxUses} used")
                                    append(if (code.expires > 0) " · expires ${date(code.expires)}" else " · no expiry")
                                    if (code.note.isNotBlank()) append(" · ${code.note}")
                                    if (!code.active) append(" · revoked")
                                    if (code.usedBy.isNotEmpty()) append(" · used by ${code.usedBy.joinToString(", ")}")
                                },
                                color = design.dim,
                                fontSize = 10.sp,
                                lineHeight = 14.sp,
                            )
                        }
                        if (code.active) {
                            SmallButton("Copy") {
                                val link = "${Prefs.server}/?invite=${code.code}"
                                context.getSystemService(ClipboardManager::class.java)
                                    ?.setPrimaryClip(ClipData.newPlainText("invite", link))
                                message = "Invite link copied"
                            }
                            SmallButton("Revoke", danger = true) {
                                act("Revoke") { Api.adminRevokeInvite(code.id) }
                            }
                        }
                    }
                }
            }
        }

        item { SectionLabel("Accounts", Modifier.padding(top = 4.dp), Lucide.User) }
        items(users, key = { "u-${it.id}" }) { user ->
            AdminCard {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    Column(Modifier.weight(1f)) {
                        Text(
                            text = user.username + if (user.isAdmin) "  ·  admin" else "",
                            color = if (user.isAdmin) design.accent else design.fg,
                            fontSize = 14.sp,
                            fontWeight = FontWeight.SemiBold,
                        )
                        Text(
                            listOfNotNull(
                                user.email,
                                "${user.plays} plays",
                                "${user.likes} likes",
                                "${user.requests} requests",
                            ).joinToString(" · "),
                            color = design.dim,
                            fontSize = 11.sp,
                        )
                    }
                    SmallButton(if (user.isAdmin) "Demote" else "Promote") {
                        act(if (user.isAdmin) "Demote" else "Promote") {
                            Api.adminSetRole(user.id, !user.isAdmin)
                        }
                    }
                    if (user.id != me?.id) {
                        SmallButton("Delete", danger = true) {
                            pending = Pending(
                                title = "Delete ${user.username}?",
                                body = "Their plays, likes and playlists are removed too.",
                                label = "Delete",
                            ) { Api.adminDeleteUser(user.id) }
                        }
                    }
                }
            }
        }

        item { SectionLabel("Download requests", Modifier.padding(top = 4.dp), Lucide.Download) }
        if (requests.isEmpty()) {
            item { Text("Nothing queued.", color = design.dim, fontSize = 12.sp) }
        }
        items(requests.take(25), key = { "q-${it.id}" }) { request ->
            AdminCard {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Column(Modifier.weight(1f)) {
                        Text(
                            "#${request.id} · ${request.status}${if (request.running) " · running" else ""}",
                            color = when (request.status) {
                                "done" -> design.accent
                                "failed", "rejected" -> Color(0xFFE5484D)
                                else -> design.fg
                            },
                            fontSize = 13.sp,
                            fontWeight = FontWeight.SemiBold,
                        )
                        Text(
                            listOfNotNull(
                                request.username.takeIf { it.isNotBlank() },
                                request.url.take(70),
                            ).joinToString(" · "),
                            color = design.dim,
                            fontSize = 10.sp,
                            maxLines = 2,
                        )
                        lastLog(request.log)?.let { line ->
                            Text(line, color = design.dim, fontSize = 10.sp, maxLines = 1, fontFamily = FontFamily.Monospace)
                        }
                    }
                }
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    if (request.status in listOf("pending", "failed")) {
                        SmallButton("Approve") { act("Approve") { Api.adminRequestAction(request.id, "approve") } }
                        SmallButton("Reject") { act("Reject") { Api.adminRequestAction(request.id, "reject") } }
                    }
                    if (request.running) {
                        SmallButton("Cancel", danger = true) { act("Cancel") { Api.adminRequestAction(request.id, "cancel") } }
                    }
                    if (request.status in listOf("failed", "cancelled", "done")) {
                        SmallButton("Retry") { act("Retry") { Api.adminRequestAction(request.id, "retry") } }
                    }
                    if (!request.running) {
                        SmallButton("Delete", danger = true) {
                            pending = Pending(
                                title = "Delete request #${request.id}?",
                                body = "The request and its log are removed.",
                                label = "Delete",
                            ) { Api.adminRequestAction(request.id, "delete") }
                        }
                    }
                }
            }
        }
    }

    pending?.let { action ->
        Dialog(onDismissRequest = { pending = null }) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .mcSurface(RoundedCornerShape(design.cardRadius), tint = design.palette.bg.copy(alpha = 0.35f))
                    .padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                Text(action.title, color = design.fg, fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
                Text(action.body, color = design.dim, fontSize = 12.sp, lineHeight = 17.sp)
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
                    Box(Modifier.clickable { pending = null }.padding(horizontal = 12.dp, vertical = 8.dp)) {
                        Text("Cancel", color = design.dim, fontSize = 13.sp)
                    }
                    Box(
                        Modifier
                            .clip(RoundedCornerShape(50))
                            .mcSurface(RoundedCornerShape(50), tint = Color(0xFFE5484D))
                            .clickable {
                                val run = action.run
                                pending = null
                                act(action.label, run)
                            }
                            .padding(horizontal = 16.dp, vertical = 8.dp),
                    ) {
                        Text(action.label, color = Color.White, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
                    }
                }
            }
        }
    }
}

@Composable
private fun AdminCard(content: @Composable ColumnScope.() -> Unit) {
    val design = LocalDesign.current
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .mcSurface(RoundedCornerShape(design.cardRadius))
            .padding(horizontal = 14.dp, vertical = 10.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
        content = content,
    )
}

@Composable
private fun Stat(label: String, value: String, modifier: Modifier = Modifier) {
    val design = LocalDesign.current
    Column(
        modifier = modifier
            .mcSurface(RoundedCornerShape(design.tileRadius))
            .padding(horizontal = 12.dp, vertical = 10.dp),
        verticalArrangement = Arrangement.spacedBy(2.dp),
    ) {
        Text(value, color = design.fg, fontSize = 17.sp, fontWeight = FontWeight.Bold)
        Text(label, color = design.dim, fontSize = 10.sp, maxLines = 1)
    }
}

@Composable
private fun SmallButton(label: String, danger: Boolean = false, onClick: () -> Unit) {
    val design = LocalDesign.current
    val tint = if (danger) Color(0xFFE5484D) else design.accent
    Box(
        Modifier
            .clip(RoundedCornerShape(50))
            .mcSurface(RoundedCornerShape(50), tint = tint.copy(alpha = 0.14f))
            .clickable { onClick() }
            .padding(horizontal = 10.dp, vertical = 6.dp),
    ) {
        Text(label, color = tint, fontSize = 11.sp, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
private fun PillButton(label: String, onClick: () -> Unit) {
    val design = LocalDesign.current
    Box(
        Modifier
            .height(32.dp)
            .clip(RoundedCornerShape(50))
            .mcSurface(RoundedCornerShape(50), tint = design.accent)
            .clickable { onClick() }
            .padding(horizontal = 14.dp),
        contentAlignment = Alignment.Center,
    ) {
        Text(label, color = design.palette.bg2, fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
private fun NumberField(label: String, value: String, modifier: Modifier = Modifier, onChange: (String) -> Unit) {
    OutlinedTextField(
        value = value,
        onValueChange = onChange,
        modifier = modifier,
        shape = RoundedCornerShape(14.dp),
        label = { Text(label, fontSize = 11.sp) },
        singleLine = true,
        textStyle = androidx.compose.ui.text.TextStyle(fontSize = 13.sp),
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number, imeAction = ImeAction.Next),
        colors = fieldColors(),
    )
}

@Composable
private fun fieldColors() = OutlinedTextFieldDefaults.colors(
    focusedBorderColor = LocalDesign.current.accent,
    unfocusedBorderColor = LocalDesign.current.hairline,
    focusedTextColor = LocalDesign.current.fg,
    unfocusedTextColor = LocalDesign.current.fg,
    cursorColor = LocalDesign.current.accent,
    focusedLabelColor = LocalDesign.current.accent,
    unfocusedLabelColor = LocalDesign.current.dim,
)

private fun bytes(value: Long): String = when {
    value <= 0 -> "—"
    value >= 1_073_741_824 -> "%.1f GB".format(value / 1_073_741_824.0)
    value >= 1_048_576 -> "%.0f MB".format(value / 1_048_576.0)
    else -> "${value / 1024} KB"
}

private fun uptime(seconds: Long): String = when {
    seconds <= 0 -> "—"
    seconds >= 86_400 -> "${seconds / 86_400}d"
    seconds >= 3_600 -> "${seconds / 3_600}h"
    else -> "${seconds / 60}m"
}

private fun date(epoch: Long): String =
    java.text.SimpleDateFormat("d MMM", java.util.Locale.getDefault()).format(java.util.Date(epoch * 1000))

private fun lastLog(log: String): String? =
    log.trim().lineSequence().lastOrNull { it.isNotBlank() }?.take(120)
