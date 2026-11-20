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
import androidx.compose.runtime.immutableOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.kyant.backdrop.Backdrop
import dev.mcmusic.app.data.Prefs

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
        McPalette("dusk", "Dusk", Color(0xFF1E1422), Color(0xFF120C18), Color(0xFFF8F4F0), Color(0xFFB4A8A1), Color(0xFF4A3D4E), Color(0xFFAB9ECE), true),
        McPalette("paper", "Paper", Color(0xFFFDF8F0), Color(0xF9F5EB), Color(0xFF251D14), Color(0xFF6B5B47), Color(0xFFB4A28C), Color(0xFFC9A86A), false),
        McPalette("ink", "Ink", Color(0xFF0F0B12), Color(0xFF07060A), Color(0xFFE8E3EC), Color(0xFF8C8494), Color(0xFF3A3441), Color(0xFFB5A8C5), true),
        McPalette("tide", "Tide", Color(0xFF0C1822), Color(0xFF050D12), Color(0xFFEDF3F5), Color(0xFF9CB9C7), Color(0xFF354A56), Color(0xFF9FD6E8), true),
        McPalette("copper", "Copper", Color(0xFF1C120C), Color(0xFF140A06), Color(0xFFF7E7E0), Color(0xFFB89B8C), Color(0xFF523830), Color(0xFFA4756E), true),
        McPalette("forest", "Forest", Color(0xFF0D1612), Color(0xFF060D0A), Color(0xFFEFEFE8), Color(0xFF9AA89B), Color(0xFF3D483A), Color(0xFF8FA896), true),
        McPalette("rose", "Rose", Color(0xFF1B0E12), Color(0xFF12070E), Color(0xFFF8F0F5), Color(0xFFA8909F), Color(0xFF52303F), Color(0xFFA77A88), true),
    )

    const val AUTO = "auto"

    fun byId(id: String?): McPalette = all.firstOrNull { it.id == id } ?: all.first()

    /** `auto` follows the system, the way `theme="auto"` does in the embeds. */
    fun resolve(id: String?, systemDark: Boolean): McPalette = when (id) {
        AUTO, null, "" -> if (systemDark) byId("dusk") else byId("paper")
        else -> byId(id)
    }
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
    val tileRadius = if (ios) 18.dp else 22.dp
    val screenPadding = if (ios) 20.dp else 18.dp
    val gap = if (ios) 14.dp else 13.dp

    val titleSize = if (ios) 34.sp else 33.sp
    val titleWeight = if (ios) FontWeight.Bold else FontWeight.ExtraBold
    val sectionSize = 13.sp
    val sectionWeight = FontWeight.SemiBold

    val fg = palette.fg
    val dim = palette.dim
    val accent = palette.accent
    val accentSoft = palette.accent.copy(alpha = if (palette.dark) 0.18f else 0.12f)
    val hairline = palette.line.copy(alpha = 0.45f)

    /** Flat card fill used when glass is off, or below Android 13. */
    val cardFill = if (palette.dark) palette.bg.copy(alpha = 0.94f) else palette.bg2.copy(alpha = 0.97f)
}

val LocalDesign = compositionLocalOf { McDesign(DesignLanguage.Ios, Palettes.byId("dusk")) }

/** Recorded backdrop for the glass; null on devices without RuntimeShader. */
val LocalBackdrop = compositionLocalOf { null }

/** Palette/window stage: two soft-glow circles + a vertical gradient background. */
@Composable
private fun Stage(modifier: Modifier, design: McDesign) {
    val palette = design.palette
    Canvas(modifier) {
        // Soft vertical gradient background
        drawRect(
            Brush.verticalGradient(
                listOf(palette.bg, palette.bg2),
                startY = 0f,
                endY = size.height,
            ),
        )
        // Two gentle glow accents — one top-left, one bottom-right
        drawCircle(
            color = palette.accent.copy(alpha = if (palette.dark) 0.14f else 0.10f),
            radius = size.minDimension * 0.52f,
            center = Offset(size.width * 0.18f, size.height * 0.16f),
        )
        drawCircle(
            color = palette.accent.copy(alpha = if (palette.dark) 0.08f else 0.06f),
            radius = size.minDimension * 0.42f,
            center = Offset(size.width * 0.82f, size.height * 0.52f),
        )
    }
}

/** Liquid-glass surface, unified across both languages. */
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