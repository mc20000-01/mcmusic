package dev.mcmusic.app.ui.design

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.compositionLocalOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/**
 * The client ships exactly one visual language: the flufi-ui palette the web
 * client uses. The old iOS/One UI switcher is gone, so every screen, sheet and
 * widget renders with the same flat, dark tokens.
 */
enum class DesignLanguage(val id: String, val label: String, val blurb: String) {
    Flufi("flufi", "Flufi", "Flat panels, thin borders, one accent");

    companion object {
        fun from(id: String?): DesignLanguage = Flufi
    }
}

/** One palette. Kept as a data class so screens can read bg/accent by name. */
@Immutable
data class McPalette(
    val id: String,
    val label: String,
    val bg: Color,
    val bg2: Color,
    val fg: Color,
    val dim: Color,
    val line: Color,
    val accent: Color,
    val dark: Boolean,
)

/** flufi-ui's tokens, darkened to match the web client's env.css overrides. */
object Palettes {
    val flufi = McPalette(
        id = "flufi",
        label = "Flufi",
        bg = Color(0xFF08080A),
        bg2 = Color(0xFF0D0D10),
        fg = Color(0xFFCFCFD6),
        dim = Color(0xFF8B8B93),
        line = Color(0xFF1B1B20),
        accent = Color(0xFF9D91D6),
        dark = true,
    )

    val all = listOf(flufi)

    const val AUTO = "auto"

    fun byId(id: String?): McPalette = flufi

    /** `auto` is kept for old saved preferences; it now always means flufi. */
    fun resolve(id: String?, systemDark: Boolean): McPalette = flufi
}

/**
 * Radii, sizes and surface treatment shared by every screen, so screens never
 * hard-code a corner radius or a colour.
 */
@Immutable
class McDesign(
    val language: DesignLanguage,
    val palette: McPalette,
) {
    /** flufi-ui is flat; retained so older call sites still compile. */
    val ios: Boolean get() = false

    val cardRadius = 12.dp
    val tileRadius = 8.dp
    val screenPadding = 16.dp
    val gap = 12.dp

    val titleSize = 26.sp
    val titleWeight = FontWeight.SemiBold
    val sectionSize = 11.sp
    val sectionWeight = FontWeight.SemiBold

    val fg = palette.fg
    val dim = palette.dim
    val accent = palette.accent
    val accentSoft = palette.accent.copy(alpha = 0.16f)
    val hairline = palette.line

    /** Flat card fill: no glass, no gradients. */
    val cardFill = palette.bg2
}

val LocalDesign = compositionLocalOf { McDesign(DesignLanguage.Flufi, Palettes.flufi) }

/** Palette/window stage: one flat background, no glow gradients. */
@Composable
private fun Stage(modifier: Modifier, design: McDesign) {
    androidx.compose.foundation.Canvas(modifier) {
        drawRect(color = design.palette.bg)
    }
}

/**
 * Wraps the app in the flufi palette and a matching Material scheme so dialogs,
 * switches and text fields inherit the same colours.
 */
@Composable
fun McTheme(
    paletteId: String = "flufi",
    language: DesignLanguage = DesignLanguage.Flufi,
    content: @Composable () -> Unit,
) {
    val palette = Palettes.resolve(paletteId, isSystemInDarkTheme())
    val design = remember(palette, language) { McDesign(language, palette) }
    val scheme = if (palette.dark) {
        darkColorScheme(
            primary = palette.accent,
            onPrimary = palette.bg,
            background = palette.bg,
            onBackground = palette.fg,
            surface = palette.bg2,
            onSurface = palette.fg,
            surfaceVariant = palette.bg2,
            onSurfaceVariant = palette.dim,
            outline = palette.line,
            secondary = palette.accent,
        )
    } else {
        lightColorScheme(
            primary = palette.accent,
            background = palette.bg,
            onBackground = palette.fg,
            surface = palette.bg2,
            onSurface = palette.fg,
            outline = palette.line,
        )
    }
    CompositionLocalProvider(LocalDesign provides design) {
        MaterialTheme(colorScheme = scheme) {
            content()
        }
    }
}

/** Flat flufi surface: fill + hairline, never a blur or a gradient. */
@Composable
fun Modifier.mcSurface(
    shape: Shape = RoundedCornerShape(LocalDesign.current.cardRadius),
    tint: Color = Color.Transparent,
): Modifier {
    val design = LocalDesign.current
    val fill = if (tint == Color.Transparent) design.cardFill else tint
    return clip(shape)
        .background(fill, shape)
        .border(1.dp, design.hairline, shape)
}

/** Reads the saved language; every value maps to the single flufi language. */
fun currentDesignLanguage(): DesignLanguage = DesignLanguage.from(null)
