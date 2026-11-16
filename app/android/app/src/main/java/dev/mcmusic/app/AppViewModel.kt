package dev.mcmusic.app

import android.app.ActivityManager
import android.app.Application
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.core.content.FileProvider
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import dev.mcmusic.app.data.AdminDeviceRef
import dev.mcmusic.app.data.AdminRoom
import dev.mcmusic.app.data.AdminStats
import dev.mcmusic.app.data.AdminUser
import dev.mcmusic.app.data.ChannelRef
import dev.mcmusic.app.data.EnrichStatus
import dev.mcmusic.app.data.LyricsStatus
import dev.mcmusic.app.data.AlbumRef
import dev.mcmusic.app.data.ArtistRef
import dev.mcmusic.app.data.DownloadEntry
import dev.mcmusic.app.data.HomeData
import dev.mcmusic.app.data.Me
import dev.mcmusic.app.data.PlaylistRef
import dev.mcmusic.app.data.RequestRow
import dev.mcmusic.app.data.RoomState
import dev.mcmusic.app.data.SearchData
import dev.mcmusic.app.data.DeviceRef
import dev.mcmusic.app.data.InviteCode
import dev.mcmusic.app.data.Settings
import dev.mcmusic.app.data.Track
import dev.mcmusic.app.data.UpdateChecker
import dev.mcmusic.app.data.UpdateInfo
import dev.mcmusic.app.ui.MediaUrls
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.Request
import org.json.JSONObject
import java.io.File
import java.io.IOException
import java.security.MessageDigest
import kotlin.math.abs

sealed interface Route {
    data object Home : Route
    data object Search : Route
    data object Library : Route
    data class Album(val name: String) : Route
    data class Artist(val name: String) : Route
    data object Likes : Route
    data object Playlists : Route
    data class Playlist(val id: Int, val name: String = "") : Route
    data object Requests : Route
    data object Downloads : Route
    data object Settings : Route
    data object Admin : Route
    data object NowPlaying : Route
}

data class CollectionMenu(
    val kind: String,
    val title: String,
    val subtitle: String,
    val coverId: Int?,
    val playlistId: Int?,
    val tracks: List<Track>,
)

class AppViewModel(application: Application) : AndroidViewModel(application) {

    private val mc = application as McMusicApp
    val repo get() = mc.repo
    val api get() = mc.api
    val engine get() = mc.engine
    private val store get() = mc.store

    /* ── session ────────────────────────────────────────────────────────── */
    var me by mutableStateOf<Me?>(null)
        private set
    var checked by mutableStateOf(false)
    var busy by mutableStateOf(false)
    var loginError by mutableStateOf<String?>(null)
    var toastText by mutableStateOf<String?>(null)

    /* ── GitHub updates ─────────────────────────────────────────────────── */
    var updateInfo by mutableStateOf<UpdateInfo?>(null)
        private set
    var updateChecking by mutableStateOf(false)
        private set
    var updateDownloading by mutableStateOf(false)
        private set
    var updateVerifying by mutableStateOf(false)
        private set
    var updateProgress by mutableStateOf(0)
        private set
    var updateDialogOpen by mutableStateOf(false)
        private set

    /* ── appearance ─────────────────────────────────────────────────────── */
    var settings by mutableStateOf(mc.settings.value)
        private set
    var theme by mutableStateOf(store.theme)
        private set
    var accent by mutableStateOf(store.accent)
        private set
    var material by mutableStateOf(mc.settings.value.material)
        private set
    var gfxAuto by mutableStateOf(store.gfxAuto)
        private set
    var gfxLevel by mutableStateOf(if (store.gfxLevel >= 0) store.gfxLevel else detectedGfx())
        private set

    /* ── router ─────────────────────────────────────────────────────────── */
    var route by mutableStateOf<Route>(Route.Home)
        private set
    var stack by mutableStateOf<List<Route>>(emptyList())
        private set

    /* ── screen data ────────────────────────────────────────────────────── */
    var home by mutableStateOf<HomeData?>(null)
        private set
    var searchData by mutableStateOf<SearchData?>(null)
        private set
    var searchQuery by mutableStateOf("")
        private set
    var libraryTab by mutableStateOf("songs")
        private set
    var sort by mutableStateOf("artist")
        private set
    var tracks by mutableStateOf<List<Track>>(emptyList())
        private set
    var albums by mutableStateOf<List<AlbumRef>>(emptyList())
        private set
    var artists by mutableStateOf<List<ArtistRef>>(emptyList())
        private set
    var collectionTitle by mutableStateOf("")
        private set
    var collectionTracks by mutableStateOf<List<Track>>(emptyList())
        private set
    var likes by mutableStateOf<List<Track>>(emptyList())
        private set
    var playlists by mutableStateOf<List<PlaylistRef>>(emptyList())
        private set
    var playlistName by mutableStateOf("")
        private set
    var playlistTracks by mutableStateOf<List<Track>>(emptyList())
        private set
    var requests by mutableStateOf<List<RequestRow>>(emptyList())
        private set
    var requestsAdmin by mutableStateOf(false)
        private set
    var adminStats by mutableStateOf<AdminStats?>(null)
        private set
    var adminUsers by mutableStateOf<List<AdminUser>>(emptyList())
        private set
    var adminRooms by mutableStateOf<List<AdminRoom>>(emptyList())
        private set
    var adminInvites by mutableStateOf<List<InviteCode>>(emptyList())
        private set
    var devices by mutableStateOf<List<DeviceRef>>(emptyList())
        private set
    var downloads by mutableStateOf<List<DownloadEntry>>(emptyList())
        private set
    var downloadBytes by mutableStateOf(0L)
        private set
    var downloadsTab by mutableStateOf("downloads")
        private set
    var roturStatus by mutableStateOf<JSONObject?>(null)
        private set
    var discordStatus by mutableStateOf<JSONObject?>(null)
        private set

    /* ── listen-along room ──────────────────────────────────────────────── */
    var roomRole by mutableStateOf<String?>(null)   // "host" or "guest"
        private set
    var roomCode by mutableStateOf("")
        private set
    var roomHostName by mutableStateOf("")
        private set
    var roomState by mutableStateOf<RoomState?>(null)
        private set
    var roomJoinCode by mutableStateOf("")
        private set

