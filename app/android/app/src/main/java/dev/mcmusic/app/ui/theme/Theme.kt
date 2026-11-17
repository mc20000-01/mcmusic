package dev.mcmusic.app.ui.theme

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.remember
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.em
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.R

/* ── palette tokens (static/css/variables.css) ─────────────────────────── */

@Immutable
data class McColors(
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
    val accentFg: Color,
    val accentSoft: Color,
    val ok: Color,
    val warn: Color,
    val err: Color,
    val scrim: Color,
    val ink: Color,
    val glass: Color = Color.White.copy(alpha = 0.14f),
    val glassStrong: Color = Color.White.copy(alpha = 0.22f),
    val glassBorder: Color = Color.White.copy(alpha = 0.18f),
    val glassHighlight: Color = Color.White.copy(alpha = 0.25f),
) {
    val isDark: Boolean get() = bg.luminance() < 0.5f
}

private fun c(hex: String) = Color(android.graphics.Color.parseColor(hex))

private val dusk = McColors(
    bg = c("#0e0a13"), bg2 = c("#140e1b"), surface = c("#1b1325"), surface2 = c("#241931"),
    fg = c("#f2edf7"), dim = c("#b9abc9"), dim2 = c("#9a8cab"),
    line = c("#2c1f3d"), line2 = c("#3e2b54"),
    accent = c("#b080ea"), accentFg = c("#191023"), accentSoft = c("#b080ea").copy(alpha = 0.15f),
    ok = c("#77cfa3"), warn = c("#ecc665"), err = c("#e8737a"),
    scrim = Color(0xC407050A), ink = c("#07050a"),
)

private val paper = McColors(
    bg = c("#f2ebe4"), bg2 = c("#e8dfd4"), surface = c("#faf8f4"), surface2 = c("#ebe4db"),
    fg = c("#281f15"), dim = c("#5d4f41"), dim2 = c("#716356"),
    line = c("#d3c8bb"), line2 = c("#baa997"),
    accent = c("#9a4b1d"), accentFg = c("#fbf7f4"), accentSoft = c("#9a4b1d").copy(alpha = 0.12f),
    ok = c("#28714d"), warn = c("#7f5b0c"), err = c("#a12129"),
    scrim = Color(0x57211A12), ink = c("#211a12"),
    glass = Color.White.copy(alpha = 0.38f),
    glassStrong = Color.White.copy(alpha = 0.60f),
    glassBorder = c("#281f15").copy(alpha = 0.16f),
    glassHighlight = Color.White.copy(alpha = 0.70f),
)

private val ink = McColors(
    bg = c("#0d0d0f"), bg2 = c("#131316"), surface = c("#1a1a1e"), surface2 = c("#232327"),
    fg = c("#ededf7"), dim = c("#ababc9"), dim2 = c("#8c8cab"),
    line = c("#2b2b31"), line2 = c("#3c3c44"),
    accent = c("#dadadd"), accentFg = c("#101023"), accentSoft = c("#dadadd").copy(alpha = 0.15f),
    ok = c("#77cfa3"), warn = c("#ecc665"), err = c("#e8737a"),
    scrim = Color(0xC4070708), ink = c("#070708"),
)

private val tide = McColors(
    bg = c("#0a1012"), bg2 = c("#0f181a"), surface = c("#142124"), surface2 = c("#1b2b2f"),
    fg = c("#edf5f7"), dim = c("#abc3c9"), dim2 = c("#8ca5ab"),
    line = c("#21353b"), line2 = c("#2e4a52"),
    accent = c("#89cee1"), accentFg = c("#101f23"), accentSoft = c("#89cee1").copy(alpha = 0.15f),
    ok = c("#77cfa3"), warn = c("#ecc665"), err = c("#e8737a"),
    scrim = Color(0xC406090A), ink = c("#06090a"),
)

