import SwiftUI
import Foundation

/// Five palette families from the supplied swatch sheet. A bare family id
/// follows the system appearance; `*-light` / `*-dark` pins one half.
enum PaletteID: String, CaseIterable, Identifiable {
    case violet, indigo, sky, aqua, mint

    var id: String { rawValue }
    var label: String { rawValue.capitalized }

    static func resolve(_ raw: String) -> PaletteID {
        let key = raw.lowercased().trimmingCharacters(in: .whitespacesAndNewlines)
        switch key {
        case "flufi", "dark", "dusk", "paper", "light", "rose", "copper", "mocha":
            return .violet
        case "ink", "amoled":
            return .indigo
        case "midnight":
            return .sky
        case "tide":
            return .aqua
        case "forest":
            return .mint
        default:
            return allCases.first { key == $0.rawValue || key.hasPrefix("\($0.rawValue)-") } ?? .violet
        }
    }
}

/// Concrete Material 3-style tokens for one light or dark variant.
struct PaletteTokens {
    let bg: Color
    let bg2: Color
    let surface: Color
    let surface2: Color
    let fg: Color
    let dim: Color
    let dim2: Color
    let line: Color
    let line2: Color
    let accent: Color
    let accentFg: Color
    let success: Color
    let isDark: Bool

    var accentSoft: Color { accent.opacity(isDark ? 0.16 : 0.10) }
    var accentWash: Color { accent.opacity(isDark ? 0.08 : 0.05) }
}

struct PaletteFamily {
    let id: PaletteID
    let light: PaletteTokens
    let dark: PaletteTokens

    func resolve(_ darkMode: Bool) -> PaletteTokens { darkMode ? dark : light }
}

enum Theme {
    static let violet = PaletteFamily(
        id: .violet,
        light: PaletteTokens(bg: Color(hex: "F5F2FF"), bg2: Color(hex: "EDE7FF"),
                             surface: Color(hex: "FFFFFF"), surface2: Color(hex: "F7F4FF"),
                             fg: Color(hex: "08060D"), dim: Color(hex: "473872"),
                             dim2: Color(hex: "6A54AA"), line: Color(hex: "DACDFF"),
                             line2: Color(hex: "CAB8FF"), accent: Color(hex: "9F7EFF"),
                             accentFg: Color(hex: "08060D"), success: Color(hex: "1DB954"), isDark: false),
        dark: PaletteTokens(bg: Color(hex: "171721"), bg2: Color(hex: "222130"),
                            surface: Color(hex: "2A293C"), surface2: Color(hex: "444361"),
                            fg: Color(hex: "FFFFFF"), dim: Color(hex: "AAAAB7"),
                            dim2: Color(hex: "8B8A9D"), line: Color(hex: "35344B"),
                            line2: Color(hex: "605F78"), accent: Color(hex: "9F7EFF"),
                            accentFg: Color(hex: "08060D"), success: Color(hex: "1DB954"), isDark: true)
    )

    static let indigo = PaletteFamily(
        id: .indigo,
        light: PaletteTokens(bg: Color(hex: "F2F4FF"), bg2: Color(hex: "E8EBFF"),
                             surface: Color(hex: "FFFFFF"), surface2: Color(hex: "F5F6FF"),
                             fg: Color(hex: "08060D"), dim: Color(hex: "3B4172"),
                             dim2: Color(hex: "5761AA"), line: Color(hex: "CFD5FF"),
                             line2: Color(hex: "BAC3FF"), accent: Color(hex: "8293FF"),
                             accentFg: Color(hex: "08060D"), success: Color(hex: "1DB954"), isDark: false),
        dark: PaletteTokens(bg: Color(hex: "12171F"), bg2: Color(hex: "1B212D"),
                            surface: Color(hex: "212838"), surface2: Color(hex: "36425B"),
                            fg: Color(hex: "FFFFFF"), dim: Color(hex: "A4A9B5"),
                            dim2: Color(hex: "828999"), line: Color(hex: "2A3346"),
                            line2: Color(hex: "545E73"), accent: Color(hex: "8293FF"),
                            accentFg: Color(hex: "08060D"), success: Color(hex: "1DB954"), isDark: true)
    )

