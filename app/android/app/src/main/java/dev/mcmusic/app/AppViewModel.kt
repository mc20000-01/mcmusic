package dev.mcmusic.app

import android.app.Application
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import dev.mcmusic.app.data.AdminRoom
import dev.mcmusic.app.data.AdminStats
import dev.mcmusic.app.data.AdminUser
import dev.mcmusic.app.data.AlbumRef
import dev.mcmusic.app.data.ArtistRef
import dev.mcmusic.app.data.DownloadEntry
import dev.mcmusic.app.data.HomeData
import dev.mcmusic.app.data.Me
import dev.mcmusic.app.data.PlaylistRef
import dev.mcmusic.app.data.RequestRow
import dev.mcmusic.app.data.SearchData
import dev.mcmusic.app.data.DeviceRef
import dev.mcmusic.app.data.InviteCode
import dev.mcmusic.app.data.Settings
import dev.mcmusic.app.data.Track
import dev.mcmusic.app.ui.MediaUrls
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import org.json.JSONObject

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

    /* ── appearance ─────────────────────────────────────────────────────── */
    var settings by mutableStateOf(mc.settings.value)
        private set
    var theme by mutableStateOf(store.theme)
        private set
    var accent by mutableStateOf(store.accent)
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
                    store.cachedMe = """
                        {"id":${fresh.id},"username":"${fresh.username}","is_admin":${fresh.isAdmin},
                         "rotur_id":${fresh.roturId?.let { "\"$it\"" } ?: "null"},"rotur_linked":${fresh.roturLinked}}
                    """.trimIndent()
                }.onFailure {
                    me = null
                    store.cachedMe = null
                }
            }
            checked = true
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
        engine.onTrackChanged = { t ->
            if (t != null && settings.roturActivity) {
                viewModelScope.launch {
                    runCatching { repo.pushRoturActivity(roturStatus(t)) }
                }
            }
        }
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
                store.cachedMe = JSONObject()
                    .put("id", user.id)
                    .put("username", user.username)
                    .put("is_admin", user.isAdmin)
                    .put("rotur_id", user.roturId ?: JSONObject.NULL)
                    .put("rotur_linked", user.roturLinked)
                    .toString()
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
            route = Route.Home
            stack = emptyList()
            toast("Signed out")
        }
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

    /* ── settings ───────────────────────────────────────────────────────── */

    suspend fun lyrics(id: Int): String =
        runCatching { repo.lyrics(id).first }.getOrDefault("")

    suspend fun loadSettings() {
        runCatching { repo.settings() }.onSuccess { s ->
            // The native client ships with ink + violet. Only let the server
            // palette win once the listener has actually chosen one here.
            val chosen = store.themeChosen
            val nextTheme = if (chosen) s.theme else store.theme
            val nextAccent = if (chosen) s.accent else store.accent
            settings = s.copy(theme = nextTheme, accent = nextAccent)
            mc.settings.value = settings
            theme = nextTheme
            accent = nextAccent
            store.theme = nextTheme
            store.accent = nextAccent
        }
    }

    fun setSetting(transform: (Settings) -> Settings) {
        applySettings(transform(settings))
    }

    /** What goes in the Rotur status, with the room invite when it is enabled. */
    private fun roturStatus(t: Track): String {
        val head = "Listening to ${t.title}" + if (t.artist.isNotBlank()) " — ${t.artist}" else ""
        val room = if (settings.showRoomUrl && settings.roomUrl.isNotBlank()) " · ${settings.roomUrl}" else ""
        return (head + room).take(128)
    }

    /** Re-publish now so flipping the toggle shows up without waiting for a track change. */
    fun setShowRoomUrl(on: Boolean) {
        setSetting { it.copy(showRoomUrl = on) }
        val t = engine.current ?: return
        if (!settings.roturActivity) return
        viewModelScope.launch { runCatching { repo.pushRoturActivity(roturStatus(t)) } }
    }

    fun applySettings(next: Settings) {
        settings = next
        mc.settings.value = next
        theme = next.theme
        accent = next.accent
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
        if (!on) return
        val t = engine.current ?: return
        viewModelScope.launch {
            runCatching {
                repo.pushRoturActivity(
                    "Listening to ${t.title}${if (t.artist.isNotBlank()) " — ${t.artist}" else ""}"
                )
            }.onFailure { toast("Rotur: ${it.message}") }
        }
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