    /* ── account recovery ───────────────────────────────────────────────── */
    var resetBusy by mutableStateOf(false)
        private set
    var resetNotice by mutableStateOf<String?>(null)
        private set

    /* ── admin request log ──────────────────────────────────────────────── */
    var requestLog by mutableStateOf<String?>(null)
        private set
    var requestLogTitle by mutableStateOf("")
        private set

    /* ── long-press collection menu ─────────────────────────────────────── */
    var collectionMenu by mutableStateOf<CollectionMenu?>(null)
        private set
    var collectionMenuLoading by mutableStateOf(false)
        private set

    /* ── admin extras ───────────────────────────────────────────────────── */
    var channels by mutableStateOf<List<ChannelRef>>(emptyList())
        private set
    var channelsConfigured by mutableStateOf(false)
        private set
    var adminDevices by mutableStateOf<List<AdminDeviceRef>>(emptyList())
        private set
    var enrich by mutableStateOf<EnrichStatus?>(null)
        private set
    var lyricsStatus by mutableStateOf<LyricsStatus?>(null)
        private set

    /* ── overlays ───────────────────────────────────────────────────────── */
    var queueOpen by mutableStateOf(false)
    var menuTrack by mutableStateOf<Track?>(null)
        private set
    var menuPlaylistId by mutableStateOf<Int?>(null)
        private set
    var infoTrack by mutableStateOf<Track?>(null)
        private set
    var addToPlaylistTrack by mutableStateOf<Track?>(null)
        private set
    var createPlaylistOpen by mutableStateOf(false)
    var sleepOpen by mutableStateOf(false)
    var playerOpen by mutableStateOf(false)

    private var searchJob: Job? = null
    private var roomJob: Job? = null

    init {
        mc.viewModel = this
        MediaUrls.base = api.baseUrl

        viewModelScope.launch {
            store.cachedMe?.let { raw ->
                runCatching { Me.from(JSONObject(raw)) }.getOrNull()?.let { me = it }
            }
            if (store.cookieJar.hasSession() || me != null) {
                runCatching { repo.me() }.onSuccess { fresh ->
                    me = fresh
                    cacheMe(fresh)
                }.onFailure {
                    me = null
                    store.cachedMe = null
                }
            }
            checked = true
            checkForUpdates()
            if (me != null) {
                loadSettings()
                refreshDownloads()
                loadRoute()
                heartbeatLoop()
                commandLoop()
                installRoturHook()
                runCatching { repo.heartbeat(repo.deviceHash(), repo.deviceName(), null, 0.0, true) }
            }
        }
    }

    /** Commands other devices of this account addressed to us (pause/play/seek…). */
    private fun commandLoop() {
        if (commandLoopRunning) return
        commandLoopRunning = true
        viewModelScope.launch {
            while (true) {
                delay(4_000)
                if (me == null) continue
                val r = runCatching { repo.pullPlayback(repo.deviceHash()) }.getOrNull() ?: continue
                val arr = r.optJSONArray("commands") ?: continue
                for (i in 0 until arr.length()) {
                    val cmd = arr.optJSONObject(i) ?: continue
                    applyRemote(cmd.optString("action"), cmd.optJSONObject("arg") ?: JSONObject())
                }
            }
        }
    }

    private fun applyRemote(action: String, arg: JSONObject) {
        when (action) {
            "pause" -> engine.pause()
            "play" -> if (!engine.playing) engine.toggle()
            "toggle" -> engine.toggle()
            "skip", "next" -> engine.next()
            "prev" -> engine.prev()
            "seek" -> engine.seekTo(arg.optDouble("position", 0.0))
            "play_track" -> {
                val raw = arg.optJSONObject("track") ?: return
                toast("Playing from ${arg.optString("from", "another device")}")
                playList(listOf(Track.from(raw)), 0)
            }
        }
    }

    private fun installRoturHook() {
        if (roturHookSet) return
        roturHookSet = true
        engine.onTrackChanged = { t -> pushRotur(t, engine.playing) }
        engine.onPlayStateChanged = { playing -> pushRotur(engine.current, playing) }
    }

    private var commandLoopRunning = false
    private var roturHookSet = false

    private fun heartbeatLoop() {
        viewModelScope.launch {
            while (true) {
                delay(30_000)
                val user = me ?: continue
                runCatching {
                    repo.heartbeat(
                        repo.deviceHash(),
                        repo.deviceName(),
                        engine.current?.id,
                        engine.position,
                        !engine.playing,
                    )
                }
            }
        }
    }

    /* ── auth ───────────────────────────────────────────────────────────── */

    fun login(server: String, username: String, password: String, register: Boolean, invite: String) {
        if (busy) return
        if (username.isBlank() || password.isBlank()) {
            loginError = "Enter a username and password"
            return
        }
        if (register && password.length < 6) {
            loginError = "Password must be 6+ characters"
            return
        }
        busy = true
        loginError = null
        viewModelScope.launch {
            try {
                api.setBase(server)
                MediaUrls.base = api.baseUrl
                val user = if (register) repo.register(username.trim(), password, invite.trim())
                else repo.login(username.trim(), password)
                me = user
                cacheMe(user)
                loadSettings()
                refreshDownloads()
                route = Route.Home
                stack = emptyList()
                loadRoute()
                heartbeatLoop()
                commandLoop()
                installRoturHook()
            } catch (e: Exception) {
                loginError = e.message ?: "Sign in failed"
            } finally {
                busy = false
            }
        }
    }

    fun logout() {
        val user = me ?: return
        leaveRoom(announce = false)
        viewModelScope.launch {
            engine.pause()
            runCatching { repo.logout() }
            me = null
            store.cachedMe = null
            home = null
            tracks = emptyList()
            albums = emptyList()
            artists = emptyList()
            likes = emptyList()
            playlists = emptyList()
            requests = emptyList()
            searchData = null
            collectionMenu = null
            route = Route.Home
            stack = emptyList()
            toast("Signed out")
        }
    }

