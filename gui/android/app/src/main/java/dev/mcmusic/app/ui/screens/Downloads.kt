package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Account
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.Download
import dev.mcmusic.app.data.DownloadRequest
import dev.mcmusic.app.data.Downloads
import dev.mcmusic.app.data.Track
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.ui.Danger
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.GhostButton
import dev.mcmusic.app.ui.IconButton
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.McField
import dev.mcmusic.app.ui.Muted
import dev.mcmusic.app.ui.PrimaryButton
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.SectionLabel
import dev.mcmusic.app.ui.SettingCard
import dev.mcmusic.app.ui.SettingRow
import dev.mcmusic.app.ui.TrackCover
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.formatBytes
import java.net.URI
import java.net.URLDecoder
import kotlinx.coroutines.launch

private val IMPORT_EXTS = setOf(
    ".mp3", ".m4a", ".aac", ".opus", ".flac", ".wav", ".webm", ".ogg", ".zip",
)
private val PLAYLIST_ID = Regex("[A-Za-z0-9_-]{12,}")

/** Mirrors the server's accepted links so bad links fail before being sent. */
private fun linkProblem(value: String): String? {
    val uri = runCatching { URI(value) }.getOrNull()
        ?: return "That does not look like a link."
    if (uri.scheme?.lowercase() != "https" || uri.host.isNullOrBlank() || uri.userInfo != null) {
        return "Use an https YouTube or direct audio/ZIP link."
    }
    val host = uri.host.lowercase()
    if (host == "youtu.be" || host.endsWith(".youtu.be") ||
        host == "youtube.com" || host.endsWith(".youtube.com")
    ) {
        val playlist = uri.query.orEmpty()
            .split('&').firstOrNull { it.startsWith("list=") }
            ?.removePrefix("list=").orEmpty()
        if (playlist.isNotBlank()) {
            if (!PLAYLIST_ID.matches(playlist)) {
                return "That playlist link is incomplete. Copy the full link from YouTube."
            }
            val prefix = playlist.take(2).uppercase()
            if (prefix in setOf("PL", "UU", "LL", "FL") && playlist.length != 34) {
                return "That playlist ID is ${playlist.length} characters; YouTube playlists have 34. Copy the full link."
            }
            return null
        }
        var video = Regex("(?:v=|/shorts/|/embed/)([A-Za-z0-9_-]{11})").find(value)?.groupValues?.get(1)
        if (video == null && host.startsWith("youtu.be")) {
            video = uri.path?.trim('/')?.take(11)?.takeIf { it.length == 11 }
        }
        if (video == null) return "Paste a YouTube video or playlist link, or a direct https audio/ZIP link."
        return null
    }
    val path = runCatching { URLDecoder.decode(uri.path.orEmpty(), "UTF-8") }
        .getOrDefault(uri.path.orEmpty()).lowercase()
    return if (IMPORT_EXTS.any { path.endsWith(it) }) null
    else "Direct links must end in an audio file or .zip."
}

/** The useful line from the server's tail, not the whole yt-dlp transcript. */
private fun requestError(log: String): String? = log.lineSequence()
    .map { it.trim() }
    .filter { it.isNotBlank() && !it.startsWith("[") }
    .lastOrNull()
    ?.take(200)

private fun requestLabel(status: String): String = when (status) {
    "pending" -> "Waiting for approval"
    "approved" -> "Approved"
    "running" -> "Importing…"
    "done" -> "Finished"
    "failed" -> "Failed"
    "rejected" -> "Rejected"
    "cancelled" -> "Cancelled"
    else -> status
}

/**
 * Offline copies plus server imports. Downloads are per device and stored by
 * [Downloads]; the link form submits YouTube or direct MP3/ZIP links to the
 * same request queue the web client uses.
 */