private val copper = McColors(
    bg = c("#130c09"), bg2 = c("#1c110d"), surface = c("#261812"), surface2 = c("#322018"),
    fg = c("#f7f0ed"), dim = c("#c9b4ab"), dim2 = c("#ab958c"),
    line = c("#3e271d"), line2 = c("#573729"),
    accent = c("#eaa07b"), accentFg = c("#231610"), accentSoft = c("#eaa07b").copy(alpha = 0.15f),
    ok = c("#77cfa3"), warn = c("#ecc665"), err = c("#e8737a"),
    scrim = Color(0xC40A0705), ink = c("#0a0705"),
)

private val forest = McColors(
    bg = c("#0a120e"), bg2 = c("#0e1b14"), surface = c("#14241b"), surface2 = c("#1a3024"),
    fg = c("#edf7f2"), dim = c("#abc9b9"), dim2 = c("#8cab9a"),
    line = c("#203c2d"), line2 = c("#2d533e"),
    accent = c("#79d8a5"), accentFg = c("#102319"), accentSoft = c("#79d8a5").copy(alpha = 0.15f),
    ok = c("#77cfa3"), warn = c("#ecc665"), err = c("#e8737a"),
    scrim = Color(0xC4050A07), ink = c("#050a07"),
)

private val rose = McColors(
    bg = c("#120a0e"), bg2 = c("#1b0e14"), surface = c("#24141c"), surface2 = c("#301a25"),
    fg = c("#f7edf2"), dim = c("#c9abba"), dim2 = c("#ab8c9c"),
    line = c("#3c202e"), line2 = c("#532d40"),
    accent = c("#ea90b8"), accentFg = c("#231019"), accentSoft = c("#ea90b8").copy(alpha = 0.15f),
    ok = c("#77cfa3"), warn = c("#ecc665"), err = c("#e8737a"),
    scrim = Color(0xC40A0508), ink = c("#0a0508"),
)

val McThemes = listOf("dusk", "paper", "ink", "tide", "copper", "forest", "rose", "auto")

fun themeLabel(key: String): String = when (key) {
    "dusk" -> "Night"
    "paper" -> "Paper"
    "ink" -> "Ink"
    "tide" -> "Tide"
    "copper" -> "Copper"
    "forest" -> "Forest"
    "rose" -> "Rose"
    "auto" -> "Auto"
    else -> key.replaceFirstChar { it.uppercase() }
}

val McAccents = listOf(
    "#b080ea", "#9a7cf0", "#d29cf0", "#79d8a5",
    "#77cfa3", "#ecc665", "#ea90b8", "#e8737a", "#89cee1", "#f2edf7",
)

@Immutable
data class ThemePreview(
    val bg: Color,
    val surface: Color,
    val accent: Color,
    val split: Boolean = false,
)

fun previewFor(key: String): ThemePreview = when (key) {
    "dusk" -> ThemePreview(dusk.bg, dusk.surface, dusk.accent)
    "paper" -> ThemePreview(paper.bg, paper.surface, paper.accent)
    "ink" -> ThemePreview(ink.bg, ink.surface, ink.accent)
    "tide" -> ThemePreview(tide.bg, tide.surface, tide.accent)
    "copper" -> ThemePreview(copper.bg, copper.surface, copper.accent)
    "forest" -> ThemePreview(forest.bg, forest.surface, forest.accent)
    "rose" -> ThemePreview(rose.bg, rose.surface, rose.accent)
    else -> ThemePreview(ink.bg2, paper.bg, dusk.accent, split = true)
}

private val palettes = mapOf(
    "dusk" to dusk,
    "paper" to paper,
    "ink" to ink,
    "tide" to tide,
    "copper" to copper,
    "forest" to forest,
    "rose" to rose,
    "dark" to dusk,
    "light" to paper,
    "amoled" to ink,
    "midnight" to tide,
    "mocha" to copper,
)

/** Auto follows the system, like the web's prefers-color-scheme fallback. */
fun paletteFor(theme: String, autoDark: Boolean = true): McColors = when (theme) {
    "auto" -> if (autoDark) dusk else paper
    else -> palettes[theme] ?: dusk
}

