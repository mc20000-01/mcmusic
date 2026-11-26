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
    let accentText: Color
    let accentFg: Color
    // Generated Material 3 tonal roles (HCT from this family's accent seed).
    let primary: Color, onPrimary: Color, primaryContainer: Color, onPrimaryContainer: Color
    let secondary: Color, onSecondary: Color, secondaryContainer: Color, onSecondaryContainer: Color
    let tertiary: Color, onTertiary: Color, tertiaryContainer: Color, onTertiaryContainer: Color
    let error: Color, onError: Color, errorContainer: Color, onErrorContainer: Color
    let background: Color, onBackground: Color, onSurface: Color
    let surfaceVariant: Color, onSurfaceVariant: Color
    let surfaceContainerLowest: Color, surfaceContainerLow: Color, surfaceContainer: Color
    let surfaceContainerHigh: Color, surfaceContainerHighest: Color
    let outline: Color, outlineVariant: Color
    let inverseSurface: Color, inverseOnSurface: Color, inversePrimary: Color
    let scrim: Color, shadow: Color
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
    // BEGIN GENERATED PALETTES
    static let violet = PaletteFamily(
        id: .violet,
        light: PaletteTokens(bg: Color(hex: "F5F2FF"), bg2: Color(hex: "EDE7FF"), surface: Color(hex: "FFFFFF"), surface2: Color(hex: "F7F4FF"), fg: Color(hex: "08060D"), dim: Color(hex: "473872"), dim2: Color(hex: "6A54AA"), line: Color(hex: "DACDFF"), line2: Color(hex: "CAB8FF"), accent: Color(hex: "9F7EFF"), accentText: Color(hex: "5B3F9E"), accentFg: Color(hex: "08060D"), primary: Color(hex: "64558F"), onPrimary: Color(hex: "FFFFFF"), primaryContainer: Color(hex: "E8DDFF"), onPrimaryContainer: Color(hex: "4C3E76"), secondary: Color(hex: "615B71"), onSecondary: Color(hex: "FFFFFF"), secondaryContainer: Color(hex: "E8DEF8"), onSecondaryContainer: Color(hex: "494458"), tertiary: Color(hex: "7D5261"), onTertiary: Color(hex: "FFFFFF"), tertiaryContainer: Color(hex: "FFD9E3"), onTertiaryContainer: Color(hex: "633B49"), error: Color(hex: "BA1A1A"), onError: Color(hex: "FFFFFF"), errorContainer: Color(hex: "FFDAD6"), onErrorContainer: Color(hex: "93000A"), background: Color(hex: "FFFBFF"), onBackground: Color(hex: "1D1927"), onSurface: Color(hex: "1D1927"), surfaceVariant: Color(hex: "E7DFF3"), onSurfaceVariant: Color(hex: "494454"), surfaceContainerLowest: Color(hex: "FFFBFF"), surfaceContainerLow: Color(hex: "F8F1FF"), surfaceContainer: Color(hex: "F3EAFE"), surfaceContainerHigh: Color(hex: "EDE5F9"), surfaceContainerHighest: Color(hex: "E7DFF3"), outline: Color(hex: "79757F"), outlineVariant: Color(hex: "878192"), inverseSurface: Color(hex: "322E3D"), inverseOnSurface: Color(hex: "F5EEFF"), inversePrimary: Color(hex: "CEBDFE"), scrim: Color(hex: "000000"), shadow: Color(hex: "000000"), success: Color(hex: "1DB954"), isDark: false),
        dark: PaletteTokens(bg: Color(hex: "171721"), bg2: Color(hex: "222130"), surface: Color(hex: "2A293C"), surface2: Color(hex: "444361"), fg: Color(hex: "FFFFFF"), dim: Color(hex: "AAAAB7"), dim2: Color(hex: "8B8A9D"), line: Color(hex: "35344B"), line2: Color(hex: "605F78"), accent: Color(hex: "9F7EFF"), accentText: Color(hex: "C6B2FF"), accentFg: Color(hex: "08060D"), primary: Color(hex: "CEBDFE"), onPrimary: Color(hex: "35275D"), primaryContainer: Color(hex: "4C3E76"), onPrimaryContainer: Color(hex: "E8DDFF"), secondary: Color(hex: "CBC3DC"), onSecondary: Color(hex: "332E41"), secondaryContainer: Color(hex: "494458"), onSecondaryContainer: Color(hex: "E8DEF8"), tertiary: Color(hex: "EFB8C9"), onTertiary: Color(hex: "492533"), tertiaryContainer: Color(hex: "633B49"), onTertiaryContainer: Color(hex: "FFD9E3"), error: Color(hex: "FFB4AB"), onError: Color(hex: "690005"), errorContainer: Color(hex: "93000A"), onErrorContainer: Color(hex: "FFDAD6"), background: Color(hex: "15111F"), onBackground: Color(hex: "F5EEFF"), onSurface: Color(hex: "F5EEFF"), surfaceVariant: Color(hex: "3B3746"), onSurfaceVariant: Color(hex: "CBC3D6"), surfaceContainerLowest: Color(hex: "0F0C19"), surfaceContainerLow: Color(hex: "1D1927"), surfaceContainer: Color(hex: "211E2B"), surfaceContainerHigh: Color(hex: "2C2836"), surfaceContainerHighest: Color(hex: "373341"), outline: Color(hex: "938F99"), outlineVariant: Color(hex: "878192"), inverseSurface: Color(hex: "F5EEFF"), inverseOnSurface: Color(hex: "322E3D"), inversePrimary: Color(hex: "64558F"), scrim: Color(hex: "000000"), shadow: Color(hex: "000000"), success: Color(hex: "1DB954"), isDark: true)
    )

    static let indigo = PaletteFamily(
        id: .indigo,
        light: PaletteTokens(bg: Color(hex: "F2F4FF"), bg2: Color(hex: "E8EBFF"), surface: Color(hex: "FFFFFF"), surface2: Color(hex: "F5F6FF"), fg: Color(hex: "08060D"), dim: Color(hex: "3B4172"), dim2: Color(hex: "5761AA"), line: Color(hex: "CFD5FF"), line2: Color(hex: "BAC3FF"), accent: Color(hex: "8293FF"), accentText: Color(hex: "4A56A8"), accentFg: Color(hex: "08060D"), primary: Color(hex: "525A92"), onPrimary: Color(hex: "FFFFFF"), primaryContainer: Color(hex: "DEE0FF"), onPrimaryContainer: Color(hex: "3A4379"), secondary: Color(hex: "5B5D72"), onSecondary: Color(hex: "FFFFFF"), secondaryContainer: Color(hex: "E0E1F9"), onSecondaryContainer: Color(hex: "434559"), tertiary: Color(hex: "77536D"), onTertiary: Color(hex: "FFFFFF"), tertiaryContainer: Color(hex: "FFD7F1"), onTertiaryContainer: Color(hex: "5D3C54"), error: Color(hex: "BA1A1A"), onError: Color(hex: "FFFFFF"), errorContainer: Color(hex: "FFDAD6"), onErrorContainer: Color(hex: "93000A"), background: Color(hex: "FFFBFF"), onBackground: Color(hex: "191B26"), onSurface: Color(hex: "191B26"), surfaceVariant: Color(hex: "E2E1F2"), onSurfaceVariant: Color(hex: "454653"), surfaceContainerLowest: Color(hex: "FFFBFF"), surfaceContainerLow: Color(hex: "F4F2FF"), surfaceContainer: Color(hex: "EDECFD"), surfaceContainerHigh: Color(hex: "E7E7F7"), surfaceContainerHighest: Color(hex: "E2E1F2"), outline: Color(hex: "767680"), outlineVariant: Color(hex: "828391"), inverseSurface: Color(hex: "2E303C"), inverseOnSurface: Color(hex: "F0EFFF"), inversePrimary: Color(hex: "BBC3FF"), scrim: Color(hex: "000000"), shadow: Color(hex: "000000"), success: Color(hex: "1DB954"), isDark: false),
        dark: PaletteTokens(bg: Color(hex: "12171F"), bg2: Color(hex: "1B212D"), surface: Color(hex: "212838"), surface2: Color(hex: "36425B"), fg: Color(hex: "FFFFFF"), dim: Color(hex: "A4A9B5"), dim2: Color(hex: "828999"), line: Color(hex: "2A3346"), line2: Color(hex: "545E73"), accent: Color(hex: "8293FF"), accentText: Color(hex: "B4BEFF"), accentFg: Color(hex: "08060D"), primary: Color(hex: "BBC3FF"), onPrimary: Color(hex: "232C61"), primaryContainer: Color(hex: "3A4379"), onPrimaryContainer: Color(hex: "DEE0FF"), secondary: Color(hex: "C4C5DD"), onSecondary: Color(hex: "2D2F42"), secondaryContainer: Color(hex: "434559"), onSecondaryContainer: Color(hex: "E0E1F9"), tertiary: Color(hex: "E6BAD7"), onTertiary: Color(hex: "45263D"), tertiaryContainer: Color(hex: "5D3C54"), onTertiaryContainer: Color(hex: "FFD7F1"), error: Color(hex: "FFB4AB"), onError: Color(hex: "690005"), errorContainer: Color(hex: "93000A"), onErrorContainer: Color(hex: "FFDAD6"), background: Color(hex: "11131E"), onBackground: Color(hex: "F0EFFF"), onSurface: Color(hex: "F0EFFF"), surfaceVariant: Color(hex: "373845"), onSurfaceVariant: Color(hex: "C5C5D5"), surfaceContainerLowest: Color(hex: "0C0D18"), surfaceContainerLow: Color(hex: "191B26"), surfaceContainer: Color(hex: "1D1F2B"), surfaceContainerHigh: Color(hex: "282935"), surfaceContainerHighest: Color(hex: "333440"), outline: Color(hex: "90909A"), outlineVariant: Color(hex: "828391"), inverseSurface: Color(hex: "F0EFFF"), inverseOnSurface: Color(hex: "2E303C"), inversePrimary: Color(hex: "525A92"), scrim: Color(hex: "000000"), shadow: Color(hex: "000000"), success: Color(hex: "1DB954"), isDark: true)
    )

    static let sky = PaletteFamily(
        id: .sky,
        light: PaletteTokens(bg: Color(hex: "F1F8FE"), bg2: Color(hex: "E7F3FE"), surface: Color(hex: "FFFFFF"), surface2: Color(hex: "F4F9FE"), fg: Color(hex: "08060D"), dim: Color(hex: "385272"), dim2: Color(hex: "527CA9"), line: Color(hex: "CCE5FE"), line2: Color(hex: "B6DAFE"), accent: Color(hex: "7BBDFE"), accentText: Color(hex: "235F93"), accentFg: Color(hex: "08060D"), primary: Color(hex: "32628D"), onPrimary: Color(hex: "FFFFFF"), primaryContainer: Color(hex: "CFE5FF"), onPrimaryContainer: Color(hex: "134A74"), secondary: Color(hex: "526070"), onSecondary: Color(hex: "FFFFFF"), secondaryContainer: Color(hex: "D6E4F7"), onSecondaryContainer: Color(hex: "3A4857"), tertiary: Color(hex: "695779"), onTertiary: Color(hex: "FFFFFF"), tertiaryContainer: Color(hex: "F0DBFF"), onTertiaryContainer: Color(hex: "514060"), error: Color(hex: "BA1A1A"), onError: Color(hex: "FFFFFF"), errorContainer: Color(hex: "FFDAD6"), onErrorContainer: Color(hex: "93000A"), background: Color(hex: "FCFCFF"), onBackground: Color(hex: "161C23"), onSurface: Color(hex: "161C23"), surfaceVariant: Color(hex: "DDE3ED"), onSurfaceVariant: Color(hex: "41474F"), surfaceContainerLowest: Color(hex: "FCFCFF"), surfaceContainerLow: Color(hex: "EEF4FE"), surfaceContainer: Color(hex: "E9EEF8"), surfaceContainerHigh: Color(hex: "E3E8F2"), surfaceContainerHighest: Color(hex: "DDE3ED"), outline: Color(hex: "73777F"), outlineVariant: Color(hex: "7E848D"), inverseSurface: Color(hex: "2B3138"), inverseOnSurface: Color(hex: "ECF1FB"), inversePrimary: Color(hex: "9DCBFC"), scrim: Color(hex: "000000"), shadow: Color(hex: "000000"), success: Color(hex: "1DB954"), isDark: false),
        dark: PaletteTokens(bg: Color(hex: "182127"), bg2: Color(hex: "222F39"), surface: Color(hex: "2A3A46"), surface2: Color(hex: "455F72"), fg: Color(hex: "FFFFFF"), dim: Color(hex: "ABB7BF"), dim2: Color(hex: "8B9BA7"), line: Color(hex: "354A58"), line2: Color(hex: "607787"), accent: Color(hex: "7BBDFE"), accentText: Color(hex: "A9D5FF"), accentFg: Color(hex: "08060D"), primary: Color(hex: "9DCBFC"), onPrimary: Color(hex: "003355"), primaryContainer: Color(hex: "134A74"), onPrimaryContainer: Color(hex: "CFE5FF"), secondary: Color(hex: "BAC8DA"), onSecondary: Color(hex: "243240"), secondaryContainer: Color(hex: "3A4857"), onSecondaryContainer: Color(hex: "D6E4F7"), tertiary: Color(hex: "D4BEE6"), onTertiary: Color(hex: "392A49"), tertiaryContainer: Color(hex: "514060"), onTertiaryContainer: Color(hex: "F0DBFF"), error: Color(hex: "FFB4AB"), onError: Color(hex: "690005"), errorContainer: Color(hex: "93000A"), onErrorContainer: Color(hex: "FFDAD6"), background: Color(hex: "0E141B"), onBackground: Color(hex: "ECF1FB"), onSurface: Color(hex: "ECF1FB"), surfaceVariant: Color(hex: "343A41"), onSurfaceVariant: Color(hex: "C1C7D0"), surfaceContainerLowest: Color(hex: "090F15"), surfaceContainerLow: Color(hex: "161C23"), surfaceContainer: Color(hex: "1A2027"), surfaceContainerHigh: Color(hex: "242A32"), surfaceContainerHighest: Color(hex: "2F353D"), outline: Color(hex: "8C9199"), outlineVariant: Color(hex: "7E848D"), inverseSurface: Color(hex: "ECF1FB"), inverseOnSurface: Color(hex: "2B3138"), inversePrimary: Color(hex: "32628D"), scrim: Color(hex: "000000"), shadow: Color(hex: "000000"), success: Color(hex: "1DB954"), isDark: true)
    )

    static let aqua = PaletteFamily(
        id: .aqua,
        light: PaletteTokens(bg: Color(hex: "F1FBFC"), bg2: Color(hex: "E7F9FA"), surface: Color(hex: "FFFFFF"), surface2: Color(hex: "F4FCFD"), fg: Color(hex: "08060D"), dim: Color(hex: "386168"), dim2: Color(hex: "53939A"), line: Color(hex: "CDF3F5"), line2: Color(hex: "B6EDF1"), accent: Color(hex: "7CE0E6"), accentText: Color(hex: "126F77"), accentFg: Color(hex: "08060D"), primary: Color(hex: "00696E"), onPrimary: Color(hex: "FFFFFF"), primaryContainer: Color(hex: "9CF0F6"), onPrimaryContainer: Color(hex: "004F53"), secondary: Color(hex: "4A6364"), onSecondary: Color(hex: "FFFFFF"), secondaryContainer: Color(hex: "CCE8E9"), onSecondaryContainer: Color(hex: "324B4C"), tertiary: Color(hex: "4E5F7D"), onTertiary: Color(hex: "FFFFFF"), tertiaryContainer: Color(hex: "D6E3FF"), onTertiaryContainer: Color(hex: "364764"), error: Color(hex: "BA1A1A"), onError: Color(hex: "FFFFFF"), errorContainer: Color(hex: "FFDAD6"), onErrorContainer: Color(hex: "93000A"), background: Color(hex: "F4FEFE"), onBackground: Color(hex: "141D1E"), onSurface: Color(hex: "141D1E"), surfaceVariant: Color(hex: "DAE4E5"), onSurfaceVariant: Color(hex: "3F4949"), surfaceContainerLowest: Color(hex: "F4FEFE"), surfaceContainerLow: Color(hex: "EBF6F6"), surfaceContainer: Color(hex: "E6F0F0"), surfaceContainerHigh: Color(hex: "E0EAEA"), surfaceContainerHighest: Color(hex: "DAE4E5"), outline: Color(hex: "6F7979"), outlineVariant: Color(hex: "7C8686"), inverseSurface: Color(hex: "293233"), inverseOnSurface: Color(hex: "E9F3F3"), inversePrimary: Color(hex: "80D4D9"), scrim: Color(hex: "000000"), shadow: Color(hex: "000000"), success: Color(hex: "1DB954"), isDark: false),
        dark: PaletteTokens(bg: Color(hex: "15241C"), bg2: Color(hex: "1F3328"), surface: Color(hex: "263F32"), surface2: Color(hex: "3E6751"), fg: Color(hex: "FFFFFF"), dim: Color(hex: "A8BAB0"), dim2: Color(hex: "87A093"), line: Color(hex: "30503F"), line2: Color(hex: "5A7D6B"), accent: Color(hex: "7CE0E6"), accentText: Color(hex: "A6EFF3"), accentFg: Color(hex: "08060D"), primary: Color(hex: "80D4D9"), onPrimary: Color(hex: "003739"), primaryContainer: Color(hex: "004F53"), onPrimaryContainer: Color(hex: "9CF0F6"), secondary: Color(hex: "B1CCCD"), onSecondary: Color(hex: "1B3436"), secondaryContainer: Color(hex: "324B4C"), onSecondaryContainer: Color(hex: "CCE8E9"), tertiary: Color(hex: "B6C7E9"), onTertiary: Color(hex: "1F314C"), tertiaryContainer: Color(hex: "364764"), onTertiaryContainer: Color(hex: "D6E3FF"), error: Color(hex: "FFB4AB"), onError: Color(hex: "690005"), errorContainer: Color(hex: "93000A"), onErrorContainer: Color(hex: "FFDAD6"), background: Color(hex: "0C1516"), onBackground: Color(hex: "E9F3F3"), onSurface: Color(hex: "E9F3F3"), surfaceVariant: Color(hex: "313B3B"), onSurfaceVariant: Color(hex: "BEC8C9"), surfaceContainerLowest: Color(hex: "071010"), surfaceContainerLow: Color(hex: "141D1E"), surfaceContainer: Color(hex: "182122"), surfaceContainerHigh: Color(hex: "222C2C"), surfaceContainerHighest: Color(hex: "2D3637"), outline: Color(hex: "899393"), outlineVariant: Color(hex: "7C8686"), inverseSurface: Color(hex: "E9F3F3"), inverseOnSurface: Color(hex: "293233"), inversePrimary: Color(hex: "00696E"), scrim: Color(hex: "000000"), shadow: Color(hex: "000000"), success: Color(hex: "1DB954"), isDark: true)
    )

    static let mint = PaletteFamily(
        id: .mint,
        light: PaletteTokens(bg: Color(hex: "F1FFF5"), bg2: Color(hex: "E7FFEE"), surface: Color(hex: "FFFFFF"), surface2: Color(hex: "F4FFF7"), fg: Color(hex: "08060D"), dim: Color(hex: "386E4C"), dim2: Color(hex: "52A76F"), line: Color(hex: "CCFFDC"), line2: Color(hex: "B6FFCC"), accent: Color(hex: "7BFFA4"), accentText: Color(hex: "216A43"), accentFg: Color(hex: "08060D"), primary: Color(hex: "316A42"), onPrimary: Color(hex: "FFFFFF"), primaryContainer: Color(hex: "B3F1BF"), onPrimaryContainer: Color(hex: "16512C"), secondary: Color(hex: "506352"), onSecondary: Color(hex: "FFFFFF"), secondaryContainer: Color(hex: "D2E8D3"), onSecondaryContainer: Color(hex: "394B3C"), tertiary: Color(hex: "3A656E"), onTertiary: Color(hex: "FFFFFF"), tertiaryContainer: Color(hex: "BDEAF5"), onTertiaryContainer: Color(hex: "204D56"), error: Color(hex: "BA1A1A"), onError: Color(hex: "FFFFFF"), errorContainer: Color(hex: "FFDAD6"), onErrorContainer: Color(hex: "93000A"), background: Color(hex: "F5FFF3"), onBackground: Color(hex: "121E14"), onSurface: Color(hex: "121E14"), surfaceVariant: Color(hex: "D7E7D6"), onSurfaceVariant: Color(hex: "3C4A3E"), surfaceContainerLowest: Color(hex: "F5FFF3"), surfaceContainerLow: Color(hex: "E8F8E7"), surfaceContainer: Color(hex: "E3F2E1"), surfaceContainerHigh: Color(hex: "DDECDC"), surfaceContainerHighest: Color(hex: "D7E7D6"), outline: Color(hex: "717971"), outlineVariant: Color(hex: "798879"), inverseSurface: Color(hex: "263428"), inverseOnSurface: Color(hex: "E5F5E4"), inversePrimary: Color(hex: "98D5A4"), scrim: Color(hex: "000000"), shadow: Color(hex: "000000"), success: Color(hex: "1DB954"), isDark: false),
        dark: PaletteTokens(bg: Color(hex: "15241A"), bg2: Color(hex: "1F3425"), surface: Color(hex: "26412E"), surface2: Color(hex: "3E694B"), fg: Color(hex: "FFFFFF"), dim: Color(hex: "A8BBAE"), dim2: Color(hex: "87A28F"), line: Color(hex: "30513A"), line2: Color(hex: "5A7F66"), accent: Color(hex: "7BFFA4"), accentText: Color(hex: "A9FFC2"), accentFg: Color(hex: "08060D"), primary: Color(hex: "98D5A4"), onPrimary: Color(hex: "00391A"), primaryContainer: Color(hex: "16512C"), onPrimaryContainer: Color(hex: "B3F1BF"), secondary: Color(hex: "B7CCB7"), onSecondary: Color(hex: "223526"), secondaryContainer: Color(hex: "394B3C"), onSecondaryContainer: Color(hex: "D2E8D3"), tertiary: Color(hex: "A2CED9"), onTertiary: Color(hex: "01363F"), tertiaryContainer: Color(hex: "204D56"), onTertiaryContainer: Color(hex: "BDEAF5"), error: Color(hex: "FFB4AB"), onError: Color(hex: "690005"), errorContainer: Color(hex: "93000A"), onErrorContainer: Color(hex: "FFDAD6"), background: Color(hex: "0A160D"), onBackground: Color(hex: "E5F5E4"), onSurface: Color(hex: "E5F5E4"), surfaceVariant: Color(hex: "2F3C31"), onSurfaceVariant: Color(hex: "BBCBBB"), surfaceContainerLowest: Color(hex: "051108"), surfaceContainerLow: Color(hex: "121E14"), surfaceContainer: Color(hex: "162218"), surfaceContainerHigh: Color(hex: "202D22"), surfaceContainerHighest: Color(hex: "2B382D"), outline: Color(hex: "8B938A"), outlineVariant: Color(hex: "798879"), inverseSurface: Color(hex: "E5F5E4"), inverseOnSurface: Color(hex: "263428"), inversePrimary: Color(hex: "316A42"), scrim: Color(hex: "000000"), shadow: Color(hex: "000000"), success: Color(hex: "1DB954"), isDark: true)
    )

    static let families: [PaletteFamily] = [violet, indigo, sky, aqua, mint]
