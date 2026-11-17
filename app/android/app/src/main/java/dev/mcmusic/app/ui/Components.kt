@file:OptIn(
    androidx.compose.material3.ExperimentalMaterial3Api::class,
    androidx.compose.foundation.ExperimentalFoundationApi::class,
)

package dev.mcmusic.app.ui

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.animateDpAsState
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.LocalIndication
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.gestures.detectHorizontalDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Icon
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.Text
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawWithCache
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.em
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.AlbumRef
import dev.mcmusic.app.data.ArtistRef
import dev.mcmusic.app.data.PlaylistRef
import dev.mcmusic.app.data.Track
import dev.mcmusic.app.ui.theme.D
import dev.mcmusic.app.ui.theme.LocalMc
import dev.mcmusic.app.ui.theme.McType
import dev.mcmusic.app.ui.theme.glass
import kotlinx.coroutines.delay

data class ListPrefs(val covers: Boolean = true, val compact: Boolean = false)

val LocalListPrefs = staticCompositionLocalOf { ListPrefs() }

/* ── buttons ────────────────────────────────────────────────────────────── */

@Composable
fun McButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    solid: Boolean = false,
    ghost: Boolean = false,
    small: Boolean = false,
    danger: Boolean = false,
    enabled: Boolean = true,
    leading: ImageVector? = null,
) {
    val mc = LocalMc.current
    val shape = RoundedCornerShape(99.dp)
    val interaction = remember { MutableInteractionSource() }
    val pressed by interaction.collectIsPressedAsState()
    val pressScale by animateFloatAsState(if (pressed) 0.97f else 1f, label = "btn-scale")
    val pressLift by animateFloatAsState(if (pressed) 0.6f else 1f, label = "btn-lift")

    val bgBrush = when {
        !enabled -> Brush.linearGradient(listOf(mc.glass.copy(alpha = 0.35f), mc.glass.copy(alpha = 0.25f)))
        solid -> Brush.linearGradient(
            listOf(
                mc.accent.copy(alpha = 0.98f),
                mc.accent.copy(alpha = 0.82f),
                mc.accent.copy(alpha = 0.92f),
            )
        )
        ghost -> Brush.linearGradient(listOf(Color.Transparent, Color.Transparent))
        danger -> Brush.linearGradient(
            listOf(mc.err.copy(alpha = 0.16f), mc.err.copy(alpha = 0.08f))
        )
        else -> Brush.linearGradient(
            listOf(mc.glassStrong.copy(alpha = 0.72f), mc.glass.copy(alpha = 0.56f))
        )
    }
    val borderBrush = when {
        solid -> Brush.linearGradient(
            listOf(mc.glassHighlight.copy(alpha = 0.55f), mc.accent.copy(alpha = 0.5f))
        )
        ghost -> Brush.linearGradient(listOf(Color.Transparent, Color.Transparent))
        danger -> Brush.linearGradient(
            listOf(mc.err.copy(alpha = 0.55f), mc.err.copy(alpha = 0.25f))
        )
        else -> Brush.linearGradient(
            listOf(mc.glassHighlight.copy(alpha = 0.7f), mc.glassBorder.copy(alpha = 0.7f))
        )
    }
    val fg = when {
        !enabled -> mc.dim.copy(alpha = 0.5f)
        solid -> mc.accentFg
        ghost -> mc.dim
        danger -> mc.err
        else -> mc.fg
    }
    Box(
        modifier = modifier
            .graphicsLayer {
                scaleX = pressScale
                scaleY = pressScale
                alpha = pressLift
            }
            .height(if (small) 30.dp else 38.dp)
            .clip(shape)
            .background(bgBrush)
            .border(1.dp, borderBrush, shape)
            .drawWithCache {
                onDrawWithContent {
                    drawContent()
                    if (!ghost) {
                        drawRect(
                            Brush.verticalGradient(
                                listOf(
                                    mc.glassHighlight.copy(alpha = if (solid) 0.28f else 0.18f),
                                    Color.Transparent,
                                )
                            )
                        )
                    }
                }
            }
            .clickable(
                enabled = enabled,
                interactionSource = interaction,
                indication = LocalIndication.current,
                onClick = onClick,
            )
            .padding(horizontal = if (small) 12.dp else 17.dp),
        contentAlignment = Alignment.Center,
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(7.dp),
        ) {
            if (leading != null) {
                Icon(leading, null, Modifier.size(if (small) 12.dp else 14.dp), tint = fg)
            }
            Text(
                text,
                style = if (small) McType.labelSm else McType.label,
                color = fg,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        }
    }
}

