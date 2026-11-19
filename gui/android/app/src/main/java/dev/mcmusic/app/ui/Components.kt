package dev.mcmusic.app.ui

import androidx.annotation.DrawableRes
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.mcSurface

/** Page title. iOS uses a lighter large title, One UI a heavy edge-aligned one. */
@Composable
fun ScreenTitle(title: String, subtitle: String? = null) {
    val design = LocalDesign.current
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(
            text = title,
            color = design.fg,
            fontSize = design.titleSize,
            fontWeight = design.titleWeight,
            letterSpacing = if (design.ios) (-0.5).sp else (-0.8).sp,
        )
        if (subtitle != null) {
            Text(text = subtitle, color = design.dim, fontSize = 13.sp, lineHeight = 18.sp)
        }
    }
}

/** A quiet back link with the parent page's name, used by detail pages. */
@Composable
fun ScreenBack(onBack: () -> Unit, label: String) {
    val design = LocalDesign.current
    Row(
        modifier = Modifier
            .clip(RoundedCornerShape(50))
            .clickable { onBack() }
            .padding(vertical = 4.dp, horizontal = 2.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(4.dp),
    ) {
        LucideIcon(Lucide.ChevronLeft, design.accent, Modifier.size(18.dp))
        Text(label, color = design.accent, fontSize = 13.sp, fontWeight = FontWeight.Medium)
    }
}

@Composable
fun SectionLabel(text: String, modifier: Modifier = Modifier, @DrawableRes icon: Int? = null) {
    val design = LocalDesign.current
    Row(
        modifier = modifier,
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        if (icon != null) {
            LucideIcon(icon, design.dim, Modifier.size(13.dp))
        }
        Text(
            text = text.uppercase(),
            color = design.dim,
            fontSize = if (design.ios) 11.sp else 12.sp,
            fontWeight = FontWeight.SemiBold,
            letterSpacing = if (design.ios) 0.8.sp else 0.4.sp,
        )
    }
}

@Composable
fun LiveDot(active: Boolean, size: Dp = 8.dp) {
    val design = LocalDesign.current
    Box(
        Modifier
            .size(size)
            .clip(CircleShape)
            .background(if (active) design.accent else design.dim.copy(alpha = 0.5f)),
    )
}

@Composable
fun Pill(text: String, active: Boolean = true, modifier: Modifier = Modifier) {
    val design = LocalDesign.current
    Row(
        modifier = modifier
            .mcSurface(RoundedCornerShape(50), tint = Color.Transparent)
            .padding(horizontal = 10.dp, vertical = 5.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        LiveDot(active, 6.dp)
        Text(text, color = if (active) design.fg else design.dim, fontSize = 11.sp, fontWeight = FontWeight.Medium)
    }
}

/** Segmented control for the two design languages, styled by the active one. */
@Composable
fun Segmented(options: List<String>, selectedIndex: Int, onSelect: (Int) -> Unit) {
    val design = LocalDesign.current
    Row(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(if (design.ios) 14.dp else 16.dp))
            .background(design.palette.bg2.copy(alpha = if (design.palette.dark) 0.55f else 0.75f))
            .padding(4.dp),
        horizontalArrangement = Arrangement.spacedBy(4.dp),
    ) {
        options.forEachIndexed { index, label ->
            val selected = index == selectedIndex
            Box(
                modifier = Modifier
                    .weight(1f)
                    .height(if (design.ios) 34.dp else 36.dp)
                    .clip(RoundedCornerShape(if (design.ios) 11.dp else 13.dp))
                    .then(
                        if (selected) Modifier.background(if (design.ios) design.accent else design.accentSoft)
                        else Modifier,
                    )
                    .clickable { onSelect(index) },
                contentAlignment = Alignment.Center,
            ) {
                Text(
                    text = label,
                    color = when {
                        !selected -> design.dim
                        design.ios -> design.palette.bg2
                        else -> design.accent
                    },
                    fontSize = 13.sp,
                    fontWeight = if (selected) FontWeight.SemiBold else FontWeight.Medium,
                    textAlign = TextAlign.Center,
                )
            }
        }
    }
}

@Composable
fun EmptyState(
    @DrawableRes icon: Int,
    title: String,
    body: String,
    actionLabel: String? = null,
    onAction: (() -> Unit)? = null,
) {
    val design = LocalDesign.current
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .mcSurface(RoundedCornerShape(design.cardRadius))
            .padding(horizontal = 22.dp, vertical = 30.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Box(
            Modifier
                .size(48.dp)
                .clip(CircleShape)
                .background(design.accentSoft),
            contentAlignment = Alignment.Center,
        ) {
            LucideIcon(icon, design.accent, Modifier.size(24.dp))
        }
        Text(title, color = design.fg, fontSize = 16.sp, fontWeight = FontWeight.SemiBold, textAlign = TextAlign.Center)
        Text(body, color = design.dim, fontSize = 13.sp, lineHeight = 18.sp, textAlign = TextAlign.Center)
        if (actionLabel != null && onAction != null) {
            Box(
                Modifier
                    .padding(top = 4.dp)
                    .clip(RoundedCornerShape(50))
                    .background(design.accent)
                    .clickable { onAction() }
                    .padding(horizontal = 18.dp, vertical = 9.dp),
            ) {
                Text(actionLabel, color = design.palette.bg2, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
            }
        }
    }
}

fun timecode(seconds: Double): String {
    val s = seconds.coerceAtLeast(0.0).toInt()
    return "${s / 60}:${(s % 60).toString().padStart(2, '0')}"
}
