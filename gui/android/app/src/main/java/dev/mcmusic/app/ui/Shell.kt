package dev.mcmusic.app.ui

import android.os.Build
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.kyant.backdrop.backdrops.layerBackdrop
import com.kyant.backdrop.backdrops.rememberLayerBackdrop
import dev.mcmusic.app.ui.design.LocalBackdrop
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.McDesign
import dev.mcmusic.app.ui.design.mcSurface
import dev.mcmusic.app.ui.screens.DownloadsScreen
import dev.mcmusic.app.ui.screens.HomeScreen
import dev.mcmusic.app.ui.screens.LibraryScreen
import dev.mcmusic.app.ui.screens.PlayerScreen
import dev.mcmusic.app.ui.screens.SearchScreen
import dev.mcmusic.app.ui.screens.SettingsScreen

enum class Tab(val label: String, val icon: McIcon) {
    Home("Home", McIcon.Home),
    Search("Search", McIcon.Search),
    Player("Player", McIcon.Play),
    Library("Library", McIcon.Library),
    Downloads("Downloads", McIcon.Download),
    Settings("Settings", McIcon.Settings),
}

/**
 * The window: a palette stage, a recorded backdrop for glass, then whichever
 * layout language is selected. Both languages show the same six pages; only
 * the chrome and the surface treatment change.
 */
@Composable
fun McShell() {
    val design = LocalDesign.current
    var tab by rememberSaveable { mutableStateOf(Tab.Home) }
    val backdrop = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) rememberLayerBackdrop() else null

    Box(Modifier.fillMaxSize().background(design.palette.bg)) {
        Stage(
            Modifier
                .fillMaxSize()
                .then(if (backdrop != null) Modifier.layerBackdrop(backdrop) else Modifier),
            design,
        )
        CompositionLocalProvider(LocalBackdrop provides backdrop) {
            if (design.ios) {
                IosShell(tab) { tab = it }
            } else {
                OneUiShell(tab) { tab = it }
            }
        }
    }
}

@Composable
private fun TabContent(tab: Tab) {
    Box(Modifier.fillMaxSize().statusBarsPadding()) {
        when (tab) {
            Tab.Home -> HomeScreen()
            Tab.Search -> SearchScreen()
            Tab.Player -> PlayerScreen()
            Tab.Library -> LibraryScreen()
            Tab.Downloads -> DownloadsScreen()
            Tab.Settings -> SettingsScreen()
        }
    }
}

/* ── iOS 27 layout: floating glass bar, content runs underneath ───────────── */

@Composable
private fun IosShell(tab: Tab, onTab: (Tab) -> Unit) {
    Box(Modifier.fillMaxSize()) {
        TabContent(tab)
        IosTabBar(
            tab = tab,
            onTab = onTab,
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .navigationBarsPadding()
                .padding(horizontal = 12.dp, vertical = 10.dp),
        )
    }
}

@Composable
private fun IosTabBar(tab: Tab, onTab: (Tab) -> Unit, modifier: Modifier = Modifier) {
    val design = LocalDesign.current
    Row(
        modifier = modifier
            .fillMaxWidth()
            .mcSurface(RoundedCornerShape(32.dp), tint = design.palette.bg.copy(alpha = 0.18f))
            .padding(horizontal = 6.dp, vertical = 9.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Tab.entries.forEach { entry ->
            val selected = entry == tab
            Column(
                modifier = Modifier
                    .weight(1f)
                    .clip(RoundedCornerShape(22.dp))
                    .clickable { onTab(entry) }
                    .padding(vertical = 4.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(3.dp),
            ) {
                McGlyph(
                    icon = entry.icon,
                    tint = if (selected) design.accent else design.dim,
                    modifier = Modifier.size(23.dp),
                    filled = selected,
                )
                Text(
                    text = entry.label,
                    color = if (selected) design.accent else design.dim,
                    fontSize = 9.sp,
                    fontWeight = if (selected) FontWeight.SemiBold else FontWeight.Medium,
                    textAlign = TextAlign.Center,
                    maxLines = 1,
                )
            }
        }
    }
}

/* ── One UI layout: edge-to-edge content, opaque navigation strip ─────────── */

@Composable
private fun OneUiShell(tab: Tab, onTab: (Tab) -> Unit) {
    val design = LocalDesign.current
    Column(Modifier.fillMaxSize()) {
        Box(Modifier.weight(1f)) { TabContent(tab) }
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .background(design.palette.bg)
                .drawBehind {
                    drawLine(
                        color = design.hairline,
                        start = Offset(0f, 0f),
                        end = Offset(size.width, 0f),
                        strokeWidth = 1.dp.toPx(),
                    )
                }
                .navigationBarsPadding()
                .padding(top = 6.dp, bottom = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Tab.entries.forEach { entry ->
                val selected = entry == tab
                Column(
                    modifier = Modifier
                        .weight(1f)
                        .clip(RoundedCornerShape(14.dp))
                        .clickable { onTab(entry) }
                        .padding(vertical = 2.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(2.dp),
                ) {
                    Box(
                        modifier = Modifier
                            .width(46.dp)
                            .height(30.dp)
                            .clip(RoundedCornerShape(15.dp))
                            .then(if (selected) Modifier.background(design.accentSoft) else Modifier),
                        contentAlignment = Alignment.Center,
                    ) {
                        McGlyph(
                            icon = entry.icon,
                            tint = if (selected) design.accent else design.dim,
                            modifier = Modifier.size(22.dp),
                            filled = selected,
                        )
                    }
                    Text(
                        text = entry.label,
                        color = if (selected) design.accent else design.dim,
                        fontSize = 10.sp,
                        fontWeight = if (selected) FontWeight.SemiBold else FontWeight.Normal,
                        maxLines = 1,
                    )
                }
            }
        }
    }
}

/** Palette wash behind everything: what the glass has to refract. */
@Composable
private fun Stage(modifier: Modifier, design: McDesign) {
    val palette = design.palette
    Canvas(modifier) {
        drawRect(
            Brush.verticalGradient(
                listOf(palette.bg, palette.bg2),
                startY = 0f,
                endY = size.height,
            ),
        )
        drawCircle(
            color = palette.accent.copy(alpha = if (palette.dark) 0.20f else 0.16f),
            radius = size.minDimension * 0.55f,
            center = Offset(size.width * 0.15f, size.height * 0.10f),
        )
        drawCircle(
            color = palette.accent.copy(alpha = if (palette.dark) 0.10f else 0.08f),
            radius = size.minDimension * 0.45f,
            center = Offset(size.width * 0.95f, size.height * 0.45f),
        )
    }
}
