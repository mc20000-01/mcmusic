package dev.mcmusic.app.ui

import androidx.annotation.DrawableRes
import androidx.compose.material3.Icon
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import dev.mcmusic.app.R

/**
 * Lucide glyphs, one vector drawable each. They are vendored (Lucide is ISC
 * licensed) instead of pulling an icon library in: the Compose screens and the
 * home screen widgets then draw exactly the same files, and the widget buttons
 * stop being text characters.
 */
object Lucide {
    @DrawableRes val Check = R.drawable.ic_lucide_check
    @DrawableRes val ChevronLeft = R.drawable.ic_lucide_chevron_left
    @DrawableRes val ChevronRight = R.drawable.ic_lucide_chevron_right
    @DrawableRes val Download = R.drawable.ic_lucide_download
    @DrawableRes val GripVertical = R.drawable.ic_lucide_grip_vertical
    @DrawableRes val House = R.drawable.ic_lucide_house
    @DrawableRes val Info = R.drawable.ic_lucide_info
    @DrawableRes val Library = R.drawable.ic_lucide_library
    @DrawableRes val ListMusic = R.drawable.ic_lucide_list_music
    @DrawableRes val LoaderCircle = R.drawable.ic_lucide_loader_circle
    @DrawableRes val LogIn = R.drawable.ic_lucide_log_in
    @DrawableRes val LogOut = R.drawable.ic_lucide_log_out
    @DrawableRes val Palette = R.drawable.ic_lucide_palette
    @DrawableRes val Pause = R.drawable.ic_lucide_pause
    @DrawableRes val Pencil = R.drawable.ic_lucide_pencil
    @DrawableRes val Play = R.drawable.ic_lucide_play
    @DrawableRes val Plus = R.drawable.ic_lucide_plus
    @DrawableRes val Repeat = R.drawable.ic_lucide_repeat
    @DrawableRes val Search = R.drawable.ic_lucide_search
    @DrawableRes val Server = R.drawable.ic_lucide_server
    @DrawableRes val Settings = R.drawable.ic_lucide_settings
    @DrawableRes val Shuffle = R.drawable.ic_lucide_shuffle
    @DrawableRes val SkipBack = R.drawable.ic_lucide_skip_back
    @DrawableRes val SkipForward = R.drawable.ic_lucide_skip_forward
    @DrawableRes val Trash = R.drawable.ic_lucide_trash
    @DrawableRes val User = R.drawable.ic_lucide_user
}

/** Draw a [Lucide] glyph in [tint]. Pass a size modifier, as with any icon. */
@Composable
fun LucideIcon(
    @DrawableRes icon: Int,
    tint: Color,
    modifier: Modifier = Modifier,
    contentDescription: String? = null,
) {
    Icon(
        painter = painterResource(icon),
        contentDescription = contentDescription,
        modifier = modifier,
        tint = tint,
    )
}
