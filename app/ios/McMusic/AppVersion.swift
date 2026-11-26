import Foundation

/// Numeric comparison for the dotted versions published in `/api/builds`.
/// Build names such as `mcmusic-x86_64.AppImage` are deliberately unversioned.
struct AppVersion: Comparable, CustomStringConvertible {
    let parts: [Int]

    init(_ raw: String?) {
        let pattern = #"(?<!\d)(\d+(?:\.\d+)+)(?!\d)"#
        let text = raw ?? ""
        let range = NSRange(text.startIndex..., in: text)
        let match = (try? NSRegularExpression(pattern: pattern))?
            .firstMatch(in: text, range: range)
        if let match, let found = Range(match.range(at: 1), in: text) {
            parts = String(text[found]).split(separator: ".").compactMap { Int($0) }
        } else {
            parts = []
        }
    }

    static var current: AppVersion {
        let value = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String
        return AppVersion(value ?? "0.0.0")
    }

    var isValid: Bool { !parts.isEmpty }

    var description: String { parts.map(String.init).joined(separator: ".") }

    static func == (lhs: AppVersion, rhs: AppVersion) -> Bool {
        guard lhs.isValid, rhs.isValid else { return false }
        let width = max(lhs.parts.count, rhs.parts.count)
        for index in 0..<width {
            let left = index < lhs.parts.count ? lhs.parts[index] : 0
            let right = index < rhs.parts.count ? rhs.parts[index] : 0
            if left != right { return false }
        }
        return true
    }

    static func < (lhs: AppVersion, rhs: AppVersion) -> Bool {
        guard lhs.isValid else { return false }
        let width = max(lhs.parts.count, rhs.parts.count)
        for index in 0..<width {
            let left = index < lhs.parts.count ? lhs.parts[index] : 0
            let right = index < rhs.parts.count ? rhs.parts[index] : 0
            if left != right { return left < right }
        }
        return false
    }
}
