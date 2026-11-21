package dev.mcmusic.app.ui

import androidx.annotation.DrawableRes
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Track
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface

/* ── text ──────────────────────────────────────────────────────────────── */

/** Page title, as the web client's h1. */
@Composable
fun ScreenTitle(title: String, subtitle: String? = null, modifier: Modifier = Modifier) {
    val design = LocalDesign.current
    Column(modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(3.dp)) {
        Text(title, color = design.fg, fontSize = design.titleSize, fontWeight = design.titleWeight)
        if (subtitle != null) {
            Text(subtitle, color = design.dim, fontSize = 13.sp, maxLines = 2, overflow = TextOverflow.Ellipsis)
        }
    }
}

/** Small uppercase section heading, optionally with a trailing action. */
@Composable
fun SectionLabel(text: String, modifier: Modifier = Modifier, action: (@Composable () -> Unit)? = null) {
    val design = LocalDesign.current
    Row(
        modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Text(
            text.uppercase(),
            color = design.dim,
            fontSize = design.sectionSize,
            fontWeight = design.sectionWeight,
            letterSpacing = 1.1.sp,
        )
        action?.invoke()
    }
}

@Composable
fun Muted(text: String, modifier: Modifier = Modifier, size: Int = 13) {
    Text(text, modifier = modifier, color = LocalDesign.current.dim, fontSize = size.sp)
}

/* ── buttons ───────────────────────────────────────────────────────────── */

