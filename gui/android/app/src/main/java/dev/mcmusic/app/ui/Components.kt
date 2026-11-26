package dev.mcmusic.app.ui

import androidx.annotation.DrawableRes
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.spring
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.indication
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.aspectRatio
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
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.SwipeToDismissBox
import androidx.compose.material3.SwipeToDismissBoxValue
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.rememberSwipeToDismissBoxState
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
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Account
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.LibraryState
import dev.mcmusic.app.data.Playlist
import dev.mcmusic.app.data.Prefs
import dev.mcmusic.app.data.Track
import dev.mcmusic.app.ui.design.DynamicColour
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.blobShape
import dev.mcmusic.app.ui.design.PlayfulMotion
import dev.mcmusic.app.ui.design.mcSurface
import dev.mcmusic.app.ui.design.playfulMotionEnabled
import dev.mcmusic.app.ui.design.rememberPlayfulHaptic
import kotlinx.coroutines.launch
import android.widget.Toast
import kotlin.math.PI
import kotlin.math.sin

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
    val haptic = rememberPlayfulHaptic()
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(50))
            .background(if (enabled) design.accent else design.accent.copy(alpha = 0.35f))
            .clickable(enabled = enabled) {
                haptic(PlayfulMotion.CLICK)
                onClick()
            }
            .padding(horizontal = 20.dp, vertical = 14.dp),
        contentAlignment = Alignment.Center,
    ) {
        Text(text, color = design.onAccent, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
fun GhostButton(text: String, modifier: Modifier = Modifier, danger: Boolean = false, onClick: () -> Unit) {
    val design = LocalDesign.current
    val haptic = rememberPlayfulHaptic()
    val tint = if (danger) design.palette.error else design.fg
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(50))
            .border(
                1.dp,
                if (danger) design.palette.error.copy(alpha = 0.5f) else design.hairline,
                RoundedCornerShape(50),
            )
            .clickable {
                haptic(PlayfulMotion.KEY)
                onClick()
            }
            .padding(horizontal = 18.dp, vertical = 13.dp),
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
    val motion = playfulMotionEnabled()
    val haptic = rememberPlayfulHaptic()
    val interaction = remember { MutableInteractionSource() }
    val pressed by interaction.collectIsPressedAsState()
    val scale by animateFloatAsState(
        if (pressed && motion) PlayfulMotion.PRESS_SCALE else 1f,
        spring(dampingRatio = PlayfulMotion.DAMPING_RATIO, stiffness = PlayfulMotion.STIFFNESS),
    )
    Box(
        modifier = modifier
            .size(design.touchTarget)
            .clip(CircleShape)
            .background(if (pressed && motion) design.accentWash else Color.Transparent)
            .graphicsLayer { scaleX = scale; scaleY = scale }
            .clickable(interactionSource = interaction, indication = null) {
                haptic(PlayfulMotion.KEY)
                onClick()
            },
        contentAlignment = Alignment.Center,
    ) {
        LucideIcon(icon, tint ?: design.dim, size = size)
    }
}

/** Play/pause pill-to-blob morph. The icon and haptics follow the same switch. */
@Composable
fun PlayPauseButton(
    playing: Boolean,
    modifier: Modifier = Modifier,
    size: Dp = 58.dp,
    onClick: () -> Unit,
) {
    val design = LocalDesign.current
    val motion = playfulMotionEnabled()
    val haptic = rememberPlayfulHaptic()
    val interaction = remember { MutableInteractionSource() }
    val pressed by interaction.collectIsPressedAsState()
    val shape = when {
        !motion -> RoundedCornerShape(16.dp)
        playing -> blobShape("blob-2")
        else -> RoundedCornerShape(size / 2)
    }
    val scale by animateFloatAsState(
        if (pressed && motion) PlayfulMotion.PRESS_SCALE else 1f,
        spring(dampingRatio = PlayfulMotion.DAMPING_RATIO, stiffness = PlayfulMotion.STIFFNESS),
    )
    val rotation by animateFloatAsState(
        if (playing) 90f else 0f,
        spring(dampingRatio = PlayfulMotion.DAMPING_RATIO, stiffness = PlayfulMotion.STIFFNESS),
    )
    Box(
        modifier = modifier
            .size(maxOf(size, design.touchTarget))
            .clip(shape)
            .background(design.accent, shape)
            .graphicsLayer { scaleX = scale; scaleY = scale }
            .clickable(interactionSource = interaction, indication = null) {
                haptic(PlayfulMotion.CLICK)
                onClick()
            },
        contentAlignment = Alignment.Center,
    ) {
        Box(Modifier.graphicsLayer { rotationZ = if (motion) rotation else 0f }) {
            LucideIcon(
                if (playing) Lucide.Pause else Lucide.Play,
                design.onAccent,
                size = size * 0.36f,
            )
        }
    }
}

/**
 * Flat progress line. While playing, a small wave rides the filled portion;
 * paused state is one flat bar. Reduced motion and the local switch flatten it.
 */
@Composable
fun PlayfulProgress(
    fraction: Float,
    playing: Boolean,
    modifier: Modifier = Modifier,
) {
    val design = LocalDesign.current
    val motion = playfulMotionEnabled()
    val transition = rememberInfiniteTransition()
    val phase by transition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 1818, easing = androidx.compose.animation.core.LinearEasing),
            repeatMode = RepeatMode.Restart,
        ),
    )
    val filled = fraction.coerceIn(0f, 1f)
    Canvas(
        modifier
            .height(6.dp)
            .clip(RoundedCornerShape(50))
            .background(design.hairline),
    ) {
        val width = size.width * filled
        if (width <= 0f) return@Canvas
        val mid = size.height / 2f
        if (!playing || !motion) {
            drawLine(design.accent, Offset(0f, mid), Offset(width, mid), strokeWidth = 2.dp.toPx())
            return@Canvas
        }
        val path = Path()
        val steps = (width / (4.dp.toPx())).toInt().coerceAtLeast(2)
        val amplitude = minOf(size.height * 0.28f, 2.dp.toPx())
        for (index in 0..steps) {
            val x = width * index / steps
            val envelope = sin(PI * index / steps).toFloat().coerceAtLeast(0f)
            val y = mid + sin(index * 0.36f + phase * 2f * PI.toFloat()) * amplitude * envelope
            if (index == 0) path.moveTo(x, y) else path.lineTo(x, y)
        }
        drawPath(path, design.accent, style = Stroke(width = 2.dp.toPx()))
    }
}

