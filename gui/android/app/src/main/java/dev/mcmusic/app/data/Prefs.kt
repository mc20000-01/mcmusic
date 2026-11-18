package dev.mcmusic.app.data

import android.content.Context
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue

/**
 * Small, synchronous settings store. Compose state so switching the palette or
 * the design language repaints immediately, and SharedPreferences so both
 * survive a restart. Home screen widgets read the same values.
 */
object Prefs {
    private const val FILE = "mcmusic"
    private var sp: android.content.SharedPreferences? = null

    const val DEFAULT_SERVER = "https://mcmusic.sdisk.us"

    /** iOS-style or One UI-style layout and styling. */
    var language by mutableStateOf("ios")
        private set

    /** Palette id from [dev.mcmusic.app.ui.design.Palettes], or "auto". */
    var palette by mutableStateOf("auto")
        private set

    var server by mutableStateOf(DEFAULT_SERVER)
        private set

    var username by mutableStateOf<String?>(null)
        private set

    fun init(context: Context) {
        if (sp != null) return
        val p = context.getSharedPreferences(FILE, Context.MODE_PRIVATE)
        sp = p
        language = p.getString("language", "ios") ?: "ios"
        palette = p.getString("palette", "auto") ?: "auto"
        server = (p.getString("server", DEFAULT_SERVER) ?: DEFAULT_SERVER).trimEnd('/')
        username = p.getString("username", null)
    }

    fun saveLanguage(id: String) {
        language = id
        sp?.edit()?.putString("language", id)?.apply()
    }

    fun savePalette(id: String) {
        palette = id
        sp?.edit()?.putString("palette", id)?.apply()
    }

    fun saveServer(url: String) {
        val clean = url.trim().trimEnd('/').ifEmpty { DEFAULT_SERVER }
        server = clean
        sp?.edit()?.putString("server", clean)?.apply()
    }

    fun saveUsername(name: String?) {
        username = name
        sp?.edit()?.apply { if (name == null) remove("username") else putString("username", name) }?.apply()
    }
}
