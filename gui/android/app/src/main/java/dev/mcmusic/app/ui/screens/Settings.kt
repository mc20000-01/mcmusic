package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
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
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import dev.mcmusic.app.BuildConfig
import dev.mcmusic.app.data.Account
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.Downloads
import dev.mcmusic.app.data.Me
import dev.mcmusic.app.data.Prefs
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.LucideIcon
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.SectionLabel
import dev.mcmusic.app.ui.Segmented
import dev.mcmusic.app.ui.SettingDivider
import dev.mcmusic.app.ui.SettingRow
import dev.mcmusic.app.ui.SettingSwitch
import dev.mcmusic.app.ui.design.DesignLanguage
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.Palettes
import dev.mcmusic.app.ui.design.mcSurface
import dev.mcmusic.app.widget.Widgets
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

@Composable
fun SettingsScreen() {
    val design = LocalDesign.current
    val scope = rememberCoroutineScope()
    val context = LocalContext.current
    val uriHandler = LocalUriHandler.current
    val playback = Playback.state
    val offline = Downloads.items

    var me by remember { mutableStateOf<Me?>(null) }
    var showLogin by remember { mutableStateOf(false) }
    var showPassword by remember { mutableStateOf(false) }
    var showEmail by remember { mutableStateOf(false) }
    var showWidgetSource by remember { mutableStateOf(false) }
    var reload by remember { mutableIntStateOf(0) }
    var serverDraft by remember { mutableStateOf(Prefs.server) }
    var savedHint by remember { mutableStateOf(false) }
    var checkResult by remember { mutableStateOf<String?>(null) }
    var checking by remember { mutableStateOf(false) }

    LaunchedEffect(reload) {
        Account.refresh()
        me = Account.me
        serverDraft = Prefs.server
    }
    // The sleep countdown is derived from playback state; nudge it while open.
    LaunchedEffect(Unit) {
        while (true) {
            Playback.tick()
            delay(1000)
        }
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
        item { ScreenTitle("Settings", "Appearance, playback, account and server") }

        item { SectionLabel("Appearance", Modifier.padding(top = 4.dp), Lucide.Palette) }

        item {
            SettingsCard {
                Text("Layout and style", color = design.fg, fontSize = 14.sp, fontWeight = FontWeight.Medium)
                Segmented(
                    options = DesignLanguage.entries.map { it.label },
                    selectedIndex = DesignLanguage.entries.indexOf(DesignLanguage.from(Prefs.language)),
                    onSelect = { index ->
                        Prefs.saveLanguage(DesignLanguage.entries[index].id)
                        Widgets.refresh(context.applicationContext)
                    },
                )
                Text(
                    text = DesignLanguage.from(Prefs.language).blurb,
                    color = design.dim,
                    fontSize = 12.sp,
                    lineHeight = 17.sp,
                )
                SettingDivider()
                SettingSwitch(
                    title = "Reduce motion",
                    subtitle = "Tab changes appear instead of fading in",
                    checked = !Prefs.motion,
                    onChange = { Prefs.saveMotion(!it) },
                )
            }
        }

        item {
            SettingsCard {
                Text("Palette", color = design.fg, fontSize = 14.sp, fontWeight = FontWeight.Medium)
                Text(
                    "The same seven palettes the web embeds use. Auto follows the system.",
                    color = design.dim,
                    fontSize = 12.sp,
                    lineHeight = 17.sp,
                )
                PaletteGrid(
                    selected = Prefs.palette,
                    onSelect = {
                        Prefs.savePalette(it)
                        Widgets.refresh(context.applicationContext)
                    },
                )
            }
        }

        item { SectionLabel("Playback", Modifier.padding(top = 4.dp), Lucide.Play) }

        item {
            SettingsCard {
                Text("Sleep timer", color = design.fg, fontSize = 14.sp, fontWeight = FontWeight.Medium)
                Segmented(
                    options = listOf("Off", "15 min", "30 min", "60 min"),
                    selectedIndex = when (playback.sleepMinutes) {
                        15 -> 1
                        30 -> 2
                        60 -> 3
                        else -> 0
                    },
                    onSelect = { index -> Playback.setSleep(listOf(0, 15, 30, 60)[index]) },
                )
                Text(
                    text = if (playback.sleepMinutes > 0) {
                        "Pauses in ${(playback.sleepRemaining + 59_999) / 60_000} min — playback stops on its own."
                    } else {
                        "Pauses playback after a set time, so falling asleep with headphones on doesn't play all night."
                    },
                    color = design.dim,
                    fontSize = 12.sp,
                    lineHeight = 17.sp,
                )
            }
        }

        item { SectionLabel("Downloads", Modifier.padding(top = 4.dp), Lucide.Download) }

        item {
            SettingsCard {
                SettingSwitch(
                    title = "Wi-Fi only",
                    subtitle = "Cellular downloads wait for a Wi-Fi network",
                    icon = Lucide.Wifi,
                    checked = Prefs.wifiOnly,
                    onChange = { Prefs.saveWifiOnly(it) },
                )
                SettingDivider()
                SettingRow(
                    title = "Storage used",
                    subtitle = if (offline.isEmpty()) {
                        "No offline copies yet"
                    } else {
                        "${"%.1f".format(offline.sumOf { it.bytes } / 1048576.0)} MB across " +
                            "${offline.size} track${if (offline.size == 1) "" else "s"}"
                    },
                    icon = Lucide.HardDrive,
                )
                SettingDivider()
                SettingRow(
                    title = "Clear downloads",
                    subtitle = if (offline.isEmpty()) "Nothing to remove" else "Delete every offline copy on this phone",
                    icon = Lucide.Trash,
                    danger = offline.isNotEmpty(),
                    onClick = if (offline.isEmpty()) null else ({ Downloads.clearAll() }),
                )
            }
        }

        item { SectionLabel("Account", Modifier.padding(top = 4.dp), Lucide.User) }

        item {
            SettingsCard {
                Row(
                    modifier = Modifier.fillMaxWidth().padding(vertical = 10.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    Box(
                        Modifier
                            .size(42.dp)
                            .clip(CircleShape)
                            .background(design.accentSoft),
                        contentAlignment = Alignment.Center,
                    ) {
                        LucideIcon(Lucide.User, design.accent, Modifier.size(20.dp))
                    }
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                        Text(
                            text = me?.username ?: "Not signed in",
                            color = design.fg,
                            fontSize = 14.sp,
                            fontWeight = FontWeight.Medium,
                        )
                        Text(
                            text = if (me != null) "Session shared with ${Prefs.server}" else "Sign in to reach your library and playback",
                            color = design.dim,
                            fontSize = 11.sp,
                        )
                    }
                    Box(
                        Modifier
                            .clip(RoundedCornerShape(50))
                            .background(if (me == null) design.accent else design.accentSoft)
                            .clickable {
                                if (me == null) {
                                    showLogin = true
                                } else {
                                    scope.launch {
                                        Api.logout()
                                        reload++
                                    }
                                }
                            }
                            .padding(horizontal = 14.dp, vertical = 8.dp),
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(5.dp),
                        ) {
                            LucideIcon(
                                icon = if (me == null) Lucide.LogIn else Lucide.LogOut,
                                tint = if (me == null) design.palette.bg2 else design.accent,
                                modifier = Modifier.size(13.dp),
                            )
                            Text(
                                text = if (me == null) "Sign in" else "Sign out",
                                color = if (me == null) design.palette.bg2 else design.accent,
                                fontSize = 12.sp,
                                fontWeight = FontWeight.SemiBold,
                            )
                        }
                    }
                }
                SettingDivider()
                SettingRow(
                    title = "Change password",
                    subtitle = if (me == null) "Sign in first" else "Update the password used on every device",
                    icon = Lucide.Lock,
                    onClick = { if (me == null) showLogin = true else showPassword = true },
                )
                SettingDivider()
                SettingRow(
                    title = "Reset email",
                    subtitle = me?.email ?: "Not set — password reset links have nowhere to go",
                    icon = Lucide.Mail,
                    onClick = { if (me == null) showLogin = true else showEmail = true },
                )
                SettingDivider()
                SettingRow(
                    title = "Rotur account",
                    subtitle = when {
                        me == null -> "Sign in to check"
                        me?.roturLinked == true -> "Linked — listening can post to Rotur"
                        else -> "Not linked — link it on the website"
                    },
                    icon = Lucide.User,
                )
            }
        }

        item { SectionLabel("Widgets", Modifier.padding(top = 4.dp), Lucide.Library) }

        item {
            SettingsCard {
                SettingRow(
                    title = "Now playing source",
                    subtitle = Prefs.widgetUser ?: "Signed-in account",
                    icon = Lucide.User,
                    onClick = { showWidgetSource = true },
                )
                SettingDivider()
                SettingRow(
                    title = "Refresh widgets",
                    subtitle = "Redraw the home screen widgets with the current palette",
                    icon = Lucide.RefreshCw,
                    onClick = { Thread { runCatching { Widgets.refresh(context.applicationContext) } }.start() },
                )
            }
        }

        item { SectionLabel("Server", Modifier.padding(top = 4.dp), Lucide.Server) }

        item {
            SettingsCard {
                OutlinedTextField(
                    value = serverDraft,
                    onValueChange = {
                        serverDraft = it
                        savedHint = false
                        checkResult = null
                    },
                    modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
                    shape = RoundedCornerShape(if (design.ios) 16.dp else 18.dp),
                    label = { Text("Base URL", fontSize = 12.sp) },
                    singleLine = true,
                    textStyle = androidx.compose.ui.text.TextStyle(fontSize = 14.sp),
                    keyboardOptions = KeyboardOptions(imeAction = ImeAction.Done),
                    colors = fieldColors(design.accent, design.hairline, design.fg, design.dim, design.palette.bg2),
                )
                Row(
                    modifier = Modifier.fillMaxWidth().padding(top = 10.dp, bottom = 4.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    Box(
                        Modifier
                            .clip(RoundedCornerShape(50))
                            .background(design.accent)
                            .clickable {
                                Prefs.saveServer(serverDraft)
                                serverDraft = Prefs.server
                                savedHint = true
                                reload++
                            }
                            .padding(horizontal = 14.dp, vertical = 8.dp),
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(5.dp),
                        ) {
                            LucideIcon(Lucide.Check, design.palette.bg2, Modifier.size(13.dp))
                            Text("Save", color = design.palette.bg2, fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                        }
                    }
                    Text(
                        text = if (savedHint) "Saved — widgets will use it too" else "Home screen widgets read this too",
                        color = design.dim,
                        fontSize = 11.sp,
                    )
                }
                SettingDivider()
                SettingRow(
                    title = "Test connection",
                    subtitle = checkResult ?: "Ask the server what it is playing right now",
                    icon = Lucide.Server,
                    onClick = {
                        if (!checking) {
                            checking = true
                            checkResult = "Checking…"
                            scope.launch {
                                checkResult = Api.listening().fold(
                                    onSuccess = { "Reachable — ${it.size} listener${if (it.size == 1) "" else "s"}" },
                                    onFailure = { "Failed: ${it.message ?: "unreachable"}" },
                                )
                                checking = false
                            }
                        }
                    },
                )
            }
        }

        item { SectionLabel("About", Modifier.padding(top = 4.dp), Lucide.Info) }

        item {
            SettingsCard {
                SettingRow(
                    title = "mcmusic ${BuildConfig.VERSION_NAME}",
                    subtitle = "Android client — audio streams from ${Prefs.server}",
                    icon = Lucide.Info,
                )
                SettingDivider()
                SettingRow(
                    title = "Check for updates",
                    subtitle = "Opens the download page for this server",
                    icon = Lucide.Download,
                    onClick = { runCatching { uriHandler.openUri(Prefs.server + "/get") } },
                )
                SettingDivider()
                SettingRow(
                    title = "Licences",
                    subtitle = "Lucide icons (ISC), Jetpack Compose, AndroidX Media3",
                    icon = Lucide.Info,
                )
            }
        }
    }

    LoginDialog(
        visible = showLogin,
        onDismiss = { showLogin = false },
        onSignedIn = {
            showLogin = false
            reload++
        },
    )
    if (showPassword) {
        PasswordDialog(
            onDismiss = { showPassword = false },
            onChanged = { showPassword = false },
        )
    }
    if (showEmail) {
        EmailDialog(
            initial = me?.email,
            onDismiss = { showEmail = false },
            onSaved = {
                showEmail = false
                reload++
            },
        )
    }
    if (showWidgetSource) {
        WidgetSourceDialog(onDismiss = { showWidgetSource = false })
    }
}

