package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.dp
import dev.mcmusic.app.ui.design.LocalDesign
import kotlin.math.PI
import kotlin.math.sin

/** The three lyric visualizer modes, shared by name with web/desktop/iOS. */
enum class LyricVisualizerMode(val label: String) {
    Bars("Bars"),
    Wave("Wave"),
    Glow("Glow"),
    ;

    fun next(): LyricVisualizerMode = values()[(ordinal + 1) % values().size]
}

/**
 * A small deterministic visualizer for the lyrics pane. It uses playback
 * position and the highlighted lyric line, so it animates in sync with the
 * music without a separate analyser or microphone permission.
 */
@Composable
fun LyricVisualizer(
    mode: LyricVisualizerMode,
    positionMs: Long,
    activeLine: Int,
    playing: Boolean,
    onCycle: () -> Unit,
) {
    val design = LocalDesign.current
    val seconds = positionMs / 1000f
    val pulse = if (activeLine >= 0) 1f else 0.72f
    val alpha = if (playing) 1f else 0.55f
    val visualAccent = if (design.palette.dark) design.accent else design.accentText
    Box(
        Modifier
            .fillMaxWidth()
            .height(58.dp)
            .clip(RoundedCornerShape(12.dp))
            .background(design.accentWash)
            .clickable(onClick = onCycle),
        contentAlignment = Alignment.Center,
    ) {
        Canvas(Modifier.fillMaxWidth().height(58.dp).padding(horizontal = 12.dp, vertical = 8.dp)) {
            val w = size.width
            val h = size.height
            val tint = visualAccent.copy(alpha = alpha)
            when (mode) {
                LyricVisualizerMode.Bars -> {
                    val count = 36
                    val gap = 3.dp.toPx()
                    val barWidth = ((w - gap * (count - 1)) / count).coerceAtLeast(1f)
                    for (i in 0 until count) {
                        val wave = (sin(seconds * 3.1f + i * 0.48f) + 1f) / 2f
                        val shimmer = (sin(seconds * 7.7f - i * 0.21f) + 1f) / 2f
                        val target = (0.14f + wave * 0.55f + shimmer * 0.18f) * pulse
                        val barHeight = (h * target.coerceIn(0.08f, 1f))
                        drawRoundRect(
                            color = tint.copy(alpha = 0.35f + wave * 0.55f),
                            topLeft = Offset(i * (barWidth + gap), h - barHeight),
                            size = Size(barWidth, barHeight),
                            cornerRadius = androidx.compose.ui.geometry.CornerRadius(barWidth / 2),
                        )
                    }
                }
                LyricVisualizerMode.Wave -> {
                    val steps = 90
                    val path = androidx.compose.ui.graphics.Path()
                    for (i in 0..steps) {
                        val x = w * i / steps
                        val envelope = (sin(PI * i / steps).toFloat()).coerceAtLeast(0f)
                        val y = h / 2 + sin(i * 0.17f - seconds * 3.4f) * h * 0.32f * envelope * pulse
                        if (i == 0) path.moveTo(x, y) else path.lineTo(x, y)
                    }
                    drawPath(path, tint, style = Stroke(width = 2.5.dp.toPx()))
                }
                LyricVisualizerMode.Glow -> {
                    val radius = (h * 0.36f) * pulse
                    for (i in 6 downTo 1) {
                        val r = radius * (1f + i * 0.22f)
                        drawCircle(
                            color = visualAccent.copy(alpha = 0.10f * alpha / i),
                            center = Offset(w / 2, h / 2),
                            radius = r,
                        )
                    }
                    drawCircle(
                        color = visualAccent.copy(alpha = 0.85f * alpha),
                        center = Offset(w / 2, h / 2),
                        radius = radius * (0.55f + 0.08f * sin(seconds * 3f)),
                    )
                }
            }
        }
    }
}
