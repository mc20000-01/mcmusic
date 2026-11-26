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
import dev.mcmusic.app.data.Prefs

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
    // Generated Material 3 tonal roles (HCT from this family's accent seed).
    val primary: Color, val onPrimary: Color,
    val primaryContainer: Color, val onPrimaryContainer: Color,
    val secondary: Color, val onSecondary: Color,
    val secondaryContainer: Color, val onSecondaryContainer: Color,
    val tertiary: Color, val onTertiary: Color,
    val tertiaryContainer: Color, val onTertiaryContainer: Color,
    val error: Color, val onError: Color,
    val errorContainer: Color, val onErrorContainer: Color,
    val background: Color, val onBackground: Color, val onSurface: Color,
    val surfaceVariant: Color, val onSurfaceVariant: Color,
    val surfaceContainerLowest: Color, val surfaceContainerLow: Color,
    val surfaceContainer: Color, val surfaceContainerHigh: Color,
    val surfaceContainerHighest: Color,
    val outline: Color, val outlineVariant: Color,
    val inverseSurface: Color, val inverseOnSurface: Color,
    val inversePrimary: Color, val scrim: Color, val shadow: Color,
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

// BEGIN GENERATED PALETTES
object Palettes {
    private fun color(hex: String) = Color(android.graphics.Color.parseColor("#$hex"))

    private fun variant(
        family: String, label: String, dark: Boolean,
        bg: String, bg2: String, surface: String, surface2: String,
        fg: String, dim: String, dim2: String, line: String, line2: String,
        accent: String, accentText: String, accentFg: String,
    primary: String,
    onPrimary: String,
    primaryContainer: String,
    onPrimaryContainer: String,
    secondary: String,
    onSecondary: String,
    secondaryContainer: String,
    onSecondaryContainer: String,
    tertiary: String,
    onTertiary: String,
    tertiaryContainer: String,
    onTertiaryContainer: String,
    error: String,
    onError: String,
    errorContainer: String,
    onErrorContainer: String,
    background: String,
    onBackground: String,
    onSurface: String,
    surfaceVariant: String,
    onSurfaceVariant: String,
    surfaceContainerLowest: String,
    surfaceContainerLow: String,
    surfaceContainer: String,
    surfaceContainerHigh: String,
    surfaceContainerHighest: String,
    outline: String,
    outlineVariant: String,
    inverseSurface: String,
    inverseOnSurface: String,
    inversePrimary: String,
    scrim: String,
    shadow: String,
    ) = McPalette(
        id = "$family-" + (if (dark) "dark" else "light"),
        label = label, dark = dark,
        bg = color(bg), bg2 = color(bg2), surface = color(surface), surface2 = color(surface2),
        fg = color(fg), dim = color(dim), dim2 = color(dim2), line = color(line), line2 = color(line2),
        accent = color(accent), accentText = color(accentText), accentFg = color(accentFg),
        primary = color(primary),
        onPrimary = color(onPrimary),
        primaryContainer = color(primaryContainer),
        onPrimaryContainer = color(onPrimaryContainer),
        secondary = color(secondary),
        onSecondary = color(onSecondary),
        secondaryContainer = color(secondaryContainer),
        onSecondaryContainer = color(onSecondaryContainer),
        tertiary = color(tertiary),
        onTertiary = color(onTertiary),
        tertiaryContainer = color(tertiaryContainer),
        onTertiaryContainer = color(onTertiaryContainer),
        error = color(error),
        onError = color(onError),
        errorContainer = color(errorContainer),
        onErrorContainer = color(onErrorContainer),
        background = color(background),
        onBackground = color(onBackground),
        onSurface = color(onSurface),
        surfaceVariant = color(surfaceVariant),
        onSurfaceVariant = color(onSurfaceVariant),
        surfaceContainerLowest = color(surfaceContainerLowest),
        surfaceContainerLow = color(surfaceContainerLow),
        surfaceContainer = color(surfaceContainer),
        surfaceContainerHigh = color(surfaceContainerHigh),
        surfaceContainerHighest = color(surfaceContainerHighest),
        outline = color(outline),
        outlineVariant = color(outlineVariant),
        inverseSurface = color(inverseSurface),
        inverseOnSurface = color(inverseOnSurface),
        inversePrimary = color(inversePrimary),
        scrim = color(scrim),
        shadow = color(shadow),
    )

