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
    bg = c("#08060d"), bg2 = c("#0d0a15"), surface = c("#151022"), surface2 = c("#1d1630"),
    fg = c("#f2ecff"), dim = c("#a89ec6"), dim2 = c("#726a8c"),
    line = c("#1f1832"), line2 = c("#332a4d"),
    accent = c("#a06bff"), accentFg = c("#0b0616"), accentSoft = c("#a06bff").copy(alpha = 0.16f),
    ok = c("#63c98d"), warn = c("#e3bd52"), err = c("#e4627e"),
    scrim = Color(0xC408060D), ink = c("#050309"),
)

private val paper = McColors(
    bg = c("#f4efe4"), bg2 = c("#ece4d5"), surface = c("#fbf7ee"), surface2 = c("#efe7d8"),
    fg = c("#241d14"), dim = c("#6d6151"), dim2 = c("#8d8069"),
    line = c("#dcd1bd"), line2 = c("#bfb098"),
    accent = c("#b4531f"), accentFg = c("#fff8ef"), accentSoft = c("#b4531f").copy(alpha = 0.12f),
    ok = c("#5c8a4a"), warn = c("#a97f1f"), err = c("#b04a2c"),
    scrim = Color(0x57282014), ink = c("#1b1610"),
    glass = Color.White.copy(alpha = 0.38f),
    glassStrong = Color.White.copy(alpha = 0.60f),
    glassBorder = c("#241d14").copy(alpha = 0.16f),
    glassHighlight = Color.White.copy(alpha = 0.70f),
)

private val ink = McColors(
    bg = c("#050505"), bg2 = c("#0b0b0c"), surface = c("#121214"), surface2 = c("#191a1d"),
    fg = c("#f5f5f5"), dim = c("#8f8f96"), dim2 = c("#64646b"),
    line = c("#212126"), line2 = c("#34343b"),
    accent = c("#d7d7de"), accentFg = c("#0a0a0a"), accentSoft = c("#d7d7de").copy(alpha = 0.10f),
    ok = c("#87a878"), warn = c("#d8b45c"), err = c("#d4735f"),
    scrim = Color(0xCC0A0A0E), ink = c("#07070a"),
)

private val tide = McColors(
    bg = c("#0e161a"), bg2 = c("#131e23"), surface = c("#18262c"), surface2 = c("#1f3038"),
    fg = c("#e4eef1"), dim = c("#8ba3ab"), dim2 = c("#647e87"),
    line = c("#23363d"), line2 = c("#33505a"),
    accent = c("#6fb3c4"), accentFg = c("#06171c"), accentSoft = c("#6fb3c4").copy(alpha = 0.14f),
    ok = c("#7fa86a"), warn = c("#d9b13d"), err = c("#c9603f"),
    scrim = Color(0xC4060F13), ink = c("#070d10"),
)

private val copper = McColors(
    bg = c("#1a0f0d"), bg2 = c("#221412"), surface = c("#2b1a16"), surface2 = c("#37211c"),
    fg = c("#f6e7df"), dim = c("#b2928a"), dim2 = c("#856a63"),
    line = c("#3a241f"), line2 = c("#553229"),
    accent = c("#e08a5f"), accentFg = c("#1c0d08"), accentSoft = c("#e08a5f").copy(alpha = 0.14f),
    ok = c("#7fa86a"), warn = c("#d9b13d"), err = c("#c9603f"),
    scrim = Color(0xCC120807), ink = c("#0d0706"),
)

private val forest = McColors(
    bg = c("#0b1410"), bg2 = c("#101d16"), surface = c("#15261d"), surface2 = c("#1c3126"),
    fg = c("#e7f3ec"), dim = c("#95b2a2"), dim2 = c("#6d8a7a"),
    line = c("#1e3328"), line2 = c("#2f4d3d"),
    accent = c("#6fcf97"), accentFg = c("#07130d"), accentSoft = c("#6fcf97").copy(alpha = 0.15f),
    ok = c("#7fdca5"), warn = c("#e0c46b"), err = c("#e07a7a"),
    scrim = Color(0xC4060D0A), ink = c("#050a07"),
)

private val rose = McColors(
    bg = c("#171015"), bg2 = c("#1f151b"), surface = c("#2a1b23"), surface2 = c("#35222d"),
    fg = c("#f7ebf1"), dim = c("#c2a6b4"), dim2 = c("#937786"),
    line = c("#352430"), line2 = c("#523646"),
    accent = c("#e58ab2"), accentFg = c("#1a0a12"), accentSoft = c("#e58ab2").copy(alpha = 0.15f),
    ok = c("#7fdca5"), warn = c("#e6c76f"), err = c("#ef8a8a"),
    scrim = Color(0xC40E080B), ink = c("#0b0608"),
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
    "#a06bff", "#7c5cff", "#c77dff", "#6fcf97",
    "#63c98d", "#e3bd52", "#e58ab2", "#e4627e", "#6fb3c4", "#f2ecff",
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

/**
 * One glass layer for every floating surface. The blur is supplied by the
 * platform where available; every version keeps the same fill, border and
 * top highlight so the hierarchy never changes.
 */
@Composable
fun Modifier.glass(
    shape: Shape = RoundedCornerShape(D.r3),
    strong: Boolean = false,
): Modifier {
    val mc = LocalMc.current
    val gfx = LocalGfxLevel.current
    val solid = gfx <= 1
    val fill = when {
        solid && strong -> mc.bg2.copy(alpha = 0.94f)
        solid -> mc.bg2.copy(alpha = 0.88f)
        strong -> mc.glassStrong
        else -> mc.glass
    }
    return this
        .shadow(if (gfx == 0) 0.dp else if (gfx == 1) 2.dp else 8.dp, shape)
        .clip(shape)
        .background(fill, shape)
        .background(
            Brush.verticalGradient(
                listOf(mc.glassHighlight.copy(alpha = 0.10f), Color.Transparent),
            ),
            shape,
        )
        .border(
            1.dp,
            Brush.linearGradient(listOf(mc.glassHighlight, mc.glassBorder)),
            shape,
        )
}

@Composable
fun McTheme(theme: String, accent: String?, gfxLevel: Int = 3, content: @Composable () -> Unit) {
    val systemDark = isSystemInDarkTheme()
    val colors = remember(theme, accent, systemDark) {
        withAccent(paletteFor(theme, systemDark), accent)
    }
    CompositionLocalProvider(LocalMc provides colors, LocalGfxLevel provides gfxLevel) { content() }
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
