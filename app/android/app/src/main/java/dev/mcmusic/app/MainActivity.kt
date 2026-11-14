package dev.mcmusic.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
import dev.mcmusic.app.ui.AppRoot
import dev.mcmusic.app.ui.theme.McTheme

class MainActivity : ComponentActivity() {

    private val vm: AppViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            McTheme(vm.theme, vm.accent) {
                AppRoot(vm)
            }
        }
    }
}
