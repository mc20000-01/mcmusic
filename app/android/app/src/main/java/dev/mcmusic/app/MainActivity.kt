package dev.mcmusic.app

import android.app.Activity
import android.graphics.drawable.ColorDrawable
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat
import dev.mcmusic.app.ui.AppRoot
import dev.mcmusic.app.ui.theme.LocalMc
import dev.mcmusic.app.ui.theme.McTheme
import dev.mcmusic.app.ui.theme.paletteFor

class MainActivity : ComponentActivity() {

    private val vm: AppViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.setBackgroundDrawable(ColorDrawable(paletteFor(vm.theme).bg.toArgb()))
        enableEdgeToEdge()
        setContent {
            McTheme(vm.theme, vm.accent, vm.gfxLevel) {
                val mc = LocalMc.current
                val view = LocalView.current
                SideEffect {
                    val window = (view.context as? Activity)?.window ?: return@SideEffect
                    window.statusBarColor = Color.Transparent.toArgb()
                    window.navigationBarColor = mc.bg.toArgb()
                    WindowCompat.getInsetsController(window, view).apply {
                        isAppearanceLightStatusBars = !mc.isDark
                        isAppearanceLightNavigationBars = !mc.isDark
                    }
                }
                AppRoot(vm)
            }
        }
    }
}