@Composable
private fun SettingsCard(content: @Composable ColumnScope.() -> Unit) {
    val design = LocalDesign.current
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .mcSurface(RoundedCornerShape(design.cardRadius))
            .padding(horizontal = 16.dp, vertical = 8.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
        content = content,
    )
}

@Composable
private fun PaletteGrid(selected: String, onSelect: (String) -> Unit) {
    val design = LocalDesign.current
    val systemDark = isSystemInDarkTheme()
    val entries = listOf(Palettes.AUTO to "Auto") + Palettes.all.map { it.id to it.label }
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        entries.chunked(4).forEach { row ->
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                row.forEach { (id, label) ->
                    val palette = Palettes.resolve(id, systemDark)
                    val active = id == selected
                    Column(
                        modifier = Modifier
                            .weight(1f)
                            .clip(RoundedCornerShape(14.dp))
                            .background(palette.bg)
                            .border(
                                width = if (active) 2.dp else 1.dp,
                                color = if (active) design.accent else design.hairline,
                                shape = RoundedCornerShape(14.dp),
                            )
                            .clickable { onSelect(id) }
                            .padding(vertical = 9.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.spacedBy(5.dp),
                    ) {
                        Box(
                            Modifier
                                .size(16.dp)
                                .clip(CircleShape)
                                .background(palette.accent),
                        )
                        Text(
                            text = label,
                            color = palette.fg,
                            fontSize = 10.sp,
                            fontWeight = if (active) FontWeight.SemiBold else FontWeight.Normal,
                            maxLines = 1,
                        )
                    }
                }
                repeat(4 - row.size) { Box(Modifier.weight(1f)) }
            }
        }
    }
}