@Composable
fun IconBtn(
    icon: ImageVector,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    size: Dp = 32.dp,
    active: Boolean = false,
    tint: Color? = null,
    contentDescription: String? = null,
) {
    val mc = LocalMc.current
    Box(
        modifier
            .size(size)
            .clip(CircleShape)
            .background(if (active) mc.accentSoft else Color.Transparent)
            .then(
                if (active) Modifier.border(1.dp, mc.accent.copy(alpha = 0.35f), CircleShape)
                else Modifier
            )
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center,
    ) {
        Icon(
            icon,
            contentDescription,
            Modifier.size(minOf(size * 0.6f, 24.dp)),
            tint = tint ?: if (active) mc.accent else mc.dim,
        )
    }
}

/* ── artwork ────────────────────────────────────────────────────────────── */

@Composable
fun Art(
    trackId: Int?,
    size: Dp?,
    round: Boolean = false,
    modifier: Modifier = Modifier,
) {
    val mc = LocalMc.current
    val shape = if (round) CircleShape else RoundedCornerShape(D.r2)
    val bmp = rememberArt(trackId)
    val sized = if (size != null) modifier.size(size) else modifier
    Box(
        sized
            .clip(shape)
            .background(mc.surface2)
            .border(1.dp, mc.line, shape),
        contentAlignment = Alignment.Center,
    ) {
        if (bmp != null) {
            Image(bmp, null, Modifier.fillMaxSize(), contentScale = ContentScale.Crop)
        } else {
            Icon(
                if (round) AppIcons.Users else AppIcons.Disc,
                null,
                Modifier.fillMaxSize(0.34f),
                tint = mc.dim2,
            )
        }
    }
}

/* ── inputs ─────────────────────────────────────────────────────────────── */

@Composable
fun McField(
    value: String,
    onValueChange: (String) -> Unit,
    placeholder: String,
    modifier: Modifier = Modifier,
    password: Boolean = false,
    keyboardType: KeyboardType = KeyboardType.Text,
    leading: ImageVector? = null,
    trailing: (@Composable () -> Unit)? = null,
) {
    val mc = LocalMc.current
    val shape = RoundedCornerShape(16.dp)
    BasicTextField(
        value = value,
        onValueChange = onValueChange,
        singleLine = true,
        textStyle = McType.body.copy(fontSize = 15.sp, color = mc.fg),
        cursorBrush = SolidColor(mc.accent),
        visualTransformation = if (password) PasswordVisualTransformation() else VisualTransformation.None,
        keyboardOptions = KeyboardOptions(keyboardType = keyboardType),
        modifier = modifier
            .fillMaxWidth()
            .height(40.dp)
            .clip(shape)
            .background(mc.glass)
            .border(1.dp, mc.glassBorder, shape)
            .padding(horizontal = 12.dp),
        decorationBox = { inner ->
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(7.dp)) {
                if (leading != null) {
                    Icon(leading, null, Modifier.size(18.dp), tint = LocalMc.current.dim2)
                }
                Box(Modifier.weight(1f), contentAlignment = Alignment.CenterStart) {
                    if (value.isEmpty()) {
                        Text(placeholder, style = McType.body.copy(fontSize = 15.sp), color = mc.dim2, maxLines = 1)
                    }
                    inner()
                }
                trailing?.invoke()
            }
        },
    )
}

