import SwiftUI

/// Lucide geometry rendered as SwiftUI paths. No SF Symbols, no icon font, and
/// no downloaded assets: the same 24×24 Lucide outlines used on web/Android.
enum Lucide {
    /// Width multipliers shared by the appearance pickers on every client.
    static let strokeChoices: [Double] = [1, 1.5, 2]
    // BEGIN GENERATED ICONS
    static let paths: [String: [Primitive]] = [
        "audio-lines": [.path("M2 10v3"), .path("M6 6v11"), .path("M10 3v18"), .path("M14 8v7"), .path("M18 5v13"), .path("M22 10v3")],
        "cast": [.path("M2 8V6a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-6"), .path("M2 12a9 9 0 0 1 8 8"), .path("M2 16a5 5 0 0 1 4 4"), .path("M2 20L2.01 20")],
        "check": [.path("M20 6 9 17l-5-5")],
        "chevron-down": [.path("m6 9 6 6 6-6")],
        "chevron-left": [.path("m15 18-6-6 6-6")],
        "chevron-right": [.path("m9 18 6-6-6-6")],
        "chevron-up": [.path("m18 15-6-6-6 6")],
        "circle": [.circle(12, 12, 10)],
        "circle_help": [.circle(12, 12, 10), .path("M9 9.5a3 2.5 0 016 0c0 2-2 2-3 3.5"), .path("M12 17h.01")],
        "circle-alert": [.circle(12, 12, 10), .path("M12 8L12 12"), .path("M12 16L12.01 16")],
        "circle-check": [.circle(12, 12, 10), .path("m16 9-5.5 5.5L8 12")],
        "circle-help": [.circle(12, 12, 10), .path("M9 9.5a3 2.5 0 016 0c0 2-2 2-3 3.5"), .path("M12 17h.01")],
        "circle-x": [.circle(12, 12, 10), .path("m15 9-6 6"), .path("m9 9 6 6")],
        "clock": [.circle(12, 12, 10), .path("M12 6v6l4 2")],
        "coffee": [.path("M10 2v2"), .path("M14 2v2"), .path("M16 8a1 1 0 0 1 1 1v8a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V9a1 1 0 0 1 1-1h14a4 4 0 1 1 0 8h-1"), .path("M6 2v2")],
        "compass": [.circle(12, 12, 10), .path("m16.24 7.76-1.804 5.411a2 2 0 0 1-1.265 1.265L7.76 16.24l1.804-5.411a2 2 0 0 1 1.265-1.265z")],
        "cookie": [.path("M11 17h.01"), .path("M11.496 2c.324-.016.558.292.529.615a4 4 0 004.235 4.368.713.713 0 01.758.757 4 4 0 004.366 4.237c.323-.03.63.204.614.527a10 10 0 01-2.915 6.566A1 1 0 114.93 4.918 10 10 0 0111.496 2"), .path("M12 12h.01"), .path("M16 16h.01"), .path("M16 3h.01"), .path("M21 4h.01"), .path("M21 8h.01"), .path("M7 14h.01"), .path("M9 8h.01")],
        "disc-3": [.circle(12, 12, 10), .path("M6 12c0-1.7.7-3.2 1.8-4.2"), .circle(12, 12, 2), .path("M18 12c0 1.7-.7 3.2-1.8 4.2")],
        "download": [.path("M12 15V3"), .path("M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"), .path("m7 10 5 5 5-5")],
        "dumbbell": [.path("M17.596 12.768a2 2 0 1 0 2.829-2.829l-1.768-1.767a2 2 0 0 0 2.828-2.829l-2.828-2.828a2 2 0 0 0-2.829 2.828l-1.767-1.768a2 2 0 1 0-2.829 2.829z"), .path("m2.5 21.5 1.4-1.4"), .path("m20.1 3.9 1.4-1.4"), .path("M5.343 21.485a2 2 0 1 0 2.829-2.828l1.767 1.768a2 2 0 1 0 2.829-2.829l-6.364-6.364a2 2 0 1 0-2.829 2.829l1.768 1.767a2 2 0 0 0-2.828 2.829z"), .path("m9.6 14.4 4.8-4.8")],
        "ellipsis": [.circle(12, 12, 1), .circle(19, 12, 1), .circle(5, 12, 1)],
        "eye-off": [.path("M10.733 5.076a10.744 10.744 0 0 1 11.205 6.575 1 1 0 0 1 0 .696 10.747 10.747 0 0 1-1.444 2.49"), .path("M14.084 14.158a3 3 0 0 1-4.242-4.242"), .path("M17.479 17.499a10.75 10.75 0 0 1-15.417-5.151 1 1 0 0 1 0-.696 10.75 10.75 0 0 1 4.446-5.143"), .path("m2 2 20 20")],
        "film": [.rect(3, 3, 18, 18, 2), .path("M7 3v18"), .path("M3 7.5h4"), .path("M3 12h18"), .path("M3 16.5h4"), .path("M17 3v18"), .path("M17 7.5h4"), .path("M17 16.5h4")],
        "flame": [.path("M12 3q1 4 4 6.5t3 5.5a1 1 0 0 1-14 0 5 5 0 0 1 1-3 1 1 0 0 0 5 0c0-2-1.5-3-1.5-5q0-2 2.5-4")],
        "flower": [.circle(12, 12, 3), .path("M12 16.5A4.5 4.5 0 1 1 7.5 12 4.5 4.5 0 1 1 12 7.5a4.5 4.5 0 1 1 4.5 4.5 4.5 4.5 0 1 1-4.5 4.5"), .path("M12 7.5V9"), .path("M7.5 12H9"), .path("M16.5 12H15"), .path("M12 16.5V15"), .path("m8 8 1.88 1.88"), .path("M14.12 9.88 16 8"), .path("m8 16 1.88-1.88"), .path("M14.12 14.12 16 16")],
        "folder-plus": [.path("M12 10v6"), .path("M9 13h6"), .path("M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z")],
        "grip-vertical": [.circle(9, 12, 1), .circle(9, 5, 1), .circle(9, 19, 1), .circle(15, 12, 1), .circle(15, 5, 1), .circle(15, 19, 1)],
        "hard-drive": [.path("M10 16h.01"), .path("M2.212 11.577a2 2 0 0 0-.212.896V18a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-5.527a2 2 0 0 0-.212-.896L18.55 5.11A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"), .path("M21.946 12.013H2.054"), .path("M6 16h.01")],
        "headphones": [.path("M3 14h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a9 9 0 0 1 18 0v7a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3")],
        "heart": [.path("M2 9.5a5.5 5.5 0 0 1 9.591-3.676.56.56 0 0 0 .818 0A5.49 5.49 0 0 1 22 9.5c0 2.29-1.5 4-3 5.5l-5.492 5.313a2 2 0 0 1-3 .019L5 15c-1.5-1.5-3-3.2-3-5.5")],
        "home": [.path("M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"), .path("M3 10a2 2 0 0 1 .709-1.528l7-6a2 2 0 0 1 2.582 0l7 6A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z")],
        "house": [.path("M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"), .path("M3 10a2 2 0 0 1 .709-1.528l7-6a2 2 0 0 1 2.582 0l7 6A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z")],
        "image": [.rect(3, 3, 18, 18, 2), .circle(9, 9, 2), .path("m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21")],
        "inbox": [.path("M22 12L16 12L14 15L10 15L8 12L2 12"), .path("M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z")],
        "info": [.circle(12, 12, 10), .path("M12 16v-4"), .path("M12 8h.01")],
        "key": [.path("m2 21 9.6-9.6"), .path("m7.5 15.5 2.3 2.3a1 1 0 0 1 0 1.4l-2.1 2.1a1 1 0 0 1-1.4 0L4 19"), .circle(15.5, 7.5, 5.5)],
        "library": [.path("m16 6 4 14"), .path("M12 6v14"), .path("M8 8v12"), .path("M4 4v16")],
        "link": [.path("M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"), .path("M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71")],
        "list": [.path("M3 5h.01"), .path("M3 12h.01"), .path("M3 19h.01"), .path("M8 5h13"), .path("M8 12h13"), .path("M8 19h13")],
        "list-music": [.path("M16 5H3"), .path("M11 12H3"), .path("M11 19H3"), .path("M21 16V5"), .circle(18, 16, 3)],
        "list-plus": [.path("M16 5H3"), .path("M11 12H3"), .path("M16 19H3"), .path("M18 9v6"), .path("M21 12h-6")],
        "loader-circle": [.path("M21 12a9 9 0 1 1-6.219-8.56")],
        "lock": [.rect(3, 11, 18, 11, 2), .path("M7 11V7a5 5 0 0 1 10 0v4")],
        "log-in": [.path("m10 17 5-5-5-5"), .path("M15 12H3"), .path("M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4")],
        "log-out": [.path("m16 17 5-5-5-5"), .path("M21 12H9"), .path("M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4")],
        "mail": [.path("m22 7-8.991 5.727a2 2 0 0 1-2.009 0L2 7"), .rect(2, 4, 20, 16, 2)],
        "message-circle": [.path("M2.992 16.342a2 2 0 0 1 .094 1.167l-1.065 3.29a1 1 0 0 0 1.236 1.168l3.413-.998a2 2 0 0 1 1.099.092 10 10 0 1 0-4.777-4.719")],
        "mic-vocal": [.path("m11 7.601-5.994 8.19a1 1 0 0 0 .1 1.298l.817.818a1 1 0 0 0 1.314.087L15.09 12"), .path("M16.5 21.174C15.5 20.5 14.372 20 13 20c-2.058 0-3.928 2.356-6 2-2.072-.356-2.775-3.369-1.5-4.5"), .circle(16, 7, 5)],
        "monitor": [.rect(2, 3, 20, 14, 2), .path("M8 21L16 21"), .path("M12 17L12 21")],
        "moon": [.path("M20.985 12.486a9 9 0 1 1-9.473-9.472c.405-.022.617.46.402.803a6 6 0 0 0 8.268 8.268c.344-.215.825-.004.803.401")],
        "more-horizontal": [.circle(12, 12, 1), .circle(19, 12, 1), .circle(5, 12, 1)],
        "music": [.path("M21 16V3a1 1 0 0 0-1.28-.96l-10 2.917a1 1 0 0 0-.72.96V19"), .circle(18, 16, 3), .circle(6, 19, 3)],
        "music-note": [.path("M21 16V3a1 1 0 0 0-1.28-.96l-10 2.917a1 1 0 0 0-.72.96V19"), .circle(18, 16, 3), .circle(6, 19, 3)],
        "palette": [.path("M12 22a1 1 0 0 1 0-20 10 9 0 0 1 10 9 5 5 0 0 1-5 5h-2.25a1.75 1.75 0 0 0-1.4 2.8l.3.4a1.75 1.75 0 0 1-1.4 2.8z"), .circle(13.5, 6.5, 0.5), .circle(17.5, 10.5, 0.5), .circle(6.5, 12.5, 0.5), .circle(8.5, 7.5, 0.5)],
        "pause": [.rect(14, 3, 5, 18, 1), .rect(5, 3, 5, 18, 1)],
        "pencil": [.path("M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z"), .path("m15 5 4 4")],
        "pentagon": [.path("M10.83 2.38a2 2 0 0 1 2.34 0l8 5.74a2 2 0 0 1 .73 2.25l-3.04 9.26a2 2 0 0 1-1.9 1.37H7.04a2 2 0 0 1-1.9-1.37L2.1 10.37a2 2 0 0 1 .73-2.25z")],
        "picture-in-picture-2": [.path("M21 9V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v10c0 1.1.9 2 2 2h4"), .rect(12, 13, 10, 7, 2)],
        "pin": [.path("M12 17v5"), .path("M9 10.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V7a1 1 0 0 1 1-1 2 2 0 0 0 0-4H8a2 2 0 0 0 0 4 1 1 0 0 1 1 1z")],
        "play": [.path("M5 5a2 2 0 0 1 3.008-1.728l11.997 6.998a2 2 0 0 1 .003 3.458l-12 7A2 2 0 0 1 5 19z")],
        "plus": [.path("M5 12h14"), .path("M12 5v14")],
        "radio": [.path("M16.247 7.761a6 6 0 0 1 0 8.478"), .path("M19.075 4.933a10 10 0 0 1 0 14.134"), .path("M4.925 19.067a10 10 0 0 1 0-14.134"), .path("M7.753 16.239a6 6 0 0 1 0-8.478"), .circle(12, 12, 2)],
        "refresh-cw": [.path("M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"), .path("M21 3v5h-5"), .path("M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"), .path("M8 16H3v5")],
        "repeat": [.path("m17 2 4 4-4 4"), .path("M3 11v-1a4 4 0 0 1 4-4h14"), .path("m7 22-4-4 4-4"), .path("M21 13v1a4 4 0 0 1-4 4H3")],
        "repeat-1": [.path("m17 2 4 4-4 4"), .path("M3 11v-1a4 4 0 0 1 4-4h14"), .path("m7 22-4-4 4-4"), .path("M21 13v1a4 4 0 0 1-4 4H3"), .path("M11 10h1v4")],
        "search": [.path("m21 21-4.34-4.34"), .circle(11, 11, 8)],
        "server": [.rect(2, 2, 20, 8, 2), .rect(2, 14, 20, 8, 2), .path("M6 6L6.01 6"), .path("M6 18L6.01 18")],
        "settings": [.path("M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"), .circle(12, 12, 3)],
        "shield": [.path("M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z")],
        "shield-alert": [.path("M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"), .path("M12 8v4"), .path("M12 16h.01")],
        "shield-check": [.path("M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"), .path("m9 12 2 2 4-4")],
        "shuffle": [.path("m18 14 4 4-4 4"), .path("m18 2 4 4-4 4"), .path("M2 18h1.973a4 4 0 0 0 3.3-1.7l5.454-8.6a4 4 0 0 1 3.3-1.7H22"), .path("M2 6h1.972a4 4 0 0 1 3.6 2.2"), .path("M22 18h-6.041a4 4 0 0 1-3.3-1.8l-.359-.45")],
        "skip-back": [.path("M17.971 4.285A2 2 0 0 1 21 6v12a2 2 0 0 1-3.029 1.715l-9.997-5.998a2 2 0 0 1-.003-3.432z"), .path("M3 20V4")],
        "skip-forward": [.path("M21 4v16"), .path("M6.029 4.285A2 2 0 0 0 3 6v12a2 2 0 0 0 3.029 1.715l9.997-5.998a2 2 0 0 0 .003-3.432z")],
        "smartphone": [.rect(5, 2, 14, 20, 2), .path("M12 18h.01")],
        "sparkles": [.path("M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z"), .path("M20 2v4"), .path("M22 4h-4"), .circle(4, 20, 2)],
        "squircle": [.path("M12 3c7.2 0 9 1.8 9 9s-1.8 9-9 9-9-1.8-9-9 1.8-9 9-9")],
        "star": [.path("M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z")],
        "trash": [.path("M10 11v6"), .path("M14 11v6"), .path("M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"), .path("M3 6h18"), .path("M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2")],
        "trash-2": [.path("M10 11v6"), .path("M14 11v6"), .path("M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"), .path("M3 6h18"), .path("M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2")],
        "user": [.circle(12, 8, 5), .path("M20 21a8 8 0 0 0-16 0")],
        "user-round": [.circle(12, 8, 5), .path("M20 21a8 8 0 0 0-16 0")],
        "volume-1": [.path("M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"), .path("M16 9a5 5 0 0 1 0 6")],
        "volume-2": [.path("M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"), .path("M16 9a5 5 0 0 1 0 6"), .path("M19.364 18.364a9 9 0 0 0 0-12.728")],
        "volume-x": [.path("M11 4.702a.7.7 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.7.7 0 0 0 11 19.298z"), .path("m16.5 14.5 5-5"), .path("m16.5 9.5 5 5")],
        "wifi": [.path("M12 20h.01"), .path("M2 8.82a15 15 0 0 1 20 0"), .path("M5 12.859a10 10 0 0 1 14 0"), .path("M8.5 16.429a5 5 0 0 1 7 0")],
        "wifi-off": [.path("M12 20h.01"), .path("M8.5 16.429a5 5 0 0 1 7 0"), .path("M5 12.859a10 10 0 0 1 5.17-2.69"), .path("M19 12.859a10 10 0 0 0-2.007-1.523"), .path("M2 8.82a15 15 0 0 1 4.177-2.643"), .path("M22 8.82a15 15 0 0 0-11.288-3.764"), .path("m2 2 20 20")],
        "x": [.path("M18 6 6 18"), .path("m6 6 12 12")],
        "x-circle": [.circle(12, 12, 10), .path("m15 9-6 6"), .path("m9 9 6 6")],
        "zap": [.path("M15.914 4a1.5 1.5 0 00-2.474-1.561l-9 9A1.5 1.5 0 005.5 14h4.002a.5.5 0 01.471.666L8.086 20a1.5 1.5 0 002.475 1.56l9-9A1.5 1.5 0 0018.5 10h-3.997a.5.5 0 01-.472-.667z")],
    ]
    // END GENERATED ICONS

