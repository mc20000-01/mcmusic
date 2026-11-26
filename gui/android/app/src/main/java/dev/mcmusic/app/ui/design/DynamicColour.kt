package dev.mcmusic.app.ui.design

import android.app.WallpaperColors
import android.app.WallpaperManager
import android.content.Context
import android.graphics.Bitmap
import android.graphics.Color as FrameworkColor
import android.os.Build
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.graphics.Color
import com.materialkolor.hct.Hct
import com.materialkolor.scheme.SchemeTonalSpot
import dev.mcmusic.app.data.Prefs

/**
 * Runtime colour seeds for the 4.2.0 Android theme.
 *
 * The five family palettes remain the generated source of truth for stored ids
 * and legacy aliases. This layer only supplies an HCT seed: cover art and (when
 * chosen explicitly) the Android wallpaper generate a tonal-spot scheme with
 * the same 2021 spec used by the generator, and the resulting roles are layered
 * over the selected family. No bitmap is recoloured and no family id is rewritten.
 */
object DynamicColour {
    const val WALLPAPER = "wallpaper"

    private var coverKey: String? = null
    private val coverSeedState = mutableStateOf<Int?>(null)
    private val wallpaperSeedState = mutableStateOf<Int?>(null)

    val coverSeed: Int? get() = coverSeedState.value
    val wallpaperSeed: Int? get() = wallpaperSeedState.value

    /** Call from the currently playing cover only, so list tiles never retint the app. */
    fun setCover(bitmap: Bitmap, key: String) {
        val argb = dominantArgb(bitmap) ?: return
        if (coverKey == key && coverSeedState.value == argb) return
        coverKey = key
        coverSeedState.value = argb
    }

    /** A failed or missing current cover restores the selected family palette. */
    fun clearCover(key: String) {
        if (coverKey != key) return
        coverKey = null
        coverSeedState.value = null
    }

    /** Called when the playing track changes, before its replacement loads. */
    fun clearCover() {
        coverKey = null
        coverSeedState.value = null
    }

    /** Android 12+ exposes wallpaper colours as a system signal, not a network call. */
    fun refreshWallpaper(context: Context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) return
        val colors: WallpaperColors = runCatching {
            WallpaperManager.getInstance(context).getWallpaperColors(WallpaperManager.FLAG_SYSTEM)
        }.getOrNull() ?: return
        val argb = colors.primaryColor.toArgb()
        if (argb != wallpaperSeedState.value) wallpaperSeedState.value = argb
    }

    /**
     * Quantised dominant colour from a small copy of the artwork. Near-white,
     * near-black and very low-chroma pixels are ignored so a logo on a white
     * sleeve does not wash the theme out. A neutral sleeve yields no seed.
     */
    private fun dominantArgb(bitmap: Bitmap): Int? {
        if (bitmap.width <= 0 || bitmap.height <= 0) return null
        val thumb = runCatching {
            Bitmap.createScaledBitmap(bitmap, 24, 24, false)
        }.getOrNull() ?: return null
        val pixels = IntArray(thumb.width * thumb.height)
        thumb.getPixels(pixels, 0, thumb.width, 0, 0, thumb.width, thumb.height)
        if (thumb !== bitmap) thumb.recycle()

        val counts = HashMap<Int, Int>()
        var total = 0
        for (pixel in pixels) {
            if (FrameworkColor.alpha(pixel) < 200) continue
            val r = FrameworkColor.red(pixel)
            val g = FrameworkColor.green(pixel)
            val b = FrameworkColor.blue(pixel)
            val max = maxOf(r, g, b)
            val min = minOf(r, g, b)
            if (max < 36 || min > 232 || max - min < 14) continue
            val bucket = (r / 32 shl 10) or (g / 32 shl 5) or (b / 32)
            counts[bucket] = (counts[bucket] ?: 0) + 1
            total++
        }
        if (total == 0) return null

        val winner = counts.maxByOrNull { it.value }?.key ?: return null
        val r = ((winner shr 10) and 0x1f) * 8 + 4
        val g = ((winner shr 5) and 0x1f) * 8 + 4
        val b = (winner and 0x1f) * 8 + 4
        return FrameworkColor.rgb(r.coerceIn(0, 255), g.coerceIn(0, 255), b.coerceIn(0, 255))
    }

    /** Resolve the stored id, then overlay an HCT tonal scheme when a seed exists. */
    fun resolve(id: String, systemDark: Boolean): McPalette {
        val base = Palettes.resolve(if (id == WALLPAPER) Palettes.AUTO else id, systemDark)
        val seed = when {
            id == WALLPAPER -> wallpaperSeed
            Prefs.dynamicColour -> coverSeed
            else -> null
        } ?: return base

        val scheme = SchemeTonalSpot(Hct.fromInt(seed), systemDark, 0.0)
        return base.copy(
            bg = Color(scheme.background),
            bg2 = Color(scheme.surfaceContainerLow),
            surface = Color(scheme.surfaceContainerLow),
            surface2 = Color(scheme.surfaceContainerHigh),
            fg = Color(scheme.onSurface),
            dim = Color(scheme.onSurfaceVariant),
            dim2 = Color(scheme.onSurfaceVariant),
            line = Color(scheme.outlineVariant),
            line2 = Color(scheme.outline),
            accent = Color(scheme.primary),
            accentText = Color(scheme.primary),
            accentFg = Color(scheme.onPrimary),
            primary = Color(scheme.primary),
            onPrimary = Color(scheme.onPrimary),
            primaryContainer = Color(scheme.primaryContainer),
            onPrimaryContainer = Color(scheme.onPrimaryContainer),
            secondary = Color(scheme.secondary),
            onSecondary = Color(scheme.onSecondary),
            secondaryContainer = Color(scheme.secondaryContainer),
            onSecondaryContainer = Color(scheme.onSecondaryContainer),
            tertiary = Color(scheme.tertiary),
            onTertiary = Color(scheme.onTertiary),
            tertiaryContainer = Color(scheme.tertiaryContainer),
            onTertiaryContainer = Color(scheme.onTertiaryContainer),
            error = Color(scheme.error),
            onError = Color(scheme.onError),
            errorContainer = Color(scheme.errorContainer),
            onErrorContainer = Color(scheme.onErrorContainer),
            background = Color(scheme.background),
            onBackground = Color(scheme.onBackground),
            onSurface = Color(scheme.onSurface),
            surfaceVariant = Color(scheme.surfaceVariant),
            onSurfaceVariant = Color(scheme.onSurfaceVariant),
            surfaceContainerLowest = Color(scheme.surfaceContainerLowest),
            surfaceContainerLow = Color(scheme.surfaceContainerLow),
            surfaceContainer = Color(scheme.surfaceContainer),
            surfaceContainerHigh = Color(scheme.surfaceContainerHigh),
            surfaceContainerHighest = Color(scheme.surfaceContainerHighest),
            outline = Color(scheme.outline),
            outlineVariant = Color(scheme.outlineVariant),
            inverseSurface = Color(scheme.inverseSurface),
            inverseOnSurface = Color(scheme.inverseOnSurface),
            inversePrimary = Color(scheme.inversePrimary),
            scrim = Color(scheme.scrim),
        )
    }
}