    private fun cacheMe(u: Me) {
        store.cachedMe = JSONObject()
            .put("id", u.id)
            .put("username", u.username)
            .put("is_admin", u.isAdmin)
            .put("rotur_id", u.roturId ?: JSONObject.NULL)
            .put("rotur_linked", u.roturLinked)
            .put("email", u.email ?: JSONObject.NULL)
            .toString()
    }

    fun changePassword(old: String, new: String, onDone: () -> Unit) {
        viewModelScope.launch {
            runCatching { repo.changePassword(old, new) }
                .onSuccess {
                    onDone()
                    toast("Password changed")
                }
                .onFailure { toast(it.message ?: "Could not change password") }
        }
    }

    /** The address one-time reset links go to; also shown in Settings → Account. */
    fun setEmail(email: String, onDone: () -> Unit = {}) {
        viewModelScope.launch {
            runCatching { repo.setEmail(email.trim()) }
                .onSuccess { fresh ->
                    me = fresh
                    cacheMe(fresh)
                    onDone()
                    toast("Email saved — reset links go there")
                }
                .onFailure { toast(it.message ?: "Could not save email") }
        }
    }

    fun requestReset(email: String) {
        if (resetBusy) return
        resetBusy = true
        resetNotice = null
        viewModelScope.launch {
            runCatching { repo.requestPasswordReset(email.trim()) }
                .onSuccess {
                    resetNotice = "If that address is on an account, a reset link is on its way. Open it on any device to choose a new password."
                }
                .onFailure { resetNotice = it.message ?: "Could not send the link" }
            resetBusy = false
        }
    }

    /** Spend a reset token or full link pasted from the email. */
    fun resetPassword(tokenOrLink: String, password: String, onDone: () -> Unit) {
        val token = tokenOrLink.substringAfter("token=", tokenOrLink)
            .substringBefore("&").trim()
        if (token.isBlank()) {
            resetNotice = "Paste the link or token from the email"
            return
        }
        if (password.length < 6) {
            resetNotice = "Password must be 6+ characters"
            return
        }
        if (resetBusy) return
        resetBusy = true
        viewModelScope.launch {
            runCatching { repo.resetPassword(token, password) }
                .onSuccess {
                    resetNotice = "Password changed — sign in with the new one"
                    onDone()
                }
                .onFailure { resetNotice = it.message ?: "Could not reset the password" }
            resetBusy = false
        }
    }

    fun clearResetNotice() {
        resetNotice = null
    }

    fun unlinkRotur() {
        viewModelScope.launch {
            runCatching { repo.unlinkRotur() }
                .onSuccess {
                    roturStatus = runCatching { repo.roturStatus() }.getOrNull()
                    toast("Rotur unlinked")
                }
                .onFailure { toast(it.message ?: "Could not unlink") }
        }
    }

    fun unlinkDiscord() {
        viewModelScope.launch {
            runCatching { repo.unlinkDiscord() }
                .onSuccess {
                    discordStatus = runCatching { repo.discordStatus() }.getOrNull()
                    toast("Discord unlinked")
                }
                .onFailure { toast(it.message ?: "Could not unlink Discord") }
        }
    }

    /* ── settings ───────────────────────────────────────────────────────── */

    suspend fun lyrics(id: Int): String =
        runCatching { repo.lyrics(id).first }.getOrDefault("")

    suspend fun loadSettings() {
        runCatching { repo.settings() }.onSuccess { s ->
            // The native client ships with Night + violet. Only let the server
            // palette win once the listener has actually chosen one here.
            val chosen = store.themeChosen
            val nextTheme = if (chosen) s.theme else store.theme
            val nextAccent = if (chosen) s.accent else store.accent
            settings = s.copy(theme = nextTheme, accent = nextAccent)
            mc.settings.value = settings
            theme = nextTheme
            accent = nextAccent
            material = settings.material
            store.theme = nextTheme
            store.accent = nextAccent
        }
    }

    fun setSetting(transform: (Settings) -> Settings) {
        applySettings(transform(settings))
    }

    /* ── local graphics quality ─────────────────────────────────────────── */

    private fun detectedGfx(): Int {
        val app = getApplication<Application>()
        val am = app.getSystemService(Context.ACTIVITY_SERVICE) as? ActivityManager
        val power = app.getSystemService(Context.POWER_SERVICE) as? android.os.PowerManager
        if (power?.isPowerSaveMode == true) return 1
        val lowRam = am?.isLowRamDevice == true
        val memoryClass = am?.memoryClass ?: 256
        return when {
            lowRam || memoryClass < 128 -> 1
            Build.VERSION.SDK_INT >= 33 && memoryClass >= 256 -> 3
            else -> 2
        }
    }

    fun updateGfxLevel(level: Int) {
        gfxAuto = false
        gfxLevel = level.coerceIn(0, 4)
        store.gfxAuto = false
        store.gfxLevel = gfxLevel
    }

    fun updateGfxAuto(on: Boolean) {
        gfxAuto = on
        if (on) {
            gfxLevel = detectedGfx()
            store.gfxLevel = gfxLevel
        }
        store.gfxAuto = on
    }

    private fun pushRotur(t: Track?, playing: Boolean, force: Boolean = false) {
        if (!settings.roturActivity && !force) return
        viewModelScope.launch {
            runCatching {
                repo.pushRoturActivity(if (t != null && playing) t.id else null, engine.position, playing && t != null)
            }.onFailure {
                if (force) toast(it.message ?: "Rotur activity failed")
            }
        }
    }

    /** Re-publish now so flipping the toggle shows up without waiting for a track change. */
    fun setShowRoomUrl(on: Boolean) {
        setSetting { it.copy(showRoomUrl = on) }
        pushRotur(engine.current, settings.roturActivity && engine.playing, force = true)
    }

    fun applySettings(next: Settings) {
        settings = next
        mc.settings.value = next
        theme = next.theme
        accent = next.accent
        material = next.material
        store.theme = next.theme
        store.accent = next.accent
        store.themeChosen = true
        if (next.rememberVolume) store.volume = next.volume
        viewModelScope.launch { runCatching { repo.saveSettings(next) } }
    }

    fun setVolume(v: Float) = engine.setVolume(v)

    /* ── router ─────────────────────────────────────────────────────────── */

