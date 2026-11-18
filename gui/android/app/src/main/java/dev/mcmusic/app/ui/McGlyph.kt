package dev.mcmusic.app.ui

import androidx.compose.foundation.Canvas
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke

/** The tab icons, drawn as vectors so the app carries no icon dependency. */
enum class McIcon { Home, Search, Play, Library, Download, Settings }

@Composable
fun McGlyph(
    icon: McIcon,
    tint: Color,
    modifier: Modifier = Modifier,
    filled: Boolean = false,
) {
    Canvas(modifier) {
        val u = size.minDimension / 24f
        val stroke = (if (filled) 2.0f else 1.7f) * u

        fun line(x1: Float, y1: Float, x2: Float, y2: Float) = drawLine(
            color = tint,
            start = Offset(x1 * u, y1 * u),
            end = Offset(x2 * u, y2 * u),
            strokeWidth = stroke,
            cap = StrokeCap.Round,
        )

        when (icon) {
            McIcon.Home -> {
                val roof = Path().apply {
                    moveTo(3.5f * u, 10.8f * u)
                    lineTo(12f * u, 3.4f * u)
                    lineTo(20.5f * u, 10.8f * u)
                }
                drawPath(roof, tint, style = Stroke(stroke, cap = StrokeCap.Round))
                line(5.8f, 10.4f, 5.8f, 20f)
                line(18.2f, 10.4f, 18.2f, 20f)
                line(9.8f, 20f, 9.8f, 14.2f)
                line(14.2f, 14.2f, 14.2f, 20f)
            }

            McIcon.Search -> {
                drawCircle(tint, radius = 6.6f * u, center = Offset(10.4f * u, 10.4f * u), style = Stroke(stroke))
                line(15.4f, 15.4f, 20.4f, 20.4f)
            }

            McIcon.Play -> {
                val tri = Path().apply {
                    moveTo(7.6f * u, 4.6f * u)
                    lineTo(19.4f * u, 12f * u)
                    lineTo(7.6f * u, 19.4f * u)
                    close()
                }
                drawPath(tri, tint)
            }

            McIcon.Library -> {
                line(4.2f, 6.6f, 19.8f, 6.6f)
                line(4.2f, 12f, 19.8f, 12f)
                line(4.2f, 17.4f, 13.6f, 17.4f)
            }

            McIcon.Download -> {
                line(12f, 3.6f, 12f, 15f)
                line(7.2f, 10.4f, 12f, 15.2f)
                line(16.8f, 10.4f, 12f, 15.2f)
                line(4.6f, 19.6f, 19.4f, 19.6f)
            }

            McIcon.Settings -> {
                drawCircle(tint, radius = 3.4f * u, center = Offset(12f * u, 12f * u), style = Stroke(stroke))
                drawCircle(tint, radius = 8.2f * u, center = Offset(12f * u, 12f * u), style = Stroke(stroke * 0.8f))
                line(12f, 1.2f, 12f, 3f)
                line(12f, 21f, 12f, 22.8f)
                line(1.2f, 12f, 3f, 12f)
                line(21f, 12f, 22.8f, 12f)
            }
        }
    }
}
