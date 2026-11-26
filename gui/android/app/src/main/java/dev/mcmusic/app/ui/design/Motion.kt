package dev.mcmusic.app.ui.design

import android.content.Context
import android.provider.Settings
import android.view.HapticFeedbackConstants
import android.view.View
import androidx.compose.animation.core.Spring
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import dev.mcmusic.app.data.Prefs

/** Shared 4.2.0 motion values. All are flat, short and dismissible. */
object PlayfulMotion {
    const val PRESS_SCALE = 0.96f
    const val DAMPING_RATIO = 0.7f
    val STIFFNESS = Spring.StiffnessMedium

    const val CLICK = HapticFeedbackConstants.CONTEXT_CLICK
    const val KEY = HapticFeedbackConstants.VIRTUAL_KEY
    const val LONG_PRESS = HapticFeedbackConstants.LONG_PRESS
}

/** Honour both the local switch and Android's reduced-animation system settings. */
@Composable
fun playfulMotionEnabled(): Boolean {
    val context = LocalContext.current
    val systemScale = remember(context) {
        runCatching {
            val resolver = context.contentResolver
            minOf(
                Settings.Global.getFloat(resolver, Settings.Global.ANIMATOR_DURATION_SCALE, 1f),
                Settings.Global.getFloat(resolver, Settings.Global.TRANSITION_ANIMATION_SCALE, 1f),
            )
        }.getOrDefault(1f)
    }
    return Prefs.playfulMotion && Prefs.motion && systemScale > 0f
}

/** Standard system haptics only; no custom waveform or continuous feedback. */
@Composable
fun rememberPlayfulHaptic(): (Int) -> Unit {
    val view: View = LocalView.current
    val enabled = playfulMotionEnabled()
    return remember(view, enabled) { { effect: Int ->
        if (enabled) runCatching { view.performHapticFeedback(effect) }
    } }
}

/** Exposed for settings copy and tests; no animation runs when this is false. */
fun platformMotionScale(context: Context): Float = runCatching {
    val resolver = context.contentResolver
    minOf(
        Settings.Global.getFloat(resolver, Settings.Global.ANIMATOR_DURATION_SCALE, 1f),
        Settings.Global.getFloat(resolver, Settings.Global.TRANSITION_ANIMATION_SCALE, 1f),
    )
}.getOrDefault(1f)
