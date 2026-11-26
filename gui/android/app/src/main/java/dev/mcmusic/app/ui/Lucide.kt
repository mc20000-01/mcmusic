package dev.mcmusic.app.ui

import androidx.annotation.DrawableRes
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Icon
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.Dp
import dev.mcmusic.app.R
import dev.mcmusic.app.data.Prefs

/**
 * Lucide glyphs, one vector drawable each. They are vendored (Lucide is ISC
 * licensed) instead of pulling an icon library in: the Compose screens and the
 * home screen widgets then draw exactly the same files, and the widget buttons
 * stop being text characters.
 */
object Lucide {
    // BEGIN GENERATED ICONS
    @DrawableRes val AudioLines = R.drawable.ic_lucide_audio_lines
    @DrawableRes val Cast = R.drawable.ic_lucide_cast
    @DrawableRes val Check = R.drawable.ic_lucide_check
    @DrawableRes val ChevronDown = R.drawable.ic_lucide_chevron_down
    @DrawableRes val ChevronLeft = R.drawable.ic_lucide_chevron_left
    @DrawableRes val ChevronRight = R.drawable.ic_lucide_chevron_right
    @DrawableRes val ChevronUp = R.drawable.ic_lucide_chevron_up
    @DrawableRes val Circle = R.drawable.ic_lucide_circle
    @DrawableRes val CircleAlert = R.drawable.ic_lucide_circle_alert
    @DrawableRes val CircleCheck = R.drawable.ic_lucide_circle_check
    @DrawableRes val CircleHelp = R.drawable.ic_lucide_circle_help
    @DrawableRes val CircleX = R.drawable.ic_lucide_circle_x
    @DrawableRes val Clock = R.drawable.ic_lucide_clock
    @DrawableRes val Coffee = R.drawable.ic_lucide_coffee
    @DrawableRes val Compass = R.drawable.ic_lucide_compass
    @DrawableRes val Cookie = R.drawable.ic_lucide_cookie
    @DrawableRes val Disc3 = R.drawable.ic_lucide_disc_3
    @DrawableRes val Download = R.drawable.ic_lucide_download
    @DrawableRes val Dumbbell = R.drawable.ic_lucide_dumbbell
    @DrawableRes val Ellipsis = R.drawable.ic_lucide_ellipsis
    @DrawableRes val EyeOff = R.drawable.ic_lucide_eye_off
    @DrawableRes val Film = R.drawable.ic_lucide_film
    @DrawableRes val Flame = R.drawable.ic_lucide_flame
    @DrawableRes val Flower = R.drawable.ic_lucide_flower
    @DrawableRes val FolderPlus = R.drawable.ic_lucide_folder_plus
    @DrawableRes val GripVertical = R.drawable.ic_lucide_grip_vertical
    @DrawableRes val HardDrive = R.drawable.ic_lucide_hard_drive
    @DrawableRes val Headphones = R.drawable.ic_lucide_headphones
    @DrawableRes val Heart = R.drawable.ic_lucide_heart
    @DrawableRes val Home = R.drawable.ic_lucide_house
    @DrawableRes val House = R.drawable.ic_lucide_house
    @DrawableRes val Image = R.drawable.ic_lucide_image
    @DrawableRes val Inbox = R.drawable.ic_lucide_inbox
    @DrawableRes val Info = R.drawable.ic_lucide_info
    @DrawableRes val Key = R.drawable.ic_lucide_key
    @DrawableRes val Library = R.drawable.ic_lucide_library
    @DrawableRes val Link = R.drawable.ic_lucide_link
    @DrawableRes val List = R.drawable.ic_lucide_list
    @DrawableRes val ListMusic = R.drawable.ic_lucide_list_music
    @DrawableRes val ListPlus = R.drawable.ic_lucide_list_plus
    @DrawableRes val LoaderCircle = R.drawable.ic_lucide_loader_circle
    @DrawableRes val Lock = R.drawable.ic_lucide_lock
    @DrawableRes val LogIn = R.drawable.ic_lucide_log_in
    @DrawableRes val LogOut = R.drawable.ic_lucide_log_out
    @DrawableRes val Mail = R.drawable.ic_lucide_mail
    @DrawableRes val MessageCircle = R.drawable.ic_lucide_message_circle
    @DrawableRes val MicVocal = R.drawable.ic_lucide_mic_vocal
    @DrawableRes val Monitor = R.drawable.ic_lucide_monitor
    @DrawableRes val Moon = R.drawable.ic_lucide_moon
    @DrawableRes val MoreHorizontal = R.drawable.ic_lucide_ellipsis
    @DrawableRes val Music = R.drawable.ic_lucide_music
    @DrawableRes val MusicNote = R.drawable.ic_lucide_music
    @DrawableRes val Palette = R.drawable.ic_lucide_palette
    @DrawableRes val Pause = R.drawable.ic_lucide_pause
    @DrawableRes val Pencil = R.drawable.ic_lucide_pencil
    @DrawableRes val Pentagon = R.drawable.ic_lucide_pentagon
    @DrawableRes val PictureInPicture2 = R.drawable.ic_lucide_picture_in_picture_2
    @DrawableRes val Pin = R.drawable.ic_lucide_pin
    @DrawableRes val Play = R.drawable.ic_lucide_play
    @DrawableRes val Plus = R.drawable.ic_lucide_plus
    @DrawableRes val Radio = R.drawable.ic_lucide_radio
    @DrawableRes val RefreshCw = R.drawable.ic_lucide_refresh_cw
    @DrawableRes val Repeat = R.drawable.ic_lucide_repeat
    @DrawableRes val Repeat1 = R.drawable.ic_lucide_repeat_1
    @DrawableRes val Search = R.drawable.ic_lucide_search
    @DrawableRes val Server = R.drawable.ic_lucide_server
    @DrawableRes val Settings = R.drawable.ic_lucide_settings
    @DrawableRes val Shield = R.drawable.ic_lucide_shield
    @DrawableRes val ShieldAlert = R.drawable.ic_lucide_shield_alert
    @DrawableRes val ShieldCheck = R.drawable.ic_lucide_shield_check
    @DrawableRes val Shuffle = R.drawable.ic_lucide_shuffle
    @DrawableRes val SkipBack = R.drawable.ic_lucide_skip_back
    @DrawableRes val SkipForward = R.drawable.ic_lucide_skip_forward
    @DrawableRes val Smartphone = R.drawable.ic_lucide_smartphone
    @DrawableRes val Sparkles = R.drawable.ic_lucide_sparkles
    @DrawableRes val Squircle = R.drawable.ic_lucide_squircle
    @DrawableRes val Star = R.drawable.ic_lucide_star
    @DrawableRes val Trash = R.drawable.ic_lucide_trash_2
    @DrawableRes val Trash2 = R.drawable.ic_lucide_trash_2
    @DrawableRes val User = R.drawable.ic_lucide_user_round
    @DrawableRes val UserRound = R.drawable.ic_lucide_user_round
    @DrawableRes val Volume1 = R.drawable.ic_lucide_volume_1
    @DrawableRes val Volume2 = R.drawable.ic_lucide_volume_2
    @DrawableRes val VolumeX = R.drawable.ic_lucide_volume_x
    @DrawableRes val Wifi = R.drawable.ic_lucide_wifi
    @DrawableRes val WifiOff = R.drawable.ic_lucide_wifi_off
    @DrawableRes val X = R.drawable.ic_lucide_x
    @DrawableRes val Zap = R.drawable.ic_lucide_zap
    // END GENERATED ICONS
}

/**
 * Draw a [Lucide] glyph in [tint] at its logical [size]. The size is required
 * because the shared Lucide width formula depends on the rendered icon size.
 */
@Composable
fun LucideIcon(
    @DrawableRes icon: Int,
    tint: Color,
    size: Dp,
    modifier: Modifier = Modifier,
    contentDescription: String? = null,
) {
    val context = LocalContext.current
    val scale = Prefs.iconStroke.scale
    val vector = remember(context, icon, size, scale) {
        LucideVectors.imageVector(context, icon, size, scale)
    }
    Icon(
        imageVector = vector,
        contentDescription = contentDescription,
        modifier = modifier.size(size),
        tint = tint,
    )
}