    static let fallback = "circle-help"

    /// Keep values arriving from older servers or hand-edited storage on the
    /// same 1x / 1.5x / 2x scale as the picker.
    static func nearestStroke(_ value: Double) -> Double {
        strokeChoices.min { abs($0 - value) < abs($1 - value) } ?? 1
    }

    /// Lucide draws on a 24x24 grid with a standard stroke of 2, so `scale`
    /// 1/1.5/2 renders at 2/3/4 viewBox units (`size * scale / 12` points).
    /// The `size / 6` ceiling keeps 2x from crowding small icons; there is no
    /// pixel floor, so 1x stays at Lucide's default weight.
    static func strokeWidth(_ scale: Double, size: CGFloat) -> CGFloat {
        let base = Double(size) * scale / 12
        return CGFloat(min(base, Double(size) / 6))
    }

    enum Primitive {
        case path(String)
        case circle(Double, Double, Double)
        case rect(Double, Double, Double, Double, Double)

        /// Only Lucide primitives that are already simple shapes can be
        /// filled without turning a detailed outline into a solid blob.
        var isFillable: Bool {
            switch self {
            case .circle, .rect: return true
            case .path: return false
            }
        }

        func add(to path: inout Path, scale: CGFloat) {
            switch self {
            case .path(let d):
                path.addPath(Self.build(d, scale: scale))
            case .circle(let x, let y, let r):
                path.addEllipse(in: CGRect(x: (x - r) * scale, y: (y - r) * scale,
                                           width: r * 2 * scale, height: r * 2 * scale))
            case .rect(let x, let y, let w, let h, let radius):
                path.addPath(Path(roundedRect: CGRect(x: x * scale, y: y * scale,
                                                      width: w * scale, height: h * scale),
                                  cornerRadius: radius * scale))
            }
        }

