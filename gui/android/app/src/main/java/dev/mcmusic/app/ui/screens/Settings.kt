package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
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
import androidx.compose.foundation.shape.CircleShape
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import dev.mcmusic.app.BuildConfig
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.Me
import dev.mcmusic.app.data.Prefs
import dev.mcmusic.app.ui.McIcon
import dev.mcmusic.app.ui.McGlyph
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.SectionLabel
import dev.mcmusic.app.ui.Segmented
import dev.mcmusic.app.ui.design.DesignLanguage
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.Palettes
import dev.mcmusic.app.ui.design.mcSurface
import kotlinx.coroutines.launch

@Composable
fun SettingsScreen() {
    val design = LocalDesign.current
    val scope = rememberCoroutineScope()
    var me by remember { mutableStateOf<Me?>(null) }
    var showLogin by remember { mutableStateOf(false) }
    var reload by remember { mutableIntStateOf(0) }
    var serverDraft by remember { mutableStateOf(Prefs.server) }
    var savedHint by remember { mutableStateOf(false) }

    LaunchedEffect(reload) {
        me = Api.me()
        serverDraft = Prefs.server
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
        item { ScreenTitle("Settings", "Appearance, account and server") }

        item { SectionLabel("Appearance", Modifier.padding(top = 4.dp)) }

        item {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .mcSurface(RoundedCornerShape(design.cardRadius))
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                Text("Layout and style", color = design.fg, fontSize = 14.sp, fontWeight = FontWeight.Medium)
                Segmented(
                    options = DesignLanguage.entries.map { it.label },
                    selectedIndex = DesignLanguage.entries.indexOf(DesignLanguage.from(Prefs.language)),
                    onSelect = { index -> Prefs.saveLanguage(DesignLanguage.entries[index].id) },
                )
                Text(
                    text = DesignLanguage.from(Prefs.language).blurb,
                    color = design.dim,
                    fontSize = 12.sp,
                    lineHeight = 17.sp,
                )
            }
        }

        item {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .mcSurface(RoundedCornerShape(design.cardRadius))
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                Text("Palette", color = design.fg, fontSize = 14.sp, fontWeight = FontWeight.Medium)
                Text(
                    "The same seven palettes the web embeds use. Auto follows the system.",
                    color = design.dim,
                    fontSize = 12.sp,
                    lineHeight = 17.sp,
                )
                PaletteGrid(
                    selected = Prefs.palette,
                    onSelect = { Prefs.savePalette(it) },
                )
            }
        }

        item { SectionLabel("Account", Modifier.padding(top = 4.dp)) }

        item {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .mcSurface(RoundedCornerShape(design.cardRadius))
                    .padding(16.dp),
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
                    McGlyph(McIcon.Settings, design.accent, Modifier.size(20.dp))
                }
                Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                    Text(
                        text = me?.username ?: "Not signed in",
                        color = design.fg,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Medium,
                    )
                    Text(
                        text = if (me != null) "Session shared with this server" else "Sign in to reach your library and playback",
                        color = design.dim,
                        fontSize = 12.sp,
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
                    Text(
                        text = if (me == null) "Sign in" else "Sign out",
                        color = if (me == null) design.palette.bg2 else design.accent,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.SemiBold,
                    )
                }
            }
        }

        item { SectionLabel("Server", Modifier.padding(top = 4.dp)) }

        item {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .mcSurface(RoundedCornerShape(design.cardRadius))
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                OutlinedTextField(
                    value = serverDraft,
                    onValueChange = {
                        serverDraft = it
                        savedHint = false
                    },
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(if (design.ios) 16.dp else 18.dp),
                    label = { Text("Base URL", fontSize = 12.sp) },
                    singleLine = true,
                    textStyle = androidx.compose.ui.text.TextStyle(fontSize = 14.sp),
                    keyboardOptions = KeyboardOptions(imeAction = ImeAction.Done),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = design.accent,
                        unfocusedBorderColor = design.hairline,
                        focusedTextColor = design.fg,
                        unfocusedTextColor = design.fg,
                        cursorColor = design.accent,
                        focusedLabelColor = design.accent,
                        unfocusedLabelColor = design.dim,
                        focusedContainerColor = design.palette.bg2.copy(alpha = 0.35f),
                        unfocusedContainerColor = design.palette.bg2.copy(alpha = 0.35f),
                    ),
                )
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
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
                        Text("Save", color = design.palette.bg2, fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                    }
                    Text(
                        text = if (savedHint) "Saved — widgets will use it too" else "Home screen widgets read this too",
                        color = design.dim,
                        fontSize = 11.sp,
                    )
                }
            }
        }

        item { SectionLabel("About", Modifier.padding(top = 4.dp)) }

        item {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .mcSurface(RoundedCornerShape(design.cardRadius))
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                Text("mcmusic ${BuildConfig.VERSION_NAME}", color = design.fg, fontSize = 14.sp, fontWeight = FontWeight.Medium)
                Text(
                    "The phone is a client of ${Prefs.server} — no music is stored in this app except downloads.",
                    color = design.dim,
                    fontSize = 12.sp,
                    lineHeight = 17.sp,
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
}

@Composable
private fun PaletteGrid(selected: String, onSelect: (String) -> Unit) {
    val design = LocalDesign.current
    val systemDark = androidx.compose.foundation.isSystemInDarkTheme()
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
 * the same account the web app uses.
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
                .padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Text("Sign in", color = design.fg, fontSize = 19.sp, fontWeight = FontWeight.SemiBold)
            Text(
                "Uses your mcmusic account on ${Prefs.server}.",
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
                colors = loginFieldColors(design.accent, design.hairline, design.fg, design.dim, design.palette.bg2),
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
                textStyle = androidx.compose.ui.text.TextStyle(fontSize = 14.sp),
                colors = loginFieldColors(design.accent, design.hairline, design.fg, design.dim, design.palette.bg2),
            )
            error?.let {
                Text(it, color = Color(0xFFFF6B6B), fontSize = 12.sp)
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
private fun loginFieldColors(accent: Color, line: Color, fg: Color, dim: Color, bg2: Color) =
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
