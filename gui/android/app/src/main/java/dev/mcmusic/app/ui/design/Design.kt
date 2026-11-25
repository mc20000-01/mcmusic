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
 * Material 3 shape, type and colour roles with Lucide as the only icon source.
 *
 * Five palette families come from the supplied swatch sheet. Each family has a
 * light variant from the top half of the sheet and a dark variant from the
 * bottom half, so "System" follows the device appearance without a second
 * settings control. Replace the token values here when colours change again.
 */
enum class DesignLanguage(val id: String, val label: String, val blurb: String) {
    Flufi("flufi", "Flufi", "Material 3 surfaces, one Lucide icon language");

    companion object {
        fun from(id: String?): DesignLanguage = Flufi
    }
}

/** Concrete Material 3 token set for one light or dark variant. */
@Immutable
data class McPalette(
    val id: String,
    val label: String,
    val bg: Color,
    val bg2: Color,
    val surface: Color,
    val surface2: Color,
    val fg: Color,
    val dim: Color,
    val dim2: Color,
    val line: Color,
    val line2: Color,
    val accent: Color,
    /** Accent shade used as text/icon on surfaces; bright accents stay fills. */
    val accentText: Color,
    val accentFg: Color,
    val dark: Boolean,
    val error: Color = if (dark) Color(0xFFFF6B72) else Color(0xFFB3261E),
)

/** One family = one light variant + one dark variant from the same hues. */
@Immutable
data class PaletteFamily(
    val id: String,
    val label: String,
    val light: McPalette,
    val dark: McPalette,
) {
    fun resolve(systemDark: Boolean): McPalette = if (systemDark) dark else light
}

object Palettes {
    private fun variant(
        family: String,
        label: String,
        dark: Boolean,
        bg: String,
        bg2: String,
        surface: String,
        surface2: String,
        fg: String,
        dim: String,
        dim2: String,
        line: String,
        line2: String,
        accent: String,
        accentText: String = accent,
        accentFg: String = "08060D",
    ) = McPalette(
        id = "$family-${if (dark) "dark" else "light"}",
        label = label,
        bg = Color(android.graphics.Color.parseColor("#$bg")),
        bg2 = Color(android.graphics.Color.parseColor("#$bg2")),
        surface = Color(android.graphics.Color.parseColor("#$surface")),
        surface2 = Color(android.graphics.Color.parseColor("#$surface2")),
        fg = Color(android.graphics.Color.parseColor("#$fg")),
        dim = Color(android.graphics.Color.parseColor("#$dim")),
        dim2 = Color(android.graphics.Color.parseColor("#$dim2")),
        line = Color(android.graphics.Color.parseColor("#$line")),
        line2 = Color(android.graphics.Color.parseColor("#$line2")),
        accent = Color(android.graphics.Color.parseColor("#$accent")),
        accentText = Color(android.graphics.Color.parseColor("#$accentText")),
        accentFg = Color(android.graphics.Color.parseColor("#$accentFg")),
        dark = dark,
    )

    val violet = PaletteFamily(
        id = "violet",
        label = "Violet",
        light = variant("violet", "Violet", false, "F5F2FF", "EDE7FF", "FFFFFF", "F7F4FF",
            "08060D", "473872", "6A54AA", "DACDFF", "CAB8FF", "9F7EFF",
            accentText = "5B3F9E"),
        dark = variant("violet", "Violet", true, "171721", "222130", "2A293C", "444361",
            "FFFFFF", "AAAAB7", "8B8A9D", "35344B", "605F78", "9F7EFF"),
    )

    val indigo = PaletteFamily(
        id = "indigo",
        label = "Indigo",
        light = variant("indigo", "Indigo", false, "F2F4FF", "E8EBFF", "FFFFFF", "F5F6FF",
            "08060D", "3B4172", "5761AA", "CFD5FF", "BAC3FF", "8293FF",
            accentText = "4A56A8"),
        dark = variant("indigo", "Indigo", true, "12171F", "1B212D", "212838", "36425B",
            "FFFFFF", "A4A9B5", "828999", "2A3346", "545E73", "8293FF"),
    )