@Composable
fun SwitchPill(checked: Boolean, onChange: (Boolean) -> Unit) {
    val mc = LocalMc.current
    val knob by animateDpAsState(
        targetValue = if (checked) 20.dp else 2.dp,
        animationSpec = spring(
            dampingRatio = Spring.DampingRatioMediumBouncy,
            stiffness = Spring.StiffnessMediumLow,
        ),
        label = "switch knob",
    )
    val trackBrush = Brush.horizontalGradient(
        if (checked) listOf(mc.accent.copy(alpha = 0.85f), mc.accent.copy(alpha = 0.55f))
        else listOf(mc.glassStrong.copy(alpha = 0.55f), mc.glass.copy(alpha = 0.45f))
    )
    Box(
        Modifier
            .size(width = 42.dp, height = 24.dp)
            .clip(CircleShape)
            .background(trackBrush)
            .border(
                1.dp,
                Brush.linearGradient(
                    if (checked) listOf(mc.accent.copy(alpha = 0.65f), mc.glassHighlight.copy(alpha = 0.5f))
                    else listOf(mc.glassHighlight.copy(alpha = 0.45f), mc.glassBorder)
                ),
                CircleShape,
            )
            .drawWithCache {
                onDrawWithContent {
                    drawContent()
                    drawRect(
                        Brush.verticalGradient(
                            listOf(mc.glassHighlight.copy(alpha = 0.22f), Color.Transparent)
                        )
                    )
                }
            }
            .clickable { onChange(!checked) }
            .padding(2.dp),
    ) {
        Box(
            Modifier
                .offset(x = knob)
                .size(18.dp)
                .clip(CircleShape)
                .background(
                    Brush.radialGradient(
                        listOf(Color.White.copy(alpha = 0.96f), if (checked) mc.accentFg else mc.fg.copy(alpha = 0.88f))
                    )
                )
                .border(1.dp, mc.glassBorder.copy(alpha = 0.8f), CircleShape),
        )
    }
}

@Composable
fun Seg(
    options: List<Pair<String, String>>,
    selected: String,
    onSelect: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val mc = LocalMc.current
    val shape = RoundedCornerShape(99.dp)
    Row(
        modifier
            .clip(shape)
            .background(
                Brush.linearGradient(
                    listOf(mc.glassStrong.copy(alpha = 0.58f), mc.glass.copy(alpha = 0.45f))
                )
            )
            .border(1.dp, Brush.linearGradient(listOf(mc.glassHighlight.copy(alpha = 0.5f), mc.glassBorder)), shape)
            .drawWithCache {
                onDrawWithContent {
                    drawContent()
                    drawRect(Brush.verticalGradient(listOf(mc.glassHighlight.copy(alpha = 0.12f), Color.Transparent)))
                }
            }
            .padding(3.dp),
        horizontalArrangement = Arrangement.spacedBy(3.dp),
    ) {
        options.forEach { (key, label) ->
            val on = key == selected
            Box(
                Modifier
                    .clip(shape)
                    .background(
                        if (on) Brush.linearGradient(listOf(mc.accent.copy(alpha = 0.95f), mc.accent.copy(alpha = 0.78f)))
                        else Brush.linearGradient(listOf(Color.Transparent, Color.Transparent))
                    )
                    .then(
                        if (on) Modifier.border(
                            1.dp,
                            Brush.linearGradient(listOf(mc.glassHighlight.copy(alpha = 0.45f), mc.accent.copy(alpha = 0.35f))),
                            shape,
                        ) else Modifier
                    )
                    .clickable { onSelect(key) }
                    .padding(horizontal = 13.dp, vertical = 6.dp),
            ) {
                Text(
                    label,
                    style = McType.labelSm,
                    color = if (on) mc.accentFg else mc.dim,
                    maxLines = 1,
                )
            }
        }
    }
}

/* ── headings and panels ────────────────────────────────────────────────── */

@Composable
fun SectionHead(text: String, meta: String? = null, actions: @Composable RowScope.() -> Unit = {}) {
    val mc = LocalMc.current
    Row(
        Modifier
            .fillMaxWidth()
            .padding(bottom = 14.dp),
        verticalAlignment = Alignment.Bottom,
        horizontalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Text(text, style = McType.h1Small, color = mc.fg)
        if (meta != null) {
            Text(meta, style = McType.bodyXs, color = mc.fg.copy(alpha = 0.62f))
        }
        Spacer(Modifier.weight(1f))
        actions()
    }
}

@Composable
fun Panel(title: String? = null, content: @Composable ColumnScope.() -> Unit) {
    val mc = LocalMc.current
    Column(
        Modifier
            .fillMaxWidth()
            .padding(bottom = 26.dp)
            .glass(RoundedCornerShape(D.r3)),
    ) {
        if (title != null) {
            Text(
                title.uppercase(),
                style = McType.mono10.copy(fontSize = 11.sp, letterSpacing = 0.12.em),
                color = mc.fg.copy(alpha = 0.55f),
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(start = 16.dp, end = 16.dp, top = 18.dp, bottom = 8.dp),
            )
        }
        content()
    }
}

