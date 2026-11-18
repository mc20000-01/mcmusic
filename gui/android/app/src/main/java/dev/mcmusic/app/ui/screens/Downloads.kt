package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.runtime.Composable
import androidx.compose.ui.unit.dp
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.McIcon
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.design.LocalDesign

@Composable
fun DownloadsScreen() {
    val design = LocalDesign.current
    LazyColumn(
        contentPadding = PaddingValues(
            start = design.screenPadding,
            end = design.screenPadding,
            top = 12.dp,
            bottom = 124.dp,
        ),
        verticalArrangement = Arrangement.spacedBy(design.gap),
    ) {
        item { ScreenTitle("Downloads", "Music kept on this phone") }
        item {
            EmptyState(
                icon = McIcon.Download,
                title = "No downloads yet",
                body = "Offline copies need the playback service to own the files. The page and its empty state exist now so the download flow has somewhere to land.",
            )
        }
    }
}
