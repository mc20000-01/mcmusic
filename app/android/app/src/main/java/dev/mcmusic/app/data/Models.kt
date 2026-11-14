package dev.mcmusic.app.data

import org.json.JSONArray
import org.json.JSONObject

/* ── tolerant JSON helpers ─────────────────────────────────────────────── */
fun JSONObject.stringOrNull(key: String): String? =
    if (!has(key) || isNull(key)) null else optString(key).ifBlank { null }

fun JSONObject.longOrNull(key: String): Long? =
    if (!has(key) || isNull(key)) null else optLong(key)

fun JSONObject.intOrNull(key: String): Int? =
    if (!has(key) || isNull(key)) null else optInt(key)

fun JSONObject.array(key: String): JSONArray = optJSONArray(key) ?: JSONArray()

/* ── models (mirroring database.py track_dict and route payloads) ──────── */

data class Track(
    val id: Int,
    val title: String,
    val artist: String,
    val album: String,
    val trackNo: Int,
    val genre: String,
    val year: String,
    val duration: Double,
    val liked: Boolean,
    val explicit: Boolean,
    val ytId: String?,
    val ytLikes: Long?,
    val ytViews: Long?,
    val ytChannel: String?,
    val ytDate: String?,
    val added: Double,
    val artists: List<String> = emptyList(),
) {
    val initials: String
        get() = (title.firstOrNull()?.uppercase() ?: "?")

    companion object {
        fun from(o: JSONObject) = Track(
            id = o.optInt("id"),
            title = o.optString("title", "Unknown"),
            artist = o.optString("artist", "Unknown Artist"),
            album = o.optString("album", ""),
            trackNo = o.optInt("track_no"),
            genre = o.optString("genre", ""),
            year = o.optString("year", ""),
            duration = o.optDouble("duration", 0.0),
            liked = o.optBoolean("liked"),
            explicit = o.optBoolean("explicit"),
            ytId = o.stringOrNull("yt_id"),
            ytLikes = o.longOrNull("yt_likes"),
            ytViews = o.longOrNull("yt_views"),
            ytChannel = o.stringOrNull("yt_channel"),
            ytDate = o.stringOrNull("yt_date"),
            added = o.optDouble("added", 0.0),
            artists = o.optJSONArray("artists")?.let { arr ->
                (0 until arr.length()).mapNotNull { i ->
                    arr.optString(i).ifBlank { null }
                }
            } ?: emptyList(),
        )

        fun list(arr: JSONArray): List<Track> =
            (0 until arr.length()).mapNotNull { i -> arr.optJSONObject(i)?.let(::from) }
    }
}

data class AlbumRef(
    val album: String,
    val artist: String,
    val n: Int,
    val coverId: Int?,
) {
    companion object {
        fun from(o: JSONObject) = AlbumRef(
            album = o.optString("album", "Unknown Album"),
            artist = o.optString("artist", ""),
            n = o.optInt("n"),
            coverId = o.intOrNull("cover_id"),
        )

        fun list(arr: JSONArray): List<AlbumRef> =
            (0 until arr.length()).mapNotNull { i -> arr.optJSONObject(i)?.let(::from) }
    }
}

data class ArtistRef(
    val artist: String,
    val n: Int,
    val albums: Int,
    val coverId: Int?,
) {
    companion object {
        fun from(o: JSONObject) = ArtistRef(
            artist = o.optString("artist", "Unknown Artist"),
            n = o.optInt("n"),
            albums = o.optInt("albums"),
            coverId = o.intOrNull("cover_id"),
        )

        fun list(arr: JSONArray): List<ArtistRef> =
            (0 until arr.length()).mapNotNull { i -> arr.optJSONObject(i)?.let(::from) }
    }
}

data class PlaylistRef(
    val id: Int,
    val name: String,
    val n: Int,
    val coverId: Int?,
) {
    companion object {
        fun from(o: JSONObject) = PlaylistRef(
            id = o.optInt("id"),
            name = o.optString("name", "Playlist"),
            n = o.optInt("n"),
            coverId = o.intOrNull("cover_id"),
        )

        fun list(arr: JSONArray): List<PlaylistRef> =
            (0 until arr.length()).mapNotNull { i -> arr.optJSONObject(i)?.let(::from) }
    }
}

data class Section(val title: String, val tracks: List<Track>)

data class HomeData(
    val sections: List<Section>,
    val albums: List<AlbumRef>,
)

data class SearchData(
    val tracks: List<Track>,
    val albums: List<AlbumRef>,
    val artists: List<ArtistRef>,
)

data class Me(
    val id: Int,
    val username: String,
    val isAdmin: Boolean,
    val roturId: String?,
    val roturLinked: Boolean,
    val email: String? = null,
) {
    companion object {
        fun from(o: JSONObject) = Me(
            id = o.optInt("id"),
            username = o.optString("username", ""),
            isAdmin = o.optBoolean("is_admin"),
            roturId = o.stringOrNull("rotur_id"),
            roturLinked = o.optBoolean("rotur_linked"),
            email = o.stringOrNull("email"),
        )
    }
}

/** Live snapshot of a listen-along room (same payload as GET /api/rooms/<code>). */
data class RoomState(
    val hostId: Int,
    val hostName: String,
    val track: Track?,
    val pos: Double,
    val playing: Boolean,
    val hostAway: Boolean,
    val stateTs: Double,
    val serverNow: Double,
) {
    companion object {
        fun from(o: JSONObject) = RoomState(
            hostId = o.optInt("host_id"),
            hostName = o.optString("host_name", "host"),
            track = o.optJSONObject("track")?.let(Track::from),
            pos = o.optDouble("pos", 0.0),
            playing = o.optBoolean("playing"),
            hostAway = o.optBoolean("host_away"),
            stateTs = o.optDouble("state_ts", 0.0),
            serverNow = o.optDouble("server_now", 0.0),
        )
    }
}