    static let sky = PaletteFamily(
        id: .sky,
        light: PaletteTokens(bg: Color(hex: "F1F8FE"), bg2: Color(hex: "E7F3FE"),
                             surface: Color(hex: "FFFFFF"), surface2: Color(hex: "F4F9FE"),
                             fg: Color(hex: "08060D"), dim: Color(hex: "385272"),
                             dim2: Color(hex: "527CA9"), line: Color(hex: "CCE5FE"),
                             line2: Color(hex: "B6DAFE"), accent: Color(hex: "7BBDFE"),
                             accentFg: Color(hex: "08060D"), success: Color(hex: "1DB954"), isDark: false),
        dark: PaletteTokens(bg: Color(hex: "182127"), bg2: Color(hex: "222F39"),
                            surface: Color(hex: "2A3A46"), surface2: Color(hex: "455F72"),
                            fg: Color(hex: "FFFFFF"), dim: Color(hex: "ABB7BF"),
                            dim2: Color(hex: "8B9BA7"), line: Color(hex: "354A58"),
                            line2: Color(hex: "607787"), accent: Color(hex: "7BBDFE"),
                            accentFg: Color(hex: "08060D"), success: Color(hex: "1DB954"), isDark: true)
    )

    static let aqua = PaletteFamily(
        id: .aqua,
        light: PaletteTokens(bg: Color(hex: "F1FBFC"), bg2: Color(hex: "E7F9FA"),
                             surface: Color(hex: "FFFFFF"), surface2: Color(hex: "F4FCFD"),
                             fg: Color(hex: "08060D"), dim: Color(hex: "386168"),
                             dim2: Color(hex: "53939A"), line: Color(hex: "CDF3F5"),
                             line2: Color(hex: "B6EDF1"), accent: Color(hex: "7CE0E6"),
                             accentFg: Color(hex: "08060D"), success: Color(hex: "1DB954"), isDark: false),
        dark: PaletteTokens(bg: Color(hex: "15241C"), bg2: Color(hex: "1F3328"),
                            surface: Color(hex: "263F32"), surface2: Color(hex: "3E6751"),
                            fg: Color(hex: "FFFFFF"), dim: Color(hex: "A8BAB0"),
                            dim2: Color(hex: "87A093"), line: Color(hex: "30503F"),
                            line2: Color(hex: "5A7D6B"), accent: Color(hex: "7CE0E6"),
                            accentFg: Color(hex: "08060D"), success: Color(hex: "1DB954"), isDark: true)
    )

    static let mint = PaletteFamily(
        id: .mint,
        light: PaletteTokens(bg: Color(hex: "F1FFF5"), bg2: Color(hex: "E7FFEE"),
                             surface: Color(hex: "FFFFFF"), surface2: Color(hex: "F4FFF7"),
                             fg: Color(hex: "08060D"), dim: Color(hex: "386E4C"),
                             dim2: Color(hex: "52A76F"), line: Color(hex: "CCFFDC"),
                             line2: Color(hex: "B6FFCC"), accent: Color(hex: "7BFFA4"),
                             accentFg: Color(hex: "08060D"), success: Color(hex: "1DB954"), isDark: false),
        dark: PaletteTokens(bg: Color(hex: "15241A"), bg2: Color(hex: "1F3425"),
                            surface: Color(hex: "26412E"), surface2: Color(hex: "3E694B"),
                            fg: Color(hex: "FFFFFF"), dim: Color(hex: "A8BBAE"),
                            dim2: Color(hex: "87A28F"), line: Color(hex: "30513A"),
                            line2: Color(hex: "5A7F66"), accent: Color(hex: "7BFFA4"),
                            accentFg: Color(hex: "08060D"), success: Color(hex: "1DB954"), isDark: true)
    )

