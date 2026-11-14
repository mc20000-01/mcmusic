package dev.mcmusic.app.data

import org.json.JSONArray
import org.json.JSONObject
import java.net.URLEncoder
import java.util.TimeZone

/**
 * Every endpoint used by the native client, mirroring the server's routes package.
 */
class Repo(private val api: Api, private val store: SessionStore) {

    /* ── auth ──────────────────────────────────────────────────────────── */
    suspend fun me(): Me = Me.from(api.get("me"))

    suspend fun login(username: String, password: String): Me =
        Me.from(api.post("login", JSONObject().put("username", username).put("password", password)))

    suspend fun register(username: String, password: String, invite: String): Me =
        Me.from(
            api.post(
                "register",
                JSONObject().put("username", username).put("password", password).put("invite", invite)
            )
        )

    suspend fun logout() {
        runCatching { api.post("logout") }
        store.clearSession()
    }

    suspend fun changePassword(old: String, new: String) {
        api.post("password", JSONObject().put("old", old).put("new", new))
    }

    /** Attach or change the address one-time reset links are sent to. */
    suspend fun setEmail(email: String): Me =
        Me.from(api.post("auth/email", JSONObject().put("email", email)))

    /** Ask the server to mail a reset link. The reply is identical for unknown addresses. */
    suspend fun requestPasswordReset(email: String): Boolean =
        api.post("auth/reset/request", JSONObject().put("email", email)).optBoolean("mail")

    suspend fun resetPassword(token: String, password: String) {
        api.post("auth/reset/confirm", JSONObject().put("token", token).put("password", password))
    }

    suspend fun roturStatus(): JSONObject = api.get("auth/rotur/status")

    suspend fun unlinkRotur() {
        api.post("auth/rotur/unlink")
    }

    /** Publish "Listening to …" as the Rotur status (needs account:profile). */
    suspend fun pushRoturActivity(status: String): Boolean =
        api.post("auth/rotur/live", JSONObject().put("status", status)).optBoolean("ok")

    /** Ask the server to download liked songs, Faves, or one playlist. */
    suspend fun downloadCollection(kind: String, id: Int? = null): Int {
        val body = JSONObject().put("kind", kind)
        if (id != null) body.put("id", id)
        return api.post("download/collection", body).optInt("queued")
    }

    /* ── settings ──────────────────────────────────────────────────────── */
    suspend fun settings(): Settings = Settings.from(api.get("settings"))

    suspend fun saveSettings(s: Settings) {
        api.put("settings", s.toJson())
    }

    /* ── library ───────────────────────────────────────────────────────── */
    suspend fun home(): HomeData {
        val o = api.get("home")
        val sections = ArrayList<Section>()
        val arr = o.array("sections")
        for (i in 0 until arr.length()) {
            val s = arr.optJSONObject(i) ?: continue
            sections.add(Section(s.optString("title", ""), Track.list(s.array("tracks"))))
        }
        return HomeData(sections, AlbumRef.list(o.array("albums")))
    }

    suspend fun tracks(query: String = "", limit: Int = 2000): List<Track> {
        val q = HashMap<String, String>()
        q["limit"] = limit.toString()
        if (query.isNotBlank()) q["q"] = query
        return Track.list(api.get("tracks", q).array("tracks"))
    }

    suspend fun search(query: String): SearchData {
        val o = api.get("search", mapOf("q" to query))
        return SearchData(
            Track.list(o.array("tracks")),
            AlbumRef.list(o.array("albums")),
            ArtistRef.list(o.array("artists")),
        )
    }

    suspend fun albums(): List<AlbumRef> = AlbumRef.list(api.get("albums").array("albums"))

    suspend fun album(name: String): List<Track> =
        Track.list(api.get("album", mapOf("name" to name)).array("tracks"))

    suspend fun artists(): List<ArtistRef> = ArtistRef.list(api.get("artists").array("artists"))

    suspend fun artist(name: String): List<Track> =
        Track.list(api.get("artist", mapOf("name" to name)).array("tracks"))

    suspend fun likes(): List<Track> = Track.list(api.get("likes").array("tracks"))

    suspend fun like(trackId: Int): Boolean =
        api.post("like/$trackId").optBoolean("liked")

    suspend fun reportPlay(trackId: Int, completed: Boolean) {
        api.post("plays", JSONObject().put("track_id", trackId).put("completed", completed))
    }

