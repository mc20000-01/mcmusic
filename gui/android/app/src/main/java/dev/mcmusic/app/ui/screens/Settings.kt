package dev.mcmusic.app.ui.screens

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
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.PasswordFieldValue
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Account
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.Lucide
import dev.mcmusic.app.ui.LucideIcon
import dev.mcmusic.app.ui.Segmented
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface
import kotlinx.coroutines.launch

@Composable
fun SettingsScreen() {
    val design = LocalDesign.current
    var signedIn by remember { mutableStateOf<Boolean?>(null) }
    var motd by remember { mutableStateOf<String?>(null) }
    var theme by rememberSaveable { currentDesignLanguage() }
    var language by rememberSaveable { currentDesignLanguage() }
    var motion by rememberSaveable { Prefs.motion }
    var showCovers by rememberSaveable { true }
    var hideExplicit by rememberSaveable { false }

    Column(
        modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()),
        verticalArrangement = androidx.compose.foundation.Arrangement.spacedBy(12.dp),
    ) {
        SettingsHeader()

        // Appearance
        SettingsSection("Appearance") {
            SettingsToggle(
                title = "Theme",
                subtitle = design.language.label,
                icon = dev.mcmusic.app.ui.Lucide.Palette,
                checked = language.id == design.language.id,
                onChange = { language = it },
            )
            SettingsToggle(
                title = "Design language",
                subtitle = if (language.id == "ios") "iOS 27 chrome" else "One UI flat chrome",
                icon = dev.mcmusic.app.ui.Lucide.Compass,
                checked = language.id == "ios",
                onChange = { language = it },
            )
            SettingsToggle(
                title = "Reduce motion",
                subtitle = "Animate transitions",
                icon = dev.mcmusic.app.ui.Lucide.Sync,
                checked = motion,
                onChange = { motion = !it },
            )
            SettingsToggle(
                title = "Show song covers",
                subtitle = " artwork in lists and tiles",
                icon = dev.mcmusic.app.ui.Lucide.Image,
                checked = showCovers,
                onChange = { showCovers = it },
            )
            SettingsToggle(
                title = "Hide explicit",
                subtitle = "Filter explicit lyrics",
                icon = dev.mcmusic.app.ui.Lucide.Lock,
                checked = hideExplicit,
                onChange = { hideExplicit = it },
            )
        }

        // Social
        SettingsSection("Social") {
            SettingsToggle(
                title = "Discord Rich Presence",
                subtitle = "Show what you're listening to on Discord",
                icon = dev.mcmusic.app.ui.Lucide.Discord,
                checked = true, // TODO: read from prefs
                onChange = {},
            )
            SettingsToggle(
                title = "Rotur activity",
                subtitle = "Share what you're listening to on Rotur",
                icon = dev.mcmusic.app.ui.Lucide.Server,
                checked = true, // TODO: read from prefs
                onChange = {},
            )
        }

        // About
        SettingsSection("About") {
            SettingsRow(
                title = "Version",
                subtitle = "mcmusic ${Prefs.version}",
                icon = dev.mcmusic.app.ui.Lucide.Info,
                onClick = {},
            )
            SettingsRow(
                title = "Contact",
                subtitle = "Report issues or say hello",
                icon = dev.mcmusic.app.ui.Lucide.Mail,
                onClick = {},
            )
        }
    }
}

@Composable
fun SettingsHeader() {
    val design = LocalDesign.current
    SettingsSection("", {
        Row(
            modifier = Modifier.fillMaxWidth().padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = "mcmusic",
                color = design.accent,
                fontSize = 20.sp,
                fontWeight = FontWeight.ExtraBold,
            )
            Spacer(Modifier.width(8.dp))
            Text(
                text = Prefs.version,
                color = design.dim,
                fontSize = 12.sp,
            )
        }
    })
}

@Composable
fun SettingsSection(title: String, content: @Composable () -> Unit) {
    val design = LocalDesign.current
    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(4.dp),
    ) {
        if (title.isNotBlank()) {
            SectionLabel(title)
        }
        content()
    }
}

@Composable
fun SettingsToggle(
    title: String,
    subtitle: String,
    @DrawableRes icon: Int,
    checked: Boolean,
    onChange: (Boolean) -> Unit,
) {
    val design = LocalDesign.current
    SettingsRow(
        title = title,
        subtitle = subtitle,
        icon = icon,
        onClick = { onChange(!checked) },
        trailing = {
            Icon(
                painter = androidx.compose.ui.graphics.painterResource(
                    dev.mcmusic.app.R.drawable.ic_lucide_check
                ),
                tint = if (checked) design.accent else design.dim,
                modifier = Modifier.size(18.dp),
            )
        },
    )
}

@Composable
fun SettingsRow(
    title: String,
    subtitle: String? = null,
    @DrawableRes icon: Int? = null,
    danger: Boolean = false,
    onClick: (() -> Unit)? = null,
    trailing: (@Composable () -> Unit)? = null,
) {
    val design = LocalDesign.current
    val titleColor = if (danger) Color(0xFFE5484D) else design.fg
    val iconTint = if (danger) Color(0xFFE5484D) else design.accent
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .then(if (onClick != null) Modifier.clickable(onClick = onClick) else Modifier)
            .padding(vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        if (icon != null) {
            Box(
                modifier = Modifier
                    .size(30.dp)
                    .clip(RoundedCornerShape(9.dp))
                    .background(if (danger) Color(0xFFE5484D).copy(alpha = 0.14f) else design.accentSoft),
                contentAlignment = Alignment.Center,
            ) {
                LucideIcon(icon, iconTint, Modifier.size(15.dp))
            }
        }
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Text(title, color = titleColor, fontSize = 14.sp, fontWeight = FontWeight.Medium)
            if (subtitle != null) {
                Text(subtitle, color = design.dim, fontSize = 11.sp, lineHeight = 15.sp)
            }
        }
        trailing?.invoke()
    }
}