/** Touch-friendly seek target carrying the flat progress line. */
@Composable
fun PlayfulSeek(
    fraction: Float,
    playing: Boolean,
    onSeek: (Float) -> Unit,
    modifier: Modifier = Modifier,
) {
    val value = fraction.coerceIn(0f, 1f)
    val haptic = rememberPlayfulHaptic()
    Box(
        modifier
            .fillMaxWidth()
            .height(designTouchTarget())
            .pointerInput(value) {
                detectTapGestures { offset ->
                    haptic(PlayfulMotion.KEY)
                    onSeek((offset.x / size.width).coerceIn(0f, 1f))
                }
            }
            .pointerInput(value) {
                detectDragGestures(onDragEnd = { haptic(PlayfulMotion.KEY) }) { change, _ ->
                    onSeek((change.position.x / size.width).coerceIn(0f, 1f))
                }
            },
        contentAlignment = Alignment.Center,
    ) {
        PlayfulProgress(value, playing, Modifier.fillMaxWidth())
    }
}

/** Kept as a function so the shared touch target stays in one place. */
@Composable
private fun designTouchTarget(): Dp = LocalDesign.current.touchTarget

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
            focusedBorderColor = design.accentText,
            unfocusedBorderColor = design.hairline,
            focusedLabelColor = design.accentText,
            unfocusedLabelColor = design.dim,
            cursorColor = design.accentText,
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
            color = design.accentText,
        )
        Box(Modifier.width(10.dp))
        Text(text, color = design.dim, fontSize = 13.sp)
    }
}

