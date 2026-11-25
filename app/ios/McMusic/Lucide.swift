import SwiftUI

/// Lucide geometry rendered as SwiftUI paths. No SF Symbols, no icon font, and
/// no downloaded assets: the same 24×24 Lucide outlines used on web/Android.
enum Lucide {
    static let paths: [String: [Primitive]] = [
        "play": [.path("M7 4.5 L19 12 L7 19.5 Z")],
        "pause": [.path("M8 5V19"), .path("M16 5V19")],
        "skip-forward": [.path("M5 4 L15 12 L5 20 Z"), .path("M19 5V19")],
        "skip-back": [.path("M19 4 L9 12 L19 20 Z"), .path("M5 5V19")],
        "shuffle": [.path("M16 3H21V8"), .path("M4 20L21 3"), .path("M21 16V21H16"),
                    .path("M15 15L21 21"), .path("M4 4L9 9")],
        "repeat": [.path("M17 2L21 6L17 10"), .path("M3 11V9C3 6.8 4.8 5 7 5H21"),
                   .path("M7 22L3 18L7 14"), .path("M21 13V15C21 17.2 19.2 19 17 19H3")],
        "repeat-1": [.path("M17 2L21 6L17 10"), .path("M3 11V9C3 6.8 4.8 5 7 5H21"),
                     .path("M7 22L3 18L7 14"), .path("M21 13V15C21 17.2 19.2 19 17 19H3"),
                     .path("M11 10H13V15")],
        "volume-2": [.path("M11 5L6 9H2V15H6L11 19Z"), .path("M15.5 8.5C17 10 17 14 15.5 15.5"),
                     .path("M18.5 5.5C22 9 22 15 18.5 18.5")],
        "volume-1": [.path("M11 5L6 9H2V15H6L11 19Z"), .path("M15.5 8.5C17 10 17 14 15.5 15.5")],
        "volume-x": [.path("M11 5L6 9H2V15H6L11 19Z"), .path("M22 9L16 15"), .path("M16 9L22 15")],
        "home": [.path("M3 10.5L12 3L21 10.5"), .path("M5 9.5V21H19V9.5")],
        "search": [.circle(11, 11, 8), .path("M21 21L16.7 16.7")],
        "library": [.path("M4 4H9V20H4Z"), .path("M11 4H16V20H11Z"), .path("M18 5L21 6L18 20L15 19Z")],
        "music": [.path("M9 18V5L21 3V16"), .circle(6, 18, 3), .circle(18, 16, 3)],
        "music-note": [.path("M9 18V5L20 3V16"), .circle(6, 18, 3), .circle(17, 16, 3)],
        "radio": [.rect(3, 9, 18, 11, 2), .path("M3 9L19 4"), .circle(7, 14, 1),
                  .circle(11, 14, 1), .circle(15, 14, 1)],
        "settings": [.circle(12, 12, 3), .path("M12 2V5"), .path("M12 19V22"),
                     .path("M4.2 4.2L6.3 6.3"), .path("M17.7 17.7L19.8 19.8"),
                     .path("M2 12H5"), .path("M19 12H22"),
                     .path("M4.2 19.8L6.3 17.7"), .path("M17.7 6.3L19.8 4.2")],
        "user": [.path("M19 21V19C19 16.8 17.2 15 15 15H9C6.8 15 5 16.8 5 19V21"),
                 .circle(12, 7, 4)],
        "list-music": [.path("M8 6H21"), .path("M8 12H21"), .path("M8 18H21"),
                       .path("M3 6H3.01"), .path("M3 12H3.01"), .path("M3 18H3.01")],
        "list": [.path("M8 6H21"), .path("M8 12H21"), .path("M8 18H21"),
                 .path("M3 6H3.01"), .path("M3 12H3.01"), .path("M3 18H3.01")],
        "list-plus": [.path("M8 6H12"), .path("M8 12H12"), .path("M8 18H12"),
                      .path("M3 6H3.01"), .path("M3 12H3.01"), .path("M3 18H3.01"),
                      .path("M18 9V21"), .path("M12 15H24")],
        "heart": [.path("M12 20.5L4.2 12.8C1.8 10.4 2 6.5 4.6 4.6C6.8 3 9.7 3.4 12 5.8C14.3 3.4 17.2 3 19.4 4.6C22 6.5 22.2 10.4 19.8 12.8Z")],
        "download": [.path("M12 3V15"), .path("M7 11L12 16L17 11"), .path("M4 21H20")],
        "plus": [.path("M12 5V19"), .path("M5 12H19")],
        "x": [.path("M6 6L18 18"), .path("M18 6L6 18")],
        "x-circle": [.circle(12, 12, 9), .path("M9 9L15 15"), .path("M15 9L9 15")],
        "check": [.path("M20 6L9 17L4 12")],
        "chevron-up": [.path("M5 15L12 8L19 15")],
        "chevron-down": [.path("M5 9L12 16L19 9")],
        "chevron-left": [.path("M15 5L8 12L15 19")],
        "chevron-right": [.path("M9 5L16 12L9 19")],
        "more-horizontal": [.circle(5, 12, 1.4), .circle(12, 12, 1.4), .circle(19, 12, 1.4)],
        "clock": [.circle(12, 12, 9), .path("M12 7V12L16 14")],
        "link": [.path("M10.5 13.5C12.3 15.3 15.1 15.3 16.9 13.5L19.5 10.9C21.7 8.6 21.7 5.1 19.5 2.9L18 4.4"),
                 .path("M13.5 10.5C11.7 8.7 8.9 8.7 7.1 10.5L4.5 13.1C2.3 15.4 2.3 19 4.5 21.2"),
                 .path("M10.9 19.5L12.2 18.2")],
        "trash-2": [.path("M3 6H21"), .path("M8 6V4H16V6"), .path("M19 6L18 20H6L5 6"),
                    .path("M10 11V16"), .path("M14 11V16")],
        "folder-plus": [.path("M3 7C3 5.9 3.9 5 5 5H9L11 7H19C20.1 7 21 7.9 21 9V18C21 19.1 20.1 20 19 20H5C3.9 20 3 19.1 3 18Z"),
                        .path("M12 11V16"), .path("M9.5 13.5H14.5")],
        "info": [.circle(12, 12, 9), .path("M12 16V11"), .path("M12 8H12.01")],
        "circle-help": [.circle(12, 12, 9), .path("M9.1 9C9.6 7.8 10.7 7 12 7C13.7 7 15 8.3 15 10C15 12 12 12.5 12 14.5"),
                        .path("M12 18H12.01")],
        "moon": [.path("M20 14.5C18.5 17.5 15 19.5 11 19.5C6.9 19.5 3.5 16.1 3.5 12C3.5 8 6.5 4.9 10.5 4.5C8.5 6.2 7 8.8 7 12C7 16.3 10.5 19.8 14.8 19.8C16.7 19.8 18.5 19.1 20 17.9Z")],
        "message-circle": [.path("M20 11.5C20 16 16 19.5 11.5 19.5C10.5 19.5 9.5 19.4 8.5 19.1L3 21L4.6 15.8C3.6 14.4 3 13 3 11.5C3 7 7 3 11.5 3C16 3 20 7 20 11.5Z")],
        "inbox": [.path("M4 4H20V20H4Z"), .path("M4 14H8L10 17H14L16 14H20")],
        "shield": [.path("M12 3L20 7V12C20 17 16.6 20.3 12 21C7.4 20.3 4 17 4 12V7Z")],
        "monitor": [.rect(3, 4, 18, 13, 2), .path("M8 21H16"), .path("M12 17V21")],
        "smartphone": [.rect(6, 2, 12, 20, 2.5), .path("M11 18H13")],
        "audio-lines": [.path("M3 12H5"), .path("M8 8V16"), .path("M12 5V19"),
                        .path("M16 8V16"), .path("M20 10V14")],
        "pencil": [.path("M4 20L4.8 16L16 4.8L19.2 8L8 19.2Z"), .path("M14 7L17 10")],
        "server": [.rect(3, 3, 18, 7, 2), .rect(3, 14, 18, 7, 2),
                   .circle(7, 6.5, 1), .circle(7, 17.5, 1),
                   .path("M11 6.5H16"), .path("M11 17.5H16")],
        "key": [.circle(8, 15, 4), .path("M11 12L21 2"),
                .path("M18 5L21 8"), .path("M15 8L18 11")],
        "shield-alert": [.path("M12 3L20 7V12C20 17 16.6 20.3 12 21C7.4 20.3 4 17 4 12V7Z"),
                         .path("M12 8V13"), .path("M12 16H12.01")],
        "circle-alert": [.circle(12, 12, 9), .path("M12 7V13"), .path("M12 16H12.01")],
        "wifi-off": [.path("M2 8.5C7.5 4 16.5 4 22 8.5"),
                     .path("M5 12C9 9 14 9 18 11"),
                     .path("M8.5 15.5C10.5 14 13 14 15.5 15.5"),
                     .circle(12, 19, 1), .path("M3 3L21 21")],
    ]

    static let fallback = "circle-help"

    enum Primitive {
        case path(String)
        case circle(Double, Double, Double)
        case rect(Double, Double, Double, Double, Double)

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

    private var primitives: [Lucide.Primitive] {
        Lucide.paths[name] ?? Lucide.paths[Lucide.fallback] ?? []
    }

    /// A nil colour inherits the ambient foreground style (currentColor);
    /// a supplied colour overrides it for stateful icons.
    private var foreground: AnyShapeStyle {
        if let color { return AnyShapeStyle(color) }
        return AnyShapeStyle(HierarchicalShapeStyle.primary)
    }

    var body: some View {
        ZStack {
            ForEach(Array(primitives.enumerated()), id: \.offset) { item in
                LucideShape(primitive: item.element, scale: size / 24)
                    .stroke(style: StrokeStyle(lineWidth: 1.8, lineCap: .round, lineJoin: .round))
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