        private enum Token {
            case command(Character)
            case number(Double)
        }

        private static func build(_ d: String, scale: CGFloat) -> Path {
            var tokens: [Token] = []
            let chars = Array(d)
            var i = 0
            while i < chars.count {
                let ch = chars[i]
                if ch.isLetter {
                    tokens.append(.command(ch))
                    i += 1
                } else if ch.isNumber || ch == "-" || ch == "." {
                    var text = ""
                    while i < chars.count && (chars[i].isNumber || chars[i] == "-" || chars[i] == ".") {
                        text.append(chars[i]); i += 1
                    }
                    if let value = Double(text) { tokens.append(.number(value)) }
                } else {
                    i += 1
                }
            }

            var path = Path()
            var current = CGPoint.zero
            var start = CGPoint.zero
            var command: Character? = nil
            var index = 0

            func number() -> Double? {
                guard index < tokens.count, case .number(let value) = tokens[index] else { return nil }
                index += 1
                return value
            }
            func point(_ relative: Bool) -> CGPoint? {
                guard let x = number(), let y = number() else { return nil }
                return relative ? CGPoint(x: current.x + x * scale, y: current.y + y * scale)
                                : CGPoint(x: x * scale, y: y * scale)
            }

            while index < tokens.count {
                var consumedCommand = false
                if case .command(let c) = tokens[index] {
                    command = c
                    index += 1
                    consumedCommand = true
                }
                guard let active = command else { break }
                let relative = active.isLowercase
                switch active.lowercased() {
                case "m":
                    guard let next = point(relative) else { return path }
                    current = next; start = next
                    path.move(to: next)
                    command = relative ? "l" : "L"
                case "l":
                    guard let next = point(relative) else { return path }
                    current = next
                    path.addLine(to: next)
                case "h":
                    guard let value = number() else { return path }
                    current = CGPoint(x: relative ? current.x + value * scale : value * scale, y: current.y)
                    path.addLine(to: current)
                case "v":
                    guard let value = number() else { return path }
                    current = CGPoint(x: current.x, y: relative ? current.y + value * scale : value * scale)
                    path.addLine(to: current)
                case "c":
                    guard let c1 = point(relative), let c2 = point(relative), let end = point(relative) else { return path }
                    path.addCurve(to: end, control1: c1, control2: c2)
                    current = end
                case "z":
                    path.closeSubpath()
                    current = start
                    command = nil
                    // The command token was already consumed above; only skip
                    // a stray operand here (e.g. a malformed "Z 0 0").
                    if !consumedCommand { index += 1 }
                default:
                    index += 1
                }
            }
            return path
        }
    }
}

