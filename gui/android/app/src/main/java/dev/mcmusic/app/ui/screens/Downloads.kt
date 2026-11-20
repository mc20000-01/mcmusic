package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.Background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Account
import dev.mcmusic.app.data.Download
import dev.mcmusic.app.data.Downloads
import dev.mcmusic.app.data.Track
import dev.mcmusic.app.playback.Playback
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.LucideIcon
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.SectionLabel
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface
import kotlinx.coroutines.launch

@Composable
fun DownloadsScreen() {
    val design = LocalDesign.current
    var signedIn by remember { mutableStateOf<Boolean?>(null) }
    var downloads by remember { mutableStateOf<List<Download>>(emptyList()) }
    var loading by remember { mutableStateOf(true) }
    var error by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(Unit) {
        if (me != null) {
            loading = true
            Api.downloads { it ->
                loading = false
                downloads = it
                error = null
            }.onFailure { loading = false; error = it.message ?: "could not load downloads" }
        } else {
            loading = false
        }
        signedIn = me != null
    }

    val me = Account.me

    LazyColumn(
        contentPadding = PaddingValues(
            start = design.screenPadding,
            end = design.screenPadding,
            top = 10.dp,
            bottom = design.gap,
        ),
        verticalArrangement = androidx.compose.foundation.Arrangement.spacedBy(design.gap),
    ) {
        item {
            ScreenTitle(
                if (me != null) "Downloads" else "Sign in to download",
            )
        }

        if (me != null) {
            if (loading) {
                item { Text("Loading downloads…", color = design.dim, fontSize = 13.sp, align = androidx.compose.ui.Alignment.CenterHorizontally) }
            }
            if (error != null) {
                EmptyState(
                    icon = dev.mcmusic.app.ui.Lucide.Download,
                    title = "Couldn't load downloads",
                    body = error,
                    actionLabel = "Try again",
                    onAction = {},
                )
            }
            if (downloads.isNotEmpty()) {
                items(downloads, key = { it.id }) { download ->
                    DownloadRow(download)
                }
            }
            if (downloads.isEmpty()) {
                EmptyState(
                    icon = dev.mcmusic.app.ui.Lucide.Download,
                    title = "No downloads",
                    body = "Your downloads will appear here.",
                    actionLabel = "",
                )
            }
        } else {
            if (!me!.value) {
                item {
                    ScreenBack(onBack = { }) {}
                    Text("Sign in to access downloads", color = design.dim, fontSize = 14.sp, align = androidx.compose.ui.Alignment.CenterHorizontally)
                }
            }
            item {
                EmptyState(
                    icon = dev.mcmusic.app.ui.Lucide.Download,
                    title = "Sign in to download",
                    body = "Download tracks from YouTube playlists.",
                    actionLabel = "Sign in",
                )
            }
        }
    }
}

@Composable
fun DownloadRow(download: Download) {
    val design = LocalDesign.current
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .mcSurface(RoundedCornerShape(design.cardRadius))
            .padding(12.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.start,
    ) {
        Cover(
            url = "${Api.server}/api/tracks/${download.trackId}/cover",
            shape = RoundedCornerShape(8.dp),
            modifier = Modifier.size(40.dp),
            fallback = design.accentSoft,
        )
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Text(download.title, color = design.fg, fontSize = 14.sp, fontWeight = FontWeight.Medium, maxLines = 1)
            Text(
                text = download.artist.ifBlank { "unknown artist" },
                color = design.dim,
                fontSize = 11.sp,
                maxLines = 1,
            )
            if (download.progress >= 0) {
                Text(
                    text = "${download.progress.toInt()}% complete",
                    color = design.dim,
                    fontSize = 11.sp,
                )
            }
        }
        Spacer(Modifier.width(8.dp))
        Box(
            modifier = Modifier
                .size(24.dp)
                .clip(CircleShape)
                .background(design.palette.bg),
            contentAlignment = Alignment.Center,
        ) {
            LucideIcon(Lucide.Download, design.dim, Modifier.size(14.dp))
        }
    }
}