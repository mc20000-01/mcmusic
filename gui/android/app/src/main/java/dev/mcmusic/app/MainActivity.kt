package dev.mcmusic.app

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.content.ContextCompat
import androidx.activity.SystemBarStyle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.DisposableEffect
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.Downloads
import dev.mcmusic.app.data.Prefs
import dev.mcmusic.app.ui.McShell
import dev.mcmusic.app.ui.design.DesignLanguage
import dev.mcmusic.app.ui.design.McTheme
import dev.mcmusic.app.ui.design.Palettes
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.widget.Widgets

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Prefs.init(applicationContext)
        Api.init(applicationContext)
        Downloads.init(applicationContext)
        Playback.init(applicationContext)

        // The playback notification is how a stream keeps running off-screen.
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) !=
            PackageManager.PERMISSION_GRANTED
        ) {
            registerForActivityResult(ActivityResultContracts.RequestPermission()) { }.launch(Manifest.permission.POST_NOTIFICATIONS)
        }

        // Widgets are redrawn from the same prefs: opening the app is the
        // cheapest moment to bring them up to date.
        Thread { runCatching { Widgets.refresh(applicationContext) } }.start()

        val dark = Palettes.resolve(Prefs.palette, isSystemDark()).dark
        enableEdgeToEdge(
            statusBarStyle = if (dark) SystemBarStyle.dark(android.graphics.Color.TRANSPARENT)
            else SystemBarStyle.light(android.graphics.Color.TRANSPARENT, android.graphics.Color.TRANSPARENT),
            navigationBarStyle = if (dark) SystemBarStyle.dark(android.graphics.Color.TRANSPARENT)
            else SystemBarStyle.light(android.graphics.Color.TRANSPARENT, android.graphics.Color.TRANSPARENT),
        )

        setContent {
            McTheme(paletteId = Prefs.palette, language = DesignLanguage.from(Prefs.language)) {
                val darkPalette = Palettes.resolve(Prefs.palette, isSystemDark()).dark
                val view = LocalView.current
                DisposableEffect(darkPalette) {
                    val window = (view.context as? ComponentActivity)?.window
                    if (window != null) {
                        WindowCompat.getInsetsController(window, view).apply {
                            isAppearanceLightStatusBars = !darkPalette
                            isAppearanceLightNavigationBars = !darkPalette
                        }
                    }
                    onDispose {}
                }
                Box(Modifier.fillMaxSize()) {
                    McShell()
                }
            }
        }
    }

    private fun isSystemDark(): Boolean =
        (resources.configuration.uiMode and android.content.res.Configuration.UI_MODE_NIGHT_MASK) ==
            android.content.res.Configuration.UI_MODE_NIGHT_YES
}
