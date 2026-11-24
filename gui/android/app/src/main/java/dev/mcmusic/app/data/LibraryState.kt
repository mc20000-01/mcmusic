package dev.mcmusic.app.data

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue

/**
 * One shared signal for "the server's music changed".
 *
 * Likes and admin track deletions can happen from a row on any screen. Screens
 * watch [revision] in their load effect so the row they came from refreshes
 * without passing callbacks through every list and sheet.
 */
object LibraryState {
    var revision by mutableStateOf(0)
        private set

    fun changed() {
        revision++
    }
}