    suspend fun setExplicit(trackId: Int, explicit: Boolean): Boolean =
        api.patch("tracks/$trackId", JSONObject().put("explicit", explicit))
            .optBoolean("explicit")

    suspend fun radio(trackId: Int): List<Track> =
        Track.list(api.get("radio/$trackId").array("tracks"))

    /* ── playlists ─────────────────────────────────────────────────────── */
    suspend fun playlists(): List<PlaylistRef> = PlaylistRef.list(api.get("playlists").array("playlists"))

    suspend fun playlist(id: Int): Pair<String, List<Track>> {
        val o = api.get("playlists/$id")
        return o.optString("name", "Playlist") to Track.list(o.array("tracks"))
    }

    suspend fun createPlaylist(name: String): Int =
        api.post("playlists", JSONObject().put("name", name)).optInt("id")

    suspend fun renamePlaylist(id: Int, name: String) {
        api.patch("playlists/$id", JSONObject().put("name", name))
    }

    suspend fun deletePlaylist(id: Int) {
        api.delete("playlists/$id")
    }

    suspend fun addToPlaylist(playlistId: Int, trackId: Int) {
        api.post("playlists/$playlistId/tracks", JSONObject().put("track_id", trackId))
    }

    suspend fun removeFromPlaylist(playlistId: Int, trackId: Int) {
        api.delete("playlists/$playlistId/tracks/$trackId")
    }

    /* ── requests ──────────────────────────────────────────────────────── */
    suspend fun requests(): Pair<Boolean, List<RequestRow>> {
        val o = api.get("requests")
        val arr = o.array("requests")
        val rows = (0 until arr.length()).mapNotNull { i ->
            arr.optJSONObject(i)?.let { r ->
                RequestRow(
                    id = r.optInt("id"),
                    url = r.optString("url"),
                    status = r.optString("status"),
                    created = r.optDouble("created"),
                    log = r.optString("log"),
                    username = r.stringOrNull("username"),
                )
            }
        }
        return o.optBoolean("is_admin") to rows
    }

    suspend fun requestAdd(url: String): String =
        api.post("requests", JSONObject().put("url", url)).optString("status")

    suspend fun requestAct(id: Int, action: String) {
        api.post("requests/$id/$action")
    }

    /* ── control channels + admin extras ──────────────────────────────── */
    suspend fun channels(): Pair<Boolean, List<ChannelRef>> {
        val o = api.get("channels")
        return o.optBoolean("configured") to ChannelRef.list(o.array("channels"))
    }

    suspend fun bindChannel(
        platform: String,
        channelId: String,
        guildId: String,
        mode: String,
    ): ChannelRef = ChannelRef.from(
        api.post(
            "channels",
            JSONObject()
                .put("platform", platform)
                .put("channel_id", channelId)
                .put("guild_id", guildId)
                .put("mode", mode),
        ).getJSONObject("channel")
    )

    suspend fun unbindChannel(id: Int) {
        api.delete("channels/$id")
    }

    suspend fun adminDevices(): List<AdminDeviceRef> {
        val arr = api.get("admin/devices").array("devices")
        return (0 until arr.length()).mapNotNull { i ->
            arr.optJSONObject(i)?.let(AdminDeviceRef::from)
        }
    }

    suspend fun enrichStatus(): EnrichStatus {
        val o = api.get("admin/enrich")
        return EnrichStatus(
            total = o.optInt("total"),
            linked = o.optInt("linked"),
            fetched = o.optInt("fetched"),
        )
    }

    suspend fun enrichStart(force: Boolean = false) {
        api.post("admin/enrich", JSONObject().put("force", force))
    }

    suspend fun lyricsStatus(): LyricsStatus = LyricsStatus.from(api.get("admin/lyrics"))

    suspend fun lyricsStart(): LyricsStatus = LyricsStatus.from(api.post("admin/lyrics"))

    /* ── listen-along rooms ────────────────────────────────────────────── */
    suspend fun createRoom(): String = api.post("rooms", JSONObject()).optString("code")

    suspend fun roomState(code: String): RoomState =
        RoomState.from(api.get("rooms/${encoded(code)}"))

    suspend fun pushRoomState(code: String, trackId: Int?, pos: Double, playing: Boolean) {
        api.post(
            "rooms/${encoded(code)}/state",
            JSONObject()
                .put("track_id", trackId ?: JSONObject.NULL)
                .put("pos", pos)
                .put("playing", playing),
        )
    }