/// Draws a named Lucide glyph, tinted by the current foreground style unless a
/// colour is supplied. This is the only icon component used by the iOS client.
struct LucideIcon: View {
    let name: String
    var size: CGFloat = 20
    var color: Color?

    @AppStorage("iconStroke") private var iconStroke = 1.0
    @AppStorage("iconFilled") private var iconFilled = false

    private var primitives: [Lucide.Primitive] {
        Lucide.paths[name] ?? Lucide.paths[Lucide.fallback] ?? []
    }

    /// A nil colour inherits the ambient foreground style (currentColor);
    /// a supplied colour overrides it for stateful icons.
    private var foreground: AnyShapeStyle {
        if let color { return AnyShapeStyle(color) }
        return AnyShapeStyle(HierarchicalShapeStyle.primary)
    }

    private var strokeWidth: CGFloat {
        Lucide.strokeWidth(iconStroke, size: size)
    }

    var body: some View {
        ZStack {
            ForEach(Array(primitives.enumerated()), id: \.offset) { item in
                let shape = LucideShape(primitive: item.element, scale: size / 24)
                if iconFilled && item.element.isFillable {
                    shape.fill(foreground)
                } else {
                    shape.stroke(style: StrokeStyle(lineWidth: strokeWidth,
                                                    lineCap: .round, lineJoin: .round))
                }
            }
        }
        .frame(width: size, height: size)
        .foregroundStyle(foreground)
    }
}

private struct LucideShape: Shape {
    let primitive: Lucide.Primitive
    let scale: CGFloat

    func path(in rect: CGRect) -> Path {
        var path = Path()
        primitive.add(to: &path, scale: scale)
        return path
    }
}