@Composable
fun PrimaryButton(text: String, modifier: Modifier = Modifier, enabled: Boolean = true, onClick: () -> Unit) {
    val design = LocalDesign.current
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(design.tileRadius))
            .background(if (enabled) design.accent else design.accent.copy(alpha = 0.35f))
            .clickable(enabled = enabled) { onClick() }
            .padding(horizontal = 18.dp, vertical = 12.dp),
        contentAlignment = Alignment.Center,
    ) {
        Text(text, color = design.palette.bg, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
fun GhostButton(text: String, modifier: Modifier = Modifier, danger: Boolean = false, onClick: () -> Unit) {
    val design = LocalDesign.current
    val tint = if (danger) Danger else design.fg
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(design.tileRadius))
            .border(
                1.dp,
                if (danger) Danger.copy(alpha = 0.5f) else design.hairline,
                RoundedCornerShape(design.tileRadius),
            )
            .clickable { onClick() }
            .padding(horizontal = 16.dp, vertical = 11.dp),
        contentAlignment = Alignment.Center,
    ) {
        Text(text, color = tint, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
fun IconButton(
    @DrawableRes icon: Int,
    modifier: Modifier = Modifier,
    size: Dp = 20.dp,
    tint: Color? = null,
    onClick: () -> Unit,
) {
    val design = LocalDesign.current
    Box(
        modifier = modifier.size(44.dp).clip(CircleShape).clickable { onClick() },
        contentAlignment = Alignment.Center,
    ) {
        LucideIcon(icon, tint ?: design.dim, Modifier.size(size))
    }
}

/* ── text field ────────────────────────────────────────────────────────── */

@Composable
fun McField(
    value: String,
    onValueChange: (String) -> Unit,
    label: String,
    modifier: Modifier = Modifier,
    password: Boolean = false,
    keyboard: KeyboardOptions = KeyboardOptions(imeAction = ImeAction.Next),
    actions: KeyboardActions = KeyboardActions.Default,
) {
    val design = LocalDesign.current
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        label = { Text(label, fontSize = 12.sp) },
        singleLine = true,
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(design.tileRadius),
        textStyle = androidx.compose.ui.text.TextStyle(color = design.fg, fontSize = 14.sp),
        visualTransformation = if (password) PasswordVisualTransformation() else VisualTransformation.None,
        keyboardOptions = keyboard,
        keyboardActions = actions,
        colors = OutlinedTextFieldDefaults.colors(
            focusedTextColor = design.fg,
            unfocusedTextColor = design.fg,
            focusedBorderColor = design.accent,
            unfocusedBorderColor = design.hairline,
            focusedLabelColor = design.accent,
            unfocusedLabelColor = design.dim,
            cursorColor = design.accent,
            focusedContainerColor = design.cardFill,
            unfocusedContainerColor = design.cardFill,
        ),
    )
}

/* ── status ────────────────────────────────────────────────────────────── */

@Composable
fun LiveDot(active: Boolean, size: Dp = 6.dp) {
    val design = LocalDesign.current
    Box(
        Modifier
            .size(size)
            .clip(CircleShape)
            .background(if (active) design.accent else design.dim.copy(alpha = 0.4f)),
    )
}

@Composable
fun Pill(text: String, active: Boolean = true, modifier: Modifier = Modifier) {
    val design = LocalDesign.current
    Row(
        modifier
            .clip(RoundedCornerShape(50))
            .background(design.accentWash)
            .border(1.dp, design.hairline, RoundedCornerShape(50))
            .padding(horizontal = 11.dp, vertical = 5.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        LiveDot(active, 6.dp)
        Text(text, color = if (active) design.fg else design.dim, fontSize = 11.sp, fontWeight = FontWeight.Medium)
    }
}

@Composable
fun Loading(text: String = "Loading…", modifier: Modifier = Modifier) {
    val design = LocalDesign.current
    Row(
        modifier.fillMaxWidth().padding(vertical = 28.dp),
        horizontalArrangement = Arrangement.Center,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        CircularProgressIndicator(
            modifier = Modifier.size(16.dp),
            strokeWidth = 2.dp,
            color = design.accent,
        )
        Box(Modifier.width(10.dp))
        Text(text, color = design.dim, fontSize = 13.sp)
    }
}

@Composable
fun ErrorLine(message: String, modifier: Modifier = Modifier) {
    Text(
        message,
        modifier = modifier.fillMaxWidth().clip(RoundedCornerShape(8.dp))
            .background(Danger.copy(alpha = 0.10f))
            .border(1.dp, Danger.copy(alpha = 0.35f), RoundedCornerShape(8.dp))
            .padding(horizontal = 12.dp, vertical = 9.dp),
        color = Danger,
        fontSize = 12.sp,
    )
}

@Composable
fun EmptyState(
    @DrawableRes icon: Int,
    title: String,
    body: String,
    modifier: Modifier = Modifier,
    actionLabel: String? = null,
    onAction: (() -> Unit)? = null,
) {
    val design = LocalDesign.current
    Column(
        modifier.fillMaxWidth().mcSurface().padding(horizontal = 24.dp, vertical = 32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Box(Modifier.size(56.dp).clip(CircleShape).background(design.accentSoft), Alignment.Center) {
            LucideIcon(icon, design.accent, Modifier.size(24.dp))
        }
        Text(title, color = design.fg, fontSize = 17.sp, fontWeight = FontWeight.SemiBold, textAlign = TextAlign.Center)
        Text(body, color = design.dim, fontSize = 13.sp, lineHeight = 19.sp, textAlign = TextAlign.Center)
        if (actionLabel != null && onAction != null) {
            PrimaryButton(actionLabel, Modifier.padding(top = 2.dp), onClick = onAction)
        }
    }
}

@Composable
fun ScreenBack(onBack: () -> Unit) {
    Row(
        Modifier
            .clip(RoundedCornerShape(50))
            .background(LocalDesign.current.accentWash)
            .clickable { onBack() }
            .padding(vertical = 9.dp, horizontal = 14.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        LucideIcon(Lucide.ChevronLeft, LocalDesign.current.accent, Modifier.size(16.dp))
        Text("Back", color = LocalDesign.current.fg, fontSize = 13.sp, fontWeight = FontWeight.Medium)
    }
}

/* ── music pieces ──────────────────────────────────────────────────────── */

/** Square cover that falls back to a neutral tile when a track has no art. */
@Composable
fun TrackCover(track: Track, size: Dp = 44.dp, radius: Dp = 6.dp) {
    Cover(
        url = trackCoverUrl(track.id),
        shape = RoundedCornerShape(radius),
        modifier = Modifier.size(size),
        fallback = LocalDesign.current.accentSoft,
    )
}

@Composable
fun TrackRow(
    track: Track,
    modifier: Modifier = Modifier,
    subtitle: String? = null,
    trailing: (@Composable RowScope.() -> Unit)? = null,
    onClick: () -> Unit,
) {
    val design = LocalDesign.current
    val current = dev.mcmusic.app.playback.Playback.state.track?.id == track.id
    Row(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(design.tileRadius))
            .background(if (current) design.accentWash else Color.Transparent)
            .clickable { onClick() }
            .padding(horizontal = 10.dp, vertical = 9.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        TrackCover(track, 46.dp, 12.dp)
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Text(
                track.title,
                color = if (current) design.accent else design.fg,
                fontSize = 15.sp,
                fontWeight = FontWeight.Medium,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            Text(
                subtitle ?: listOf(track.artist, track.album).filter { it.isNotBlank() }.joinToString(" · "),
                color = design.dim,
                fontSize = 12.sp,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        }
        trailing?.invoke(this)
    }
}

/** Cover + two lines, used in horizontal rows of albums/artists/playlists. */
@Composable
fun MediaCard(
    title: String,
    subtitle: String,
    coverUrl: String,
    modifier: Modifier = Modifier,
    width: Dp = 132.dp,
    round: Boolean = false,
    onClick: () -> Unit,
) {
    val design = LocalDesign.current
    Column(
        modifier.width(width).clip(RoundedCornerShape(design.tileRadius)).clickable { onClick() },
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Cover(
            url = coverUrl,
            shape = if (round) CircleShape else RoundedCornerShape(design.tileRadius),
            modifier = Modifier.size(width),
            fallback = design.accentSoft,
        )
        Text(
            title,
            color = design.fg,
            fontSize = 14.sp,
            fontWeight = FontWeight.SemiBold,
            maxLines = 2,
            overflow = TextOverflow.Ellipsis,
        )
        Text(subtitle, color = design.dim, fontSize = 12.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
    }
}

/* ── settings pieces ───────────────────────────────────────────────────── */

/** Card that groups settings rows. */
@Composable
fun SettingCard(modifier: Modifier = Modifier, content: @Composable () -> Unit) {
    Column(modifier.fillMaxWidth().mcSurface().padding(horizontal = 14.dp, vertical = 2.dp)) {
        content()
    }
}

@Composable
fun SettingRow(
    title: String,
    subtitle: String? = null,
    @DrawableRes icon: Int? = null,
    value: String? = null,
    danger: Boolean = false,
    onClick: (() -> Unit)? = null,
    trailing: (@Composable () -> Unit)? = null,
) {
    val design = LocalDesign.current
    val tint = if (danger) Danger else design.fg
    Row(
        Modifier
            .fillMaxWidth()
            .then(if (onClick != null) Modifier.clickable { onClick() } else Modifier)
            .padding(vertical = 11.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(11.dp),
    ) {
        if (icon != null) {
            Box(
                Modifier.size(28.dp).clip(RoundedCornerShape(7.dp))
                    .background(if (danger) Danger.copy(alpha = 0.12f) else design.accentSoft),
                Alignment.Center,
            ) {
                LucideIcon(icon, if (danger) Danger else design.accent, Modifier.size(14.dp))
            }
        }
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(1.dp)) {
            Text(
                title,
                color = tint,
                fontSize = 14.sp,
                fontWeight = FontWeight.Medium,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            if (subtitle != null) {
                Text(subtitle, color = design.dim, fontSize = 11.sp, lineHeight = 15.sp)
            }
        }
        if (value != null) {
            Text(
                value,
                color = design.dim,
                fontSize = 12.sp,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        }
        trailing?.invoke()
    }
}

@Composable
fun SettingDivider() {
    Box(Modifier.fillMaxWidth().height(1.dp).background(LocalDesign.current.hairline))
}

@Composable
fun SwitchRow(
    title: String,
    subtitle: String? = null,
    @DrawableRes icon: Int? = null,
    checked: Boolean,
    onChange: (Boolean) -> Unit,
) {
    val design = LocalDesign.current
    SettingRow(title = title, subtitle = subtitle, icon = icon) {
        Switch(
            checked = checked,
            onCheckedChange = onChange,
            colors = SwitchDefaults.colors(
                checkedThumbColor = design.palette.bg,
                checkedTrackColor = design.accent,
                uncheckedThumbColor = design.dim,
                uncheckedTrackColor = design.palette.bg2,
                uncheckedBorderColor = design.hairline,
            ),
        )
    }
}

/* ── helpers ───────────────────────────────────────────────────────────── */

val Danger = Color(0xFFE5484D)

fun formatDuration(seconds: Double): String {
    if (seconds <= 0) return "--:--"
    val total = seconds.toLong()
    return "%d:%02d".format(total / 60, total % 60)
}

fun formatMillis(ms: Long): String = formatDuration(ms / 1000.0)

fun formatBytes(bytes: Long): String = when {
    bytes >= 1L shl 30 -> "%.1f GB".format(bytes / (1L shl 30).toDouble())
    bytes >= 1L shl 20 -> "%.1f MB".format(bytes / (1L shl 20).toDouble())
    bytes >= 1L shl 10 -> "%.0f KB".format(bytes / 1024.0)
    else -> "$bytes B"
}

fun trackCoverUrl(id: Int): String = "${dev.mcmusic.app.data.Api.server}/api/tracks/$id/cover"

fun emptyModifier(): Modifier = Modifier.fillMaxSize()