@Composable
fun SettingRow(
    title: String,
    subtitle: String? = null,
    last: Boolean = false,
    trailing: @Composable () -> Unit = {},
) {
    val mc = LocalMc.current
    Row(
        Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(18.dp),
    ) {
        Column(Modifier.weight(1f)) {
            Text(
                title,
                style = McType.bodySm.copy(fontSize = 14.sp, fontWeight = FontWeight.Medium),
                color = mc.fg,
            )
            if (subtitle != null) {
                Text(subtitle, style = McType.bodyXs, color = mc.fg.copy(alpha = 0.62f))
            }
        }
        trailing()
    }
}

@Composable
fun EmptyState(
    title: String,
    hint: String? = null,
    icon: ImageVector = AppIcons.Music,
    actionLabel: String? = null,
    onAction: (() -> Unit)? = null,
) {
    val mc = LocalMc.current
    Column(
        Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 16.dp)
            .glass(RoundedCornerShape(24.dp))
            .padding(vertical = 44.dp, horizontal = 24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Box(
            Modifier
                .size(52.dp)
                .clip(CircleShape)
                .background(mc.accentSoft),
            contentAlignment = Alignment.Center,
        ) {
            Icon(icon, null, Modifier.size(24.dp), tint = mc.accent)
        }
        Text(title, style = McType.h3.copy(fontWeight = FontWeight.SemiBold), color = mc.fg)
        if (hint != null) {
            Text(
                hint,
                style = McType.bodySm,
                color = mc.dim,
                modifier = Modifier.widthIn(max = 320.dp),
            )
        }
        if (actionLabel != null && onAction != null) {
            Spacer(Modifier.height(2.dp))
            McButton(actionLabel, onAction, solid = true)
        }
    }
}

@Composable
fun Notice(text: String, actionLabel: String? = null, onAction: (() -> Unit)? = null) {
    val mc = LocalMc.current
    Row(
        Modifier
            .fillMaxWidth()
            .padding(bottom = 14.dp)
            .glass(RoundedCornerShape(D.r2))
            .padding(horizontal = 14.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Icon(AppIcons.Info, null, Modifier.size(15.dp), tint = mc.accent)
        Text(text, style = McType.bodySm, color = mc.fg, modifier = Modifier.weight(1f))
        if (actionLabel != null && onAction != null) {
            McButton(actionLabel, onAction, small = true)
        }
    }
}

/* ── progress ───────────────────────────────────────────────────────────── */

@Composable
fun ProgressBar(
    position: Double,
    duration: Double,
    onSeekFraction: (Float) -> Unit,
    modifier: Modifier = Modifier,
) {
    val mc = LocalMc.current
    val fraction = if (duration > 0) (position / duration).toFloat().coerceIn(0f, 1f) else 0f
    Row(
        modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(9.dp),
    ) {
        Text(
            fmtTime(position),
            style = McType.mono9,
            color = mc.dim,
            modifier = Modifier.width(28.dp),
        )
        Canvas(
            Modifier
                .weight(1f)
                .height(30.dp)
                .pointerInput(duration) {
                    detectTapGestures { offset ->
                        onSeekFraction((offset.x / size.width).coerceIn(0f, 1f))
                    }
                }
                .pointerInput(duration) {
                    detectHorizontalDragGestures { change, _ ->
                        onSeekFraction((change.position.x / size.width).coerceIn(0f, 1f))
                    }
                },
        ) {
            val cy = size.height / 2f
            val groove = 3.dp.toPx()
            val radius = CornerRadius(groove / 2f, groove / 2f)
            drawRoundRect(
                color = mc.line,
                topLeft = Offset(0f, cy - groove / 2f),
                size = Size(size.width, groove),
                cornerRadius = radius,
            )
            if (fraction > 0f) {
                drawRoundRect(
                    color = mc.accent,
                    topLeft = Offset(0f, cy - groove / 2f),
                    size = Size(size.width * fraction, groove),
                    cornerRadius = radius,
                )
            }
            drawCircle(
                color = mc.fg,
                radius = 5.dp.toPx(),
                center = Offset(size.width * fraction, cy),
            )
        }
        Text(
            fmtTime(duration),
            style = McType.mono9,
            color = mc.dim,
            modifier = Modifier.width(28.dp),
        )
    }
}

/* ── track rows ─────────────────────────────────────────────────────────── */

/** Lets track rows open an artist page without threading a callback everywhere. */
object ArtistNav {
    var go: ((String) -> Unit)? = null
}

/** One tappable credit per collaborator; used by rows, the deck and the queue. */
@Composable
fun ArtistCredits(
    t: Track,
    style: androidx.compose.ui.text.TextStyle,
    color: androidx.compose.ui.graphics.Color,
) {
    val nav = ArtistNav.go
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        t.artists.ifEmpty { listOf(t.artist) }.forEach { name ->
            Text(
                name,
                style = style,
                color = color,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                modifier = Modifier
                    .then(if (nav != null) Modifier.clickable { nav(name) } else Modifier)
                    .padding(horizontal = 1.dp),
            )
        }
    }
}

