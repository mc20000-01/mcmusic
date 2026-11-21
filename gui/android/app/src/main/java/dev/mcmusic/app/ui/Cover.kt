package dev.mcmusic.app.ui

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.LruCache
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
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

private val cache = LruCache<String, Bitmap>(64)

/**
 * Cover art straight from the public API. A tiny cache plus a request per URL
 * is enough here: covers are 72 px and the API sets a short max-age.
 */
@Composable
fun Cover(
    url: String,
    shape: Shape,
    modifier: Modifier = Modifier,
    fallback: Color = Color.White.copy(alpha = 0.06f),
) {
    var bitmap by remember(url) { mutableStateOf(cache.get(url)) }

    LaunchedEffect(url) {
        if (bitmap == null && url.isNotBlank()) {
            val bytes = Api.cover(url) ?: return@LaunchedEffect
            BitmapFactory.decodeByteArray(bytes, 0, bytes.size)?.let {
                cache.put(url, it)
                bitmap = it
            }
        }
    }

    Box(
        modifier
            .clip(shape)
            .background(fallback)
            .border(1.dp, Color.White.copy(alpha = 0.06f), shape),
    ) {
        if (bitmap == null) {
            Box(Modifier.fillMaxSize(), Alignment.Center) {
                LucideIcon(
                    Lucide.Play,
                    Color.White.copy(alpha = 0.24f),
                    Modifier.fillMaxSize(0.34f),
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