    val violet = PaletteFamily(
        id = "violet",
        label = "Violet",
        light = variant("violet", "Violet", false, bg = "F5F2FF", bg2 = "EDE7FF", surface = "FFFFFF", surface2 = "F7F4FF", fg = "08060D", dim = "473872", dim2 = "6A54AA", line = "DACDFF", line2 = "CAB8FF", accent = "9F7EFF", accentText = "5B3F9E", accentFg = "08060D", primary = "64558F", onPrimary = "FFFFFF", primaryContainer = "E8DDFF", onPrimaryContainer = "4C3E76", secondary = "615B71", onSecondary = "FFFFFF", secondaryContainer = "E8DEF8", onSecondaryContainer = "494458", tertiary = "7D5261", onTertiary = "FFFFFF", tertiaryContainer = "FFD9E3", onTertiaryContainer = "633B49", error = "BA1A1A", onError = "FFFFFF", errorContainer = "FFDAD6", onErrorContainer = "93000A", background = "FFFBFF", onBackground = "1D1927", onSurface = "1D1927", surfaceVariant = "E7DFF3", onSurfaceVariant = "494454", surfaceContainerLowest = "FFFBFF", surfaceContainerLow = "F8F1FF", surfaceContainer = "F3EAFE", surfaceContainerHigh = "EDE5F9", surfaceContainerHighest = "E7DFF3", outline = "79757F", outlineVariant = "878192", inverseSurface = "322E3D", inverseOnSurface = "F5EEFF", inversePrimary = "CEBDFE", scrim = "000000", shadow = "000000"),
        dark = variant("violet", "Violet", true, bg = "171721", bg2 = "222130", surface = "2A293C", surface2 = "444361", fg = "FFFFFF", dim = "AAAAB7", dim2 = "8B8A9D", line = "35344B", line2 = "605F78", accent = "9F7EFF", accentText = "C6B2FF", accentFg = "08060D", primary = "CEBDFE", onPrimary = "35275D", primaryContainer = "4C3E76", onPrimaryContainer = "E8DDFF", secondary = "CBC3DC", onSecondary = "332E41", secondaryContainer = "494458", onSecondaryContainer = "E8DEF8", tertiary = "EFB8C9", onTertiary = "492533", tertiaryContainer = "633B49", onTertiaryContainer = "FFD9E3", error = "FFB4AB", onError = "690005", errorContainer = "93000A", onErrorContainer = "FFDAD6", background = "15111F", onBackground = "F5EEFF", onSurface = "F5EEFF", surfaceVariant = "3B3746", onSurfaceVariant = "CBC3D6", surfaceContainerLowest = "0F0C19", surfaceContainerLow = "1D1927", surfaceContainer = "211E2B", surfaceContainerHigh = "2C2836", surfaceContainerHighest = "373341", outline = "938F99", outlineVariant = "878192", inverseSurface = "F5EEFF", inverseOnSurface = "322E3D", inversePrimary = "64558F", scrim = "000000", shadow = "000000"),
    )

