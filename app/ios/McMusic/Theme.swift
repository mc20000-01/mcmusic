import SwiftUI

/// The shared mcmusic design tokens (ink + violet), mirrored from the web and
/// Android clients. All screens use these colours rather than system defaults.
enum Theme {
    static let ink = Color(hex: "08060D")
    static let violet = Color(hex: "A06BFF")
    static let surface = Color(hex: "14111C")
    static let surface2 = Color(hex: "1D1927")
    static let line = Color(hex: "2C2539")
    static let text = Color(hex: "F2F0F7")
    static let dim = Color(hex: "A6A0B5")

    static let palettes: [String: [Color]] = [
        "dusk": [Color(hex: "08060D"), Color(hex: "14111C"), Color(hex: "A06BFF")],
        "paper": [Color(hex: "F6F4F1"), Color(hex: "FFFFFF"), Color(hex: "6A4BB5")],
        "ink": [Color(hex: "050609"), Color(hex: "101318"), Color(hex: "7BD6A0")],
        "tide": [Color(hex: "06151B"), Color(hex: "0B232E"), Color(hex: "56C7D8")],
        "copper": [Color(hex: "160E09"), Color(hex: "241710"), Color(hex: "E39B62")],
        "forest": [Color(hex: "08150E"), Color(hex: "102118"), Color(hex: "7BD6A0")],
        "rose": [Color(hex: "190C13"), Color(hex: "28121D"), Color(hex: "F09ABC")]
    ]

    static func background(_ name: String) -> Color {
        palettes[name]?.first ?? ink
    }

    static func surface(_ name: String) -> Color {
        palettes[name]?[safe: 1] ?? surface
    }

    static func accent(_ name: String) -> Color {
        palettes[name]?[safe: 2] ?? violet
    }
}

extension Array {
    subscript(safe index: Int) -> Element? {
        indices.contains(index) ? self[index] : nil
    }
}

extension Color {
    init(hex: String) {
        let cleaned = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var value: UInt64 = 0
        Scanner(string: cleaned).scanHexInt64(&value)
        let r, g, b: Double
        switch cleaned.count {
        case 6:
            r = Double((value >> 16) & 0xFF) / 255
            g = Double((value >> 8) & 0xFF) / 255
            b = Double(value & 0xFF) / 255
        case 3:
            r = Double((value >> 8) & 0xF) / 15
            g = Double((value >> 4) & 0xF) / 15
            b = Double(value & 0xF) / 15
        default:
            r = 0.04; g = 0.02; b = 0.05
        }
        self.init(.sRGB, red: r, green: g, blue: b, opacity: 1)
    }
}

struct Palette: ViewModifier {
    @AppStorage("palette") private var palette = "dusk"
    @AppStorage("accent") private var accentHex = ""

    func body(content: Content) -> some View {
        let base = Theme.background(palette)
        let accent = accentHex.isEmpty ? Theme.accent(palette) : Color(hex: accentHex)
        content
            .background(base.ignoresSafeArea())
            .tint(accent)
            .environment(\.mcAccent, accent)
            .environment(\.mcSurface, Theme.surface(palette))
    }
}

extension View {
    func mcmusicPalette() -> some View {
        modifier(Palette())
    }
}

private struct AccentKey: EnvironmentKey {
    static let defaultValue: Color = Theme.violet
}

private struct SurfaceKey: EnvironmentKey {
    static let defaultValue: Color = Theme.surface
}

extension EnvironmentValues {
    var mcAccent: Color {
        get { self[AccentKey.self] }
        set { self[AccentKey.self] = newValue }
    }

    var mcSurface: Color {
        get { self[SurfaceKey.self] }
        set { self[SurfaceKey.self] = newValue }
    }
}