// END GENERATED PALETTES

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
                accentText: tokens.accentText, accentFg: readableOn(accentHex),
                primary: tokens.primary, onPrimary: tokens.onPrimary,
                primaryContainer: tokens.primaryContainer, onPrimaryContainer: tokens.onPrimaryContainer,
                secondary: tokens.secondary, onSecondary: tokens.onSecondary,
                secondaryContainer: tokens.secondaryContainer, onSecondaryContainer: tokens.onSecondaryContainer,
                tertiary: tokens.tertiary, onTertiary: tokens.onTertiary,
                tertiaryContainer: tokens.tertiaryContainer, onTertiaryContainer: tokens.onTertiaryContainer,
                error: tokens.error, onError: tokens.onError,
                errorContainer: tokens.errorContainer, onErrorContainer: tokens.onErrorContainer,
                background: tokens.background, onBackground: tokens.onBackground,
                onSurface: tokens.onSurface, surfaceVariant: tokens.surfaceVariant,
                onSurfaceVariant: tokens.onSurfaceVariant,
                surfaceContainerLowest: tokens.surfaceContainerLowest,
                surfaceContainerLow: tokens.surfaceContainerLow,
                surfaceContainer: tokens.surfaceContainer,
                surfaceContainerHigh: tokens.surfaceContainerHigh,
                surfaceContainerHighest: tokens.surfaceContainerHighest,
                outline: tokens.outline, outlineVariant: tokens.outlineVariant,
                inverseSurface: tokens.inverseSurface, inverseOnSurface: tokens.inverseOnSurface,
                inversePrimary: tokens.inversePrimary, scrim: tokens.scrim, shadow: tokens.shadow,
                success: tokens.success, isDark: tokens.isDark
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
