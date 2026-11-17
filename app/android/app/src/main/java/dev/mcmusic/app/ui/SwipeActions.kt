package dev.mcmusic.app.ui

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.spring
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectHorizontalDragGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.unit.dp
import dev.mcmusic.app.ui.theme.LocalMc
import dev.mcmusic.app.ui.theme.McType
import kotlinx.coroutines.launch
import kotlin.math.abs

/**
 * Swipe the compact now-playing deck sideways to step through the queue.
 *
 * Swipe left for the next track, right for the previous one. Dragging only
 * *previews* the action: the label slides in and ticks once when it passes the
 * threshold, but nothing changes until the finger lifts. Releasing early, or
 * swiping out and drifting back, settles the deck home and leaves playback
 * alone. That makes it safe to peek at what a swipe would do without
 * accidentally skipping.
 *
 * The full player uses its own track tape instead, where the queue itself is
 * the swipeable surface.
 */
@Composable
fun SwipeToSkip(
    onPrevious: () -> Unit,
    onNext: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    compact: Boolean = false,
    content: @Composable BoxScope.() -> Unit,
) {
    val mc = LocalMc.current
    val haptics = LocalHapticFeedback.current
    val scope = rememberCoroutineScope()
    val offset = remember { Animatable(0f) }
    val threshold = with(LocalDensity.current) { 68.dp.toPx() }

    var widthPx by remember { mutableIntStateOf(0) }
    // -1 = next armed, 0 = neutral, 1 = previous armed. Drives the hint copy so
    // a held swipe says "release" instead of just naming the direction.
    var armed by remember { mutableIntStateOf(0) }

    val dx = offset.value
    val prevProgress = (dx / threshold).coerceIn(0f, 1f)
    val nextProgress = (-dx / threshold).coerceIn(0f, 1f)

    val settle: () -> Unit = {
        armed = 0
        scope.launch {
            offset.animateTo(
                0f,
                spring(dampingRatio = 0.72f, stiffness = Spring.StiffnessMediumLow),
            )
        }
    }

    Box(
        modifier
            .onSizeChanged { widthPx = it.width }
            .pointerInput(enabled) {
                if (!enabled) return@pointerInput
                // Read these from the pointer scope, not the composition: the
                // gesture block is long-lived and must not capture a stale
                // width from the first layout pass.
                val thresholdPx = 68.dp.toPx()
                val limitPx = size.width.toFloat().coerceAtLeast(thresholdPx) * 0.9f
                detectHorizontalDragGestures(
                    onDragStart = {
                        armed = 0
                        scope.launch { offset.stop() }
                    },
                    onDragCancel = { settle() },
                    onHorizontalDrag = { change, dragAmount ->
                        change.consume()
                        val target = (offset.value + dragAmount).coerceIn(-limitPx, limitPx)
                        scope.launch { offset.snapTo(target) }

                        val direction = when {
                            target >= thresholdPx -> 1
                            target <= -thresholdPx -> -1
                            else -> 0
                        }
                        if (direction != armed) {
                            armed = direction
                            // One crisp tick as the action arms. Drifting back
                            // under the threshold is silent so it feels like a
                            // cancelled peek, not another action.
                            if (direction != 0) {
                                haptics.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                            }
                        }
                    },
                    onDragEnd = {
                        val released = offset.value
                        when {
                            released >= thresholdPx -> {
                                armed = 0
                                haptics.performHapticFeedback(HapticFeedbackType.LongPress)
                                scope.launch {
                                    offset.animateTo(limitPx, tween(130))
                                    offset.snapTo(0f)
                                    onPrevious()
                                }
                            }

                            released <= -thresholdPx -> {
                                armed = 0
                                haptics.performHapticFeedback(HapticFeedbackType.LongPress)
                                scope.launch {
                                    offset.animateTo(-limitPx, tween(130))
                                    offset.snapTo(0f)
                                    onNext()
                                }
                            }

                            else -> settle()
                        }
                    },
                )
            },
    ) {
        // Direction hints live underneath the card, so they are uncovered by
        // the drag instead of drawn on top of the artwork.
        Row(
            Modifier
                .align(Alignment.CenterStart)
                .padding(start = if (compact) 10.dp else 18.dp)
                .graphicsLayer { alpha = prevProgress },
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(
                AppIcons.SkipBack,
                contentDescription = null,
                modifier = Modifier.size(if (compact) 16.dp else 22.dp),
                tint = mc.accent,
            )
            if (!compact) {
                Spacer(Modifier.width(8.dp))
                Text(
                    if (armed > 0) "Release for previous" else "Previous",
                    style = McType.kicker,
                    color = mc.accent,
                    modifier = Modifier
                        .background(mc.accent.copy(alpha = 0.12f), RoundedCornerShape(50))
                        .padding(horizontal = 10.dp, vertical = 4.dp),
                )
            }
        }
        Row(
            Modifier
                .align(Alignment.CenterEnd)
                .padding(end = if (compact) 10.dp else 18.dp)
                .graphicsLayer { alpha = nextProgress },
            verticalAlignment = Alignment.CenterVertically,
        ) {
            if (!compact) {
                Text(
                    if (armed < 0) "Release for next" else "Next",
                    style = McType.kicker,
                    color = mc.accent,
                    modifier = Modifier
                        .background(mc.accent.copy(alpha = 0.12f), RoundedCornerShape(50))
                        .padding(horizontal = 10.dp, vertical = 4.dp),
                )
                Spacer(Modifier.width(8.dp))
            }
            Icon(
                AppIcons.SkipForward,
                contentDescription = null,
                modifier = Modifier.size(if (compact) 16.dp else 22.dp),
                tint = mc.accent,
            )
        }

        Box(
            Modifier
                .fillMaxSize()
                .graphicsLayer {
                    translationX = offset.value
                    if (widthPx > 0) rotationZ = (offset.value / widthPx) * 2.2f
                    val pull = (abs(offset.value) / threshold).coerceIn(0f, 1f)
                    scaleX = 1f - pull * 0.015f
                    scaleY = 1f - pull * 0.015f
                },
            content = content,
        )
    }
}
