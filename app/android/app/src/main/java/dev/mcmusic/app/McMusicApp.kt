package dev.mcmusic.app

import android.app.Application
import androidx.compose.runtime.mutableStateOf
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.DownloadStore
import dev.mcmusic.app.data.Repo
import dev.mcmusic.app.data.SessionStore
import dev.mcmusic.app.data.Settings
import dev.mcmusic.app.play.PlaybackEngine
import dev.mcmusic.app.ui.ArtLoader
import dev.mcmusic.app.ui.MediaUrls
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob

class McMusicApp : Application() {

    val appScope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)

    lateinit var store: SessionStore
        private set
    lateinit var api: Api
        private set
    lateinit var repo: Repo
        private set
    lateinit var engine: PlaybackEngine
        private set
    lateinit var downloads: DownloadStore
        private set

    var settings = mutableStateOf(Settings())

    var viewModel: AppViewModel? = null

    override fun onCreate() {
        super.onCreate()
        store = SessionStore(this)
        api = Api(store)
        api.setBase(store.baseUrl)
        repo = Repo(api, store)
        downloads = DownloadStore(this, api)
        engine = PlaybackEngine(this)
        settings.value = store.let { s ->
            Settings(theme = s.theme, accent = s.accent, volume = s.volume)
        }
        MediaUrls.base = api.baseUrl
        ArtLoader.client = api.client
    }
}