    val indigo = PaletteFamily(
        id = "indigo",
        label = "Indigo",
        light = variant("indigo", "Indigo", false, bg = "F2F4FF", bg2 = "E8EBFF", surface = "FFFFFF", surface2 = "F5F6FF", fg = "08060D", dim = "3B4172", dim2 = "5761AA", line = "CFD5FF", line2 = "BAC3FF", accent = "8293FF", accentText = "4A56A8", accentFg = "08060D", primary = "525A92", onPrimary = "FFFFFF", primaryContainer = "DEE0FF", onPrimaryContainer = "3A4379", secondary = "5B5D72", onSecondary = "FFFFFF", secondaryContainer = "E0E1F9", onSecondaryContainer = "434559", tertiary = "77536D", onTertiary = "FFFFFF", tertiaryContainer = "FFD7F1", onTertiaryContainer = "5D3C54", error = "BA1A1A", onError = "FFFFFF", errorContainer = "FFDAD6", onErrorContainer = "93000A", background = "FFFBFF", onBackground = "191B26", onSurface = "191B26", surfaceVariant = "E2E1F2", onSurfaceVariant = "454653", surfaceContainerLowest = "FFFBFF", surfaceContainerLow = "F4F2FF", surfaceContainer = "EDECFD", surfaceContainerHigh = "E7E7F7", surfaceContainerHighest = "E2E1F2", outline = "767680", outlineVariant = "828391", inverseSurface = "2E303C", inverseOnSurface = "F0EFFF", inversePrimary = "BBC3FF", scrim = "000000", shadow = "000000"),
        dark = variant("indigo", "Indigo", true, bg = "12171F", bg2 = "1B212D", surface = "212838", surface2 = "36425B", fg = "FFFFFF", dim = "A4A9B5", dim2 = "828999", line = "2A3346", line2 = "545E73", accent = "8293FF", accentText = "B4BEFF", accentFg = "08060D", primary = "BBC3FF", onPrimary = "232C61", primaryContainer = "3A4379", onPrimaryContainer = "DEE0FF", secondary = "C4C5DD", onSecondary = "2D2F42", secondaryContainer = "434559", onSecondaryContainer = "E0E1F9", tertiary = "E6BAD7", onTertiary = "45263D", tertiaryContainer = "5D3C54", onTertiaryContainer = "FFD7F1", error = "FFB4AB", onError = "690005", errorContainer = "93000A", onErrorContainer = "FFDAD6", background = "11131E", onBackground = "F0EFFF", onSurface = "F0EFFF", surfaceVariant = "373845", onSurfaceVariant = "C5C5D5", surfaceContainerLowest = "0C0D18", surfaceContainerLow = "191B26", surfaceContainer = "1D1F2B", surfaceContainerHigh = "282935", surfaceContainerHighest = "333440", outline = "90909A", outlineVariant = "828391", inverseSurface = "F0EFFF", inverseOnSurface = "2E303C", inversePrimary = "525A92", scrim = "000000", shadow = "000000"),
    )

