package dev.mcmusic.app.ui.screens

import android.content.Intent
import android.net.Uri
import androidx.activity.compose.BackHandler
import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
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
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Account
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.Prefs
import dev.mcmusic.app.data.SELFHOST_GUIDE_URL
import dev.mcmusic.app.ui.ErrorLine
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.LucideIcon
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface
import kotlinx.coroutines.launch

/** The brief flat screen while a saved token is verified on cold start. */
@Composable
fun AuthSplash() {
    val design = LocalDesign.current
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(18.dp),
        ) {
            Box(
                Modifier.size(44.dp).clip(RoundedCornerShape(design.tileRadius)).background(design.accent),
                Alignment.Center,
            ) {
                Text("m", color = design.onAccent, fontSize = 24.sp, fontWeight = FontWeight.Bold)
            }
            Text("mcmusic", color = design.fg, fontSize = 20.sp, fontWeight = FontWeight.SemiBold)
            LinearProgressIndicator(
                modifier = Modifier.width(120.dp).height(3.dp).clip(RoundedCornerShape(4.dp)),
                color = design.accentText,
                trackColor = design.hairline,
            )
        }
    }
}

/**
 * The sign-in gate. Nothing in the app is reachable until [Account.signIn] or
 * [Account.acceptRoturToken] publishes a verified account, so the shell below
 * this screen never has to guess whether a stored token still works.
 *
 * Styling follows flufimusic v3 exactly: flat ink surfaces, one 10dp radius,
 * hairline borders, and a single violet interaction colour.
 */
@Composable
fun SignInScreen() {
    val design = LocalDesign.current
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    // Back must not drop the user into a half-unlocked shell.
    BackHandler(enabled = true) {}

    var identifier by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var showServer by remember { mutableStateOf(false) }
    var server by remember { mutableStateOf(Prefs.server) }

    val appear = remember { Animatable(if (Prefs.motion) 0f else 1f) }
    LaunchedEffect(Unit) {
        if (Prefs.playfulMotion) appear.animateTo(1f, tween(320, easing = FastOutSlowInEasing))
    }

    fun submit() {
        if (identifier.isBlank() || password.isBlank() || busy) return
        busy = true
        error = null
        scope.launch {
            Account.signIn(identifier.trim(), password).fold(
                onSuccess = { password = "" },
                onFailure = { error = it.message ?: "could not sign in" },
            )
            busy = false
        }
    }

    fun openRotur() {
        val url = "${Prefs.server}/api/auth/rotur/authorize?app=1" +
            "&device_hash=${Uri.encode(Api.deviceHash)}"
        runCatching {
            context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
        }.onFailure { error = it.message ?: "no browser available" }
    }

    fun openSelfHostGuide() {
        runCatching {
            context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(SELFHOST_GUIDE_URL)))
        }.onFailure { error = it.message ?: "no browser available" }
    }

    Box(
        Modifier
            .fillMaxSize()
            .statusBarsPadding()
            .navigationBarsPadding()
            .imePadding(),
    ) {
        Column(
            Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .graphicsLayer {
                    alpha = appear.value
                    translationY = (1f - appear.value) * 18.dp.toPx()
                }
                .padding(horizontal = 24.dp, vertical = 26.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    Modifier.size(34.dp).clip(RoundedCornerShape(design.tileRadius)).background(design.accent),
                    Alignment.Center,
                ) {
                    Text("m", color = design.onAccent, fontSize = 19.sp, fontWeight = FontWeight.Bold)
                }
                Spacer(Modifier.width(10.dp))
                Column {
                    Text("mcmusic", color = design.fg, fontSize = 19.sp, fontWeight = FontWeight.SemiBold)
                    Text("your room, your rules", color = design.dim, fontSize = 10.sp)
                }
            }

            Box(Modifier.fillMaxWidth().height(1.dp).background(design.hairline))

            Column(verticalArrangement = Arrangement.spacedBy(5.dp)) {
                Text("Welcome back", color = design.fg, fontSize = 28.sp, fontWeight = FontWeight.Bold)
                Text(
                    "Sign in for your library, playlists and downloads.",
                    color = design.dim,
                    fontSize = 13.sp,
                )
            }

            Column(
                Modifier.fillMaxWidth().mcSurface().padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                AuthField(
                    icon = Lucide.Mail,
                    label = "Email or username",
                    value = identifier,
                    onChange = { identifier = it },
                    imeAction = ImeAction.Next,
                )
                AuthField(
                    icon = Lucide.Lock,
                    label = "Password",
                    value = password,
                    onChange = { password = it },
                    password = true,
                    imeAction = ImeAction.Done,
                    done = { submit() },
                )

                error?.let { ErrorLine(it) }
                Account.gateError?.let { reason ->
                    ErrorLine(reason)
                    Box(
                        Modifier
                            .clip(RoundedCornerShape(design.tileRadius))
                            .border(1.dp, design.hairline, RoundedCornerShape(design.tileRadius))
                            .clickable { scope.launch { Account.refresh() } }
                            .padding(horizontal = 14.dp, vertical = 9.dp),
                    ) {
                        Text("Retry connection", color = design.accentText, fontSize = 12.sp, fontWeight = FontWeight.Medium)
                    }
                }

                Box(
                    Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(design.tileRadius))
                        .background(if (busy) design.accentSoft else design.accent)
                        .clickable(enabled = !busy) { submit() }
                        .padding(vertical = 13.dp),
                    contentAlignment = Alignment.Center,
                ) {
                    if (busy) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(18.dp),
                            strokeWidth = 2.dp,
                            color = design.accentText,
                        )
                    } else {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            Text("Sign in", color = design.onAccent, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
                            LucideIcon(Lucide.ChevronRight, design.onAccent, size = 16.dp)
                        }
                    }
                }

                Row(
                    Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    Box(Modifier.weight(1f).height(1.dp).background(design.hairline))
                    Text("or", color = design.dim, fontSize = 11.sp)
                    Box(Modifier.weight(1f).height(1.dp).background(design.hairline))
                }

                Box(
                    Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(design.tileRadius))
                        .border(1.dp, design.hairline, RoundedCornerShape(design.tileRadius))
                        .background(design.accentWash)
                        .clickable { openRotur() }
                        .padding(vertical = 12.dp),
                    contentAlignment = Alignment.Center,
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        LucideIcon(Lucide.User, design.accentText, size = 16.dp)
                        Text("Continue with Rotur", color = design.fg, fontSize = 13.sp, fontWeight = FontWeight.Medium)
                    }
                }
            }

            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                FeatureChip(Lucide.Library, "Library")
                FeatureChip(Lucide.ListMusic, "Playlists")
                FeatureChip(Lucide.Download, "Offline")
            }

            Column {
                Row(
                    Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(design.tileRadius))
                        .clickable { showServer = !showServer }
                        .padding(vertical = 8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    LucideIcon(Lucide.Server, design.dim, size = 15.dp)
                    Text(
                        "Server: ${Prefs.server.removePrefix("https://").removePrefix("http://")}",
                        color = design.dim,
                        fontSize = 11.sp,
                        modifier = Modifier.weight(1f),
                    )
                    LucideIcon(Lucide.ChevronRight, design.dim, size = 14.dp)
                }
                if (showServer) {
                    AuthField(
                        icon = Lucide.Server,
                        label = "Server URL",
                        value = server,
                        onChange = { server = it },
                        imeAction = ImeAction.Done,
                        done = {
                            Prefs.saveServer(server)
                            server = Prefs.server
                        },
                    )
                    Spacer(Modifier.height(8.dp))
                    Box(
                        Modifier
                            .clip(RoundedCornerShape(design.tileRadius))
                            .border(1.dp, design.hairline, RoundedCornerShape(design.tileRadius))
                            .clickable {
                                Prefs.saveServer(server)
                                server = Prefs.server
                            }
                            .padding(horizontal = 14.dp, vertical = 9.dp),
                    ) {
                        Text("Use this server", color = design.accentText, fontSize = 12.sp, fontWeight = FontWeight.Medium)
                    }
                }
            }

            Spacer(Modifier.height(8.dp))
            Text(
                "New accounts need an invite from an admin.",
                color = design.dim,
                fontSize = 11.sp,
            )
            Row(
                Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(design.tileRadius))
                    .clickable { openSelfHostGuide() }
                    .padding(vertical = 6.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(7.dp),
            ) {
                LucideIcon(Lucide.Info, design.accentText, size = 14.dp)
                Column {
                    Text("Self-hosting guide", color = design.accentText, fontSize = 11.sp, fontWeight = FontWeight.Medium)
                    Text(
                        "Point this app at your own mcmusic server.",
                        color = design.dim,
                        fontSize = 10.sp,
                    )
                }
            }
        }
    }
}