@Composable
fun ErrorLine(message: String, modifier: Modifier = Modifier) {
    val design = LocalDesign.current
    Text(
        message,
        modifier = modifier.fillMaxWidth().clip(RoundedCornerShape(design.cardRadius))
            .background(design.palette.error.copy(alpha = 0.10f))
            .border(1.dp, design.palette.error.copy(alpha = 0.35f), RoundedCornerShape(design.cardRadius))
            .padding(horizontal = 12.dp, vertical = 9.dp),
        color = design.palette.error,
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
            LucideIcon(icon, design.accentText, size = 24.dp)
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
        LucideIcon(Lucide.ChevronLeft, LocalDesign.current.accent, size = 16.dp)
        Text("Back", color = LocalDesign.current.fg, fontSize = 13.sp, fontWeight = FontWeight.Medium)
    }
}

/* ── music pieces ──────────────────────────────────────────────────────── */

/** Square cover that falls back to a neutral tile when a track has no art. */
@Composable
fun TrackCover(
    track: Track,
    size: Dp = 48.dp,
    radius: Dp = 20.dp,
    dynamic: Boolean = false,
) {
    val design = LocalDesign.current
    val url = trackCoverUrl(track.id)
    if (!Prefs.showCovers) {
        // A list tile only hides its own art; the player owns the live seed.
        if (dynamic) DynamicColour.clearCover(url)
        Box(
            Modifier.size(size).clip(RoundedCornerShape(radius)).background(design.accentSoft),
            Alignment.Center,
        ) {
            LucideIcon(Lucide.ListMusic, design.accentText, size = size / 2)
        }
        return
    }
    Cover(
        url = url,
        shape = RoundedCornerShape(radius),
        modifier = Modifier.size(size),
        fallback = design.accentSoft,
        dynamic = dynamic,
    )
}

/** Appearance setting: filter tracks the server flagged explicit. */
fun List<Track>.visibleTracks(): List<Track> =
    if (Prefs.hideExplicit) filterNot { it.explicit } else this