@Composable
fun TrackRow(
    track: Track,
    number: Int,
    isCurrent: Boolean,
    onClick: () -> Unit,
    onLike: () -> Unit,
    onMore: () -> Unit,
    showStats: Boolean = false,
    modifier: Modifier = Modifier,
) {
    val mc = LocalMc.current
    val prefs = LocalListPrefs.current
    val haptics = LocalHapticFeedback.current
    Row(
        modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(D.r2))
            .background(if (isCurrent) mc.glassStrong else Color.Transparent)
            .combinedClickable(
                onClick = onClick,
                onLongClickLabel = "Track options",
                onLongClick = {
                    haptics.performHapticFeedback(HapticFeedbackType.LongPress)
                    onMore()
                },
            )
            .padding(horizontal = 6.dp, vertical = if (prefs.compact) 3.dp else 5.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text(
            (number + 1).toString().padStart(2, '0'),
            style = McType.mono10,
            color = if (isCurrent) mc.accent else mc.dim2,
            modifier = Modifier.width(24.dp),
        )
        if (prefs.covers) Art(track.id, if (prefs.compact) 30.dp else 34.dp)
        Column(Modifier.weight(1f)) {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                Text(
                    track.title,
                    style = McType.bodySm.copy(fontWeight = FontWeight.Medium),
                    color = if (isCurrent) mc.accent else mc.fg,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.weight(1f, fill = false),
                )
                if (track.explicit) {
                    Text(
                        "E",
                        style = McType.mono9,
                        color = mc.dim,
                        modifier = Modifier
                            .border(1.dp, mc.dim2, RoundedCornerShape(D.r1))
                            .padding(horizontal = 3.dp, vertical = 1.dp),
                    )
                }
            }
            val nav = ArtistNav.go
            if (nav == null) {
                Text(
                    track.artist,
                    style = McType.mono10,
                    color = mc.dim,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            } else {
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    track.artists.ifEmpty { listOf(track.artist) }.forEach { name ->
                        Text(
                            name,
                            style = McType.mono10,
                            color = mc.dim,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                            modifier = Modifier
                                .clickable { nav.invoke(name) }
                                .padding(horizontal = 1.dp),
                        )
                    }
                }
            }
        }
        if (showStats && track.ytLikes != null) {
            Text(fmtCount(track.ytLikes), style = McType.mono10, color = mc.dim2)
        }
        IconBtn(
            AppIcons.Heart,
            onLike,
            size = 30.dp,
            active = track.liked,
            tint = if (track.liked) mc.accent else mc.dim,
        )
        IconBtn(AppIcons.MoreVertical, onMore, size = 30.dp)
    }
}

@Composable
fun TrackList(
    tracks: List<Track>,
    currentId: Int?,
    onPlay: (Int) -> Unit,
    onLike: (Track) -> Unit,
    onMore: (Track) -> Unit,
    showStats: Boolean = false,
    modifier: Modifier = Modifier,
) {
    Column(modifier.fillMaxWidth()) {
        tracks.forEachIndexed { i, t ->
            TrackRow(
                track = t,
                number = i,
                isCurrent = t.id == currentId,
                onClick = { onPlay(i) },
                onLike = { onLike(t) },
                onMore = { onMore(t) },
                showStats = showStats,
            )
        }
    }
}

/* ── shelves and tiles ──────────────────────────────────────────────────── */

