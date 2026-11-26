package dev.mcmusic.app.ui.design

import androidx.compose.foundation.shape.GenericShape
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.Shape
import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.atan2
import kotlin.math.ceil
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin
import kotlin.math.sqrt
import kotlin.math.tan

/** Uppercase SVG-style commands, kept separate from drawing so geometry is testable. */
sealed interface BlobCommand {
    data class Move(val x: Float, val y: Float) : BlobCommand
    data class Line(val x: Float, val y: Float) : BlobCommand
    data class Cubic(val x1: Float, val y1: Float, val x2: Float, val y2: Float, val x3: Float, val y3: Float) : BlobCommand
    data class Quad(val x1: Float, val y1: Float, val x2: Float, val y2: Float) : BlobCommand
    object Close : BlobCommand
}

/** Flat commands plus their bounds in the normalised 100x100 coordinate space. */
data class BlobGeometry(
    val commands: List<BlobCommand>,
    val minX: Float,
    val minY: Float,
    val maxX: Float,
    val maxY: Float,
) {
    val width: Float get() = maxX - minX
    val height: Float get() = maxY - minY

    fun drawInto(path: Path, scaleX: Float, scaleY: Float) {
        commands.forEach { command ->
            when (command) {
                is BlobCommand.Move -> path.moveTo(command.x * scaleX, command.y * scaleY)
                is BlobCommand.Line -> path.lineTo(command.x * scaleX, command.y * scaleY)
                is BlobCommand.Cubic -> path.cubicTo(
                    command.x1 * scaleX, command.y1 * scaleY, command.x2 * scaleX, command.y2 * scaleY,
                    command.x3 * scaleX, command.y3 * scaleY,
                )
                is BlobCommand.Quad -> path.quadraticBezierTo(
                    command.x1 * scaleX, command.y1 * scaleY, command.x2 * scaleX, command.y2 * scaleY,
                )
                BlobCommand.Close -> path.close()
            }
        }
    }
}

private val blobToken = Regex("""[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?|[A-Z]""")

