package dev.mcmusic.app.data

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.setValue

/** Browser OAuth returns through a deep link; Settings listens for this bump. */
object LinkEvents {
    var revision by mutableIntStateOf(0)
        private set

    fun changed() {
        revision++
    }
}