    val sky = PaletteFamily(
        id = "sky",
        label = "Sky",
        light = variant("sky", "Sky", false, bg = "F1F8FE", bg2 = "E7F3FE", surface = "FFFFFF", surface2 = "F4F9FE", fg = "08060D", dim = "385272", dim2 = "527CA9", line = "CCE5FE", line2 = "B6DAFE", accent = "7BBDFE", accentText = "235F93", accentFg = "08060D", primary = "32628D", onPrimary = "FFFFFF", primaryContainer = "CFE5FF", onPrimaryContainer = "134A74", secondary = "526070", onSecondary = "FFFFFF", secondaryContainer = "D6E4F7", onSecondaryContainer = "3A4857", tertiary = "695779", onTertiary = "FFFFFF", tertiaryContainer = "F0DBFF", onTertiaryContainer = "514060", error = "BA1A1A", onError = "FFFFFF", errorContainer = "FFDAD6", onErrorContainer = "93000A", background = "FCFCFF", onBackground = "161C23", onSurface = "161C23", surfaceVariant = "DDE3ED", onSurfaceVariant = "41474F", surfaceContainerLowest = "FCFCFF", surfaceContainerLow = "EEF4FE", surfaceContainer = "E9EEF8", surfaceContainerHigh = "E3E8F2", surfaceContainerHighest = "DDE3ED", outline = "73777F", outlineVariant = "7E848D", inverseSurface = "2B3138", inverseOnSurface = "ECF1FB", inversePrimary = "9DCBFC", scrim = "000000", shadow = "000000"),
        dark = variant("sky", "Sky", true, bg = "182127", bg2 = "222F39", surface = "2A3A46", surface2 = "455F72", fg = "FFFFFF", dim = "ABB7BF", dim2 = "8B9BA7", line = "354A58", line2 = "607787", accent = "7BBDFE", accentText = "A9D5FF", accentFg = "08060D", primary = "9DCBFC", onPrimary = "003355", primaryContainer = "134A74", onPrimaryContainer = "CFE5FF", secondary = "BAC8DA", onSecondary = "243240", secondaryContainer = "3A4857", onSecondaryContainer = "D6E4F7", tertiary = "D4BEE6", onTertiary = "392A49", tertiaryContainer = "514060", onTertiaryContainer = "F0DBFF", error = "FFB4AB", onError = "690005", errorContainer = "93000A", onErrorContainer = "FFDAD6", background = "0E141B", onBackground = "ECF1FB", onSurface = "ECF1FB", surfaceVariant = "343A41", onSurfaceVariant = "C1C7D0", surfaceContainerLowest = "090F15", surfaceContainerLow = "161C23", surfaceContainer = "1A2027", surfaceContainerHigh = "242A32", surfaceContainerHighest = "2F353D", outline = "8C9199", outlineVariant = "7E848D", inverseSurface = "ECF1FB", inverseOnSurface = "2B3138", inversePrimary = "32628D", scrim = "000000", shadow = "000000"),
    )

    val aqua = PaletteFamily(
        id = "aqua",
        label = "Aqua",
        light = variant("aqua", "Aqua", false, bg = "F1FBFC", bg2 = "E7F9FA", surface = "FFFFFF", surface2 = "F4FCFD", fg = "08060D", dim = "386168", dim2 = "53939A", line = "CDF3F5", line2 = "B6EDF1", accent = "7CE0E6", accentText = "126F77", accentFg = "08060D", primary = "00696E", onPrimary = "FFFFFF", primaryContainer = "9CF0F6", onPrimaryContainer = "004F53", secondary = "4A6364", onSecondary = "FFFFFF", secondaryContainer = "CCE8E9", onSecondaryContainer = "324B4C", tertiary = "4E5F7D", onTertiary = "FFFFFF", tertiaryContainer = "D6E3FF", onTertiaryContainer = "364764", error = "BA1A1A", onError = "FFFFFF", errorContainer = "FFDAD6", onErrorContainer = "93000A", background = "F4FEFE", onBackground = "141D1E", onSurface = "141D1E", surfaceVariant = "DAE4E5", onSurfaceVariant = "3F4949", surfaceContainerLowest = "F4FEFE", surfaceContainerLow = "EBF6F6", surfaceContainer = "E6F0F0", surfaceContainerHigh = "E0EAEA", surfaceContainerHighest = "DAE4E5", outline = "6F7979", outlineVariant = "7C8686", inverseSurface = "293233", inverseOnSurface = "E9F3F3", inversePrimary = "80D4D9", scrim = "000000", shadow = "000000"),
        dark = variant("aqua", "Aqua", true, bg = "15241C", bg2 = "1F3328", surface = "263F32", surface2 = "3E6751", fg = "FFFFFF", dim = "A8BAB0", dim2 = "87A093", line = "30503F", line2 = "5A7D6B", accent = "7CE0E6", accentText = "A6EFF3", accentFg = "08060D", primary = "80D4D9", onPrimary = "003739", primaryContainer = "004F53", onPrimaryContainer = "9CF0F6", secondary = "B1CCCD", onSecondary = "1B3436", secondaryContainer = "324B4C", onSecondaryContainer = "CCE8E9", tertiary = "B6C7E9", onTertiary = "1F314C", tertiaryContainer = "364764", onTertiaryContainer = "D6E3FF", error = "FFB4AB", onError = "690005", errorContainer = "93000A", onErrorContainer = "FFDAD6", background = "0C1516", onBackground = "E9F3F3", onSurface = "E9F3F3", surfaceVariant = "313B3B", onSurfaceVariant = "BEC8C9", surfaceContainerLowest = "071010", surfaceContainerLow = "141D1E", surfaceContainer = "182122", surfaceContainerHigh = "222C2C", surfaceContainerHighest = "2D3637", outline = "899393", outlineVariant = "7C8686", inverseSurface = "E9F3F3", inverseOnSurface = "293233", inversePrimary = "00696E", scrim = "000000", shadow = "000000"),
    )