/** Parse the generated M/H/V/C/Q/A/Z/L paths; arcs become explicit cubic segments. */
fun parseBlobPath(source: String): BlobGeometry {
    val tokens = blobToken.findAll(source).map { it.value }.toList()
    require(tokens.isNotEmpty()) { "Empty blob path" }
    val commands = mutableListOf<BlobCommand>()
    var index = 0
    var x = 0f
    var y = 0f
    var startX = 0f
    var startY = 0f
    var minX = Float.POSITIVE_INFINITY
    var minY = Float.POSITIVE_INFINITY
    var maxX = Float.NEGATIVE_INFINITY
    var maxY = Float.NEGATIVE_INFINITY

    fun number(): Float {
        require(index < tokens.size) { "Truncated blob path" }
        return tokens[index++].toFloatOrNull() ?: throw IllegalArgumentException("Bad blob number: ${tokens[index - 1]}")
    }

    fun track(px: Float, py: Float) {
        minX = min(minX, px); minY = min(minY, py)
        maxX = max(maxX, px); maxY = max(maxY, py)
    }

    fun cubicArc(
        fromX: Float, fromY: Float,
        rxArg: Float, ryArg: Float, degrees: Float, large: Boolean, sweep: Boolean,
        toX: Float, toY: Float,
    ) {
        var rx = abs(rxArg).toDouble()
        var ry = abs(ryArg).toDouble()
        if (rx < 1e-6 || ry < 1e-6 || (fromX == toX && fromY == toY)) {
            commands += BlobCommand.Line(toX, toY)
            track(toX, toY)
            return
        }
        val phi = Math.toRadians(degrees.toDouble())
        val cosPhi = cos(phi); val sinPhi = sin(phi)
        val halfX = (fromX - toX) / 2.0; val halfY = (fromY - toY) / 2.0
        val localX = cosPhi * halfX + sinPhi * halfY
        val localY = -sinPhi * halfX + cosPhi * halfY
        val scale = localX * localX / (rx * rx) + localY * localY / (ry * ry)
        if (scale > 1.0) {
            val factor = sqrt(scale)
            rx *= factor
            ry *= factor
        }
        val sign = if (large != sweep) 1.0 else -1.0
        val numerator = rx * rx * ry * ry - rx * rx * localY * localY - ry * ry * localX * localX
        val denominator = rx * rx * localY * localY + ry * ry * localX * localX
        val factor = sign * sqrt(max(0.0, numerator / denominator))
        val centreLocalX = factor * rx * localY / ry; val centreLocalY = -factor * ry * localX / rx
        val centreX = cosPhi * centreLocalX - sinPhi * centreLocalY + (fromX + toX) / 2.0
        val centreY = sinPhi * centreLocalX + cosPhi * centreLocalY + (fromY + toY) / 2.0

        fun point(t: Double) = Pair(
            centreX + rx * cosPhi * cos(t) - ry * sinPhi * sin(t),
            centreY + rx * sinPhi * cos(t) + ry * cosPhi * sin(t),
        )

        fun slope(t: Double) = Pair(
            -rx * cosPhi * sin(t) - ry * sinPhi * cos(t),
            -rx * sinPhi * sin(t) + ry * cosPhi * cos(t),
        )

        val startAngle = atan2((localY - centreLocalY) / ry, (localX - centreLocalX) / rx)
        val endAngle = atan2((-localY - centreLocalY) / ry, (-localX - centreLocalX) / rx)
        var sweepAngle = endAngle - startAngle
        if (!sweep && sweepAngle > 0.0) sweepAngle -= 2 * PI
        if (sweep && sweepAngle < 0.0) sweepAngle += 2 * PI
        val steps = ceil(abs(sweepAngle) / (PI / 2.0)).toInt().coerceAtLeast(1)
        val step = sweepAngle / steps
        val handle = 4.0 / 3.0 * tan(step / 4.0)
        var angle = startAngle
        repeat(steps) {
            val next = angle + step
            val (sx, sy) = point(angle)
            val (sdX, sdY) = slope(angle)
            val (ex, ey) = point(next)
            val (edX, edY) = slope(next)
            val c1x = (sx + handle * sdX).toFloat(); val c1y = (sy + handle * sdY).toFloat()
            val c2x = (ex - handle * edX).toFloat(); val c2y = (ey - handle * edY).toFloat()
            val endX = ex.toFloat(); val endY = ey.toFloat()
            commands += BlobCommand.Cubic(c1x, c1y, c2x, c2y, endX, endY)
            track(c1x, c1y); track(c2x, c2y); track(endX, endY)
            angle = next
        }
    }

    while (index < tokens.size) {
        when (tokens[index++]) {
            "M" -> {
                require(index + 1 < tokens.size) { "Truncated blob move" }
                x = number()
                y = number()
                startX = x
                startY = y
                commands += BlobCommand.Move(x, y)
                track(x, y)
            }
            "L" -> {
                var count = 0
                while (index < tokens.size && tokens[index].toFloatOrNull() != null) {
                    val nx = number()
                    val ny = number()
                    commands += BlobCommand.Line(nx, ny)
                    track(nx, ny)
                    x = nx
                    y = ny
                    count++
                }
                require(count > 0) { "Empty blob line" }
            }
            "H" -> {
                var count = 0
                while (index < tokens.size && tokens[index].toFloatOrNull() != null) {
                    x = number()
                    commands += BlobCommand.Line(x, y)
                    track(x, y)
                    count++
                }
                require(count > 0) { "Empty blob horizontal line" }
            }
            "V" -> {
                var count = 0
                while (index < tokens.size && tokens[index].toFloatOrNull() != null) {
                    y = number()
                    commands += BlobCommand.Line(x, y)
                    track(x, y)
                    count++
                }
                require(count > 0) { "Empty blob vertical line" }
            }
            "C" -> {
                var count = 0
                while (index < tokens.size && tokens[index].toFloatOrNull() != null) {
                    val x1 = number(); val y1 = number()
                    val x2 = number(); val y2 = number()
                    val x3 = number(); val y3 = number()
                    commands += BlobCommand.Cubic(x1, y1, x2, y2, x3, y3)
                    track(x1, y1); track(x2, y2); track(x3, y3)
                    x = x3
                    y = y3
                    count++
                }
                require(count > 0) { "Empty blob curve" }
            }
            "Q" -> {
                var count = 0
                while (index < tokens.size && tokens[index].toFloatOrNull() != null) {
                    val x1 = number(); val y1 = number()
                    val x2 = number(); val y2 = number()
                    commands += BlobCommand.Quad(x1, y1, x2, y2)
                    track(x1, y1); track(x2, y2)
                    x = x2
                    y = y2
                    count++
                }
                require(count > 0) { "Empty blob quadratic curve" }
            }
            "A" -> {
                var count = 0
                while (index < tokens.size && tokens[index].toFloatOrNull() != null) {
                    val rx = number(); val ry = number(); val rotation = number()
                    val large = number() != 0f
                    val sweep = number() != 0f
                    val nx = number(); val ny = number()
                    cubicArc(x, y, rx, ry, rotation, large, sweep, nx, ny)
                    x = nx
                    y = ny
                    count++
                }
                require(count > 0) { "Empty blob arc" }
            }
            "Z" -> {
                commands += BlobCommand.Close
                x = startX
                y = startY
            }
            else -> throw IllegalArgumentException("Unsupported blob command: ${tokens[index - 1]}")
        }
    }
    return BlobGeometry(commands, minX, minY, maxX, maxY)
}

private val geometries: Map<String, BlobGeometry> = BlobShapes.paths.mapValues { parseBlobPath(it.value) }

private fun geometry(id: String): BlobGeometry =
    geometries[id] ?: geometries.getValue(BlobShapes.ids.first())

/** Compose path in the caller's coordinate space, scaled from the 100-unit tokens. */
fun blobPath(id: String, scaleX: Float, scaleY: Float): Path {
    val path = Path()
    geometry(id).drawInto(path, scaleX, scaleY)
    return path
}

/** Flat silhouette for missing artwork; real covers never use this shape. */
fun blobShape(id: String): Shape = GenericShape { size, _ ->
    geometry(id).drawInto(this, size.width / 100f, size.height / 100f)
}