    static let families: [PaletteFamily] = [violet, indigo, sky, aqua, mint]

    /// Legacy ids keep the half they used to imply. `auto`/`system` and bare
    /// family ids stay unpinned so they still follow the device appearance.
    static func canonicalID(_ raw: String) -> String {
        switch raw.lowercased().trimmingCharacters(in: .whitespacesAndNewlines) {
        case "", "auto", "system":
            return "violet"
        case "flufi", "dark", "dusk", "rose", "copper", "mocha":
            return "violet-dark"
        case "paper", "light":
            return "violet-light"
        case "ink", "amoled":
            return "indigo-dark"
        case "midnight":
            return "sky-dark"
        case "tide":
            return "aqua-dark"
        case "forest":
            return "mint-dark"
        default:
            return raw.lowercased().trimmingCharacters(in: .whitespacesAndNewlines)
        }
    }

    /// Legacy aliases still work; unknown values fall back to Violet.
    static func family(for raw: String) -> PaletteFamily {
        let id = PaletteID.resolve(canonicalID(raw))
        return families.first { $0.id == id } ?? violet
    }

    static func tokens(for raw: String, accentHex: String = "",
                        colorScheme: ColorScheme = .dark) -> PaletteTokens {
        let key = canonicalID(raw)
        let family = family(for: key)
        var tokens: PaletteTokens
        if key.hasSuffix("-light") {
            tokens = family.light
        } else if key.hasSuffix("-dark") {
            tokens = family.dark
        } else {
            tokens = family.resolve(colorScheme == .dark)
        }
        if !accentHex.isEmpty {
            tokens = PaletteTokens(
                bg: tokens.bg, bg2: tokens.bg2, surface: tokens.surface, surface2: tokens.surface2,
                fg: tokens.fg, dim: tokens.dim, dim2: tokens.dim2, line: tokens.line,
                line2: tokens.line2, accent: Color(hex: accentHex),
                accentFg: readableOn(accentHex), success: tokens.success, isDark: tokens.isDark
            )
        }
        return tokens
    }

    static func readableOn(_ hex: String) -> Color {
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
            return Color(hex: "FFFFFF")
        }
        let luminance = 0.299 * r + 0.587 * g + 0.114 * b
        return Color(hex: luminance > 0.55 ? "08060D" : "FFFFFF")
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
    @Environment(\.colorScheme) private var colorScheme
    @AppStorage("palette") private var palette = "violet"
    @AppStorage("accent") private var accentHex = ""

    func body(content: Content) -> some View {
        let tokens = Theme.tokens(for: palette, accentHex: accentHex,
                                  colorScheme: colorScheme)
        content
            .foregroundStyle(tokens.fg)
            .background(tokens.bg.ignoresSafeArea())
            .tint(tokens.accent)
            .preferredColorScheme(tokens.isDark ? .dark : .light)
            .environment(\.mcTokens, tokens)
            .environment(\.mcAccent, tokens.accent)
            .environment(\.mcSurface, tokens.surface)
    }
}

extension View {
    func mcmusicPalette() -> some View {
        modifier(Palette())
    }
}

private struct TokensKey: EnvironmentKey {
    static let defaultValue: PaletteTokens = Theme.violet.dark
}

private struct AccentKey: EnvironmentKey {
    static let defaultValue: Color = Theme.violet.dark.accent
}

private struct SurfaceKey: EnvironmentKey {
    static let defaultValue: Color = Theme.violet.dark.surface
}

extension EnvironmentValues {
    var mcTokens: PaletteTokens {
        get { self[TokensKey.self] }
        set { self[TokensKey.self] = newValue }
    }

    var mcAccent: Color {
        get { self[AccentKey.self] }
        set { self[AccentKey.self] = newValue }
    }

    var mcSurface: Color {
        get { self[SurfaceKey.self] }
        set { self[SurfaceKey.self] = newValue }
    }
}