/**
 * Shared sign-in sheet: the phone keeps the server's session cookie, so this is
 * the same account the web app uses. It scrolls with the keyboard up, so the
 * button is never buried under the IME.
 */
@Composable
fun LoginDialog(visible: Boolean, onDismiss: () -> Unit, onSignedIn: () -> Unit) {
    if (!visible) return
    val design = LocalDesign.current
    val scope = rememberCoroutineScope()
    var username by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    fun submit() {
        if (busy || username.isBlank() || password.isEmpty()) return
        scope.launch {
            busy = true
            error = null
            Api.login(username.trim(), password).fold(
                onSuccess = { onSignedIn() },
                onFailure = { error = it.message ?: "sign-in failed" },
            )
            busy = false
        }
    }

    Dialog(onDismissRequest = { if (!busy) onDismiss() }) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .mcSurface(RoundedCornerShape(design.cardRadius), tint = design.palette.bg.copy(alpha = 0.35f))
                .imePadding()
                .verticalScroll(rememberScrollState())
                .padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Text("Sign in", color = design.fg, fontSize = 19.sp, fontWeight = FontWeight.SemiBold)
            Text(
                "Uses your mcmusic account on ${Prefs.server}, the same one the website uses.",
                color = design.dim,
                fontSize = 12.sp,
                lineHeight = 17.sp,
            )
            OutlinedTextField(
                value = username,
                onValueChange = { username = it; error = null },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                label = { Text("Username", fontSize = 12.sp) },
                singleLine = true,
                textStyle = androidx.compose.ui.text.TextStyle(fontSize = 14.sp),
                colors = fieldColors(design.accent, design.hairline, design.fg, design.dim, design.palette.bg2),
            )
            OutlinedTextField(
                value = password,
                onValueChange = { password = it; error = null },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                label = { Text("Password", fontSize = 12.sp) },
                singleLine = true,
                visualTransformation = PasswordVisualTransformation(),
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Done),
                keyboardActions = KeyboardActions(onDone = { submit() }),
                textStyle = androidx.compose.ui.text.TextStyle(fontSize = 14.sp),
                colors = fieldColors(design.accent, design.hairline, design.fg, design.dim, design.palette.bg2),
            )
            error?.let {
                Text(it, color = Color(0xFFFF6B6B), fontSize = 12.sp, lineHeight = 16.sp)
            }
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Box(Modifier.weight(1f))
                Box(
                    Modifier
                        .clip(RoundedCornerShape(50))
                        .clickable { if (!busy) onDismiss() }
                        .padding(horizontal = 14.dp, vertical = 9.dp),
                ) {
                    Text("Cancel", color = design.dim, fontSize = 13.sp)
                }
                Box(
                    Modifier
                        .height(38.dp)
                        .clip(RoundedCornerShape(50))
                        .background(if (busy) design.accentSoft else design.accent)
                        .clickable { submit() }
                        .padding(horizontal = 18.dp),
                    contentAlignment = Alignment.Center,
                ) {
                    Text(
                        text = if (busy) "Signing in…" else "Sign in",
                        color = design.palette.bg2,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.SemiBold,
                    )
                }
            }
        }
    }
}