/** Mirror of applySet(): accent override plus readable foreground. */
fun withAccent(base: McColors, accentHex: String?): McColors {
    if (accentHex.isNullOrBlank()) return base
    val parsed = runCatching { c(accentHex) }.getOrNull() ?: return base
    val lum = 0.299 * parsed.red + 0.587 * parsed.green + 0.114 * parsed.blue
    return base.copy(
        accent = parsed,
        accentFg = if (lum > 0.6f) Color.Black else Color.White,
        accentSoft = parsed.copy(alpha = if (base.isDark) 0.14f else 0.12f),
    )
}

val LocalMc = staticCompositionLocalOf { dusk }
val LocalGfxLevel = staticCompositionLocalOf { 3 }
val LocalMaterial = staticCompositionLocalOf { "glass" }

/**
 * Surface material layer for floating chrome.
 *
 * Glass is built from a near-opaque palette surface plus a soft specular
 * sheen, never from a RenderEffect on the container. A container-level blur
 * also blurs the panel's own children (text, icons), which is what made
 * "glass" unreadable on Android 12+. Keeping the base opaque enough means the
 * text always sits on the palette surface, so contrast is stable no matter
 * what artwork or content is behind the panel.
 */
@Composable
fun Modifier.glass(
    shape: Shape = RoundedCornerShape(D.r3),
    strong: Boolean = false,
): Modifier {
    val mc = LocalMc.current
    val gfx = LocalGfxLevel.current
    val material = LocalMaterial.current
    val fill = when {
        material == "solid" && strong -> mc.surface2
        material == "solid" -> mc.surface
        material == "plane" && strong -> mc.surface
        material == "plane" -> mc.bg2
        material == "metal" && strong -> mc.surface2.copy(alpha = 0.97f)
        material == "metal" -> mc.surface.copy(alpha = 0.94f)
        strong -> mc.surface2.copy(alpha = 0.95f)
        else -> mc.surface.copy(alpha = 0.90f)
    }
    val borderBrush = when {
        material == "metal" -> Brush.linearGradient(
            listOf(
                mc.glassHighlight.copy(alpha = 0.95f),
                mc.glassBorder,
                mc.fg.copy(alpha = 0.14f),
                mc.glassBorder,
            )
        )
        material == "plane" -> Brush.linearGradient(listOf(mc.line.copy(alpha = 0.7f), mc.line.copy(alpha = 0.7f)))
        material == "solid" -> Brush.linearGradient(listOf(mc.line2, mc.line2))
        material == "glass" -> Brush.linearGradient(
            listOf(
                mc.glassHighlight.copy(alpha = 0.65f),
                mc.glassBorder.copy(alpha = 0.75f),
                mc.accent.copy(alpha = 0.35f),
            )
        )
        else -> Brush.linearGradient(listOf(mc.glassHighlight, mc.glassBorder))
    }
    val highlight = when {
        material == "metal" -> Brush.verticalGradient(listOf(mc.glassHighlight.copy(alpha = 0.18f), Color.Transparent))
        material == "solid" -> Brush.verticalGradient(listOf(mc.fg.copy(alpha = 0.04f), Color.Transparent))
        material == "plane" -> Brush.verticalGradient(listOf(Color.Transparent, Color.Transparent))
        material == "glass" -> Brush.verticalGradient(
            listOf(
                mc.fg.copy(alpha = 0.06f),
                Color.Transparent,
                mc.accent.copy(alpha = 0.05f),
            )
        )
        else -> Brush.verticalGradient(listOf(mc.fg.copy(alpha = 0.05f), Color.Transparent))
    }
    val elevation = when {
        material == "plane" -> 0.dp
        material == "solid" -> if (gfx == 0) 0.dp else 3.dp
        material == "metal" -> if (gfx == 0) 0.dp else 10.dp
        gfx == 0 -> 0.dp
        gfx == 1 -> 2.dp
        else -> 8.dp
    }
    return this
        .shadow(elevation, shape)
        .clip(shape)
        .background(fill, shape)
        .background(highlight, shape)
        .border(1.dp, borderBrush, shape)
}