@Composable
fun Shelf(title: String, meta: String? = null, content: @Composable () -> Unit) {
    Column(Modifier.fillMaxWidth().padding(bottom = 24.dp)) {
        Row(
            Modifier.fillMaxWidth().padding(bottom = 12.dp),
            verticalAlignment = Alignment.Bottom,
            horizontalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Text(title, style = McType.h3, color = LocalMc.current.fg)
            if (meta != null) {
                Text(meta, style = McType.mono9, color = LocalMc.current.dim2)
            }
        }
        content()
    }
}

@Composable
fun Tile(
    title: String,
    subtitle: String?,
    coverId: Int?,
    onClick: () -> Unit,
    onPlay: (() -> Unit)? = null,
    onLongPress: (() -> Unit)? = null,
    round: Boolean = false,
    width: Dp = 138.dp,
    fillWidth: Boolean = false,
) {
    val mc = LocalMc.current
    val haptics = LocalHapticFeedback.current
    val interaction = remember { MutableInteractionSource() }
    val pressed by interaction.collectIsPressedAsState()
    val pressScale by animateFloatAsState(
        targetValue = if (pressed) 0.955f else 1f,
        animationSpec = spring(stiffness = Spring.StiffnessMediumLow),
        label = "tile press",
    )
    Column(
        Modifier
            .then(if (fillWidth) Modifier.fillMaxWidth() else Modifier.width(width))
            .graphicsLayer {
                scaleX = pressScale
                scaleY = pressScale
            }
            .clip(RoundedCornerShape(D.r3))
            .combinedClickable(
                interactionSource = interaction,
                indication = LocalIndication.current,
                onClick = onClick,
                onLongClickLabel = "More options",
                onLongClick = onLongPress?.let {
                    {
                        haptics.performHapticFeedback(HapticFeedbackType.LongPress)
                        it()
                    }
                },
            )
            .padding(0.dp),
        verticalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        Box {
            Art(
                coverId,
                if (fillWidth) null else width,
                round = round,
                modifier = if (fillWidth) Modifier.fillMaxWidth().aspectRatio(1f) else Modifier,
            )
            if (onPlay != null) {
                Box(
                    Modifier
                        .align(Alignment.BottomEnd)
                        .padding(6.dp)
                        .size(32.dp)
                        .clip(CircleShape)
                        .background(mc.accent)
                        .clickable(onClick = onPlay),
                    contentAlignment = Alignment.Center,
                ) {
                    Icon(AppIcons.Play, null, Modifier.size(14.dp), tint = mc.accentFg)
                }
            }
        }
        Text(
            title,
            style = McType.bodySm.copy(fontWeight = FontWeight.Medium),
            color = mc.fg,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
        )
        if (subtitle != null) {
            Text(
                subtitle,
                style = McType.mono9,
                color = mc.dim,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        }
    }
}

@Composable
fun AlbumTile(
    a: AlbumRef,
    onClick: () -> Unit,
    onPlay: () -> Unit,
    onLongPress: (() -> Unit)? = null,
    fillWidth: Boolean = false,
) {
    Tile(
        title = a.album,
        subtitle = listOfNotNull(a.artist.ifBlank { null }, a.n.takeIf { it > 0 }?.let { "$it" })
            .joinToString(" · "),
        coverId = a.coverId,
        onClick = onClick,
        onPlay = onPlay,
        onLongPress = onLongPress,
        fillWidth = fillWidth,
    )
}

@Composable
fun ArtistTile(
    a: ArtistRef,
    onClick: () -> Unit,
    onPlay: () -> Unit,
    onLongPress: (() -> Unit)? = null,
    fillWidth: Boolean = false,
) {
    Tile(
        title = a.artist,
        subtitle = "${a.n} tracks",
        coverId = a.coverId,
        onClick = onClick,
        onPlay = onPlay,
        onLongPress = onLongPress,
        round = true,
        fillWidth = fillWidth,
    )
}

@Composable
fun PlaylistTile(
    p: PlaylistRef,
    onClick: () -> Unit,
    onPlay: () -> Unit,
    onLongPress: (() -> Unit)? = null,
    fillWidth: Boolean = false,
) {
    Tile(
        title = p.name,
        subtitle = "${p.n} tracks",
        coverId = p.coverId,
        onClick = onClick,
        onPlay = onPlay,
        onLongPress = onLongPress,
        fillWidth = fillWidth,
    )
}

/* ── hero ───────────────────────────────────────────────────────────────── */

@Composable
fun Hero(
    coverId: Int?,
    kicker: String,
    title: String,
    subs: List<String> = emptyList(),
    round: Boolean = false,
    actions: @Composable RowScope.() -> Unit = {},
) {
    val mc = LocalMc.current
    Column(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(D.r3))
            .background(
                Brush.radialGradient(
                    listOf(mc.accent.copy(alpha = 0.24f), Color.Transparent),
                ),
            )
            .padding(18.dp)
            .padding(bottom = 2.dp),
    ) {
        Row(verticalAlignment = Alignment.Bottom, horizontalArrangement = Arrangement.spacedBy(16.dp)) {
            Art(coverId, 144.dp, round = round)
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text(kicker.uppercase(), style = McType.kicker, color = mc.accent)
                Text(title, style = McType.h1Small, color = mc.fg, maxLines = 2, overflow = TextOverflow.Ellipsis)
                if (subs.isNotEmpty()) {
                    Text(
                        subs.filter { it.isNotBlank() }.joinToString("  ·  "),
                        style = McType.mono9,
                        color = mc.dim,
                    )
                }
            }
        }
        Row(
            Modifier
                .fillMaxWidth()
                .padding(top = 14.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.CenterVertically,
            content = actions,
        )
    }
}