@OptIn(ExperimentalFoundationApi::class, ExperimentalMaterial3Api::class)
@Composable
fun TrackRow(
    track: Track,
    modifier: Modifier = Modifier,
    subtitle: String? = null,
    trailing: (@Composable RowScope.() -> Unit)? = null,
    menu: Boolean = false,
    onClick: () -> Unit,
    onOpenArtist: ((String) -> Unit)? = null,
) {
    val design = LocalDesign.current
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val current = dev.mcmusic.app.playback.Playback.state.track?.id == track.id
    var menuOpen by remember { mutableStateOf(false) }
    var confirmRemove by remember { mutableStateOf(false) }

    fun toggleLike() {
        scope.launch {
            Api.toggleLike(track.id).fold(
                onSuccess = {
                    Toast.makeText(
                        context,
                        if (it) "Added to likes" else "Removed from likes",
                        Toast.LENGTH_SHORT,
                    ).show()
                    LibraryState.changed()
                },
                onFailure = {
                    Toast.makeText(context, it.message ?: "Could not update like", Toast.LENGTH_SHORT).show()
                },
            )
        }
    }

    fun askRemove() {
        if (!Account.isAdmin) {
            Toast.makeText(context, "Only admins can remove tracks", Toast.LENGTH_SHORT).show()
            return
        }
        confirmRemove = true
    }

    fun removeTrack() {
        confirmRemove = false
        scope.launch {
            Api.deleteTrack(track.id).fold(
                onSuccess = {
                    dev.mcmusic.app.playback.Playback.removeTrack(track.id)
                    LibraryState.changed()
                    Toast.makeText(context, "Removed ${track.title} from mcmusic", Toast.LENGTH_SHORT).show()
                },
                onFailure = {
                    Toast.makeText(context, it.message ?: "Could not remove track", Toast.LENGTH_SHORT).show()
                },
            )
        }
    }

    val dismissState = rememberSwipeToDismissBoxState(
        confirmValueChange = { value ->
            when (value) {
                SwipeToDismissBoxValue.StartToEnd -> toggleLike()
                SwipeToDismissBoxValue.EndToStart -> askRemove()
                SwipeToDismissBoxValue.Settled -> Unit
            }
            // Always settle back; the action (or confirmation) is the result.
            false
        },
    )

    SwipeToDismissBox(
        state = dismissState,
        modifier = modifier.fillMaxWidth(),
        enableDismissFromStartToEnd = menu,
        enableDismissFromEndToStart = menu && Account.isAdmin,
        backgroundContent = {
            Row(
                Modifier.fillMaxSize().padding(horizontal = 20.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                if (menu) {
                    LucideIcon(
                        Lucide.Heart,
                        if (track.liked) design.palette.error else design.accentText,
                        size = 24.dp,
                        contentDescription = if (track.liked) "Unlike" else "Like",
                    )
                } else {
                    Box(Modifier.weight(1f))
                }
                if (menu && Account.isAdmin) {
                    LucideIcon(
                        Lucide.Trash,
                        design.palette.error,
                        size = 24.dp,
                        contentDescription = "Remove track",
                    )
                }
            }
        },
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(design.tileRadius))
                .background(if (current) design.accentWash else Color.Transparent)
                .combinedClickable(
                    onClick = onClick,
                    onLongClick = if (menu) ({ menuOpen = true }) else null,
                )
                .padding(horizontal = 10.dp, vertical = 9.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            TrackCover(track, 48.dp, 20.dp)
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Text(
                    track.title,
                    color = if (current) design.accentText else design.fg,
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
            if (menu) {
                TrackActionsMenu(
                    track = track,
                    expanded = menuOpen,
                    onExpandedChange = { menuOpen = it },
                    onRemove = ::askRemove,
                    onOpenArtist = onOpenArtist,
                )
            }
        }
    }

    if (confirmRemove) {
        AlertDialog(
            onDismissRequest = { confirmRemove = false },
            title = { Text("Remove track?") },
            text = {
                Text(
                    "\"${track.title}\" will be deleted from mcmusic for everyone. " +
                        "Playlists, likes and queues pointing at it are updated too.",
                )
            },
            confirmButton = {
                TextButton(onClick = ::removeTrack) { Text("Remove", color = design.palette.error) }
            },
            dismissButton = {
                TextButton(onClick = { confirmRemove = false }) { Text("Cancel") }
            },
        )
    }
}

/**
 * Track actions: like, playlist, radio, artist and info. The playlists load
 * when the menu opens (also on a long press), so ordinary browsing makes no
 * extra requests. Admins also get Remove from mcmusic. [onOpenArtist] is only
 * supplied from screens that can show an artist collection.
 */
@Composable
fun TrackActionsMenu(
    track: Track,
    expanded: Boolean,
    onExpandedChange: (Boolean) -> Unit,
    modifier: Modifier = Modifier,
    onRemove: () -> Unit,
    onOpenArtist: ((String) -> Unit)? = null,
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val design = LocalDesign.current
    var picker by remember { mutableStateOf(false) }
    var showInfo by remember { mutableStateOf(false) }
    var playlists by remember { mutableStateOf<List<Playlist>>(emptyList()) }
    var busy by remember { mutableStateOf(false) }

    LaunchedEffect(expanded) {
        if (expanded) Api.playlists().onSuccess { playlists = it }
    }

    Box(modifier) {
        IconButton(Lucide.Ellipsis, size = 16.dp, onClick = { onExpandedChange(true) })
        DropdownMenu(expanded, onDismissRequest = { onExpandedChange(false) }) {
            DropdownMenuItem(
                text = { Text(if (track.liked) "Unlike" else "Like", fontSize = 13.sp) },
                leadingIcon = { LucideIcon(Lucide.Heart, LocalDesign.current.accent, size = 16.dp) },
                onClick = {
                    onExpandedChange(false)
                    scope.launch {
                        Api.toggleLike(track.id).fold(
                            onSuccess = {
                                Toast.makeText(
                                    context,
                                    if (it) "Added to likes" else "Removed from likes",
                                    Toast.LENGTH_SHORT,
                                ).show()
                                LibraryState.changed()
                            },
                            onFailure = {
                                Toast.makeText(context, it.message ?: "Could not update like", Toast.LENGTH_SHORT).show()
                            },
                        )
                    }
                },
            )
            DropdownMenuItem(
                text = { Text("Play next", fontSize = 13.sp) },
                leadingIcon = { LucideIcon(Lucide.ListPlus, design.accentText, size = 16.dp) },
                onClick = {
                    onExpandedChange(false)
                    dev.mcmusic.app.playback.Playback.playNext(track)
                    Toast.makeText(context, "Playing ${track.title} next", Toast.LENGTH_SHORT).show()
                },
            )
            DropdownMenuItem(
                text = { Text("Add to queue", fontSize = 13.sp) },
                leadingIcon = { LucideIcon(Lucide.ListMusic, design.accentText, size = 16.dp) },
                onClick = {
                    onExpandedChange(false)
                    dev.mcmusic.app.playback.Playback.addToQueue(track)
                    Toast.makeText(context, "Added ${track.title} to the queue", Toast.LENGTH_SHORT).show()
                },
            )
            DropdownMenuItem(
                text = { Text("Add to playlist", fontSize = 13.sp) },
                leadingIcon = { LucideIcon(Lucide.ListPlus, design.accentText, size = 16.dp) },
                onClick = { onExpandedChange(false); picker = true },
            )
            DropdownMenuItem(
                text = { Text("Start radio", fontSize = 13.sp) },
                leadingIcon = { LucideIcon(Lucide.Radio, design.accentText, size = 16.dp) },
                onClick = {
                    onExpandedChange(false)
                    scope.launch {
                        Api.radio(track.id).fold(
                            onSuccess = { suggestions ->
                                val queue = buildList {
                                    add(track)
                                    suggestions
                                        .filter { it.id > 0 && it.id != track.id }
                                        .distinctBy { it.id }
                                        .forEach { add(it) }
                                }
                                dev.mcmusic.app.playback.Playback.play(queue, 0)
                                Toast.makeText(
                                    context,
                                    "Radio started from ${track.title}",
                                    Toast.LENGTH_SHORT,
                                ).show()
                            },
                            onFailure = {
                                Toast.makeText(context, it.message ?: "Could not start radio", Toast.LENGTH_SHORT).show()
                            },
                        )
                    }
                },
            )
            onOpenArtist?.let { openArtist ->
                DropdownMenuItem(
                    text = { Text("Go to artist", fontSize = 13.sp) },
                    leadingIcon = { LucideIcon(Lucide.User, design.accentText, size = 16.dp) },
                    onClick = { onExpandedChange(false); openArtist(track.artist) },
                )
            }
            DropdownMenuItem(
                text = { Text("Track info", fontSize = 13.sp) },
                leadingIcon = { LucideIcon(Lucide.Info, design.accentText, size = 16.dp) },
                onClick = { onExpandedChange(false); showInfo = true },
            )
            if (Account.isAdmin) {
                DropdownMenuItem(
                    text = { Text("Remove from mcmusic", color = design.palette.error, fontSize = 13.sp) },
                    leadingIcon = { LucideIcon(Lucide.Trash, design.palette.error, size = 16.dp) },
                    onClick = { onExpandedChange(false); onRemove() },
                )
            }
        }
    }

    if (picker) {
        Dialog(onDismissRequest = { picker = false }) {
            Column(
                Modifier.fillMaxWidth().mcSurface(RoundedCornerShape(design.cardRadius)).padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Text("Add to playlist", color = LocalDesign.current.fg, fontSize = 16.sp, fontWeight = FontWeight.SemiBold)
                Text(track.title, color = LocalDesign.current.dim, fontSize = 12.sp, maxLines = 1)
                if (playlists.isEmpty()) {
                    Muted("Create a playlist first, then add tracks from here.")
                } else {
                    playlists.forEach { playlist ->
                        Row(
                            Modifier.fillMaxWidth().clip(RoundedCornerShape(design.cardRadius))
                                .clickable(enabled = !busy) {
                                    busy = true
                                    scope.launch {
                                        Api.addToPlaylist(playlist.id, track.id).fold(
                                            onSuccess = {
                                                Toast.makeText(context, "Added to ${playlist.name}", Toast.LENGTH_SHORT).show()
                                                picker = false
                                            },
                                            onFailure = {
                                                Toast.makeText(context, it.message ?: "Could not add track", Toast.LENGTH_SHORT).show()
                                            },
                                        )
                                        busy = false
                                    }
                                }
                                .padding(horizontal = 10.dp, vertical = 11.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            LucideIcon(Lucide.ListMusic, LocalDesign.current.accent, size = 16.dp)
                            Text(playlist.name, color = LocalDesign.current.fg, fontSize = 13.sp)
                        }
                    }
                }
                GhostButton("Close") { picker = false }
            }
        }
    }

    if (showInfo) {
        AlertDialog(
            onDismissRequest = { showInfo = false },
            title = { Text("Track info") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    listOf(
                        "Title" to track.title,
                        "Artist" to track.artist.ifBlank { "Unknown artist" },
                        "Album" to track.album.ifBlank { "Unknown album" },
                        "Duration" to formatDuration(track.duration),
                        "Explicit" to if (track.explicit) "Yes" else "No",
                        "Track ID" to track.id.toString(),
                    ).forEach { (label, value) ->
                        Column(verticalArrangement = Arrangement.spacedBy(1.dp)) {
                            Text(label, color = design.dim, fontSize = 11.sp)
                            Text(value, color = design.fg, fontSize = 13.sp)
                        }
                    }
                }
            },
            confirmButton = { TextButton(onClick = { showInfo = false }) { Text("Close") } },
        )
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
    fill: Boolean = false,
    onClick: () -> Unit,
) {
    val design = LocalDesign.current
    val cardModifier = if (fill) modifier.fillMaxWidth() else modifier.width(width)
    Column(
        cardModifier.clip(RoundedCornerShape(design.tileRadius)).clickable { onClick() },
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Cover(
            url = coverUrl,
            shape = if (round) CircleShape else RoundedCornerShape(design.tileRadius),
            modifier = if (fill) Modifier.fillMaxWidth().aspectRatio(1f) else Modifier.size(width),
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
    val tint = if (danger) design.palette.error else design.fg
    Row(
        Modifier
            .fillMaxWidth()
            .then(if (onClick != null) Modifier.clickable { onClick() } else Modifier)
            .padding(vertical = 14.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(11.dp),
    ) {
        if (icon != null) {
            Box(
                Modifier.size(28.dp).clip(RoundedCornerShape(8.dp))
                    .background(if (danger) design.palette.error.copy(alpha = 0.12f) else design.accentSoft),
                Alignment.Center,
            ) {
                LucideIcon(icon, if (danger) design.palette.error else design.accentText, size = 14.dp)
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
                checkedThumbColor = design.onAccent,
                checkedTrackColor = design.accentText,
                uncheckedThumbColor = design.dim,
                uncheckedTrackColor = design.palette.surface2,
                uncheckedBorderColor = design.hairline,
            ),
        )
    }
}

/* ── helpers ───────────────────────────────────────────────────────────── */

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

fun trackCoverUrl(id: Int): String = Api.url("/api/tracks/$id/cover")

fun emptyModifier(): Modifier = Modifier.fillMaxSize()
