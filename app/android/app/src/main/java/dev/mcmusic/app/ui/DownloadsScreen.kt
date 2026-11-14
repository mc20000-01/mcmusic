package dev.mcmusic.app.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import dev.mcmusic.app.AppViewModel
import dev.mcmusic.app.Route
import dev.mcmusic.app.ui.theme.LocalMc
import dev.mcmusic.app.ui.theme.McType

/** One page, two tabs: what is on the phone and what is still being fetched. */
@Composable
fun DownloadsScreen(vm: AppViewModel) {
    Column(Modifier.fillMaxSize()) {
        Box(Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 10.dp)) {
            Seg(
                options = listOf("downloads" to "Downloads", "requests" to "Requests"),
                selected = vm.downloadsTab,
                onSelect = { vm.selectDownloadsTab(it) },
            )
        }
        Box(Modifier.weight(1f)) {
            if (vm.downloadsTab == "requests") RequestsScreen(vm) else DownloadsBody(vm)
        }
    }
}

@Composable
private fun DownloadsBody(vm: AppViewModel) {
    val mc = LocalMc.current
    val list = vm.downloads

    Column(Modifier.fillMaxSize()) {
        Row(
            Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f)) {
                Text("Offline", style = McType.h1Small, color = mc.fg)
                Text(
                    "${list.size} tracks · ${fmtBytes(vm.downloadBytes)}",
                    style = McType.mono9,
                    color = mc.dim2,
                )
            }
            if (list.isNotEmpty()) {
                McButton(
                    "Clear",
                    { vm.clearDownloads() },
                    small = true,
                    ghost = true,
                    leading = AppIcons.Trash,
                )
            }
        }

        if (list.isEmpty()) {
            EmptyState(
                "Nothing downloaded",
                "Open any track's menu and choose Download for offline to keep it on this phone.",
                icon = AppIcons.Download,
                actionLabel = "Browse library",
                onAction = { vm.navigate(Route.Library, push = false) },
            )
        } else {
            LazyColumn(
                Modifier.fillMaxSize(),
                contentPadding = PaddingValues(start = 14.dp, end = 14.dp, bottom = 24.dp),
            ) {
                items(list, key = { it.id }) { d ->
                    Row(
                        Modifier.fillMaxWidth().padding(vertical = 7.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(10.dp),
                    ) {
                        Art(d.id, 42.dp)
                        Column(Modifier.weight(1f)) {
                            Text(
                                d.title,
                                style = McType.bodySm,
                                color = mc.fg,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis,
                            )
                            Text(
                                listOfNotNull(
                                    d.artist.ifBlank { null },
                                    d.album.ifBlank { null },
                                    fmtBytes(d.bytes),
                                ).joinToString(" · "),
                                style = McType.mono10,
                                color = mc.dim,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis,
                            )
                        }
                        IconBtn(
                            AppIcons.Play,
                            { vm.playDownloaded(d) },
                            size = 36.dp,
                            tint = mc.accent,
                            contentDescription = "Play",
                        )
                        IconBtn(
                            AppIcons.Trash,
                            { vm.removeDownload(d.id) },
                            size = 36.dp,
                            tint = mc.dim,
                            contentDescription = "Remove download",
                        )
                    }
                    Box(Modifier.fillMaxWidth().height(1.dp).background(mc.line))
                }
            }
        }
    }
}
