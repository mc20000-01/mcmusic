import SwiftUI

/// Authored 4.2.0 shape, spacing and type values mirrored from
/// `design/tokens.json`. Colours remain in `Theme.swift`'s generated block;
/// these constants are the iOS half of the single-source token contract.
enum M3Shape {
    static let xs: CGFloat = 4
    static let sm: CGFloat = 8
    static let md: CGFloat = 12
    static let lg: CGFloat = 16
    static let xl: CGFloat = 28
    static let xxl: CGFloat = 36
    static let pill: CGFloat = 999

    static let coverSmall: CGFloat = 20
    static let coverLarge: CGFloat = 28
    static let card: CGFloat = 28
    static let hero: CGFloat = 36
    static let touch: CGFloat = 48
}

enum M3Space {
    static let unit: CGFloat = 4
}

/// Material 3 type scale. Lexend stays the web face; iOS uses the system
/// rounded design so the native client matches the friendly 4.2.0 voice
/// without adding a downloaded font.
enum M3Type {
    static let display = Font.system(size: 36, weight: .bold, design: .rounded)
    static let headline = Font.system(size: 28, weight: .bold, design: .rounded)
    static let title = Font.system(size: 22, weight: .bold, design: .rounded)
    static let body = Font.system(size: 16, weight: .regular, design: .rounded)
    static let label = Font.system(size: 14, weight: .semibold, design: .rounded)

    static let displayLine: CGFloat = 44
    static let headlineLine: CGFloat = 36
    static let titleLine: CGFloat = 28
    static let bodyLine: CGFloat = 24
    static let labelLine: CGFloat = 20
}