@Composable
private fun PasswordDialog(onDismiss: () -> Unit, onChanged: () -> Unit) {
    val design = LocalDesign.current
    val scope = rememberCoroutineScope()
    var current by remember { mutableStateOf("") }
    var next by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    fun submit() {
        if (busy) return
        if (current.isEmpty()) {
            error = "Enter the current password"
            return
        }
        if (next.length < 6) {
            error = "New password needs at least 6 characters"
            return
        }
        scope.launch {
            busy = true
            error = null
            Api.changePassword(current, next).fold(
                onSuccess = { onChanged() },
                onFailure = { error = it.message ?: "Could not change the password" },
            )
            busy = false
        }
    }

    Dialog(onDismissRequest = { if (!busy) onDismiss() }) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .mcSurface(RoundedCornerShape(design.cardRadius), tint = design.palette.bg.copy(alpha = 0.35f))
                .imePadding()
                .verticalScroll(rememberScrollState())
                .padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Text("Change password", color = design.fg, fontSize = 19.sp, fontWeight = FontWeight.SemiBold)
            Text(
                "The new password works on the website and on this phone.",
                color = design.dim,
                fontSize = 12.sp,
                lineHeight = 17.sp,
            )
            OutlinedTextField(
                value = current,
                onValueChange = { current = it; error = null },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                label = { Text("Current password", fontSize = 12.sp) },
                singleLine = true,
                visualTransformation = PasswordVisualTransformation(),
                textStyle = androidx.compose.ui.text.TextStyle(fontSize = 14.sp),
                colors = fieldColors(design.accent, design.hairline, design.fg, design.dim, design.palette.bg2),
            )
            OutlinedTextField(
                value = next,
                onValueChange = { next = it; error = null },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                label = { Text("New password (6+ characters)", fontSize = 12.sp) },
                singleLine = true,
                visualTransformation = PasswordVisualTransformation(),
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Done),
                keyboardActions = KeyboardActions(onDone = { submit() }),
                textStyle = androidx.compose.ui.text.TextStyle(fontSize = 14.sp),
                colors = fieldColors(design.accent, design.hairline, design.fg, design.dim, design.palette.bg2),
            )
            error?.let { Text(it, color = Color(0xFFFF6B6B), fontSize = 12.sp, lineHeight = 16.sp) }
            DialogButtons(
                busy = busy,
                confirm = "Save",
                onCancel = { if (!busy) onDismiss() },
                onConfirm = { submit() },
            )
        }
    }
}

