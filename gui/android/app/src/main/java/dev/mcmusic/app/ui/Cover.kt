package dev.mcmusic.app.ui

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.LruCache
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.dp
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.Prefs
import dev.mcmusic.app.ui.design.BlobShapes
import dev.mcmusic.app.ui.design.DynamicColour
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.blobShape

private val cache = LruCache<String, Bitmap>(64)

private val placeholderGlyphs = listOf(
    Lucide.Circle,
    Lucide.Squircle,
    Lucide.Cookie,
    Lucide.Flower,
    Lucide.Pentagon,
)

/** A stable, varied glyph for sleeves with no artwork. Real art is never altered. */
internal fun coverPlaceholder(key: String): Int =
    placeholderGlyphs[(key.hashCode().toLong() and 0x7fff_ffffL).mod(placeholderGlyphs.size.toLong()).toInt()]

/**
 * Cover art straight from the public API. A tiny cache plus a request per URL
 * is enough here: covers are 72 px and the API sets a short max-age.
 *
 * [dynamic] is only true for the playing cover; other tiles never retint the app.
 */
@Composable
fun Cover(
    url: String,
    shape: Shape,
    modifier: Modifier = Modifier,
    fallback: Color = Color.White.copy(alpha = 0.06f),
    dynamic: Boolean = false,
) {
    val design = LocalDesign.current
    var bitmap by remember(url) { mutableStateOf(cache.get(url)) }
    val placeholderShape = remember(url) {
        blobShape(BlobShapes.ids[coverPlaceholder(url).mod(BlobShapes.ids.size)])
    }

    LaunchedEffect(url) {
        if (bitmap == null && url.isNotBlank()) {
            val bytes = Api.cover(url) ?: return@LaunchedEffect
            BitmapFactory.decodeByteArray(bytes, 0, bytes.size)?.let {
                cache.put(url, it)
                bitmap = it
            }
        }
    }

    LaunchedEffect(url, bitmap, dynamic, Prefs.dynamicColour, Prefs.showCovers) {
        // Non-dynamic tiles must never clear a seed that the player owns, even
        // when they show the same URL in a list.
        if (!dynamic) return@LaunchedEffect
        if (!Prefs.dynamicColour || !Prefs.showCovers) {
            DynamicColour.clearCover(url)
            return@LaunchedEffect
        }
        val art = bitmap
        if (art != null) DynamicColour.setCover(art, url) else DynamicColour.clearCover(url)
    }

    Box(
        modifier
            .clip(shape)
            .background(fallback)
            .border(1.dp, design.hairline, shape),
    ) {
        if (bitmap == null) {
            Box(Modifier.fillMaxSize().clip(placeholderShape).background(design.accentSoft))
            BoxWithConstraints(Modifier.fillMaxSize(), Alignment.Center) {
                LucideIcon(
                    coverPlaceholder(url),
                    design.accentText,
                    size = minOf(maxWidth, maxHeight) * 0.42f,
                )
            }
        }
        bitmap?.let {
            Image(
                bitmap = it.asImageBitmap(),
                contentDescription = null,
                modifier = Modifier.fillMaxSize().clip(shape),
                contentScale = ContentScale.Crop,
            )
        }
    }
}