    val sky = PaletteFamily(
        id = "sky",
        label = "Sky",
        light = variant("sky", "Sky", false, "F1F8FE", "E7F3FE", "FFFFFF", "F4F9FE",
            "08060D", "385272", "527CA9", "CCE5FE", "B6DAFE", "7BBDFE",
            accentText = "235F93"),
        dark = variant("sky", "Sky", true, "182127", "222F39", "2A3A46", "455F72",
            "FFFFFF", "ABB7BF", "8B9BA7", "354A58", "607787", "7BBDFE"),
    )

    val aqua = PaletteFamily(
        id = "aqua",
        label = "Aqua",
        light = variant("aqua", "Aqua", false, "F1FBFC", "E7F9FA", "FFFFFF", "F4FCFD",
            "08060D", "386168", "53939A", "CDF3F5", "B6EDF1", "7CE0E6",
            accentText = "126F77"),
        dark = variant("aqua", "Aqua", true, "15241C", "1F3328", "263F32", "3E6751",
            "FFFFFF", "A8BAB0", "87A093", "30503F", "5A7D6B", "7CE0E6"),
    )

    val mint = PaletteFamily(
        id = "mint",
        label = "Mint",
        light = variant("mint", "Mint", false, "F1FFF5", "E7FFEE", "FFFFFF", "F4FFF7",
            "08060D", "386E4C", "52A76F", "CCFFDC", "B6FFCC", "7BFFA4",
            accentText = "216A43"),
        dark = variant("mint", "Mint", true, "15241A", "1F3425", "26412E", "3E694B",
            "FFFFFF", "A8BBAE", "87A28F", "30513A", "5A7F66", "7BFFA4"),
    )

    /** Exactly five chooser entries; each adapts to system light/dark. */
    val families = listOf(violet, indigo, sky, aqua, mint)

    private val byConcreteId: Map<String, McPalette> = families.flatMap { listOf(it.light, it.dark) }
        .associateBy { it.id }

    private val byFamilyId: Map<String, PaletteFamily> = families.associateBy { it.id }

    const val AUTO = "auto"

    /** Legacy ids keep the light/dark half they used to imply. */
    private val aliases = mapOf(
        "flufi" to "violet-dark", "dark" to "violet-dark", "dusk" to "violet-dark",
        "paper" to "violet-light", "light" to "violet-light",
        "ink" to "indigo-dark", "amoled" to "indigo-dark",
        "midnight" to "sky-dark", "tide" to "aqua-dark", "forest" to "mint-dark",
        "rose" to "violet-dark", "copper" to "violet-dark", "mocha" to "violet-dark",
        "system" to AUTO, "" to AUTO,
    )

    private fun canonicalID(id: String?): String {
        val key = (id ?: AUTO).lowercase().trim()
        return aliases[key] ?: key
    }

    /** `auto`, `system`, empty and bare family ids follow the system appearance. */
    fun resolve(id: String?, systemDark: Boolean): McPalette {
        val key = canonicalID(id)
        return byConcreteId[key]
            ?: byFamilyId[key]?.resolve(systemDark)
            ?: violet.resolve(systemDark)
    }
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

    // Material 3 shape scale expressed in the compact flufi radius.
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
    val accentText = palette.accentText
    val onAccent = palette.accentFg

    /** Translucent accent tints for chips, covers and inactive fills. */
    val accentSoft = palette.accent.copy(alpha = if (palette.dark) 0.16f else 0.10f)
    val accentWash = palette.accent.copy(alpha = if (palette.dark) 0.08f else 0.05f)
    val hairline = palette.line

    /** Flat Material 3 surface container; depth comes from the hairline edge. */
    val cardFill = palette.surface
}

val LocalDesign = compositionLocalOf { McDesign(DesignLanguage.Flufi, Palettes.violet.dark) }

/** The flat stage: solid palette background, no gradients and no blur. */
@Composable
private fun Stage(modifier: Modifier, design: McDesign) {
    androidx.compose.foundation.Canvas(modifier) {
        drawRect(color = design.palette.bg)
    }
}