data class RequestRow(
    val id: Int,
    val url: String,
    val status: String,
    val created: Double,
    val log: String,
    val username: String?,
) {
    companion object {
        fun from(o: JSONObject) = RequestRow(
            id = o.optInt("id"),
            url = o.optString("url", ""),
            status = o.optString("status", ""),
            created = o.optDouble("created", 0.0),
            log = o.optString("log", ""),
            username = o.stringOrNull("username"),
        )
    }
}

data class AdminStats(
    val users: Int,
    val admins: Int,
    val tracks: Int,
    val albums: Int,
    val playlists: Int,
    val plays: Int,
    val queue: Int,
    val rooms: Int,
    val musicBytes: Long,
    val diskFree: Long,
    val diskTotal: Long,
    val uptime: Double,
)

data class AdminRoom(
    val code: String,
    val host: String,
    val trackTitle: String?,
    val trackArtist: String?,
    val playing: Boolean,
    val idle: Double,
    val away: Boolean,
) {
    companion object {
        fun from(o: JSONObject): AdminRoom {
            val t = o.optJSONObject("track")
            return AdminRoom(
                code = o.optString("code"),
                host = o.optString("host"),
                trackTitle = t?.stringOrNull("title"),
                trackArtist = t?.stringOrNull("artist"),
                playing = o.optBoolean("playing"),
                idle = o.optDouble("idle", 0.0),
                away = o.optBoolean("away"),
            )
        }
    }
}

data class ChannelRef(
    val id: Int,
    val platform: String,
    val channelId: String,
    val guildId: String?,
    val mode: String,
    val dashboardId: String?,
    val ownerUserId: Int?,
    val updated: Double,
) {
    companion object {
        fun from(o: JSONObject) = ChannelRef(
            id = o.optInt("id"),
            platform = o.optString("platform", "discord"),
            channelId = o.optString("channel_id", ""),
            guildId = o.stringOrNull("guild_id"),
            mode = o.optString("mode", "control"),
            dashboardId = o.stringOrNull("dashboard_id"),
            ownerUserId = o.intOrNull("owner_user_id"),
            updated = o.optDouble("updated", 0.0),
        )

        fun list(arr: JSONArray): List<ChannelRef> =
            (0 until arr.length()).mapNotNull { i -> arr.optJSONObject(i)?.let(::from) }
    }
}

data class AdminDeviceRef(
    val id: Int,
    val username: String,
    val name: String,
    val deviceHash: String,
    val ip: String,
    val lastSeen: Double,
    val isActive: Boolean,
    val paused: Boolean,
) {
    companion object {
        fun from(o: JSONObject) = AdminDeviceRef(
            id = o.optInt("id"),
            username = o.optString("username", ""),
            name = o.optString("name", ""),
            deviceHash = o.optString("device_hash", ""),
            ip = o.optString("ip", ""),
            lastSeen = o.optDouble("last_seen", 0.0),
            isActive = o.optBoolean("is_active"),
            paused = o.optBoolean("current_paused"),
        )
    }
}

data class EnrichStatus(val total: Int, val linked: Int, val fetched: Int)

data class LyricsStatus(
    val running: Boolean,
    val done: Int,
    val failed: Int,
    val total: Int,
) {
    companion object {
        fun from(o: JSONObject) = LyricsStatus(
            running = o.optBoolean("running"),
            done = o.optInt("done"),
            failed = o.optInt("failed"),
            total = o.optInt("total"),
        )
    }
}

data class DeviceRef(
    val id: Int,
    val name: String,
    val hash: String,
    val active: Boolean,
    val paused: Boolean,
    val trackId: Int?,
    val lastSeen: Double,
    val trackTitle: String? = null,
    val trackArtist: String? = null,
) {
    companion object {
        fun from(o: JSONObject) = DeviceRef(
            id = o.optInt("id"),
            name = o.optString("name", "Device"),
            hash = o.optString("device_hash"),
            active = o.optBoolean("is_active"),
            paused = o.optBoolean("current_paused"),
            trackId = o.intOrNull("current_track_id"),
            lastSeen = o.optDouble("last_seen", 0.0),
            trackTitle = o.stringOrNull("track_title"),
            trackArtist = o.stringOrNull("track_artist"),
        )

        fun list(arr: JSONArray): List<DeviceRef> =
            (0 until arr.length()).mapNotNull { i -> arr.optJSONObject(i)?.let(::from) }
    }
}

data class InviteCode(
    val id: Int,
    val code: String,
    val uses: Int,
    val maxUses: Int,
    val expires: Double,
    val expired: Boolean,
    val active: Boolean,
    val note: String,
    val createdBy: String?,
    val usedBy: List<String>,
) {
    companion object {
        fun from(o: JSONObject): InviteCode {
            val arr = o.optJSONArray("used_by") ?: JSONArray()
            return InviteCode(
                id = o.optInt("id"),
                code = o.optString("code"),
                uses = o.optInt("uses"),
                maxUses = o.optInt("max_uses", 1),
                expires = o.optDouble("expires", 0.0),
                expired = o.optBoolean("expired"),
                active = o.optBoolean("active", true),
                note = o.optString("note"),
                createdBy = o.stringOrNull("created_by_name"),
                usedBy = (0 until arr.length()).mapNotNull { i ->
                    arr.optJSONObject(i)?.optString("username")?.ifBlank { null }
                },
            )
        }
    }
}

data class AdminUser(
    val id: Int,
    val username: String,
    val isAdmin: Boolean,
    val plays: Int,
    val likes: Int,
    val playlists: Int,
    val requests: Int,
)
