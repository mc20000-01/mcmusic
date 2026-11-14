package dev.mcmusic.app.ui.theme

import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.remember
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.em
import androidx.compose.ui.unit.sp

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
)

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
)

private val ink = McColors(
    bg = c("#0e0e12"), bg2 = c("#141419"), surface = c("#1b1b21"), surface2 = c("#23232b"),
    fg = c("#f1eff6"), dim = c("#a09daa"), dim2 = c("#726f7d"),
    line = c("#242430"), line2 = c("#343442"),
    accent = c("#a06bff"), accentFg = c("#0b0616"), accentSoft = c("#a06bff").copy(alpha = 0.12f),
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

val McThemes = listOf("ink", "dusk", "paper", "tide", "copper")

private val palettes = mapOf(
    "dusk" to dusk, "auto" to ink, "dark" to ink,
    "paper" to paper, "light" to paper,
    "ink" to ink, "amoled" to ink, "violet" to ink,
    "tide" to tide, "copper" to copper,
    "midnight" to tide, "mocha" to copper, "rose" to copper,
)

fun paletteFor(theme: String): McColors = palettes[theme] ?: ink

/** Mirror of applySet(): accent override plus readable foreground. */
fun withAccent(base: McColors, accentHex: String?): McColors {
    if (accentHex.isNullOrBlank()) return base
    val parsed = runCatching { c(accentHex) }.getOrNull() ?: return base
    val lum = 0.299 * parsed.red + 0.587 * parsed.green + 0.114 * parsed.blue
    return base.copy(
        accent = parsed,
        accentFg = if (lum > 0.6f) Color.Black else Color.White,
        accentSoft = parsed.copy(alpha = 0.14f),
    )
}

val LocalMc = staticCompositionLocalOf { dusk }

@Composable
fun McTheme(theme: String, accent: String?, content: @Composable () -> Unit) {
    val colors = remember(theme, accent) { withAccent(paletteFor(theme), accent) }
    CompositionLocalProvider(LocalMc provides colors) { content() }
}

/* ── geometry (variables.css) ──────────────────────────────────────────── */

object D {
    val r1 = 4.dp
    val r2 = 9.dp
    val r3 = 14.dp
    val r4 = 20.dp
    val rail = 232.dp
    val deck = 84.dp
    val top = 52.dp
    val tab = 76.dp
    val maxw = 1180.dp
    val gutter = 14.dp
}

/* ── typography ─────────────────────────────────────────────────────────── */

object McType {
    // Smooth sans everywhere: the serif display face was harder to read on
    // small screens and clashed with the UI font.
    val display = FontFamily.SansSerif
    val sans = FontFamily.SansSerif
    val mono = FontFamily.Monospace

    val h1 = TextStyle(
        fontFamily = display, fontSize = 40.sp, fontWeight = FontWeight.SemiBold,
        letterSpacing = (-0.02).em, lineHeight = 42.sp,
    )
    val h1Small = TextStyle(
        fontFamily = display, fontSize = 30.sp, fontWeight = FontWeight.SemiBold,
        letterSpacing = (-0.02).em, lineHeight = 32.sp,
    )
    val h2 = TextStyle(
        fontFamily = display, fontSize = 24.sp, fontWeight = FontWeight.SemiBold,
        letterSpacing = (-0.01).em, lineHeight = 28.sp,
    )
    val h3 = TextStyle(
        fontFamily = display, fontSize = 18.sp, fontWeight = FontWeight.SemiBold,
        lineHeight = 22.sp,
    )
    val body = TextStyle(fontFamily = sans, fontSize = 15.sp, lineHeight = 22.sp)
    val bodySm = TextStyle(fontFamily = sans, fontSize = 13.sp, lineHeight = 19.sp)
    val bodyXs = TextStyle(fontFamily = sans, fontSize = 11.sp, lineHeight = 16.sp)
    val mono10 = TextStyle(
        fontFamily = mono, fontSize = 10.sp, letterSpacing = 0.04.em, lineHeight = 14.sp,
    )
    val mono9 = TextStyle(fontFamily = mono, fontSize = 9.sp, letterSpacing = 0.12.em, lineHeight = 12.sp)
    val kicker = TextStyle(
        fontFamily = mono, fontSize = 10.sp, letterSpacing = 0.18.em, lineHeight = 14.sp,
    )
    val button = TextStyle(
        fontFamily = mono, fontSize = 10.sp, fontWeight = FontWeight.SemiBold,
        letterSpacing = 0.12.em, lineHeight = 14.sp,
    )
    val buttonSm = TextStyle(
        fontFamily = mono, fontSize = 9.sp, fontWeight = FontWeight.SemiBold,
        letterSpacing = 0.12.em, lineHeight = 12.sp,
    )

    /** Sentence-case labels: calmer than the mono micro-caps. */
    val label = TextStyle(
        fontFamily = sans, fontSize = 12.sp, fontWeight = FontWeight.Medium,
        lineHeight = 16.sp,
    )
    val labelSm = TextStyle(
        fontFamily = sans, fontSize = 11.sp, fontWeight = FontWeight.Medium,
        lineHeight = 14.sp,
    )
}