private val McTypography = Typography(
    displayLarge = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Bold, fontSize = 40.sp),
    displayMedium = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Bold, fontSize = 34.sp),
    displaySmall = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.SemiBold, fontSize = 28.sp),
    headlineLarge = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Bold, fontSize = 28.sp),
    headlineMedium = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.SemiBold, fontSize = 24.sp),
    headlineSmall = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.SemiBold, fontSize = 22.sp),
    titleLarge = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Bold, fontSize = 22.sp),
    titleMedium = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.SemiBold, fontSize = 16.sp),
    titleSmall = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.SemiBold, fontSize = 14.sp),
    bodyLarge = TextStyle(fontFamily = FontFamily.Default, fontSize = 16.sp, lineHeight = 24.sp),
    bodyMedium = TextStyle(fontFamily = FontFamily.Default, fontSize = 14.sp, lineHeight = 20.sp),
    bodySmall = TextStyle(fontFamily = FontFamily.Default, fontSize = 12.sp, lineHeight = 17.sp),
    labelLarge = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.SemiBold, fontSize = 14.sp),
    labelMedium = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.SemiBold, fontSize = 12.sp),
    labelSmall = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Medium, fontSize = 11.sp),
)

/**
 * Provides the resolved palette and a complete Material 3 scheme so dialogs,
 * switches and text fields inherit the same colours as hand-painted screens.
 */
@Composable
fun McTheme(
    paletteId: String = Palettes.AUTO,
    language: DesignLanguage = DesignLanguage.Flufi,
    content: @Composable () -> Unit,
) {
    val palette = Palettes.resolve(paletteId, isSystemInDarkTheme())
    val design = remember(palette, language) { McDesign(language, palette) }
    val onError = if (palette.dark) palette.bg else Color.White
    val scheme = if (palette.dark) {
        darkColorScheme(
            primary = palette.accent,
            onPrimary = palette.accentFg,
            primaryContainer = palette.surface2,
            onPrimaryContainer = palette.fg,
            secondary = palette.accent,
            onSecondary = palette.accentFg,
            secondaryContainer = palette.surface,
            onSecondaryContainer = palette.fg,
            tertiary = palette.accent,
            onTertiary = palette.accentFg,
            tertiaryContainer = palette.surface2,
            onTertiaryContainer = palette.fg,
            background = palette.bg,
            onBackground = palette.fg,
            surface = palette.surface,
            onSurface = palette.fg,
            surfaceVariant = palette.surface2,
            onSurfaceVariant = palette.dim,
            surfaceTint = palette.accent,
            outline = palette.line,
            outlineVariant = palette.line2,
            error = palette.error,
            onError = onError,
            onErrorContainer = palette.fg,
            inverseSurface = palette.fg,
            inverseOnSurface = palette.bg,
            inversePrimary = palette.accentText,
            scrim = Color(0x99000000),
        )
    } else {
        lightColorScheme(
            primary = palette.accent,
            onPrimary = palette.accentFg,
            primaryContainer = palette.surface2,
            onPrimaryContainer = palette.fg,
            secondary = palette.accent,
            onSecondary = palette.accentFg,
            secondaryContainer = palette.surface,
            onSecondaryContainer = palette.fg,
            tertiary = palette.accent,
            onTertiary = palette.accentFg,
            tertiaryContainer = palette.surface2,
            onTertiaryContainer = palette.fg,
            background = palette.bg,
            onBackground = palette.fg,
            surface = palette.surface,
            onSurface = palette.fg,
            surfaceVariant = palette.surface2,
            onSurfaceVariant = palette.dim,
            surfaceTint = palette.accent,
            outline = palette.line,
            outlineVariant = palette.line2,
            error = palette.error,
            onError = onError,
            onErrorContainer = palette.fg,
            inverseSurface = palette.fg,
            inverseOnSurface = palette.bg,
            inversePrimary = palette.accent,
            scrim = Color(0x99000000),
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

/** Flat Material 3 surface container: solid fill and a single hairline edge. */
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
