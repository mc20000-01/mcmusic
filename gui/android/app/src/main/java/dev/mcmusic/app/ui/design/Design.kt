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
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.kyant.backdrop.Backdrop
import dev.mcmusic.app.data.Prefs
import dev.mcmusic.app.ui.liquidGlass

/** The two visual languages the client ships with. Both share the same palettes. */
enum class DesignLanguage(val id: String, val label: String, val blurb: String) {
    Ios("ios", "iOS 27", "Floating glass tab bar, layered sheets"),
    OneUi("oneui", "One UI", "Edge-to-edge flat surfaces, big headers"),
    ;

    companion object {
        fun from(id: String?) = entries.firstOrNull { it.id == id } ?: Ios
    }
}

/**
 * One of the palettes the web embeds use, so a profile looks the same on the
 * site, in an embed and on the phone.
 */
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
    val all = listOf(
        McPalette("dusk", "Dusk", c(0xFF1B1325), c(0xFF0E0A13), c(0xFFF2EDF7), c(0xFFB9ABC9), c(0xFF3E2B54), c(0xFFB080EA), true),
        McPalette("paper", "Paper", c(0xFFFAF8F4), c(0xFFF2EBE4), c(0xFF281F15), c(0xFF5D4F41), c(0xFFBAA997), c(0xFF9A4B1D), false),
        McPalette("ink", "Ink", c(0xFF1A1A1E), c(0xFF0D0D0F), c(0xFFEDEDF7), c(0xFFABABC9), c(0xFF3C3C44), c(0xFFDADADD), true),
        McPalette("tide", "Tide", c(0xFF142124), c(0xFF0A1012), c(0xFFEDF5F7), c(0xFFABC3C9), c(0xFF2E4A52), c(0xFF89CEE1), true),
        McPalette("copper", "Copper", c(0xFF261812), c(0xFF130C09), c(0xFFF7F0ED), c(0xFFC9B4AB), c(0xFF573729), c(0xFFEAA07B), true),
        McPalette("forest", "Forest", c(0xFF14241B), c(0xFF0A120E), c(0xFFEDF7F2), c(0xFFABC9B9), c(0xFF2D533E), c(0xFF79D8A5), true),
        McPalette("rose", "Rose", c(0xFF24141C), c(0xFF120A0E), c(0xFFF7EDF2), c(0xFFC9ABBA), c(0xFF532D40), c(0xFFEA90B8), true),
    )

    const val AUTO = "auto"

    fun byId(id: String?): McPalette = all.firstOrNull { it.id == id } ?: all.first()

    /** `auto` follows the system, the way `theme="auto"` does in the embeds. */
    fun resolve(id: String?, systemDark: Boolean): McPalette = when (id) {
        AUTO, null, "" -> if (systemDark) byId("dusk") else byId("paper")
        else -> byId(id)
    }

    private fun c(argb: Long) = Color(argb)
}

/**
 * Everything a screen needs to look like whichever language is selected:
 * radii, weights and surface treatment live here instead of in each screen.
 */
@Immutable
class McDesign(
    val language: DesignLanguage,
    val palette: McPalette,
) {
    val ios: Boolean get() = language == DesignLanguage.Ios

    val cardRadius = if (ios) 28.dp else 26.dp
    val tileRadius = if (ios) 18.dp else 20.dp
    val screenPadding = if (ios) 20.dp else 18.dp
    val gap = if (ios) 14.dp else 12.dp

    val titleSize = if (ios) 34.sp else 32.sp
    val titleWeight = if (ios) FontWeight.Bold else FontWeight.ExtraBold
    val sectionSize = 13.sp
    val sectionWeight = FontWeight.SemiBold

    val fg = palette.fg
    val dim = palette.dim
    val accent = palette.accent
    val accentSoft = palette.accent.copy(alpha = if (palette.dark) 0.20f else 0.14f)
    val hairline = palette.line.copy(alpha = 0.55f)

    /** Flat card fill used when glass is off, or below Android 13. */
    val cardFill = if (palette.dark) palette.bg.copy(alpha = 0.92f) else palette.bg2.copy(alpha = 0.96f)
}

val LocalDesign = compositionLocalOf { McDesign(DesignLanguage.Ios, Palettes.byId("dusk")) }

/** Recorded backdrop for the glass; null on devices without RuntimeShader. */
val LocalBackdrop = compositionLocalOf<Backdrop?> { null }

@Composable
fun McTheme(paletteId: String, language: DesignLanguage, content: @Composable () -> Unit) {
    val systemDark = isSystemInDarkTheme()
    val palette = Palettes.resolve(paletteId, systemDark)
    val design = McDesign(language, palette)

    val scheme = if (palette.dark) {
        darkColorScheme(
            primary = palette.accent,
            onPrimary = palette.bg2,
            background = palette.bg,
            onBackground = palette.fg,
            surface = palette.bg,
            onSurface = palette.fg,
            surfaceVariant = palette.bg2,
            onSurfaceVariant = palette.dim,
            outline = palette.line,
            error = Color(0xFFFF6B6B),
        )
    } else {
        lightColorScheme(
            primary = palette.accent,
            onPrimary = Color.White,
            background = palette.bg,
            onBackground = palette.fg,
            surface = palette.bg,
            onSurface = palette.fg,
            surfaceVariant = palette.bg2,
            onSurfaceVariant = palette.dim,
            outline = palette.line,
            error = Color(0xFFB3261E),
        )
    }

    CompositionLocalProvider(LocalDesign provides design) {
        MaterialTheme(colorScheme = scheme, content = content)
    }
}

/**
 * A card: glass in the iOS language (Backdrop), a flat tinted panel in One UI
 * or wherever a backdrop is unavailable. Screens call this instead of choosing
 * a background themselves, which is what makes the language switch total.
 */
@Composable
fun Modifier.mcSurface(
    shape: Shape = RoundedCornerShape(LocalDesign.current.cardRadius),
    tint: Color = Color.Transparent,
): Modifier {
    val design = LocalDesign.current
    val backdrop = LocalBackdrop.current
    return if (design.ios && backdrop != null) {
        liquidGlass(backdrop, shape, tint = tint)
    } else {
        clip(shape)
            .background(design.cardFill, shape)
            .border(1.dp, design.hairline, shape)
    }
}

/** Reads the saved palette/language; used by the activity before composing. */
fun currentDesignLanguage(): DesignLanguage = DesignLanguage.from(Prefs.language)