    val mint = PaletteFamily(
        id = "mint",
        label = "Mint",
        light = variant("mint", "Mint", false, bg = "F1FFF5", bg2 = "E7FFEE", surface = "FFFFFF", surface2 = "F4FFF7", fg = "08060D", dim = "386E4C", dim2 = "52A76F", line = "CCFFDC", line2 = "B6FFCC", accent = "7BFFA4", accentText = "216A43", accentFg = "08060D", primary = "316A42", onPrimary = "FFFFFF", primaryContainer = "B3F1BF", onPrimaryContainer = "16512C", secondary = "506352", onSecondary = "FFFFFF", secondaryContainer = "D2E8D3", onSecondaryContainer = "394B3C", tertiary = "3A656E", onTertiary = "FFFFFF", tertiaryContainer = "BDEAF5", onTertiaryContainer = "204D56", error = "BA1A1A", onError = "FFFFFF", errorContainer = "FFDAD6", onErrorContainer = "93000A", background = "F5FFF3", onBackground = "121E14", onSurface = "121E14", surfaceVariant = "D7E7D6", onSurfaceVariant = "3C4A3E", surfaceContainerLowest = "F5FFF3", surfaceContainerLow = "E8F8E7", surfaceContainer = "E3F2E1", surfaceContainerHigh = "DDECDC", surfaceContainerHighest = "D7E7D6", outline = "717971", outlineVariant = "798879", inverseSurface = "263428", inverseOnSurface = "E5F5E4", inversePrimary = "98D5A4", scrim = "000000", shadow = "000000"),
        dark = variant("mint", "Mint", true, bg = "15241A", bg2 = "1F3425", surface = "26412E", surface2 = "3E694B", fg = "FFFFFF", dim = "A8BBAE", dim2 = "87A28F", line = "30513A", line2 = "5A7F66", accent = "7BFFA4", accentText = "A9FFC2", accentFg = "08060D", primary = "98D5A4", onPrimary = "00391A", primaryContainer = "16512C", onPrimaryContainer = "B3F1BF", secondary = "B7CCB7", onSecondary = "223526", secondaryContainer = "394B3C", onSecondaryContainer = "D2E8D3", tertiary = "A2CED9", onTertiary = "01363F", tertiaryContainer = "204D56", onTertiaryContainer = "BDEAF5", error = "FFB4AB", onError = "690005", errorContainer = "93000A", onErrorContainer = "FFDAD6", background = "0A160D", onBackground = "E5F5E4", onSurface = "E5F5E4", surfaceVariant = "2F3C31", onSurfaceVariant = "BBCBBB", surfaceContainerLowest = "051108", surfaceContainerLow = "121E14", surfaceContainer = "162218", surfaceContainerHigh = "202D22", surfaceContainerHighest = "2B382D", outline = "8B938A", outlineVariant = "798879", inverseSurface = "E5F5E4", inverseOnSurface = "263428", inversePrimary = "316A42", scrim = "000000", shadow = "000000"),
    )

    /** Exactly five chooser entries; each adapts to system light/dark. */
    val families = listOf(violet, indigo, sky, aqua, mint)

