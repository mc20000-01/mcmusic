package dev.mcmusic.app.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.kyant.backdrop.Backdrop
import com.kyant.backdrop.drawBackdrop
import com.kyant.backdrop.effects.blur
import com.kyant.backdrop.effects.colorControls
import com.kyant.backdrop.effects.lens
import com.kyant.backdrop.highlight.Highlight
import com.kyant.backdrop.shadow.Shadow

/** Fallback when there is no recorded backdrop (Android 12 and below). */
private val FallbackSurface = Color(0xFF171721).copy(alpha = 0.92f)

/**
 * The one place glass is defined, so the renderer can be swapped without
 * touching a screen: a recorded [Backdrop] is blurred, saturated and bent
 * through a lens, with a lit rim and a drop shadow. Without a backdrop it
 * degrades to a flat panel of the same size and shape.
 */
fun Modifier.liquidGlass(
    backdrop: Backdrop?,
    shape: Shape = RoundedCornerShape(28.dp),
    tint: Color = Color.White.copy(alpha = 0.06f),
    blurRadius: Dp = 22.dp,
    refractionHeight: Dp = 14.dp,
): Modifier {
    if (backdrop == null) {
        return clip(shape)
            .background(FallbackSurface, shape)
            .border(1.dp, Color.White.copy(alpha = 0.16f), shape)
    }

    return clip(shape)
        .drawBackdrop(
            backdrop = backdrop,
            shape = { shape },
            effects = {
                colorControls(brightness = 0f, contrast = 1.04f, saturation = 1.35f)
                blur(blurRadius.toPx())
                lens(
                    refractionHeight = refractionHeight.toPx(),
                    refractionAmount = (refractionHeight * 1.8f).toPx(),
                    depthEffect = true,
                    chromaticAberration = true,
                )
            },
            highlight = { Highlight(width = 1.dp, alpha = 0.60f) },
            shadow = { Shadow(radius = 26.dp, color = Color.Black.copy(alpha = 0.35f)) },
            onDrawSurface = { drawRect(tint) },
        )
        .border(1.dp, Color.White.copy(alpha = 0.18f), shape)
}
