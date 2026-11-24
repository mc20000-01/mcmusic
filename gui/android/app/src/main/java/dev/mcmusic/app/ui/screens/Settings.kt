package dev.mcmusic.app.ui.screens

import android.content.Intent
import android.net.Uri
import android.os.Build
import android.provider.Settings as AndroidSettings
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.BuildConfig
import dev.mcmusic.app.data.Account
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.AppUpdate
import dev.mcmusic.app.data.SELFHOST_GUIDE_URL
import dev.mcmusic.app.data.Downloads
import dev.mcmusic.app.data.Prefs
import dev.mcmusic.app.data.Updater
import dev.mcmusic.app.ui.ErrorLine
import dev.mcmusic.app.ui.GhostButton
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.McField
import dev.mcmusic.app.ui.Muted
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.SectionLabel
import dev.mcmusic.app.ui.SettingCard
import dev.mcmusic.app.ui.SettingDivider
import dev.mcmusic.app.ui.SettingRow
import dev.mcmusic.app.ui.SwitchRow
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.ui.design.DesignLanguage
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.Palettes
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
    val context = LocalContext.current
    val me = Account.me

    var error by remember { mutableStateOf<String?>(null) }
    var notice by remember { mutableStateOf<String?>(null) }

    var server by remember { mutableStateOf(Prefs.server) }
    var email by remember { mutableStateOf("") }
    var oldPassword by remember { mutableStateOf("") }
    var newPassword by remember { mutableStateOf("") }
    var showAccountTools by remember { mutableStateOf(false) }

    var update by remember { mutableStateOf<AppUpdate?>(null) }
    var checking by remember { mutableStateOf(false) }
    var downloading by remember { mutableStateOf(false) }
    var progress by remember { mutableIntStateOf(0) }
    var updateError by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(me?.id) { email = me?.email.orEmpty() }

    fun checkUpdate() {
        checking = true
        updateError = null
        scope.launch {
            Updater.check().fold(
                onSuccess = { update = it },
                onFailure = { updateError = it.message ?: "could not check for updates" },
            )
            checking = false
        }
    }

    fun installUpdate() {
        val found = update ?: return
        downloading = true
        progress = 0
        updateError = null
        scope.launch {
            Updater.download(context, found) { progress = it }.fold(
                onSuccess = { file ->
                    runCatching { Updater.install(context, file) }
                        .onFailure { updateError = it.message ?: "could not start the installer" }
                    downloading = false
                },
                onFailure = {
                    updateError = it.message ?: "download failed"
                    downloading = false
                },
            )
        }
    }

    LaunchedEffect(Unit) { checkUpdate() }

    LazyColumn(
        contentPadding = PaddingValues(design.screenPadding, 10.dp, design.screenPadding, 32.dp),
        verticalArrangement = Arrangement.spacedBy(9.dp),
    ) {
        item { ScreenTitle("Settings", "Account, server and this device.") }
        error?.let { item { ErrorLine(it) } }
        notice?.let { item { Muted(it) } }

        item { SectionLabel("Account") }
        if (me != null) {
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
                    SettingRow(
                        "Sign out",
                        danger = true,
                        icon = Lucide.LogOut,
                        onClick = {
                            scope.launch {
                                Account.signOut()
                                onSignedOut()
                            }
                        },
                    )
                }
            }
        }

        item { SectionLabel("Server") }
        item {
            SettingCard {
                SettingRow(
                    "Server URL",
                    "Where streams, covers and API calls go",
                    icon = Lucide.Server,
                    value = Prefs.server,
                )
                SettingDivider()
                SettingRow(
                    "App version",
                    "This Android client",
                    icon = Lucide.Info,
                    value = "${BuildConfig.VERSION_NAME} (${BuildConfig.VERSION_CODE})",
                )
                SettingDivider()
                SettingRow(
                    "Self-hosting guide",
                    "Run mcmusic on your own server",
                    icon = Lucide.House,
                    onClick = {
                        runCatching {
                            context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(SELFHOST_GUIDE_URL)))
                        }
                    },
                )
            }
        }
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

        item { SectionLabel("Appearance") }
        item {
            SettingCard {
                SettingRow(
                    "Palette",
                    "Flat violet on ink, as on the web",
                    icon = Lucide.Palette,
                    value = Palettes.byId(Prefs.palette).label,
                    onClick = { Prefs.savePalette(if (Prefs.palette == "auto") "flufi" else "auto") },
                )
                SettingDivider()
                SettingRow(
                    "Design language",
                    "One shared layout in this build",
                    icon = Lucide.Compass,
                    value = DesignLanguage.from(Prefs.language).label,
                    onClick = { Prefs.saveLanguage(DesignLanguage.Flufi.id) },
                )
                SettingDivider()
                SwitchRow(
                    "Show song covers",
                    "Artwork in lists and tiles",
                    icon = Lucide.Image,
                    checked = Prefs.showCovers,
                    onChange = { Prefs.saveShowCovers(it) },
                )
                SettingDivider()
                SwitchRow(
                    "Hide explicit tracks",
                    "Filters tracks flagged explicit by the server",
                    icon = Lucide.EyeOff,
                    checked = Prefs.hideExplicit,
                    onChange = { Prefs.saveHideExplicit(it) },
                )
            }
        }

        item { SectionLabel("Social") }
        item {
            SettingCard {
                SwitchRow(
                    "Rotur activity",
                    "Share what you are listening to on Rotur",
                    icon = Lucide.Server,
                    checked = Prefs.roturActivity,
                    onChange = { enabled ->
                        Prefs.saveRoturActivity(enabled)
                        Playback.activitySettingChanged()
                    },
                )
                SettingDivider()
                SwitchRow(
                    "Discord activity",
                    "Share what you are listening to on Discord",
                    icon = Lucide.MessageCircle,
                    checked = Prefs.discordActivity,
                    onChange = { enabled ->
                        Prefs.saveDiscordActivity(enabled)
                        Playback.activitySettingChanged()
                    },
                )
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
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    SettingDivider()
                    SettingRow(
                        "Notifications",
                        "Keep music playing when the screen is off",
                        icon = Lucide.Info,
                        onClick = {
                            runCatching {
                                context.startActivity(
                                    Intent(AndroidSettings.ACTION_APP_NOTIFICATION_SETTINGS)
                                        .putExtra(AndroidSettings.EXTRA_APP_PACKAGE, context.packageName),
                                )
                            }
                        },
                    )
                }
            }
        }

        item { SectionLabel("Update") }
        item {
            SettingCard {
                SettingRow(
                    "Version",
                    if (checking) "checking the server…"
                    else update?.let { "Update available: ${it.version}" } ?: "You are on the newest build",
                    icon = Lucide.RefreshCw,
                    value = Updater.currentVersion,
                )
                SettingDivider()
                if (update != null && !downloading) {
                    SettingRow(
                        "Install update",
                        "Downloads the signed APK from this server",
                        icon = Lucide.Download,
                        onClick = { installUpdate() },
                    )
                } else {
                    SettingRow(
                        if (downloading) "Downloading $progress%" else "Check for updates",
                        "Uses the same build the website serves",
                        icon = Lucide.RefreshCw,
                        onClick = { if (!downloading) checkUpdate() },
                    )
                }
                if (downloading) {
                    LinearProgressIndicator(
                        progress = { progress / 100f },
                        modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 6.dp),
                        color = design.accent,
                        trackColor = design.hairline,
                    )
                }
                updateError?.let { ErrorLine(it) }
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
                    value = BuildConfig.VERSION_NAME,
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
