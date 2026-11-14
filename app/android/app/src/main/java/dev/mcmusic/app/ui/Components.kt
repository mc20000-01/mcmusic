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
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
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
import dev.mcmusic.app.data.AlbumRef
import dev.mcmusic.app.data.ArtistRef
import dev.mcmusic.app.data.PlaylistRef
import dev.mcmusic.app.data.Track
import dev.mcmusic.app.ui.theme.D
import dev.mcmusic.app.ui.theme.LocalMc
import dev.mcmusic.app.ui.theme.McType
import kotlinx.coroutines.delay

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
    val shape = RoundedCornerShape(D.r2)
    val bg = if (solid) mc.accent else Color.Transparent
    val borderColor = when {
        solid -> mc.accent
        ghost -> Color.Transparent
        danger -> mc.err.copy(alpha = 0.45f)
        else -> mc.line2
    }
    val fg = when {
        solid -> mc.accentFg
        ghost -> mc.dim
        danger -> mc.err
        else -> mc.fg
    }
    Row(
        modifier = modifier
            .height(if (small) 28.dp else 36.dp)
            .clip(shape)
            .background(bg)
            .border(1.dp, borderColor, shape)
            .clickable(enabled = enabled, onClick = onClick)
            .padding(horizontal = if (small) 11.dp else 16.dp),
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
            .clip(RoundedCornerShape(D.r2))
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center,
    ) {
        Icon(
            icon,
            contentDescription,
            Modifier.size(size * 0.55f),
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
    val shape = RoundedCornerShape(D.r2)
    BasicTextField(
        value = value,
        onValueChange = onValueChange,
        singleLine = true,
        textStyle = McType.bodySm.copy(color = mc.fg),
        cursorBrush = SolidColor(mc.accent),
        visualTransformation = if (password) PasswordVisualTransformation() else VisualTransformation.None,
        keyboardOptions = KeyboardOptions(keyboardType = keyboardType),
        modifier = modifier
            .fillMaxWidth()
            .height(38.dp)
            .clip(shape)
            .background(mc.bg2)
            .border(1.dp, mc.line2, shape)
            .padding(horizontal = 11.dp),
        decorationBox = { inner ->
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(7.dp)) {
                if (leading != null) {
                    Icon(leading, null, Modifier.size(15.dp), tint = LocalMc.current.dim2)
                }
                Box(Modifier.weight(1f), contentAlignment = Alignment.CenterStart) {
                    if (value.isEmpty()) {
                        Text(placeholder, style = McType.bodySm, color = mc.dim2, maxLines = 1)
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
    Box(
        Modifier
            .size(width = 38.dp, height = 20.dp)
            .clip(CircleShape)
            .background(if (checked) mc.accent else mc.line2)
            .clickable { onChange(!checked) },
        contentAlignment = if (checked) Alignment.CenterEnd else Alignment.CenterStart,
    ) {
        Box(
            Modifier
                .padding(horizontal = 2.dp)
                .size(16.dp)
                .clip(CircleShape)
                .background(if (checked) mc.accentFg else mc.fg)
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
    Row(
        modifier
            .clip(RoundedCornerShape(D.r2))
            .background(mc.bg2)
            .border(1.dp, mc.line, RoundedCornerShape(D.r2))
            .padding(2.dp),
        horizontalArrangement = Arrangement.spacedBy(2.dp),
    ) {
        options.forEach { (key, label) ->
            val on = key == selected
            Box(
                Modifier
                    .clip(RoundedCornerShape(D.r1))
                    .background(if (on) mc.accent else Color.Transparent)
                    .clickable { onSelect(key) }
                    .padding(horizontal = 12.dp, vertical = 5.dp),
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
            Text(meta, style = McType.mono9, color = mc.dim2)
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
            .padding(bottom = 16.dp)
            .clip(RoundedCornerShape(D.r3))
            .background(mc.bg2)
            .border(1.dp, mc.line, RoundedCornerShape(D.r3)),
    ) {
        if (title != null) {
            Text(
                title.uppercase(),
                style = McType.mono9,
                color = mc.dim2,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 12.dp),
            )
            Box(Modifier.fillMaxWidth().height(1.dp).background(mc.line))
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
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Column(Modifier.weight(1f)) {
            Text(title, style = McType.bodySm.copy(fontWeight = FontWeight.Medium), color = mc.fg)
            if (subtitle != null) {
                Text(subtitle, style = McType.bodyXs, color = mc.dim2)
            }
        }
        trailing()
    }
    if (!last) Box(Modifier.fillMaxWidth().height(1.dp).background(mc.line))
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
            .padding(vertical = 40.dp, horizontal = 20.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Icon(icon, null, Modifier.size(26.dp), tint = mc.dim2)
        Text(title, style = McType.h3, color = mc.fg)
        if (hint != null) {
            Text(hint, style = McType.bodySm, color = mc.dim2)
        }
        if (actionLabel != null && onAction != null) {
            McButton(actionLabel, onAction)
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
            .clip(RoundedCornerShape(D.r2))
            .background(mc.bg2)
            .border(1.dp, mc.line2, RoundedCornerShape(D.r2))
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
            style = McType.mono10,
            color = mc.dim,
            modifier = Modifier.width(38.dp),
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
            val groove = 7.dp.toPx()
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
                radius = 8.dp.toPx(),
                center = Offset(size.width * fraction, cy),
            )
        }
        Text(
            fmtTime(duration),
            style = McType.mono10,
            color = mc.dim,
            modifier = Modifier.width(38.dp),
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
    val haptics = LocalHapticFeedback.current
    Row(
        modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(D.r2))
            .background(if (isCurrent) mc.surface else Color.Transparent)
            .combinedClickable(
                onClick = onClick,
                onLongClickLabel = "Track options",
                onLongClick = {
                    haptics.performHapticFeedback(HapticFeedbackType.LongPress)
                    onMore()
                },
            )
            .padding(horizontal = 6.dp, vertical = 5.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text(
            (number + 1).toString().padStart(2, '0'),
            style = McType.mono10,
            color = if (isCurrent) mc.accent else mc.dim2,
            modifier = Modifier.width(24.dp),
        )
        Art(track.id, 34.dp)
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
            .padding(bottom = 18.dp),
    ) {
        Row(verticalAlignment = Alignment.Bottom, horizontalArrangement = Arrangement.spacedBy(16.dp)) {
            Art(coverId, 128.dp, round = round)
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
        if (true) {
            Row(
                Modifier
                    .fillMaxWidth()
                    .padding(top = 14.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically,
                content = actions,
            )
        }
        Box(
            Modifier
                .fillMaxWidth()
                .padding(top = 18.dp)
                .height(1.dp)
                .background(mc.line)
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
                .clip(RoundedCornerShape(D.r2))
                .background(mc.fg)
                .padding(horizontal = 14.dp, vertical = 9.dp),
        ) {
            Text(message.orEmpty(), style = McType.bodySm, color = mc.bg, maxLines = 3)
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
