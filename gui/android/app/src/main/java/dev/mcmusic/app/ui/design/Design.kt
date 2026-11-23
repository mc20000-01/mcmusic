package dev.mcmusic.app.ui.design

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
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
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/**
 * One visual language: the violet-on-ink flufi theme the web client uses.
 * The old iOS/One UI switcher is gone, so every screen, sheet and widget renders
 * with the same palette and the same soft, elevated surfaces.
 */
enum class DesignLanguage(val id: String, val label: String, val blurb: String) {
    Flufi("flufi", "Flufi", "Soft violet glow, deep ink, one accent");

    companion object {
        fun from(id: String?): DesignLanguage = Flufi
    }
}

/** Palette kept as a data class so screens can read bg/accent by name. */
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

object Palettes {
    val flufi = McPalette(
        id = "flufi",
        label = "Flufi",
        // Exact flufimusic v3 web tokens: one ink scale, one violet accent.
        bg = Color(0xFF08060D),
        bg2 = Color(0xFF100C18),
        fg = Color(0xFFFFFFFF),
        dim = Color(0xFF948AA6),
        line = Color(0xFF2A2040),
        accent = Color(0xFFA06BFF),
        dark = true,
    )

    val all = listOf(flufi)

    const val AUTO = "auto"

    fun byId(id: String?): McPalette = flufi

    /** `auto` is kept for old saved preferences; it now always means flufi. */
    fun resolve(id: String?, systemDark: Boolean): McPalette = flufi
}

/**
 * Radii, sizes and surface treatment shared by every screen. Keeping these in
 * one place is what makes the app read as one product instead of ten pages.
 */
@Immutable
class McDesign(
    val language: DesignLanguage,
    val palette: McPalette,
) {
    /** Retained so older call sites still compile. */
    val ios: Boolean get() = false

    // v3 uses one corner radius and flat surfaces, not a stack of rounded tiers.
    val cardRadius = 10.dp
    val tileRadius = 10.dp
    val screenPadding = 16.dp
    val gap = 12.dp

    val titleSize = 28.sp
    val titleWeight = FontWeight.SemiBold
    val sectionSize = 11.sp
    val sectionWeight = FontWeight.SemiBold

    val fg = palette.fg
    val dim = palette.dim
    val accent = palette.accent
    val accentSoft = Color(0xFF241A38)
    val accentWash = Color(0xFF181226)
    val hairline = palette.line

    /** Flat v3 panel fill; depth comes from the one-pixel border instead. */
    val cardFill = palette.bg2
}

val LocalDesign = compositionLocalOf { McDesign(DesignLanguage.Flufi, Palettes.flufi) }

/** The flat v3 ink stage: solid ink, no gradients and no blur. */
@Composable
private fun Stage(modifier: Modifier, design: McDesign) {
    androidx.compose.foundation.Canvas(modifier) {
        drawRect(color = design.palette.bg)
    }
}

private val McTypography = Typography(
    bodyLarge = TextStyle(fontFamily = FontFamily.Default, fontSize = 16.sp, lineHeight = 24.sp),
    bodyMedium = TextStyle(fontFamily = FontFamily.Default, fontSize = 14.sp, lineHeight = 20.sp),
    bodySmall = TextStyle(fontFamily = FontFamily.Default, fontSize = 12.sp, lineHeight = 17.sp),
    titleLarge = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Bold, fontSize = 22.sp),
    titleMedium = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.SemiBold, fontSize = 16.sp),
    labelLarge = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.SemiBold, fontSize = 14.sp),
)

/**
 * Wraps the app in the flufi palette, the glow stage and a matching Material
 * scheme so dialogs, switches and text fields inherit the same colours.
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
            primaryContainer = design.accentSoft,
            onPrimaryContainer = palette.fg,
            background = palette.bg,
            onBackground = palette.fg,
            surface = palette.bg2,
            onSurface = palette.fg,
            surfaceVariant = palette.bg2,
            onSurfaceVariant = palette.dim,
            outline = palette.line,
            secondary = palette.accent,
            onSecondary = palette.bg,
            error = Color(0xFFFF6B72),
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
        MaterialTheme(colorScheme = scheme, typography = McTypography) {
            Box(Modifier.fillMaxSize()) {
                Stage(Modifier.fillMaxSize(), design)
                content()
            }
        }
    }
}

/** Flat v3 panel: solid fill and a single hairline edge, no shadow. */
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