@Composable
private fun AuthField(
    icon: Int,
    label: String,
    value: String,
    onChange: (String) -> Unit,
    password: Boolean = false,
    imeAction: ImeAction = ImeAction.Next,
    done: () -> Unit = {},
) {
    val design = LocalDesign.current
    OutlinedTextField(
        value = value,
        onValueChange = onChange,
        label = { Text(label, fontSize = 12.sp) },
        singleLine = true,
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(design.tileRadius),
        textStyle = TextStyle(color = design.fg, fontSize = 14.sp),
        visualTransformation = if (password) PasswordVisualTransformation() else VisualTransformation.None,
        leadingIcon = { LucideIcon(icon, design.dim, size = 17.dp) },
        keyboardOptions = KeyboardOptions(
            imeAction = imeAction,
            keyboardType = if (password) KeyboardType.Password else KeyboardType.Uri,
        ),
        keyboardActions = KeyboardActions(onDone = { done() }),
        colors = OutlinedTextFieldDefaults.colors(
            focusedTextColor = design.fg,
            unfocusedTextColor = design.fg,
            focusedBorderColor = design.accentText,
            unfocusedBorderColor = design.hairline,
            focusedLabelColor = design.accentText,
            unfocusedLabelColor = design.dim,
            focusedLeadingIconColor = design.accentText,
            unfocusedLeadingIconColor = design.dim,
            cursorColor = design.accentText,
            focusedContainerColor = design.accentWash,
            unfocusedContainerColor = design.accentWash,
        ),
    )
}

@Composable
private fun FeatureChip(icon: Int, label: String) {
    val design = LocalDesign.current
    Row(
        Modifier
            .clip(RoundedCornerShape(design.tileRadius))
            .border(1.dp, design.hairline, RoundedCornerShape(design.tileRadius))
            .background(design.accentWash)
            .padding(horizontal = 10.dp, vertical = 7.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        LucideIcon(icon, design.accentText, size = 14.dp)
        Text(label, color = design.dim, fontSize = 11.sp, fontWeight = FontWeight.Medium)
    }
}