/* ── sheets and menus ───────────────────────────────────────────────────── */

@Composable
fun McSheet(onDismiss: () -> Unit, title: String? = null, content: @Composable ColumnScope.() -> Unit) {
    val mc = LocalMc.current
    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true),
        containerColor = mc.bg2,
        scrimColor = mc.scrim,
        dragHandle = {
            Box(
                Modifier
                    .padding(top = 8.dp)
                    .width(34.dp)
                    .height(3.dp)
                    .clip(CircleShape)
                    .background(mc.line2)
            )
        },
    ) {
        Column(
            Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp)
                .padding(bottom = 28.dp),
        ) {
            if (title != null) {
                Text(
                    title,
                    style = McType.h3,
                    color = mc.fg,
                    modifier = Modifier.padding(vertical = 12.dp),
                )
            }
            content()
        }
    }
}

@Composable
fun MenuRow(
    icon: ImageVector,
    label: String,
    danger: Boolean = false,
    onClick: () -> Unit,
) {
    val mc = LocalMc.current
    Row(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(D.r2))
            .clickable(onClick = onClick)
            .padding(horizontal = 10.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Icon(icon, null, Modifier.size(16.dp), tint = if (danger) mc.err else mc.dim)
        Text(label, style = McType.bodySm, color = if (danger) mc.err else mc.fg)
    }
}

/* ── toast ──────────────────────────────────────────────────────────────── */

@Composable
fun ToastHost(message: String?, onDismiss: () -> Unit, modifier: Modifier = Modifier) {
    val mc = LocalMc.current
    LaunchedEffect(message) {
        if (message != null) {
            delay(2800)
            onDismiss()
        }
    }
    AnimatedVisibility(
        visible = message != null,
        enter = fadeIn() + slideInVertically { it / 2 },
        exit = fadeOut(),
        modifier = modifier,
    ) {
        Box(
            Modifier
                .padding(horizontal = 24.dp)
                .glass(RoundedCornerShape(18.dp))
                .padding(horizontal = 16.dp, vertical = 10.dp),
        ) {
            Text(message.orEmpty(), style = McType.bodySm, color = mc.fg, maxLines = 3)
        }
    }
}

/* ── chips ──────────────────────────────────────────────────────────────── */

@Composable
fun StatusChip(text: String, color: Color) {
    Text(
        text,
        style = McType.labelSm,
        color = color,
        modifier = Modifier
            .border(1.dp, color.copy(alpha = 0.45f), RoundedCornerShape(D.r1))
            .padding(horizontal = 7.dp, vertical = 2.dp),
    )
}

@Composable
fun VSpace(dp: Dp) = Spacer(Modifier.height(dp))

@Composable
fun HSpace(dp: Dp) = Spacer(Modifier.width(dp))

val ZeroPadding = PaddingValues(0.dp)