    fun navigate(target: Route, push: Boolean = true, reload: Boolean = true) {
        if (push && target != route) stack = stack + route
        route = target
        if (reload) loadRoute()
    }

    fun back() {
        val prev = stack.lastOrNull()
        if (prev != null) {
            stack = stack.dropLast(1)
            route = prev
            loadRoute()
        } else if (route != Route.Home) {
            route = Route.Home
            loadRoute()
        }
    }

    fun loadRoute() {
        val target = route
        viewModelScope.launch {
            try {
                when (target) {
                    Route.Home -> home = repo.home()
                    Route.Search -> {
                        searchData = if (searchQuery.isBlank()) null else repo.search(searchQuery)
                    }
                    Route.Library -> when (libraryTab) {
                        "albums" -> albums = repo.albums()
                        "artists" -> artists = repo.artists()
                        "playlists" -> playlists = repo.playlists()
                        "liked" -> likes = repo.likes()
                        else -> tracks = repo.tracks()
                    }
                    is Route.Album -> {
                        collectionTitle = target.name
                        collectionTracks = repo.album(target.name)
                    }
                    is Route.Artist -> {
                        collectionTitle = target.name
                        collectionTracks = repo.artist(target.name)
                    }
                    Route.Likes -> likes = repo.likes()
                    Route.Playlists -> playlists = repo.playlists()
                    is Route.Playlist -> {
                        val (name, list) = repo.playlist(target.id)
                        playlistName = name
                        playlistTracks = list
                    }
                    Route.Requests -> {
                        val (admin, rows) = repo.requests()
                        requestsAdmin = admin
                        requests = rows
                    }
                    Route.Settings -> {
                        loadSettings()
                        roturStatus = runCatching { repo.roturStatus() }.getOrNull()
                        discordStatus = runCatching { repo.discordStatus() }.getOrNull()
                        devices = runCatching { repo.devices() }.getOrDefault(devices)
                    }
                    Route.Downloads -> {
                        refreshDownloads()
                        if (downloadsTab == "requests") {
                            val (admin, rows) = repo.requests()
                            requestsAdmin = admin
                            requests = rows
                        }
                    }
                    Route.Admin -> {
                        adminStats = repo.adminStats()
                        adminUsers = repo.adminUsers()
                        adminRooms = repo.adminRooms()
                        adminInvites = runCatching { repo.adminInvites() }.getOrDefault(emptyList())
                        runCatching { repo.channels() }.onSuccess { (configured, list) ->
                            channelsConfigured = configured
                            channels = list
                        }
                        adminDevices = runCatching { repo.adminDevices() }.getOrDefault(emptyList())
                        enrich = runCatching { repo.enrichStatus() }.getOrNull()
                        lyricsStatus = runCatching { repo.lyricsStatus() }.getOrNull()
                    }
                    Route.NowPlaying -> Unit
                }
            } catch (e: Exception) {
                toast(e.message ?: "Something went wrong")
            }
        }
    }

    fun refresh() {
        viewModelScope.launch {
            if (me != null) loadSettings()
            loadRoute()
        }
    }

    fun selectLibraryTab(tab: String) {
        libraryTab = tab
        loadRoute()
    }

    fun selectDownloadsTab(tab: String) {
        if (downloadsTab == tab) return
        downloadsTab = tab
        loadRoute()
    }

    fun applySort(value: String) {
        sort = value
    }

    /* ── search ─────────────────────────────────────────────────────────── */

    fun onSearchChange(q: String) {
        searchQuery = q
        if (route != Route.Search) {
            navigate(Route.Search, push = true, reload = false)
        }
        searchJob?.cancel()
        searchJob = viewModelScope.launch {
            delay(260)
            if (searchQuery.isBlank()) {
                searchData = null
            } else {
                runCatching { repo.search(searchQuery) }
                    .onSuccess { if (it == searchData || true) searchData = it }
                    .onFailure { toast(it.message ?: "Search failed") }
            }
        }
    }

    /* ── playback ───────────────────────────────────────────────────────── */

    fun playList(list: List<Track>, index: Int) {
        val playable = if (settings.hideExplicit) list.filter { !it.explicit } else list
        if (playable.isEmpty()) {
            toast("Nothing to play")
            return
        }
        val target = list.getOrNull(index)
        val at = playable.indexOfFirst { it.id == target?.id }.coerceAtLeast(0)
        engine.play(playable, at)
        playerOpen = false
    }

    fun shufflePlay(list: List<Track>) {
        val playable = if (settings.hideExplicit) list.filter { !it.explicit } else list
        if (playable.isEmpty()) {
            toast("Nothing to play")
            return
        }
        engine.play(playable, 0, shuffleStart = true)
    }

    fun queueNext(t: Track) {
        if (engine.queue.isEmpty()) playList(listOf(t), 0)
        else {
            engine.add(t, next = true)
            toast("Playing next")
        }
    }

    fun queueAdd(t: Track) {
        if (engine.queue.isEmpty()) playList(listOf(t), 0)
        else {
            engine.add(t)
            toast("Added to queue")
        }
    }

    fun startRadio(t: Track) {
        viewModelScope.launch {
            runCatching { repo.radio(t.id) }
                .onSuccess {
                    engine.play(listOf(t) + it, 0)
                    toast("Radio started")
                }
                .onFailure { toast(it.message ?: "Could not start radio") }
        }
    }

    fun toggleLike(t: Track) {
        viewModelScope.launch {
            runCatching { repo.like(t.id) }
                .onSuccess { liked ->
                    replaceTrack(t.id) { it.copy(liked = liked) }
                    engine.markLiked(t.id, liked)
                    toast(if (liked) "Liked" else "Removed from liked")
                }
                .onFailure { toast(it.message ?: "Could not update like") }
        }
    }

    fun toggleExplicit(t: Track) {
        viewModelScope.launch {
            runCatching { repo.setExplicit(t.id, !t.explicit) }
                .onSuccess { value ->
                    replaceTrack(t.id) { it.copy(explicit = value) }
                    engine.markExplicit(t.id, value)
                    toast("Updated")
                }
                .onFailure { toast(it.message ?: "Could not update") }
        }
    }

