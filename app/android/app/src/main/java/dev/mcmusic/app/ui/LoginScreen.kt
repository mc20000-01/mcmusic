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

    val signingUp = mode == "up"

    Box(
        Modifier
            .fillMaxSize()
            .background(mc.bg)
            .systemBarsPadding()
            .imePadding(),
        contentAlignment = Alignment.Center,
    ) {
        Column(
            Modifier
                .widthIn(max = 380.dp)
                .fillMaxWidth()
                .padding(horizontal = 22.dp)
                .verticalScroll(rememberScrollState())
                .clip(RoundedCornerShape(D.r4))
                .background(mc.bg2)
                .border(1.dp, mc.line2, RoundedCornerShape(D.r4))
                .padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                androidx.compose.material3.Icon(
                    androidx.compose.ui.res.painterResource(dev.mcmusic.app.R.drawable.ic_logo),
                    contentDescription = null,
                    modifier = Modifier.size(34.dp),
                    tint = mc.accent,
                )
                Text("mcmusic", style = McType.h2, color = mc.fg)
            }
            Text(
                "Your music, on your terms.",
                style = McType.bodySm,
                color = mc.dim2,
            )

            Seg(
                options = listOf("in" to "Log in", "up" to "Sign up"),
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
                        if (signingUp) "Create account" else "Log in",
                        style = McType.label,
                        color = mc.accentFg,
                    )
                }
            }

            Box(Modifier.fillMaxWidth().height(1.dp).background(mc.line))

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

