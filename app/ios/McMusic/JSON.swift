import Foundation

/// A tolerant JSON value used for server payloads. The server has evolved over
/// years and several endpoints return optional or differently-typed fields;
/// decoding into this first keeps old and new servers working with one client.
indirect enum JSON: Sendable {
    case object([String: JSON])
    case array([JSON])
    case string(String)
    case number(Double)
    case bool(Bool)
    case null

    init(_ data: Data) throws {
        let value = try JSONSerialization.jsonObject(with: data, options: [.fragmentsAllowed])
        self = JSON(value)
    }

    init(_ value: Any?) {
        switch value {
        case let dict as [String: Any]:
            self = .object(dict.mapValues { JSON($0) })
        case let list as [Any]:
            self = .array(list.map { JSON($0) })
        case let str as String:
            self = .string(str)
        case let num as NSNumber:
            if CFGetTypeID(num) == CFBooleanGetTypeID() {
                self = .bool(num.boolValue)
            } else {
                self = .number(num.doubleValue)
            }
        case is NSNull:
            self = .null
        default:
            self = .null
        }
    }

    subscript(key: String) -> JSON? {
        if case .object(let dict) = self { return dict[key] }
        return nil
    }

    var string: String? {
        switch self {
        case .string(let s): return s
        case .number(let n): return String(n)
        default: return nil
        }
    }

    var int: Int? {
        switch self {
        case .number(let n): return Int(n)
        case .string(let s): return Int(s)
        default: return nil
        }
    }

    var double: Double? {
        switch self {
        case .number(let n): return n
        case .string(let s): return Double(s)
        default: return nil
        }
    }

    var bool: Bool? {
        switch self {
        case .bool(let b): return b
        case .number(let n): return n != 0
        case .string(let s): return ["1", "true", "yes"].contains(s.lowercased())
        default: return nil
        }
    }

    var array: [JSON]? {
        if case .array(let a) = self { return a }
        return nil
    }

    var object: [String: JSON]? {
        if case .object(let o) = self { return o }
        return nil
    }

    var isNull: Bool {
        if case .null = self { return true }
        return false
    }

    /// Convert back to Foundation types for persistence and JSONSerialization.
    var anyValue: Any {
        switch self {
        case .object(let dict): return dict.mapValues { $0.anyValue }
        case .array(let list): return list.map { $0.anyValue }
        case .string(let s): return s
        case .number(let n): return n
        case .bool(let b): return b
        case .null: return NSNull()
        }
    }

    /// First non-null value among the given keys.
    func first(_ keys: String...) -> JSON? {
        for key in keys {
            if let value = self[key], !value.isNull { return value }
        }
        return nil
    }
}

extension JSON: Identifiable {
    var id: String {
        first("id", "track_id", "username", "code", "prefix", "name")?.string ?? UUID().uuidString
    }

    var trackID: Int { first("id", "track_id")?.int ?? 0 }
    var title: String { first("title", "name")?.string ?? "Unknown" }
    var artistName: String { first("artist", "artist_name")?.string ?? "Unknown Artist" }
    var albumName: String { first("album")?.string ?? "" }
    var coverID: Int? { first("cover_id", "cover", "art")?.int }
    var itemCount: Int { first("n", "count")?.int ?? 0 }
}