    private val byConcreteId: Map<String, McPalette> = families.flatMap { listOf(it.light, it.dark) }
        .associateBy { it.id }

    private val byFamilyId: Map<String, PaletteFamily> = families.associateBy { it.id }

    const val AUTO = "auto"

    /** Legacy ids keep the light/dark half they used to imply. */
    private val aliases = mapOf(
        "auto" to AUTO,
        "system" to AUTO,
        "flufi" to "violet-dark",
        "dark" to "violet-dark",
        "dusk" to "violet-dark",
        "paper" to "violet-light",
        "light" to "violet-light",
        "ink" to "indigo-dark",
        "amoled" to "indigo-dark",
        "midnight" to "sky-dark",
        "tide" to "aqua-dark",
        "forest" to "mint-dark",
        "rose" to "violet-dark",
        "copper" to "violet-dark",
        "mocha" to "violet-dark",
    )

    private fun canonicalID(id: String?): String {
        val key = (id ?: AUTO).lowercase().trim()
        return aliases[key] ?: key
    }

    /** `auto`, `system`, empty and bare family ids follow system appearance. */
    fun resolve(id: String?, systemDark: Boolean): McPalette {
        val key = canonicalID(id)
        return byConcreteId[key]
            ?: byFamilyId[key]?.resolve(systemDark)
            ?: violet.resolve(systemDark)
    }
}
// END GENERATED PALETTES

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

    // 4.2.0 shape scale: 4/8/12/16/28/36 + pill. Large, friendly corners
    // are structural, not decoration; covers stay inside the 20-28 range.
    val cardRadius = 28.dp
    val tileRadius = 28.dp
    val heroRadius = 36.dp
    val coverRadius = 28.dp
    val chipRadius = 50
    val screenPadding = 16.dp
    val gap = 12.dp
    val touchTarget = 48.dp

    val displaySize = 36.sp
    val headlineSize = 28.sp
    val titleSize = 22.sp
    val titleWeight = FontWeight.Bold
    val sectionSize = 12.sp
    val sectionWeight = FontWeight.SemiBold

    val fg = palette.fg
    val dim = palette.dim
    val accent = palette.accent
    val accentText = palette.accentText
    val onAccent = palette.accentFg

    /** Translucent accent layers for chips, covers and flat tonal containers. */
    val accentSoft = palette.accent.copy(alpha = if (palette.dark) 0.18f else 0.12f)
    val accentWash = palette.accent.copy(alpha = if (palette.dark) 0.09f else 0.06f)
    val hairline = palette.line

    /** Material 3 surface container: a calm fill with a tonal edge. */
    val cardFill = palette.surfaceContainerLow
}

val LocalDesign = compositionLocalOf { McDesign(DesignLanguage.Flufi, Palettes.violet.dark) }

/** Flat tonal stage: one calm palette colour behind every screen. */
@Composable
private fun Stage(modifier: Modifier, design: McDesign) {
    Box(modifier.background(design.palette.bg))
}

