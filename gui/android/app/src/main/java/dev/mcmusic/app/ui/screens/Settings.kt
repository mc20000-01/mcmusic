package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Account
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.Downloads
import dev.mcmusic.app.data.Prefs
import dev.mcmusic.app.ui.ErrorLine
import dev.mcmusic.app.ui.GhostButton
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.McField
import dev.mcmusic.app.ui.Muted
import dev.mcmusic.app.ui.PrimaryButton
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.SectionLabel
import dev.mcmusic.app.ui.SettingCard
import dev.mcmusic.app.ui.SettingDivider
import dev.mcmusic.app.ui.SettingRow
import dev.mcmusic.app.ui.SwitchRow
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.formatBytes
import kotlinx.coroutines.launch

/**
 * Settings is the web client's account + preferences page: who you are, which
 * server you talk to, motion, download rules and local storage. The admin entry
 * only appears for admins, and signing out drops the shell back to Home.
 */
@Composable
fun SettingsScreen(onAdmin: () -> Unit, onSignedOut: () -> Unit) {
    val design = LocalDesign.current
    val scope = rememberCoroutineScope()
    val me = Account.me

    var username by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var notice by remember { mutableStateOf<String?>(null) }

    var server by remember { mutableStateOf(Prefs.server) }
    var email by remember { mutableStateOf("") }
    var oldPassword by remember { mutableStateOf("") }
    var newPassword by remember { mutableStateOf("") }
    var showAccountTools by remember { mutableStateOf(false) }

    LaunchedEffect(me?.id) { email = me?.email.orEmpty() }

    fun signIn() {
        if (username.isBlank() || password.isBlank()) return
        busy = true
        error = null
        notice = null
        scope.launch {
            Api.login(username.trim(), password).fold(
                onSuccess = {
                    password = ""
                    Account.refresh()
                    notice = "Signed in as ${it.username}."
                },
                onFailure = { error = it.message ?: "could not sign in" },
            )
            busy = false
        }
    }

    LazyColumn(
        contentPadding = PaddingValues(design.screenPadding, 10.dp, design.screenPadding, 32.dp),
        verticalArrangement = Arrangement.spacedBy(9.dp),
    ) {
        item { ScreenTitle("Settings", "Account, server and this device.") }
        error?.let { item { ErrorLine(it) } }
        notice?.let { item { Muted(it) } }

        item { SectionLabel("Account") }
        if (me == null) {
            item {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    McField(username, { username = it }, "Username")
                    McField(
                        password, { password = it }, "Password",
                        password = true,
                        keyboard = KeyboardOptions(imeAction = ImeAction.Done, keyboardType = KeyboardType.Password),
                        actions = KeyboardActions(onDone = { signIn() }),
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        PrimaryButton(if (busy) "Signing in…" else "Sign in", enabled = !busy) { signIn() }
                        Muted("Same account as the website.", Modifier.align(Alignment.CenterVertically))
                    }
                    Muted("New accounts need an invite from an admin.")
                }
            }
        } else {
            item {
                SettingCard {
                    SettingRow("Signed in as ${me.username}", me.email ?: "no email on file", icon = Lucide.User)
                    SettingDivider()
                    SettingRow("Account tools", "Email and password", icon = Lucide.Lock) {
                        GhostButton(if (showAccountTools) "Hide" else "Open") { showAccountTools = !showAccountTools }
                    }
                }
            }
            if (showAccountTools) {
                item {
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        McField(email, { email = it }, "Email", keyboard = KeyboardOptions(keyboardType = KeyboardType.Email))
                        GhostButton("Save email") {
                            scope.launch {
                                Api.setEmail(email.trim()).fold(
                                    onSuccess = { Account.refresh(); notice = "Email saved." },
                                    onFailure = { error = it.message ?: "could not save the email" },
                                )
                            }
                        }
                        McField(oldPassword, { oldPassword = it }, "Current password", password = true)
                        McField(newPassword, { newPassword = it }, "New password", password = true)
                        GhostButton("Change password") {
                            scope.launch {
                                Api.changePassword(oldPassword, newPassword).fold(
                                    onSuccess = {
                                        oldPassword = ""; newPassword = ""
                                        notice = "Password changed."
                                    },
                                    onFailure = { error = it.message ?: "could not change the password" },
                                )
                            }
                        }
                    }
                }
            }
            if (Account.isAdmin) {
                item {
                    SettingCard {
                        SettingRow("Admin", "Users, invites and the download queue", icon = Lucide.Server, onClick = onAdmin)
                    }
                }
            }
            item {
                SettingCard {
                    SettingRow("Sign out", danger = true, icon = Lucide.LogOut) {
                        scope.launch {
                            Api.logout()
                            Account.refresh()
                            onSignedOut()
                        }
                    }
                }
            }
        }

        item { SectionLabel("Server") }
        item {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                McField(server, { server = it }, "Server URL", keyboard = KeyboardOptions(keyboardType = KeyboardType.Uri))
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    GhostButton("Save server") {
                        Prefs.saveServer(server)
                        server = Prefs.server
                        notice = "Server saved. Restart the app if the session does not follow."
                    }
                    GhostButton("Reset default") {
                        Prefs.saveServer(Prefs.DEFAULT_SERVER)
                        server = Prefs.server
                    }
                }
                Muted("Streams, covers and the API all follow this address.")
            }
        }

        item { SectionLabel("Playback and data") }
        item {
            SettingCard {
                SwitchRow(
                    "Reduce motion",
                    "Turns off tab transitions.",
                    icon = Lucide.RefreshCw,
                    checked = !Prefs.motion,
                    onChange = { Prefs.saveMotion(!it) },
                )
                SettingDivider()
                SwitchRow(
                    "Download over Wi-Fi only",
                    "Blocks downloads on mobile data.",
                    icon = Lucide.Wifi,
                    checked = Prefs.wifiOnly,
                    onChange = { Prefs.saveWifiOnly(it) },
                )
                SettingDivider()
                SettingRow(
                    "Downloads",
                    "${Downloads.items.size} tracks · ${formatBytes(Downloads.totalBytes())}",
                    icon = Lucide.HardDrive,
                )
            }
        }

        item { SectionLabel("About") }
        item {
            SettingCard {
                SettingRow("mcmusic Android", "Native client for the mcmusic server", icon = Lucide.Info)
                SettingDivider()
                SettingRow("Server", Prefs.server.removePrefix("https://").removePrefix("http://"), icon = Lucide.Server)
                SettingDivider()
                SettingRow(
                    "Build",
                    "Compose · Media3",
                    icon = Lucide.Library,
                    value = "1.0",
                )
            }
        }
        item {
            Text(
                "Playback continues in the notification shade. Cover art and catalogs come from the same API the web client uses.",
                color = design.dim,
                fontSize = 11.sp,
                lineHeight = 16.sp,
                fontWeight = FontWeight.Normal,
                modifier = Modifier.padding(top = 4.dp, bottom = 8.dp),
            )
        }
    }
}