@Composable
private fun EmailDialog(initial: String?, onDismiss: () -> Unit, onSaved: () -> Unit) {
    val design = LocalDesign.current
    val scope = rememberCoroutineScope()
    var email by remember(initial) { mutableStateOf(initial.orEmpty()) }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    fun submit() {
        if (busy) return
        if (email.isBlank() || !email.contains("@")) {
            error = "Enter a valid email address"
            return
        }
        scope.launch {
            busy = true
            error = null
            Api.setEmail(email.trim()).fold(
                onSuccess = { onSaved() },
                onFailure = { error = it.message ?: "Could not save the address" },
            )
            busy = false
        }
    }

    Dialog(onDismissRequest = { if (!busy) onDismiss() }) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .mcSurface(RoundedCornerShape(design.cardRadius), tint = design.palette.bg.copy(alpha = 0.35f))
                .imePadding()
                .verticalScroll(rememberScrollState())
                .padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Text("Reset email", color = design.fg, fontSize = 19.sp, fontWeight = FontWeight.SemiBold)
            Text(
                "Used only to send a link when you forget your password. Leave it empty to remove it.",
                color = design.dim,
                fontSize = 12.sp,
                lineHeight = 17.sp,
            )
            OutlinedTextField(
                value = email,
                onValueChange = { email = it; error = null },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                label = { Text("Email", fontSize = 12.sp) },
                singleLine = true,
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Done),
                keyboardActions = KeyboardActions(onDone = { submit() }),
                textStyle = androidx.compose.ui.text.TextStyle(fontSize = 14.sp),
                colors = fieldColors(design.accent, design.hairline, design.fg, design.dim, design.palette.bg2),
            )
            error?.let { Text(it, color = Color(0xFFFF6B6B), fontSize = 12.sp, lineHeight = 16.sp) }
            DialogButtons(
                busy = busy,
                confirm = "Save",
                onCancel = { if (!busy) onDismiss() },
                onConfirm = { submit() },
            )
        }
    }
}

