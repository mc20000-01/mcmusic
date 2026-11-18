package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
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
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.Listener
import dev.mcmusic.app.data.Me
import dev.mcmusic.app.ui.Cover
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.LiveDot
import dev.mcmusic.app.ui.McIcon
import dev.mcmusic.app.ui.Pill
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface
import dev.mcmusic.app.ui.timecode

@Composable
fun PlayerScreen() {
    val design = LocalDesign.current
    var me by remember { mutableStateOf<Me?>(null) }
    var mine by remember { mutableStateOf<Listener?>(null) }
    var loading by remember { mutableStateOf(true) }
    var showLogin by remember { mutableStateOf(false) }
    var reload by remember { mutableStateOf(0) }

    LaunchedEffect(reload) {
        loading = true
        me = Api.me()
        mine = me?.username?.let { Api.now(it).getOrNull() }
        loading = false
    }

    val track = mine?.track

    LazyColumn(
        contentPadding = PaddingValues(
            start = design.screenPadding,
            end = design.screenPadding,
            top = 12.dp,
            bottom = 124.dp,
        ),
        verticalArrangement = Arrangement.spacedBy(design.gap),
    ) {
        item { ScreenTitle("Player", "Your account's current playback") }

        item {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .mcSurface(RoundedCornerShape(design.cardRadius), tint = design.accent.copy(alpha = 0.08f))
                    .padding(horizontal = 20.dp, vertical = 26.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(18.dp),
            ) {
                Platter(
                    coverUrl = mine?.coverUrl.orEmpty(),
                    spinning = mine?.listening == true,
                )
                Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text(
                        text = track?.title ?: if (me == null) "Not signed in" else "Nothing playing",
                        color = design.fg,
                        fontSize = 20.sp,
                        fontWeight = FontWeight.SemiBold,
                        textAlign = TextAlign.Center,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis,
                    )
                    Text(
                        text = listOfNotNull(
                            track?.artist?.takeIf { it.isNotBlank() },
                            track?.album?.takeIf { it.isNotBlank() },
                        ).joinToString(" · ").ifBlank {
                            if (loading) "Checking your account…"
                            else if (me == null) "Sign in to see what your account is playing"
                            else "Start something on the web or another device"
                        },
                        color = design.dim,
                        fontSize = 13.sp,
                        textAlign = TextAlign.Center,
                    )
                }

                if (track != null && track.duration > 0) {
                    Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Progress(position = mine?.position ?: 0.0, duration = track.duration)
                        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            Text(timecode(mine?.position ?: 0.0), color = design.dim, fontSize = 11.sp)
                            Text(timecode(track.duration), color = design.dim, fontSize = 11.sp)
                        }
                    }
                }

                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    if (me != null) {
                        Pill(if (mine?.listening == true) "playing" else "paused", mine?.listening == true)
                        Text(me!!.username, color = design.dim, fontSize = 12.sp)
                    }
                }
            }
        }

        if (me == null) {
            item {
                EmptyState(
                    icon = McIcon.Play,
                    title = "Sign in to unlock the player",
                    body = "The player reads the playback your account already has. Until the phone has its own playback service, controls live on the web and on your other devices.",
                    actionLabel = "Sign in",
                    onAction = { showLogin = true },
                )
            }
        } else {
            item {
                EmptyState(
                    icon = McIcon.Download,
                    title = "Playback service not built yet",
                    body = "This page mirrors your account's playback. Local playback, queue editing and scrubbing come with the playback service in a later pass.",
                    actionLabel = "Check again",
                    onAction = { reload++ },
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

/** A record: palette-tinted sleeve, cover as the label, grooves drawn as rings. */
@Composable
private fun Platter(coverUrl: String, spinning: Boolean) {
    val design = LocalDesign.current
    Box(
        modifier = Modifier
            .size(196.dp)
            .clip(CircleShape),
        contentAlignment = Alignment.Center,
    ) {
        Canvas(Modifier.size(196.dp)) {
            drawCircle(design.palette.bg2)
            val rings = 14
            for (i in 1..rings) {
                val r = size.minDimension / 2f * (i / (rings + 1f))
                drawCircle(
                    color = design.palette.line.copy(alpha = 0.45f),
                    radius = r,
                    style = Stroke(width = 1.dp.toPx()),
                )
            }
            drawCircle(
                color = design.accent.copy(alpha = 0.18f),
                radius = size.minDimension / 2f,
                style = Stroke(width = 2.dp.toPx()),
            )
            drawCircle(
                color = design.palette.bg2,
                radius = 6.dp.toPx(),
                center = center,
            )
            drawCircle(
                color = design.dim.copy(alpha = 0.6f),
                radius = 2.dp.toPx(),
                center = Offset(center.x, center.y),
            )
        }
        Cover(
            url = coverUrl,
            shape = CircleShape,
            modifier = Modifier.size(104.dp),
            fallback = design.palette.bg2,
        )
        if (spinning) {
            Box(
                Modifier
                    .size(20.dp)
                    .clip(CircleShape)
                    .background(design.accent.copy(alpha = 0.9f)),
            )
        }
    }
}

@Composable
private fun Progress(position: Double, duration: Double) {
    val design = LocalDesign.current
    val fraction = (position / duration).coerceIn(0.0, 1.0).toFloat()
    Box(
        Modifier
            .fillMaxWidth()
            .height(5.dp)
            .clip(RoundedCornerShape(50))
            .background(design.palette.line.copy(alpha = 0.5f)),
    ) {
        Box(
            Modifier
                .fillMaxWidth(fraction)
                .height(5.dp)
                .clip(RoundedCornerShape(50))
                .background(design.accent),
        )
    }
}