    private fun replaceTrack(id: Int, f: (Track) -> Track) {
        home = home?.let { h ->
            h.copy(sections = h.sections.map { s -> s.copy(tracks = s.tracks.map { if (it.id == id) f(it) else it }) })
        }
        searchData = searchData?.let { d -> d.copy(tracks = d.tracks.map { if (it.id == id) f(it) else it }) }
        tracks = tracks.map { if (it.id == id) f(it) else it }
        likes = likes.map { if (it.id == id) f(it) else it }
        collectionTracks = collectionTracks.map { if (it.id == id) f(it) else it }
        playlistTracks = playlistTracks.map { if (it.id == id) f(it) else it }
    }

    fun openTrackMenu(t: Track, playlistId: Int? = null) {
        menuTrack = t
        menuPlaylistId = playlistId
    }

    fun closeTrackMenu() {
        menuTrack = null
        menuPlaylistId = null
    }

    fun closeInfo() {
        infoTrack = null
    }

    fun closeAddToPlaylist() {
        addToPlaylistTrack = null
    }

    fun openInfo(t: Track) {
        infoTrack = t
    }

    fun openAddToPlaylist(t: Track) {
        addToPlaylistTrack = t
    }

    /* ── playlists ──────────────────────────────────────────────────────── */

    fun createPlaylist(name: String, addTrack: Track? = null) {
        if (name.isBlank()) return
        viewModelScope.launch {
            runCatching {
                val id = repo.createPlaylist(name.trim())
                if (addTrack != null) repo.addToPlaylist(id, addTrack.id)
                id
            }.onSuccess {
                createPlaylistOpen = false
                addToPlaylistTrack = null
                playlists = runCatching { repo.playlists() }.getOrDefault(playlists)
                toast("Playlist created")
            }.onFailure { toast(it.message ?: "Could not create playlist") }
        }
    }

    fun renamePlaylist(id: Int, name: String) {
        if (name.isBlank()) return
        viewModelScope.launch {
            runCatching { repo.renamePlaylist(id, name.trim()) }
                .onSuccess {
                    playlistName = name.trim()
                    playlists = runCatching { repo.playlists() }.getOrDefault(playlists)
                    toast("Renamed")
                }
                .onFailure { toast(it.message ?: "Could not rename") }
        }
    }

    fun deletePlaylist(id: Int) {
        viewModelScope.launch {
            runCatching { repo.deletePlaylist(id) }
                .onSuccess {
                    toast("Playlist deleted")
                    stack = emptyList()
                    navigate(Route.Playlists, push = false)
                }
                .onFailure { toast(it.message ?: "Could not delete") }
        }
    }

    fun addToPlaylist(playlistId: Int, t: Track) {
        viewModelScope.launch {
            runCatching { repo.addToPlaylist(playlistId, t.id) }
                .onSuccess {
                    addToPlaylistTrack = null
                    toast("Added to playlist")
                }
                .onFailure { toast(it.message ?: "Could not add") }
        }
    }

    fun removeFromPlaylist(playlistId: Int, t: Track) {
        viewModelScope.launch {
            runCatching { repo.removeFromPlaylist(playlistId, t.id) }
                .onSuccess {
                    playlistTracks = playlistTracks.filterNot { it.id == t.id }
                    toast("Removed from playlist")
                }
                .onFailure { toast(it.message ?: "Could not remove") }
        }
    }

    /* ── requests ───────────────────────────────────────────────────────── */

    fun addRequest(url: String): Boolean {
        if (url.isBlank() || !url.startsWith("http")) {
            toast("Paste an https YouTube link")
            return false
        }
        viewModelScope.launch {
            runCatching { repo.requestAdd(url.trim()) }
                .onSuccess {
                    toast(if (it == "pending") "Sent for approval" else "Download queued")
                    loadRoute()
                }
                .onFailure { toast(it.message ?: "Request failed") }
        }
        return true
    }

    fun actRequest(id: Int, action: String) {
        viewModelScope.launch {
            runCatching { repo.requestAct(id, action) }
                .onSuccess { loadRoute() }
                .onFailure { toast(it.message ?: "Failed") }
        }
    }

    fun openRequestLog(row: RequestRow) {
        requestLogTitle = row.url
        requestLog = "Loading…"
        viewModelScope.launch {
            requestLog = runCatching { repo.adminRequestLog(row.id) }
                .getOrElse { row.log.ifBlank { it.message ?: "No log output" } }
        }
    }

    fun closeRequestLog() {
        requestLog = null
    }

    /* ── long-press collection actions ─────────────────────────────────── */

    /** Load an album, artist, playlist or the liked songs, then show its menu. */
    fun openCollectionMenu(
        kind: String,
        title: String,
        subtitle: String = "",
        coverId: Int? = null,
        playlistId: Int? = null,
    ) {
        if (collectionMenuLoading) return
        collectionMenuLoading = true
        viewModelScope.launch {
            runCatching {
                when (kind) {
                    "album" -> repo.album(title)
                    "artist" -> repo.artist(title)
                    "playlist" -> repo.playlist(playlistId ?: 0).second
                    "likes" -> repo.likes()
                    else -> emptyList()
                }
            }.onSuccess { list ->
                if (list.isEmpty()) {
                    toast("Nothing here yet")
                } else {
                    collectionMenu = CollectionMenu(kind, title, subtitle, coverId, playlistId, list)
                }
            }.onFailure { toast(it.message ?: "Could not load ${kind}") }
            collectionMenuLoading = false
        }
    }

    fun closeCollectionMenu() {
        collectionMenu = null
    }

    fun playCollection(list: List<Track>) {
        closeCollectionMenu()
        playList(list, 0)
    }

    fun shuffleCollection(list: List<Track>) {
        closeCollectionMenu()
        shufflePlay(list)
    }

    fun queueCollection(list: List<Track>, next: Boolean) {
        val playable = if (settings.hideExplicit) list.filter { !it.explicit } else list
        if (playable.isEmpty()) {
            toast("Nothing to queue")
            closeCollectionMenu()
            return
        }
        if (engine.queue.isEmpty()) {
            playList(playable, 0)
        } else {
            engine.addAll(playable, next)
            toast(
                if (next) "Playing next · ${playable.size} tracks"
                else "Added ${playable.size} tracks to the queue"
            )
        }
        closeCollectionMenu()
    }