    suspend fun closeRoom(code: String) {
        api.delete("rooms/${encoded(code)}")
    }

    /* ── playback registry ─────────────────────────────────────────────── */
    suspend fun publishPlayback(
        trackId: Int?,
        position: Double,
        duration: Double,
        playing: Boolean,
        queue: List<Int>,
    ) {
        val body = JSONObject()
            .put("track_id", trackId ?: JSONObject.NULL)
            .put("position", position)
            .put("duration", duration)
            .put("playing", playing)
            .put("queue", JSONArray(queue))
            .put("device", deviceHash())
        api.post("playback", body)
    }

    suspend fun lyrics(id: Int): Pair<String, String> {
        val o = api.get("tracks/$id/lyrics")
        return o.optString("lyrics") to o.optString("source")
    }

    suspend fun pullPlayback(device: String? = null): JSONObject =
        api.get(if (device.isNullOrBlank()) "playback" else "playback?device=${encoded(device)}")

    suspend fun devices(): List<DeviceRef> = DeviceRef.list(api.get("devices").array("devices"))

    suspend fun activateDevice(id: Int) {
        api.post("devices/$id/activate")
    }

    /** One-shot remote control aimed at another device of this account. */
    suspend fun sendCommand(
        action: String,
        target: String?,
        trackId: Int? = null,
        position: Double = 0.0,
        originName: String = "",
    ): Boolean = api.post(
        "playback/command",
        JSONObject()
            .put("action", action)
            .put("target", target ?: JSONObject.NULL)
            .put("origin", deviceHash())
            .put("origin_name", originName)
            .put("track_id", trackId ?: JSONObject.NULL)
            .put("position", position),
    ).optBoolean("ok")

    suspend fun playbackCommand(action: String, trackId: Int?, index: Int?) {
        api.post(
            "playback/command",
            JSONObject().put("action", action)
                .put("track_id", trackId ?: JSONObject.NULL)
                .put("index", index ?: JSONObject.NULL)
        )
    }

    /* ── devices ───────────────────────────────────────────────────────── */
    suspend fun heartbeat(
        deviceHash: String,
        name: String,
        trackId: Int?,
        position: Double,
        paused: Boolean,
    ) {
        api.post(
            "devices/heartbeat",
            JSONObject()
                .put("device_hash", deviceHash)
                .put("name", name)
                .put("track_id", trackId ?: JSONObject.NULL)
                .put("position", position)
                .put("paused", paused)
        )
    }

    /* ── admin ─────────────────────────────────────────────────────────── */
    suspend fun adminStats(): AdminStats {
        val o = api.get("admin/stats")
        return AdminStats(
            users = o.optInt("users"),
            admins = o.optInt("admins"),
            tracks = o.optInt("tracks"),
            albums = o.optInt("albums"),
            playlists = o.optInt("playlists"),
            plays = o.optInt("plays"),
            queue = o.optInt("queue"),
            rooms = o.optInt("rooms"),
            musicBytes = o.optLong("music_bytes"),
            diskFree = o.optLong("disk_free"),
            diskTotal = o.optLong("disk_total"),
            uptime = o.optDouble("uptime"),
        )
    }

    suspend fun adminUsers(): List<AdminUser> {
        val arr = api.get("admin/users").array("users")
        return (0 until arr.length()).mapNotNull { i ->
            arr.optJSONObject(i)?.let {
                AdminUser(
                    id = it.optInt("id"),
                    username = it.optString("username"),
                    isAdmin = it.optBoolean("is_admin"),
                    plays = it.optInt("plays"),
                    likes = it.optInt("likes"),
                    playlists = it.optInt("playlists"),
                    requests = it.optInt("requests"),
                )
            }
        }
    }

    suspend fun adminSetAdmin(id: Int, isAdmin: Boolean) {
        api.post("admin/users/$id/admin", JSONObject().put("is_admin", isAdmin))
    }

    suspend fun adminDeleteUser(id: Int) {
        api.delete("admin/users/$id")
    }

    suspend fun adminRooms(): List<AdminRoom> {
        val arr = api.get("admin/rooms").array("rooms")
        return (0 until arr.length()).mapNotNull { i -> arr.optJSONObject(i)?.let(AdminRoom::from) }
    }