private val McTypography = Typography(
    displayLarge = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Bold, fontSize = 36.sp, lineHeight = 44.sp),
    displayMedium = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Bold, fontSize = 28.sp, lineHeight = 36.sp),
    displaySmall = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.SemiBold, fontSize = 24.sp, lineHeight = 32.sp),
    headlineLarge = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Bold, fontSize = 28.sp, lineHeight = 36.sp),
    headlineMedium = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.SemiBold, fontSize = 24.sp, lineHeight = 32.sp),
    headlineSmall = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.SemiBold, fontSize = 22.sp, lineHeight = 28.sp),
    titleLarge = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Bold, fontSize = 22.sp, lineHeight = 28.sp),
    titleMedium = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.SemiBold, fontSize = 16.sp, lineHeight = 24.sp),
    titleSmall = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.SemiBold, fontSize = 14.sp, lineHeight = 20.sp),
    bodyLarge = TextStyle(fontFamily = FontFamily.Default, fontSize = 16.sp, lineHeight = 24.sp),
    bodyMedium = TextStyle(fontFamily = FontFamily.Default, fontSize = 14.sp, lineHeight = 20.sp),
    bodySmall = TextStyle(fontFamily = FontFamily.Default, fontSize = 12.sp, lineHeight = 16.sp),
    labelLarge = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.SemiBold, fontSize = 14.sp, lineHeight = 20.sp),
    labelMedium = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.SemiBold, fontSize = 12.sp, lineHeight = 16.sp),
    labelSmall = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Medium, fontSize = 11.sp, lineHeight = 16.sp),
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
    val systemDark = isSystemInDarkTheme()
    val coverSeed = DynamicColour.coverSeed
    val wallpaperSeed = DynamicColour.wallpaperSeed
    val followCover = Prefs.dynamicColour
    val palette = remember(paletteId, systemDark, coverSeed, wallpaperSeed, followCover) {
        DynamicColour.resolve(paletteId, systemDark)
    }
    val design = remember(palette, language) { McDesign(language, palette) }
    val scheme = if (palette.dark) {
        darkColorScheme(
            primary = palette.primary,
            onPrimary = palette.onPrimary,
            primaryContainer = palette.primaryContainer,
            onPrimaryContainer = palette.onPrimaryContainer,
            secondary = palette.secondary,
            onSecondary = palette.onSecondary,
            secondaryContainer = palette.secondaryContainer,
            onSecondaryContainer = palette.onSecondaryContainer,
            tertiary = palette.tertiary,
            onTertiary = palette.onTertiary,
            tertiaryContainer = palette.tertiaryContainer,
            onTertiaryContainer = palette.onTertiaryContainer,
            error = palette.error,
            onError = palette.onError,
            errorContainer = palette.errorContainer,
            onErrorContainer = palette.onErrorContainer,
            background = palette.background,
            onBackground = palette.onBackground,
            surface = palette.surfaceContainerLow,
            onSurface = palette.onSurface,
            surfaceVariant = palette.surfaceVariant,
            onSurfaceVariant = palette.onSurfaceVariant,
            surfaceTint = palette.primary,
            outline = palette.outline,
            outlineVariant = palette.outlineVariant,
            inverseSurface = palette.inverseSurface,
            inverseOnSurface = palette.inverseOnSurface,
            inversePrimary = palette.inversePrimary,
            scrim = palette.scrim,
        )
    } else {
        lightColorScheme(
            primary = palette.primary,
            onPrimary = palette.onPrimary,
            primaryContainer = palette.primaryContainer,
            onPrimaryContainer = palette.onPrimaryContainer,
            secondary = palette.secondary,
            onSecondary = palette.onSecondary,
            secondaryContainer = palette.secondaryContainer,
            onSecondaryContainer = palette.onSecondaryContainer,
            tertiary = palette.tertiary,
            onTertiary = palette.onTertiary,
            tertiaryContainer = palette.tertiaryContainer,
            onTertiaryContainer = palette.onTertiaryContainer,
            error = palette.error,
            onError = palette.onError,
            errorContainer = palette.errorContainer,
            onErrorContainer = palette.onErrorContainer,
            background = palette.background,
            onBackground = palette.onBackground,
            surface = palette.surfaceContainerLow,
            onSurface = palette.onSurface,
            surfaceVariant = palette.surfaceVariant,
            onSurfaceVariant = palette.onSurfaceVariant,
            surfaceTint = palette.primary,
            outline = palette.outline,
            outlineVariant = palette.outlineVariant,
            inverseSurface = palette.inverseSurface,
            inverseOnSurface = palette.inverseOnSurface,
            inversePrimary = palette.inversePrimary,
            scrim = palette.scrim,
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

/** Flat Material 3 surface container: a solid tonal fill and one hairline edge.
 *  One helper keeps every card on the same scale. */
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