@Composable
fun McTheme(
    theme: String,
    accent: String?,
    gfxLevel: Int = 3,
    material: String = "glass",
    content: @Composable () -> Unit,
) {
    val systemDark = isSystemInDarkTheme()
    val colors = remember(theme, accent, systemDark) {
        withAccent(paletteFor(theme, systemDark), accent)
    }
    CompositionLocalProvider(
        LocalMc provides colors,
        LocalGfxLevel provides gfxLevel,
        LocalMaterial provides material,
    ) { content() }
}

/* ── geometry (variables.css) ──────────────────────────────────────────── */

object D {
    val r1 = 8.dp
    val r2 = 12.dp
    val r3 = 22.dp
    val r4 = 24.dp
    val rail = 240.dp
    val deck = 54.dp
    val top = 56.dp
    val tab = 58.dp
    val maxw = 1180.dp
    val gutter = 16.dp
    /** deck + tab + 24dp, so lists never sit under floating chrome. */
    val pageBottom = 136.dp
}

/* ── typography ─────────────────────────────────────────────────────────── */

private val McMono = FontFamily(
    Font(R.font.mc_mono_regular, FontWeight.Normal),
    Font(R.font.mc_mono_medium, FontWeight.Medium),
    Font(R.font.mc_mono_semibold, FontWeight.SemiBold),
    Font(R.font.mc_mono_bold, FontWeight.Bold),
)

object McType {
    val display = FontFamily.SansSerif
    val sans = FontFamily.SansSerif
    val mono = McMono

    val h1 = TextStyle(
        fontFamily = display, fontSize = 38.sp, fontWeight = FontWeight.SemiBold,
        letterSpacing = (-0.035).em, lineHeight = 40.sp,
    )
    val h1Small = TextStyle(
        fontFamily = display, fontSize = 30.sp, fontWeight = FontWeight.SemiBold,
        letterSpacing = (-0.03).em, lineHeight = 33.sp,
    )
    val h2 = TextStyle(
        fontFamily = display, fontSize = 25.sp, fontWeight = FontWeight.SemiBold,
        letterSpacing = (-0.025).em, lineHeight = 30.sp,
    )
    val h3 = TextStyle(
        fontFamily = display, fontSize = 18.sp, fontWeight = FontWeight.SemiBold,
        letterSpacing = (-0.015).em, lineHeight = 23.sp,
    )
    val body = TextStyle(fontFamily = sans, fontSize = 15.sp, lineHeight = 22.sp)
    val bodySm = TextStyle(fontFamily = sans, fontSize = 13.sp, lineHeight = 18.sp)
    val bodyXs = TextStyle(fontFamily = sans, fontSize = 12.sp, lineHeight = 16.sp)
    val mono10 = TextStyle(
        fontFamily = mono, fontSize = 11.sp, letterSpacing = 0.01.em, lineHeight = 14.sp,
    )
    val mono9 = TextStyle(fontFamily = mono, fontSize = 10.sp, letterSpacing = 0.04.em, lineHeight = 13.sp)
    val kicker = TextStyle(
        fontFamily = mono, fontSize = 11.sp, letterSpacing = 0.08.em, lineHeight = 14.sp,
    )
    val button = TextStyle(
        fontFamily = mono, fontSize = 12.sp, fontWeight = FontWeight.SemiBold,
        letterSpacing = 0.01.em, lineHeight = 16.sp,
    )
    val buttonSm = TextStyle(
        fontFamily = mono, fontSize = 11.sp, fontWeight = FontWeight.Medium,
        letterSpacing = 0.01.em, lineHeight = 14.sp,
    )
    val label = TextStyle(
        fontFamily = sans, fontSize = 13.sp, fontWeight = FontWeight.Medium,
        lineHeight = 17.sp,
    )
    val labelSm = TextStyle(
        fontFamily = sans, fontSize = 12.sp, fontWeight = FontWeight.Medium,
        lineHeight = 15.sp,
    )
}