@Composable
private fun WidgetSourceDialog(onDismiss: () -> Unit) {
    val design = LocalDesign.current
    val context = LocalContext.current
    var names by remember { mutableStateOf<List<String>>(emptyList()) }
    var loaded by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        names = Api.listening().getOrNull().orEmpty().map { it.username }.filter { it.isNotBlank() }.distinct()
        loaded = true
    }

    fun pick(name: String?) {
        Prefs.saveWidgetUser(name)
        Thread { runCatching { Widgets.refresh(context.applicationContext) } }.start()
        onDismiss()
    }

    Dialog(onDismissRequest = onDismiss) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .mcSurface(RoundedCornerShape(design.cardRadius), tint = design.palette.bg.copy(alpha = 0.35f))
                .padding(20.dp)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(2.dp),
        ) {
            Text("Widget source", color = design.fg, fontSize = 19.sp, fontWeight = FontWeight.SemiBold)
            Text(
                "Whose listening the home screen widget should show.",
                color = design.dim,
                fontSize = 12.sp,
                lineHeight = 17.sp,
                modifier = Modifier.padding(bottom = 8.dp),
            )
            SourceOption("My account", Prefs.widgetUser == null) { pick(null) }
            names.forEach { name ->
                SourceOption(name, Prefs.widgetUser == name) { pick(name) }
            }
            if (loaded && names.isEmpty()) {
                Text(
                    "No one else is listening right now.",
                    color = design.dim,
                    fontSize = 11.sp,
                    modifier = Modifier.padding(vertical = 8.dp),
                )
            }
            Row(modifier = Modifier.fillMaxWidth().padding(top = 8.dp), horizontalArrangement = Arrangement.End) {
                Box(
                    Modifier
                        .clip(RoundedCornerShape(50))
                        .clickable { onDismiss() }
                        .padding(horizontal = 14.dp, vertical = 9.dp),
                ) {
                    Text("Cancel", color = design.dim, fontSize = 13.sp)
                }
            }
        }
    }
}

@Composable
private fun SourceOption(label: String, selected: Boolean, onClick: () -> Unit) {
    val design = LocalDesign.current
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .clickable { onClick() }
            .padding(horizontal = 10.dp, vertical = 11.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Box(
            Modifier
                .size(8.dp)
                .clip(CircleShape)
                .background(if (selected) design.accent else design.hairline),
        )
        Text(label, color = design.fg, fontSize = 14.sp, modifier = Modifier.weight(1f))
        if (selected) LucideIcon(Lucide.Check, design.accent, Modifier.size(15.dp))
    }
}

@Composable
private fun DialogButtons(busy: Boolean, confirm: String, onCancel: () -> Unit, onConfirm: () -> Unit) {
    val design = LocalDesign.current
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(Modifier.weight(1f))
        Box(
            Modifier
                .clip(RoundedCornerShape(50))
                .clickable { onCancel() }
                .padding(horizontal = 14.dp, vertical = 9.dp),
        ) {
            Text("Cancel", color = design.dim, fontSize = 13.sp)
        }
        Box(
            Modifier
                .height(38.dp)
                .clip(RoundedCornerShape(50))
                .background(if (busy) design.accentSoft else design.accent)
                .clickable { onConfirm() }
                .padding(horizontal = 18.dp),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                text = if (busy) "Saving…" else confirm,
                color = design.palette.bg2,
                fontSize = 13.sp,
                fontWeight = FontWeight.SemiBold,
            )
        }
    }
}

@Composable
private fun fieldColors(accent: Color, line: Color, fg: Color, dim: Color, bg2: Color) =
    OutlinedTextFieldDefaults.colors(
        focusedBorderColor = accent,
        unfocusedBorderColor = line,
        focusedTextColor = fg,
        unfocusedTextColor = fg,
        cursorColor = accent,
        focusedLabelColor = accent,
        unfocusedLabelColor = dim,
        focusedContainerColor = bg2.copy(alpha = 0.35f),
        unfocusedContainerColor = bg2.copy(alpha = 0.35f),
    )