    fun bindChannel(
        platform: String,
        channelId: String,
        guildId: String,
        mode: String,
        done: () -> Unit = {},
    ) {
        if (channelId.isBlank()) {
            toast("Channel id required")
            return
        }
        viewModelScope.launch {
            runCatching {
                repo.bindChannel(platform.trim(), channelId.trim(), guildId.trim(), mode)
            }.onSuccess { ch ->
                channels = (channels + ch).distinctBy { it.id }
                done()
                toast("Channel bound")
            }.onFailure { toast(it.message ?: "Could not bind channel") }
        }
    }

    fun unbindChannel(ch: ChannelRef) {
        viewModelScope.launch {
            runCatching { repo.unbindChannel(ch.id) }
                .onSuccess {
                    channels = channels.filterNot { it.id == ch.id }
                    toast("Channel unbound")
                }
                .onFailure { toast(it.message ?: "Could not unbind") }
        }
    }

    fun runEnrich(force: Boolean = false) {
        viewModelScope.launch {
            runCatching {
                repo.enrichStart(force)
                repo.enrichStatus()
            }.onSuccess {
                enrich = it
                toast("Metadata enrichment queued")
            }.onFailure { toast(it.message ?: "Could not start enrichment") }
        }
    }

    fun runLyricsBackfill() {
        viewModelScope.launch {
            runCatching { repo.lyricsStart() }
                .onSuccess {
                    lyricsStatus = it
                    toast(if (it.running) "Lyrics backfill started" else "Nothing to backfill")
                }
                .onFailure { toast(it.message ?: "Could not start lyrics") }
        }
    }

    fun refreshLyricsStatus() {
        viewModelScope.launch {
            lyricsStatus = runCatching { repo.lyricsStatus() }.getOrNull()
            enrich = runCatching { repo.enrichStatus() }.getOrNull()
        }
    }

    fun cancelRequest(row: RequestRow) {
        viewModelScope.launch {
            runCatching { repo.adminCancelRequest(row.id) }
                .onSuccess {
                    toast("Request cancelled")
                    loadRoute()
                }
                .onFailure { toast(it.message ?: "Could not cancel") }
        }
    }

    fun retryRequest(row: RequestRow) {
        viewModelScope.launch {
            runCatching { repo.adminRetryRequest(row.id) }
                .onSuccess {
                    toast("Request queued again")
                    loadRoute()
                }
                .onFailure { toast(it.message ?: "Could not retry") }
        }
    }

    fun deleteRequest(row: RequestRow) {
        viewModelScope.launch {
            runCatching { repo.adminDeleteRequest(row.id) }
                .onSuccess {
                    toast("Request removed")
                    loadRoute()
                }
                .onFailure { toast(it.message ?: "Could not delete") }
        }
    }

    /* ── admin ──────────────────────────────────────────────────────────── */

    fun rescan() {
        viewModelScope.launch {
            runCatching { repo.adminScan() }
                .onSuccess { (t, a) -> toast("$t tracks · $a albums") }
                .onFailure { toast(it.message ?: "Scan failed") }
        }
    }

    fun deleteUser(user: AdminUser) {
        viewModelScope.launch {
            runCatching { repo.adminDeleteUser(user.id) }
                .onSuccess {
                    toast("${user.username} deleted")
                    adminUsers = repo.adminUsers()
                }
                .onFailure { toast(it.message ?: "Could not delete user") }
        }
    }

    fun closeRoom(room: AdminRoom) {
        viewModelScope.launch {
            runCatching { repo.adminCloseRoom(room.code) }
                .onSuccess {
                    adminRooms = repo.adminRooms()
                    toast("Room ended")
                }
                .onFailure { toast(it.message ?: "Could not end room") }
        }
    }

    fun toggleAdmin(user: AdminUser) {
        viewModelScope.launch {
            runCatching { repo.adminSetAdmin(user.id, !user.isAdmin) }
                .onSuccess {
                    toast(if (user.isAdmin) "Admin removed" else "Admin granted")
                    adminUsers = repo.adminUsers()
                }
                .onFailure { toast(it.message ?: "Could not update user") }
        }
    }

    fun createInvite(uses: Int, hours: Int, note: String, done: () -> Unit = {}) {
        viewModelScope.launch {
            runCatching { repo.adminCreateInvite(uses, hours, note) }
                .onSuccess { code ->
                    toast("Code $code created")
                    done()
                    adminInvites = runCatching { repo.adminInvites() }.getOrDefault(adminInvites)
                }
                .onFailure { toast(it.message ?: "Could not create code") }
        }
    }

    fun revokeInvite(invite: InviteCode) {
        viewModelScope.launch {
            runCatching { repo.adminRevokeInvite(invite.id) }
                .onSuccess {
                    toast("${invite.code} revoked")
                    adminInvites = runCatching { repo.adminInvites() }.getOrDefault(adminInvites)
                }
                .onFailure { toast(it.message ?: "Could not revoke code") }
        }
    }

    /** Queue server-side downloads: likes, Faves, or a playlist. */
    fun queueServerDownloads(kind: String, id: Int? = null) {
        viewModelScope.launch {
            runCatching { repo.downloadCollection(kind, id) }
                .onSuccess { n ->
                    toast(if (n > 0) "Queued $n downloads" else "Nothing new to download")
                }
                .onFailure { toast(it.message ?: "Could not queue downloads") }
        }
    }

    fun isThisDevice(d: DeviceRef): Boolean = d.hash == repo.deviceHash()

    fun refreshDevices() {
        viewModelScope.launch {
            devices = runCatching { repo.devices() }.getOrDefault(devices)
        }
    }

    fun activateDevice(d: DeviceRef) {
        viewModelScope.launch {
            runCatching { repo.activateDevice(d.id) }
                .onSuccess {
                    toast("Active device: ${d.name}")
                    refreshDevices()
                }
                .onFailure { toast(it.message ?: "Could not switch device") }
        }
    }

    /* ── listen-along rooms ─────────────────────────────────────────────── */

    fun onRoomJoinCodeChange(value: String) {
        roomJoinCode = value
    }

