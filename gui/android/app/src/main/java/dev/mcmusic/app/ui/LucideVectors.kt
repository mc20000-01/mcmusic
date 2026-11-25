package dev.mcmusic.app.ui

import android.content.Context
import androidx.annotation.DrawableRes
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.PathSegment
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.asComposePath
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.graphics.vector.PathNode
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.core.graphics.PathParser
import org.xmlpull.v1.XmlPullParser
import java.util.concurrent.ConcurrentHashMap
import kotlin.math.min

/**
 * Runtime bridge from the vendored Lucide vector drawables to Compose
 * ImageVectors. The XML files stay the single source of path geometry; this is
 * the only place that turns their path data into Compose vectors, so every
 * Compose glyph shares one configurable stroke treatment.
 *
 * Filled-icon mode is deliberately absent: the XML elements are outline
 * geometry, not separable rect/circle primitives, so filling them would turn
 * the icons into solid blobs.
 */
private const val ANDROID_NS = "http://schemas.android.com/apk/res/android"

internal object LucideVectors {
    private const val VIEWPORT = 24f
    private const val STANDARD_BAKED_WIDTH = 2f

    private data class CacheKey(val resId: Int, val sizeDp: Float, val scale: Float)
    private data class Element(val pathData: String, val bakedWidth: Float)
    private data class Spec(val viewportWidth: Float, val viewportHeight: Float, val elements: List<Element>)

    // ImageVector.Builder is single-use, so memoize the finished vectors.
    private val cache = ConcurrentHashMap<CacheKey, ImageVector>()

    fun imageVector(context: Context, @DrawableRes resId: Int, sizeDp: Dp, scale: Float): ImageVector {
        val size = sizeDp.value.coerceAtLeast(1f)
        val key = CacheKey(resId, size, scale)
        return cache.getOrPut(key) { build(context, resId, size, scale) }
    }

    private fun build(context: Context, resId: Int, sizeDp: Float, scale: Float): ImageVector {
        val spec = parse(context, resId)
        // 1x is Lucide's default: size / 12 logical pixels. Higher scales are
        // capped at size / 6; on a 24x24 viewport that yields 2/3/4 units.
        val baseWidth = vectorIconStrokeWidth(scale, sizeDp)
        return ImageVector.Builder(
            name = context.resources.getResourceEntryName(resId),
            defaultWidth = VIEWPORT.dp,
            defaultHeight = VIEWPORT.dp,
            viewportWidth = spec.viewportWidth,
            viewportHeight = spec.viewportHeight,
        ).apply {
            spec.elements.forEach { element ->
                val composePath = PathParser.createPathFromPathData(element.pathData).asComposePath()
                addPath(
                    composePath.toPathNodes(),
                    fill = null,
                    stroke = SolidColor(Color.Black),
                    strokeLineWidth = baseWidth * (element.bakedWidth / STANDARD_BAKED_WIDTH),
                    strokeLineCap = StrokeCap.Round,
                    strokeLineJoin = StrokeJoin.Round,
                )
            }
        }.build()
    }

    private fun parse(context: Context, @DrawableRes resId: Int): Spec {
        val parser = context.resources.getXml(resId)
        val elements = mutableListOf<Element>()
        var viewportWidth = VIEWPORT
        var viewportHeight = VIEWPORT
        try {
            while (parser.eventType != XmlPullParser.END_DOCUMENT) {
                if (parser.eventType == XmlPullParser.START_TAG) {
                    when (parser.name) {
                        "vector" -> {
                            viewportWidth = parser.androidFloat("viewportWidth", VIEWPORT)
                            viewportHeight = parser.androidFloat("viewportHeight", VIEWPORT)
                        }
                        else -> {
                            val pathData = parser.androidAttribute("pathData")
                            if (pathData != null) {
                                elements += Element(
                                    pathData = pathData,
                                    bakedWidth = parser.androidFloat("strokeWidth", STANDARD_BAKED_WIDTH),
                                )
                            }
                        }
                    }
                }
                parser.next()
            }
        } finally {
            parser.close()
        }
        return Spec(viewportWidth, viewportHeight, elements)
    }
}

/** Width in logical pixels after applying the shared scale and ceiling. */
internal fun renderedIconStrokeWidth(scale: Float, sizeDp: Float): Float {
    val size = sizeDp.coerceAtLeast(1f)
    return min(size * scale / 12f, size / 6f)
}

/** Convert the logical-pixel width into Lucide's 24x24 viewport units. */
internal fun vectorIconStrokeWidth(scale: Float, sizeDp: Float): Float {
    val size = sizeDp.coerceAtLeast(1f)
    return renderedIconStrokeWidth(scale, size) * 24f / size
}

/**
 * ImageVector.Builder accepts PathNodes rather than a Compose Path. Iterate the
 * path produced by AndroidX's SVG parser and preserve its curves exactly; only
 * conics are converted to their equivalent cubic Beziers because PathNode has
 * no conic variant.
 */
private fun Path.toPathNodes(): List<PathNode> {
    val nodes = mutableListOf<PathNode>()
    val iterator = androidx.compose.ui.graphics.PathIterator(
        this,
        androidx.compose.ui.graphics.PathIterator.ConicEvaluation.AsConic,
        0f,
    )
    val points = FloatArray(8)
    while (true) {
        when (iterator.next(points, 0)) {
            PathSegment.Type.Move -> nodes += PathNode.MoveTo(points[0], points[1])
            PathSegment.Type.Line -> nodes += PathNode.LineTo(points[2], points[3])
            PathSegment.Type.Quadratic ->
                nodes += PathNode.QuadTo(points[2], points[3], points[4], points[5])
            PathSegment.Type.Conic -> {
                val scale = 2f * points[6] / 3f
                val startX = points[0]
                val startY = points[1]
                val controlX = points[2]
                val controlY = points[3]
                val endX = points[4]
                val endY = points[5]
                nodes += PathNode.CurveTo(
                    startX + scale * (controlX - startX),
                    startY + scale * (controlY - startY),
                    endX + scale * (controlX - endX),
                    endY + scale * (controlY - endY),
                    endX,
                    endY,
                )
            }
            PathSegment.Type.Cubic -> nodes += PathNode.CurveTo(
                points[2],
                points[3],
                points[4],
                points[5],
                points[6],
                points[7],
            )
            PathSegment.Type.Close -> nodes += PathNode.Close
            PathSegment.Type.Done -> break
        }
    }
    return nodes
}

private fun XmlPullParser.androidAttribute(name: String): String? =
    getAttributeValue(ANDROID_NS, name) ?: getAttributeValue(null, name)

private fun XmlPullParser.androidFloat(name: String, fallback: Float): Float =
    androidAttribute(name)?.toFloatOrNull() ?: fallback
