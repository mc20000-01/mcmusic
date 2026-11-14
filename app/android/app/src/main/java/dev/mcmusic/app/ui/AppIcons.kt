package dev.mcmusic.app.ui

import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.graphics.vector.PathParser
import androidx.compose.ui.unit.dp

/**
 * Inline Lucide geometry, same 24×24 stroked grid the web client uses.
 * No icon fonts, no image assets, works offline.
 */
private fun buildIcon(name: String, path: String, filled: Boolean): ImageVector {
    val nodes = PathParser().parsePathString(path).toNodes()
    return ImageVector.Builder(
        name = name,
        defaultWidth = 24.dp,
        defaultHeight = 24.dp,
        viewportWidth = 24f,
        viewportHeight = 24f,
    ).apply {
        addPath(
            pathData = nodes,
            fill = if (filled) SolidColor(Color.Black) else null,
            stroke = if (filled) null else SolidColor(Color.Black),
            strokeLineWidth = 1.75f,
            strokeLineCap = StrokeCap.Round,
            strokeLineJoin = StrokeJoin.Round,
        )
    }.build()
}

private fun stroked(name: String, path: String) = buildIcon(name, path, false)
private fun filled(name: String, path: String) = buildIcon(name, path, true)

object AppIcons {

    val Play = stroked("play", "M5 5a2 2 0 0 1 3.008-1.728l11.997 6.998a2 2 0 0 1 .003 3.458l-12 7A2 2 0 0 1 5 19z")
    val Pause = stroked("pause", "M15.0 3.0H18.0a1.0 1.0 0 0 1 1.0 1.0V20.0a1.0 1.0 0 0 1 -1.0 1.0H15.0a1.0 1.0 0 0 1 -1.0 -1.0V4.0a1.0 1.0 0 0 1 1.0 -1.0ZM6.0 3.0H9.0a1.0 1.0 0 0 1 1.0 1.0V20.0a1.0 1.0 0 0 1 -1.0 1.0H6.0a1.0 1.0 0 0 1 -1.0 -1.0V4.0a1.0 1.0 0 0 1 1.0 -1.0Z")
    val SkipBack = stroked("skip-back", "M17.971 4.285A2 2 0 0 1 21 6v12a2 2 0 0 1-3.029 1.715l-9.997-5.998a2 2 0 0 1-.003-3.432zM3 20V4")
    val SkipForward = stroked("skip-forward", "M21 4v16M6.029 4.285A2 2 0 0 0 3 6v12a2 2 0 0 0 3.029 1.715l9.997-5.998a2 2 0 0 0 .003-3.432z")
    val Shuffle = stroked("shuffle", "m18 14 4 4-4 4m18 2 4 4-4 4M2 18h1.973a4 4 0 0 0 3.3-1.7l5.454-8.6a4 4 0 0 1 3.3-1.7H22M2 6h1.972a4 4 0 0 1 3.6 2.2M22 18h-6.041a4 4 0 0 1-3.3-1.8l-.359-.45")
    val Repeat = stroked("repeat", "m17 2 4 4-4 4M3 11v-1a4 4 0 0 1 4-4h14m7 22-4-4 4-4M21 13v1a4 4 0 0 1-4 4H3")
    val RepeatOne = stroked("repeat-1", "m17 2 4 4-4 4M3 11v-1a4 4 0 0 1 4-4h14m7 22-4-4 4-4M21 13v1a4 4 0 0 1-4 4H3M11 10h1v4")
    val Heart = stroked("heart", "M2 9.5a5.5 5.5 0 0 1 9.591-3.676.56.56 0 0 0 .818 0A5.49 5.49 0 0 1 22 9.5c0 2.29-1.5 4-3 5.5l-5.492 5.313a2 2 0 0 1-3 .019L5 15c-1.5-1.5-3-3.2-3-5.5")
    val Volume = stroked("volume-2", "M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298zM16 9a5 5 0 0 1 0 6M19.364 18.364a9 9 0 0 0 0-12.728")
    val VolumeX = stroked("volume-x", "M11 4.702a.7.7 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.7.7 0 0 0 11 19.298zm16.5 14.5 5-5m16.5 9.5 5 5")
    val Home = stroked("home", "M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8M3 10a2 2 0 0 1 .709-1.528l7-6a2 2 0 0 1 2.582 0l7 6A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z")
    val Search = stroked("search", "m21 21-4.34-4.34M3.0 11.0a8.0 8.0 0 1 0 16.0 0a8.0 8.0 0 1 0 -16.0 0")
    val Library = stroked("library", "m16 6 4 14M12 6v14M8 8v12M4 4v16")
    val Settings = stroked("settings-2", "M14 17H5M19 7h-9M14.0 17.0a3.0 3.0 0 1 0 6.0 0a3.0 3.0 0 1 0 -6.0 0M4.0 7.0a3.0 3.0 0 1 0 6.0 0a3.0 3.0 0 1 0 -6.0 0")
    val Users = stroked("users", "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M16 3.128a4 4 0 0 1 0 7.744M22 21v-2a4 4 0 0 0-3-3.87M5.0 7.0a4.0 4.0 0 1 0 8.0 0a4.0 4.0 0 1 0 -8.0 0")
    val Disc = stroked("disc-3", "M2.0 12.0a10.0 10.0 0 1 0 20.0 0a10.0 10.0 0 1 0 -20.0 0M6 12c0-1.7.7-3.2 1.8-4.2M10.0 12.0a2.0 2.0 0 1 0 4.0 0a2.0 2.0 0 1 0 -4.0 0M18 12c0 1.7-.7 3.2-1.8 4.2")
    val Music = stroked("music", "M21 16V3a1 1 0 0 0-1.28-.96l-10 2.917a1 1 0 0 0-.72.96V19M15.0 16.0a3.0 3.0 0 1 0 6.0 0a3.0 3.0 0 1 0 -6.0 0M3.0 19.0a3.0 3.0 0 1 0 6.0 0a3.0 3.0 0 1 0 -6.0 0")
    val Radio = stroked("radio", "M16.247 7.761a6 6 0 0 1 0 8.478M19.075 4.933a10 10 0 0 1 0 14.134M4.925 19.067a10 10 0 0 1 0-14.134M7.753 16.239a6 6 0 0 1 0-8.478M10.0 12.0a2.0 2.0 0 1 0 4.0 0a2.0 2.0 0 1 0 -4.0 0")
    val CloudDownload = stroked("cloud-download", "M12 13v8l-4-4m12 21 4-4M4.393 15.269A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.436 8.284")
    val Download = stroked("download", "M12 15V3M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4m7 10 5 5 5-5")
    val ListMusic = stroked("list-music", "M16 5H3M11 12H3M11 19H3M21 16V5M15.0 16.0a3.0 3.0 0 1 0 6.0 0a3.0 3.0 0 1 0 -6.0 0")
    val Plus = stroked("plus", "M5 12h14M12 5v14")
    val Close = stroked("x", "M18 6 6 18m6 6 12 12")
    val Check = stroked("check", "M20 6 9 17l-5-5")
    val ChevronLeft = stroked("chevron-left", "m15 18-6-6 6-6")
    val ChevronRight = stroked("chevron-right", "m9 18 6-6-6-6")
    val ChevronDown = stroked("chevron-down", "m6 9 6 6 6-6")
    val MoreVertical = stroked("more-vertical", "M11.0 12.0a1.0 1.0 0 1 0 2.0 0a1.0 1.0 0 1 0 -2.0 0M11.0 5.0a1.0 1.0 0 1 0 2.0 0a1.0 1.0 0 1 0 -2.0 0M11.0 19.0a1.0 1.0 0 1 0 2.0 0a1.0 1.0 0 1 0 -2.0 0")
    val MoreHorizontal = stroked("more-horizontal", "M4.0 12.0a1.0 1.0 0 1 0 2.0 0a1.0 1.0 0 1 0 -2.0 0M11.0 12.0a1.0 1.0 0 1 0 2.0 0a1.0 1.0 0 1 0 -2.0 0M18.0 12.0a1.0 1.0 0 1 0 2.0 0a1.0 1.0 0 1 0 -2.0 0")
    val Sun = stroked("sun", "M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8")
    val Moon = stroked("moon", "M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z")
    val Monitor = stroked("monitor", "M2 3h20v14H2zM8 21h8M12 17v4")
    val Clock = stroked("clock", "M2.0 12.0a10.0 10.0 0 1 0 20.0 0a10.0 10.0 0 1 0 -20.0 0M12 6v6l4 2")
    val LogOut = stroked("log-out", "m16 17 5-5-5-5M21 12H9M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4")
    val Link = stroked("link", "M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71")
    val Refresh = stroked("refresh-cw", "M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8M21 3v5h-5M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16M8 16H3v5")
    val WifiOff = stroked("wifi-off", "M12 20h.01M8.5 16.429a5 5 0 0 1 7 0M5 12.859a10 10 0 0 1 5.17-2.69M19 12.859a10 10 0 0 0-2.007-1.523M2 8.82a15 15 0 0 1 4.177-2.643M22 8.82a15 15 0 0 0-11.288-3.764m2 2 20 20")
    val Trash = stroked("trash-2", "M10 11v6M14 11v6M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2")
    val FolderPlus = stroked("folder-plus", "M12 10v6M9 13h6M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z")
    val Alert = stroked("triangle-alert", "m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3M12 9v4M12 17h.01")
    val Info = stroked("info", "M2.0 12.0a10.0 10.0 0 1 0 20.0 0a10.0 10.0 0 1 0 -20.0 0M12 16v-4M12 8h.01")
    val Help = stroked("circle-help", "M2.0 12.0a10.0 10.0 0 1 0 20.0 0a10.0 10.0 0 1 0 -20.0 0M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3M12 17h.01")
    val ArrowUpRight = stroked("arrow-up-right", "M7 7h10v10M7 17 17 7")
    val Smartphone = stroked("smartphone", "M7.0 2.0H17.0a2.0 2.0 0 0 1 2.0 2.0V20.0a2.0 2.0 0 0 1 -2.0 2.0H7.0a2.0 2.0 0 0 1 -2.0 -2.0V4.0a2.0 2.0 0 0 1 2.0 -2.0ZM12 18h.01")
    val Sparkles = stroked("sparkles", "M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594zM20 2v4M22 4h-4M2.0 20.0a2.0 2.0 0 1 0 4.0 0a2.0 2.0 0 1 0 -4.0 0")
    val Cast = stroked("cast", "M2 8V6a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-6M2 12a9 9 0 0 1 8 8M2 16a5 5 0 0 1 4 4M2 20L2.01 20")
    val SquareCheck = stroked("square-check", "M5.0 3.0H19.0a2.0 2.0 0 0 1 2.0 2.0V19.0a2.0 2.0 0 0 1 -2.0 2.0H5.0a2.0 2.0 0 0 1 -2.0 -2.0V5.0a2.0 2.0 0 0 1 2.0 -2.0Zm16 9-5.5 5.5L8 12")
    val Circle = stroked("circle", "M2.0 12.0a10.0 10.0 0 1 0 20.0 0a10.0 10.0 0 1 0 -20.0 0")
    val Pin = stroked("pin", "M12 17v5M9 10.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V7a1 1 0 0 1 1-1 2 2 0 0 0 0-4H8a2 2 0 0 0 0 4 1 1 0 0 1 1 1z")
    val Text = stroked("text", "M17 6.1H3M21 12.1H3M15.1 18H3")
}