    /** Open this account's permanent room and publish playback as the host. */
    fun startRoom() {
        viewModelScope.launch {
            runCatching { repo.createRoom() }
                .onSuccess { code ->
                    roomJob?.cancel()
                    roomRole = "host"
                    roomCode = code
                    roomHostName = me?.username.orEmpty()
                    roomState = null
                    toast("Room started — share code $code")
                    roomJob = viewModelScope.launch {
                        while (true) {
                            val t = engine.current
                            runCatching {
                                repo.pushRoomState(code, t?.id, engine.position, engine.playing)
                            }
                            delay(2_000)
                        }
                    }
                }
                .onFailure { toast(it.message ?: "Could not start the room") }
        }
    }

    /** Join a host's room. Accepts a bare code, #room=CODE or a full invite link. */
    fun joinRoom(raw: String = roomJoinCode) {
        val code = raw.trim()
            .substringAfter("#room=", raw.trim())
            .substringBefore("&").trim()
        if (code.isBlank()) {
            toast("Enter the room code")
            return
        }
        viewModelScope.launch {
            runCatching { repo.roomState(code) }
                .onSuccess { state ->
                    if (state.hostId == me?.id) {
                        toast("That is your own room")
                        return@onSuccess
                    }
                    roomJob?.cancel()
                    roomRole = "guest"
                    roomCode = code
                    roomHostName = state.hostName
                    roomState = state
                    roomJoinCode = ""
                    toast("Listening with ${state.hostName}")
                    followRoom(code)
                }
                .onFailure { toast("Could not join: ${it.message ?: "room not found"}") }
        }
    }

    private fun followRoom(code: String) {
        roomJob = viewModelScope.launch {
            while (roomRole == "guest") {
                val state = runCatching { repo.roomState(code) }.getOrNull()
                if (state == null) {
                    toast("Listen-along ended")
                    leaveRoom(announce = false)
                    break
                }
                roomState = state
                roomHostName = state.hostName
                val t = state.track
                if (t != null) {
                    if (engine.current?.id != t.id) engine.play(listOf(t), 0)
                    val drift = state.pos +
                        if (state.playing) (state.serverNow - state.stateTs).coerceAtLeast(0.0) else 0.0
                    if (abs(engine.position - drift) > 1.5) engine.seekTo(drift)
                    if (state.playing && !engine.playing) engine.toggle()
                    if (!state.playing && engine.playing) engine.pause()
                }
                delay(2_000)
            }
        }
    }

    fun leaveRoom(announce: Boolean = true) {
        val wasHost = roomRole == "host"
        val code = roomCode
        roomJob?.cancel()
        roomJob = null
        roomRole = null
        roomCode = ""
        roomHostName = ""
        roomState = null
        // A guest follows the host; leaving their room should stop the music,
        // same as the web client. The host keeps playing.
        if (!wasHost) engine.pause()
        if (wasHost && code.isNotBlank()) {
            viewModelScope.launch { runCatching { repo.closeRoom(code) } }
        }
        if (announce) toast(if (wasHost) "Room ended" else "Left the listen-along")
    }

    fun roomLink(): String =
        if (roomCode.isBlank()) "" else "${api.baseUrl}/#room=$roomCode"

    /** Pause/play/seek another device of this account. */
    fun remote(device: DeviceRef, action: String) {
        viewModelScope.launch {
            runCatching {
                repo.sendCommand(
                    action,
                    device.hash,
                    engine.current?.id,
                    engine.position,
                    repo.deviceName(),
                )
            }.onSuccess {
                toast("${action.replaceFirstChar { it.uppercase() }} sent to ${device.name}")
            }.onFailure { toast(it.message ?: "Could not reach ${device.name}") }
        }
    }

    fun setRoturActivity(on: Boolean) {
        setSetting { it.copy(roturActivity = on) }
        pushRotur(engine.current, on && engine.playing, force = true)
    }

    /* ── offline downloads ──────────────────────────────────────────────── */

    fun refreshDownloads() {
        downloads = mc.downloads.entries()
        downloadBytes = mc.downloads.bytes()
    }

    fun isDownloaded(id: Int): Boolean = mc.downloads.isDownloaded(id)

    fun downloadTrack(t: Track) {
        if (mc.downloads.isDownloaded(t.id)) {
            toast("Already available offline")
            return
        }
        toast("Downloading ${t.title}…")
        viewModelScope.launch {
            val ok = runCatching { mc.downloads.download(t) }.getOrDefault(false)
            refreshDownloads()
            toast(if (ok) "Available offline" else "Download failed")
        }
    }

    fun removeDownload(id: Int) {
        mc.downloads.remove(id)
        refreshDownloads()
        toast("Removed from offline")
    }

    fun clearDownloads() {
        val n = mc.downloads.clear()
        refreshDownloads()
        toast(if (n > 0) "Cleared $n downloads" else "Nothing to clear")
    }

    fun downloadAll(tracks: List<Track>) {
        val todo = tracks.filter { !mc.downloads.isDownloaded(it.id) }
        if (todo.isEmpty()) {
            toast("Already available offline")
            return
        }
        toast("Downloading ${todo.size} tracks…")
        viewModelScope.launch {
            var done = 0
            for (t in todo) {
                if (runCatching { mc.downloads.download(t) }.getOrDefault(false)) done += 1
            }
            refreshDownloads()
            toast(if (done > 0) "$done of ${todo.size} tracks offline" else "Download failed")
        }
    }

    fun playDownloaded(d: DownloadEntry) {
        val t = Track(
            id = d.id, title = d.title, artist = d.artist, album = d.album,
            trackNo = 0, genre = "", year = "", duration = d.duration,
            liked = false, explicit = false, ytId = null, ytLikes = null,
            ytViews = null, ytChannel = null, ytDate = null, added = d.added.toDouble(),
        )
        engine.play(listOf(t), 0)
    }

    /* ── misc ───────────────────────────────────────────────────────────── */

    fun toast(text: String) {
        toastText = text
    }

    fun clearToast() {
        toastText = null
    }

    /* ── GitHub update flow ─────────────────────────────────────────────── */