    suspend fun adminCloseRoom(code: String) {
        api.delete("admin/rooms/$code")
    }

    suspend fun adminScan(): Pair<Int, Int> {
        val o = api.post("admin/scan")
        return o.optInt("tracks") to o.optInt("albums")
    }

    suspend fun adminCancelRequest(id: Int) {
        api.post("admin/requests/$id/cancel")
    }

    suspend fun adminRetryRequest(id: Int) {
        api.post("admin/requests/$id/retry")
    }

    suspend fun adminDeleteRequest(id: Int) {
        api.delete("admin/requests/$id")
    }

    suspend fun adminRequestLog(id: Int): String =
        api.get("admin/requests/$id/log").optString("log")

    suspend fun adminInvites(): List<InviteCode> {
        val arr = api.get("admin/invite-codes").array("codes")
        return (0 until arr.length()).mapNotNull { i -> arr.optJSONObject(i)?.let(InviteCode::from) }
    }

    suspend fun adminCreateInvite(uses: Int, hours: Int, note: String): String =
        api.post(
            "admin/invite-codes",
            JSONObject().put("uses", uses).put("hours", hours).put("note", note),
        ).optString("code")

    suspend fun adminRevokeInvite(id: Int) {
        api.delete("admin/invite-codes/$id")
    }

    /* ── misc ──────────────────────────────────────────────────────────── */
    fun deviceHash(): String {
        store.deviceHash?.let { return it }
        val seed = "${android.os.Build.MANUFACTURER}-${android.os.Build.MODEL}-${android.os.Build.DEVICE}" +
            "-${java.util.Locale.getDefault()}" +
            "-${TimeZone.getDefault().id}"
        val hash = Integer.toHexString(seed.hashCode()) + Integer.toHexString(seed.reversed().hashCode())
        store.deviceHash = hash
        return hash
    }

    fun deviceName(): String {
        val m = android.os.Build.MANUFACTURER
        val model = android.os.Build.MODEL
        return if (model.lowercase().startsWith(m.lowercase())) model else "$m $model"
    }

    fun encoded(name: String): String = URLEncoder.encode(name, "UTF-8")
}

data class Settings(
    val theme: String = "ink",
    val accent: String = "#a06bff",
    val density: String = "comfy",
    val covers: Boolean = true,
    val autoplay: Boolean = true,
    val hideExplicit: Boolean = false,
    val privateSession: Boolean = false,
    val ytStats: Boolean = true,
    val rememberVolume: Boolean = true,
    val volume: Float = 0.8f,
    val prefetch: Boolean = true,
    val offlineAudio: Boolean = true,
    val roturActivity: Boolean = false,
    val showRoomUrl: Boolean = false,
    /** Server-provided: this account's permanent listen-along link. */
    val roomUrl: String = "",
) {
    fun toJson(): JSONObject = JSONObject()
        .put("theme", theme)
        .put("accent", accent)
        .put("density", density)
        .put("covers", covers)
        .put("autoplay", autoplay)
        .put("hide_explicit", hideExplicit)
        .put("private", privateSession)
        .put("yt_stats", ytStats)
        .put("remember_volume", rememberVolume)
        .put("volume", volume.toDouble())
        .put("prefetch", prefetch)
        .put("offline_audio", offlineAudio)
        .put("rotur_activity", roturActivity)
        .put("show_room_url", showRoomUrl)

    companion object {
        fun from(o: JSONObject) = Settings(
            theme = o.optString("theme", "ink"),
            accent = o.optString("accent", "#a06bff"),
            density = o.optString("density", "comfy"),
            covers = o.optBoolean("covers", true),
            autoplay = o.optBoolean("autoplay", true),
            hideExplicit = o.optBoolean("hide_explicit", false),
            privateSession = o.optBoolean("private", false),
            ytStats = o.optBoolean("yt_stats", true),
            rememberVolume = o.optBoolean("remember_volume", true),
            volume = o.optDouble("volume", 0.8).toFloat(),
            prefetch = o.optBoolean("prefetch", true),
            offlineAudio = o.optBoolean("offline_audio", true),
            roturActivity = o.optBoolean("rotur_activity", false),
            showRoomUrl = o.optBoolean("show_room_url", false),
            roomUrl = o.optString("room_url", ""),
        )
    }
}
