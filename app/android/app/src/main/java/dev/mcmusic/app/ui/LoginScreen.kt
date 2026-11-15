package dev.mcmusic.app.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.systemBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import dev.mcmusic.app.AppViewModel
import dev.mcmusic.app.ui.theme.D
import dev.mcmusic.app.ui.theme.LocalMc
import dev.mcmusic.app.ui.theme.McType

@Composable
fun LoginScreen(vm: AppViewModel) {
    val mc = LocalMc.current
    var server by remember { mutableStateOf(vm.api.baseUrl) }
    var username by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var invite by remember { mutableStateOf("") }
    var mode by remember { mutableStateOf("in") }
    var resetEmail by remember { mutableStateOf("") }
    var resetToken by remember { mutableStateOf("") }
    var resetPw by remember { mutableStateOf("") }

    val signingUp = mode == "up"
    val resetting = mode == "reset"

    Box(
        Modifier
            .fillMaxSize()
            .background(
                androidx.compose.ui.graphics.Brush.verticalGradient(
                    listOf(
                        mc.accent.copy(alpha = 0.18f),
                        mc.bg.copy(alpha = 0.98f),
                        mc.bg,
                    )
                )
            )
            .systemBarsPadding()
            .imePadding(),
        contentAlignment = Alignment.Center,
    ) {
        Column(
            Modifier
                .widthIn(max = 400.dp)
                .fillMaxWidth()
                .padding(horizontal = 20.dp, vertical = 16.dp)
                .verticalScroll(rememberScrollState())
                .clip(RoundedCornerShape(28.dp))
                .background(mc.bg2.copy(alpha = 0.92f))
                .border(1.dp, mc.glassBorder, RoundedCornerShape(28.dp))
                .padding(26.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    Box(
                        Modifier
                            .size(42.dp)
                            .clip(CircleShape)
                            .background(mc.accentSoft),
                        contentAlignment = Alignment.Center,
                    ) {
                        androidx.compose.material3.Icon(
                            androidx.compose.ui.res.painterResource(dev.mcmusic.app.R.drawable.ic_logo),
                            contentDescription = null,
                            modifier = Modifier.size(22.dp),
                            tint = mc.accent,
                        )
                    }
                    Column {
                        Text("mcmusic", style = McType.h2, color = mc.fg)
                        Text("Your music, your space", style = McType.bodyXs, color = mc.dim)
                    }
                }
                Text(
                    if (resetting) "Let’s get you back in" else if (signingUp) "Create your account" else "Welcome back",
                    style = McType.h3.copy(fontWeight = FontWeight.SemiBold),
                    color = mc.fg,
                )
                Text(
                    when {
                        resetting -> "Enter your email and we’ll help you set a new password."
                        signingUp -> "A few details and you’ll be ready to start listening."
                        else -> "Sign in to pick up your playlists, likes, and listening right where you left off."
                    },
                    style = McType.bodySm,
                    color = mc.dim,
                )
            }

            if (resetting) {
                Text("Reset your password", style = McType.h3, color = mc.fg)
                Text(
                    "Enter the address on your account and we'll mail a one-time link. You can open it in a browser, or paste it below.",
                    style = McType.bodyXs,
                    color = mc.dim2,
                )
                McField(
                    resetEmail,
                    { resetEmail = it },
                    "you@example.com",
                    keyboardType = KeyboardType.Email,
                )
                McButton(
                    if (vm.resetBusy) "Sending…" else "Send reset link",
                    { vm.requestReset(resetEmail) },
                    solid = true,
                    enabled = !vm.resetBusy && resetEmail.isNotBlank(),
                )
                Box(Modifier.fillMaxWidth().height(1.dp).background(mc.line))
                McField(resetToken, { resetToken = it }, "Paste the reset link or token")
                McField(
                    resetPw,
                    { resetPw = it },
                    "New password (6+ characters)",
                    password = true,
                    keyboardType = KeyboardType.Password,
                )
                McButton(
                    "Set new password",
                    { vm.resetPassword(resetToken, resetPw) { mode = "in" } },
                    enabled = !vm.resetBusy && resetToken.isNotBlank() && resetPw.length >= 6,
                )
                vm.resetNotice?.let { note ->
                    Text(note, style = McType.bodyXs, color = mc.accent)
                }
                Text(
                    "Back to log in",
                    style = McType.labelSm,
                    color = mc.accent,
                    modifier = Modifier
                        .align(Alignment.CenterHorizontally)
                        .clickable {
                            vm.clearResetNotice()
                            mode = "in"
                        }
                        .padding(vertical = 4.dp),
                )
            } else {
                Seg(
                    options = listOf("in" to "Sign in", "up" to "Create account"),
                    selected = mode,
                    onSelect = { mode = it },
                    modifier = Modifier.align(Alignment.CenterHorizontally),
                )

                McField(username, { username = it }, "Username")
                McField(
                    password,
                    { password = it },
                    "Password",
                    password = true,
                    keyboardType = KeyboardType.Password,
                )
                if (signingUp) {
                    McField(invite, { invite = it }, "Invite code")
                }

                if (vm.loginError != null) {
                    Text(vm.loginError.orEmpty(), style = McType.bodyXs, color = mc.err)
                }

                Box(
                    Modifier
                        .fillMaxWidth()
                        .height(40.dp)
                        .clip(RoundedCornerShape(D.r2))
                        .background(mc.accent)
                        .clickable(enabled = !vm.busy) {
                            vm.login(server, username, password, signingUp, invite)
                        },
                    contentAlignment = Alignment.Center,
                ) {
                    if (vm.busy) {
                        CircularProgressIndicator(
                            Modifier.size(16.dp),
                            color = mc.accentFg,
                            strokeWidth = 2.dp,
                        )
                    } else {
                        Text(
                            if (signingUp) "Create account" else "Sign in",
                            style = McType.label,
                            color = mc.accentFg,
                        )
                    }
                }

                Text(
                    "Forgot password?",
                    style = McType.labelSm,
                    color = mc.dim,
                    modifier = Modifier
                        .align(Alignment.CenterHorizontally)
                        .clickable {
                            vm.clearResetNotice()
                            mode = "reset"
                        }
                        .padding(vertical = 2.dp),
                )
            }

            Box(Modifier.fillMaxWidth().height(1.dp).background(mc.line))

            Text(
                "Sign in to your mcmusic account. This app uses the same server as the web player, so your music stays in sync.",
                style = McType.bodyXs,
                color = mc.dim,
            )

            Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text("Server", style = McType.mono9, color = mc.dim2)
                McField(
                    server,
                    { server = it },
                    "https://mcmusic.sdisk.us",
                    keyboardType = KeyboardType.Uri,
                    leading = AppIcons.Cast,
                )
            }

            Text(
                "Sign in with your mcmusic account. The app uses the same server API as the web player.",
                style = McType.bodyXs,
                color = mc.dim2,
            )
        }
    }
}