    fun checkForUpdates(manual: Boolean = false) {
        if (updateChecking) return
        updateChecking = true
        viewModelScope.launch {
            runCatching { UpdateChecker.latest() }
                .onSuccess { latest ->
                    val latestVersion = latest?.version
                    val newer = latest?.isNewerThan(BuildConfig.VERSION_NAME) == true
                    val skipped = latestVersion != null && store.skippedUpdateVersion == latestVersion
                    if (latest != null && newer && (manual || !skipped)) {
                        updateInfo = latest
                        updateDialogOpen = true
                        if (manual) toast("mcmusic ${latest.version} is available")
                    } else {
                        updateInfo = null
                        if (manual) {
                            toast(
                                when {
                                    latestVersion == null -> "No GitHub release found"
                                    newer && skipped -> "You skipped $latestVersion — the next release will still be offered"
                                    else -> "You're on the latest version"
                                }
                            )
                        }
                    }
                }
                .onFailure { if (manual) toast(it.message ?: "Could not check for updates") }
            updateChecking = false
        }
    }

    fun dismissUpdate() {
        if (!updateDownloading) updateDialogOpen = false
    }

    /** Hide this release from automatic prompts, but still offer the next one. */
    fun skipUpdate() {
        if (updateDownloading) return
        val version = updateInfo?.version ?: return
        store.skippedUpdateVersion = version
        updateInfo = null
        updateDialogOpen = false
        toast("Skipped $version — the next release will still be offered")
    }

    fun installUpdate() {
        val info = updateInfo ?: return
        if (updateDownloading) return
        val context = getApplication<Application>()

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O &&
            !context.packageManager.canRequestPackageInstalls()
        ) {
            toast("Allow installs for mcmusic, then tap Update again")
            runCatching {
                context.startActivity(
                    Intent(
                        android.provider.Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                        Uri.parse("package:${context.packageName}"),
                    ).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                )
            }
            return
        }

        updateDownloading = true
        updateVerifying = false
        updateProgress = 0
        viewModelScope.launch {
            runCatching {
                withContext(Dispatchers.IO) {
                    if (!info.url.startsWith("https://")) {
                        throw IOException("Update URL is not secure")
                    }
                    val dir = File(context.cacheDir, "updates").apply { mkdirs() }
                    // Remove old downloads so a failed retry cannot install a stale APK.
                    dir.listFiles()?.forEach { it.delete() }
                    val apk = File(dir, "mcmusic-${info.version}.apk")
                    val temp = File(dir, "${apk.name}.part")
                    try {
                        val request = Request.Builder()
                            .url(info.url)
                            .header("User-Agent", "mcmusic-android")
                            .build()
                        UpdateChecker.client.newCall(request).execute().use { response ->
                            if (!response.isSuccessful) {
                                throw IOException("Download failed (${response.code})")
                            }
                            val body = response.body ?: throw IOException("Download failed")
                            val total = if (body.contentLength() > 0) body.contentLength() else info.size
                            val digest = MessageDigest.getInstance("SHA-256")
                            var done = 0L
                            body.byteStream().use { input ->
                                temp.outputStream().use { output ->
                                    val buffer = ByteArray(16 * 1024)
                                    while (true) {
                                        val n = input.read(buffer)
                                        if (n <= 0) break
                                        output.write(buffer, 0, n)
                                        digest.update(buffer, 0, n)
                                        done += n
                                        if (total > 0) {
                                            updateProgress = ((done * 100) / total).toInt().coerceIn(0, 100)
                                        }
                                    }
                                }
                            }
                            if (info.size > 0 && done != info.size) {
                                throw IOException("Download incomplete — expected ${info.size} bytes, got $done")
                            }
                            updateProgress = 100
                            updateVerifying = true
                            val actual = digest.digest().joinToString("") {
                                "%02x".format(it.toInt() and 0xff)
                            }
                            if (!info.checksum.isNullOrBlank() &&
                                !actual.equals(info.checksum, ignoreCase = true)
                            ) {
                                throw IOException("Download checksum did not match the release")
                            }
                            val archive = context.packageManager
                                .getPackageArchiveInfo(temp.absolutePath, 0)
                            if (archive?.packageName != context.packageName) {
                                throw IOException("Downloaded file is not a mcmusic APK")
                            }
                        }
                        if (!temp.renameTo(apk)) {
                            temp.copyTo(apk, overwrite = true)
                            temp.delete()
                        }
                        apk
                    } catch (t: Throwable) {
                        temp.delete()
                        throw t
                    }
                }
            }.onSuccess { apk ->
                store.skippedUpdateVersion = null
                updateDownloading = false
                updateVerifying = false
                updateProgress = 100
                updateDialogOpen = false
                val uri = FileProvider.getUriForFile(
                    context,
                    "${context.packageName}.updates",
                    apk,
                )
                val install = Intent(Intent.ACTION_VIEW).apply {
                    setDataAndType(uri, "application/vnd.android.package-archive")
                    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_ACTIVITY_NEW_TASK)
                }
                runCatching { context.startActivity(install) }
                    .onFailure { toast("Open the downloaded APK from Files to install") }
            }.onFailure { error ->
                updateDownloading = false
                updateVerifying = false
                updateProgress = 0
                toast(error.message ?: "Could not download the update")
            }
        }
    }

    fun playAlbum(name: String) {
        viewModelScope.launch {
            runCatching { repo.album(name) }
                .onSuccess { playList(it, 0) }
                .onFailure { toast(it.message ?: "Could not load album") }
        }
    }

    fun playArtist(name: String) {
        viewModelScope.launch {
            runCatching { repo.artist(name) }
                .onSuccess { playList(it, 0) }
                .onFailure { toast(it.message ?: "Could not load artist") }
        }
    }

    fun playPlaylist(id: Int) {
        viewModelScope.launch {
            runCatching { repo.playlist(id) }
                .onSuccess { (_, tracks) -> playList(tracks, 0) }
                .onFailure { toast(it.message ?: "Could not load playlist") }
        }
    }

    fun playAt(index: Int) {
        val list = when (route) {
            is Route.Album, is Route.Artist -> collectionTracks
            Route.Likes -> likes
            is Route.Playlist -> playlistTracks
            else -> tracks
        }
        playList(list, index)
    }
}