@Composable
fun DownloadsScreen(onOpenPlayer: () -> Unit, onOpenVideos: () -> Unit) {
    val design = LocalDesign.current
    val scope = rememberCoroutineScope()
    val items = Downloads.items
    var confirmClear by remember { mutableStateOf(false) }
    var link by remember { mutableStateOf("") }
    var message by remember { mutableStateOf<String?>(null) }
    var sending by remember { mutableStateOf(false) }
    var requests by remember { mutableStateOf<List<DownloadRequest>?>(null) }
    var reload by remember { mutableStateOf(0) }

    LaunchedEffect(reload) {
        Api.myRequests().fold(
            onSuccess = { requests = it },
            onFailure = { requests = emptyList() },
        )
    }

    fun asTrack(d: Download) = Track(d.id, d.title, d.artist, d.album, d.duration)

    fun submit() {
        val value = link.trim()
        message = null
        if (value.isEmpty()) return
        linkProblem(value)?.let {
            message = it
            return
        }
        sending = true
        scope.launch {
            Api.requestDownload(value).fold(
                onSuccess = { status ->
                    link = ""
                    message = if (status == "pending") {
                        "Request sent. An admin will approve it, then it imports automatically."
                    } else {
                        "Download started. It will appear in the library when it finishes."
                    }
                    reload++
                },
                onFailure = { message = it.message ?: "Could not send the request." },
            )
            sending = false
        }
    }

    LazyColumn(
        contentPadding = PaddingValues(design.screenPadding, 10.dp, design.screenPadding, 24.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        item {
            ScreenTitle(
                "Downloads",
                if (items.isEmpty()) "Nothing saved on this device yet."
                else "${items.size} tracks · ${formatBytes(Downloads.totalBytes())}",
            )
        }
        item {
            Column(
                Modifier.fillMaxWidth().padding(horizontal = 4.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                SectionLabel("Add music")
                McField(
                    value = link,
                    onValueChange = { link = it; message = null },
                    label = "YouTube, MP3 or ZIP link",
                )
                PrimaryButton(
                    text = if (sending) "Sending…" else "Request download",
                    enabled = link.isNotBlank() && !sending,
                ) { submit() }
                message?.let { Muted(it, size = 12) }
                Muted("Paste a YouTube link, or a direct https link to an audio file or ZIP of tracks.", size = 12)
            }
        }
        item {
            SettingCard {
                SettingRow(
                    "Saved videos",
                    "Play cached music videos without the YouTube embed",
                    icon = Lucide.Film,
                    onClick = onOpenVideos,
                )
            }
        }
        item {
            Column(
                Modifier.fillMaxWidth().padding(horizontal = 4.dp),
                verticalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                SectionLabel("Your requests") { GhostButton("Refresh") { reload++ } }
                val list = requests.orEmpty()
                if (list.isEmpty()) {
                    Muted("No requests yet. Imported tracks show up in Search and Albums.", size = 12)
                } else {
                    list.forEach { req ->
                        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                            Column(Modifier.weight(1f)) {
                                Text(
                                    "#${req.id} · ${req.url}",
                                    color = design.fg,
                                    fontSize = 12.sp,
                                    maxLines = 1,
                                    overflow = TextOverflow.Ellipsis,
                                )
                                Muted(requestLabel(req.status), size = 11)
                                if (req.status == "failed") {
                                    requestError(req.log)?.let { detail ->
                                        Text(
                                            detail,
                                            color = Danger,
                                            fontSize = 10.sp,
                                            maxLines = 2,
                                            overflow = TextOverflow.Ellipsis,
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        if (items.isNotEmpty()) {
            item {
                SectionLabel("On this device") {
                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        GhostButton(if (confirmClear) "Really clear?" else "Clear all", danger = true) {
                            if (confirmClear) {
                                Downloads.clearAll()
                                confirmClear = false
                            } else {
                                confirmClear = true
                            }
                        }
                    }
                }
            }
            items(items, key = { it.id }) { download ->
                val track = asTrack(download)
                Row(
                    Modifier.fillMaxWidth().padding(horizontal = 4.dp, vertical = 6.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(11.dp),
                ) {
                    TrackCover(track)
                    Column(Modifier.weight(1f)) {
                        Text(track.title, color = design.fg, fontSize = 14.sp, fontWeight = FontWeight.Medium)
                        Text(
                            "${track.artist} · ${formatBytes(download.bytes)}",
                            color = design.dim, fontSize = 11.sp,
                        )
                    }
                    IconButton(Lucide.Play, tint = design.accent) {
                        Playback.play(items.map(::asTrack), items.indexOf(download))
                        onOpenPlayer()
                    }
                    IconButton(Lucide.Trash) { Downloads.remove(download.id) }
                }
            }
        } else {
            item {
                EmptyState(
                    icon = Lucide.Download,
                    title = "No downloads",
                    body = if (Account.me == null) {
                        "Sign in from Settings to save tracks. Anything already on this device still plays offline."
                    } else {
                        "Saved tracks play offline and show up in the mini player like any other queue."
                    },
                )
            }
        }
        item {
            Muted(
                if (Account.me == null) {
                    "Downloads are per device and are not synced."
                } else {
                    "Downloads are not synced between devices."
                },
            )
        }
    }
}
