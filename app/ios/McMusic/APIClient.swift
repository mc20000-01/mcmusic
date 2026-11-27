import Foundation

enum APIError: LocalizedError {
    case invalidURL(String)
    case status(Int, String)
    case decoding

    var errorDescription: String? {
        switch self {
        case .invalidURL(let value): return "Invalid server address: \(value)"
        case .status(let code, let message): return code == 0 ? message : "\(code): \(message)"
        case .decoding: return "Could not read the server response"
        }
    }
}

/// Thin async wrapper around the same HTTP API the other native clients use.
/// Cookies are kept in `HTTPCookieStorage.shared`, so a session survives a
/// restart of the app just like it does in the Qt and Android clients.
final class APIClient {
    static let shared = APIClient()

    private let session: URLSession = {
        let config = URLSessionConfiguration.default
        config.httpCookieStorage = .shared
        config.httpCookieAcceptPolicy = .always
        config.httpShouldSetCookies = true
        config.timeoutIntervalForRequest = 30
        return URLSession(configuration: config)
    }()

    private(set) var baseURL: String
    let outbox = Outbox.shared
    private var cookieStorage: HTTPCookieStorage { .shared }

    init(baseURL: String? = nil) {
        self.baseURL = Self.normalize(baseURL ?? UserDefaults.standard.string(forKey: "server_url") ?? "http://127.0.0.1:8000")
        UserDefaults.standard.set(self.baseURL, forKey: "server_url")
    }

    static func normalize(_ raw: String) -> String {
        var value = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        if !value.hasPrefix("http://") && !value.hasPrefix("https://") {
            value = "http://" + value
        }
        return value.replacingOccurrences(of: "/+$", with: "", options: .regularExpression)
    }

    func setBaseURL(_ raw: String) {
        baseURL = Self.normalize(raw)
        UserDefaults.standard.set(baseURL, forKey: "server_url")
    }

    var isSignedIn: Bool {
        let names = ["mcmusic_session", "session"]
        return cookieStorage.cookies?.contains { names.contains($0.name) && !$0.value.isEmpty } ?? false
    }

    func clearCookies() {
        for cookie in cookieStorage.cookies ?? [] {
            cookieStorage.deleteCookie(cookie)
        }
    }

    func absoluteURL(_ path: String, query: [String: String]? = nil) throws -> URL {
        var components: URLComponents
        if path.hasPrefix("http://") || path.hasPrefix("https://") {
            guard let parsed = URLComponents(string: path) else { throw APIError.invalidURL(path) }
            components = parsed
        } else {
            let clean = path.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
            let apiPath = clean.hasPrefix("api/") ? clean : "api/" + clean
            guard let parsed = URLComponents(string: baseURL + "/" + apiPath) else {
                throw APIError.invalidURL(path)
            }
            components = parsed
        }
        if let query, !query.isEmpty {
            components.queryItems = (components.queryItems ?? []) + query.map { URLQueryItem(name: $0.key, value: $0.value) }
        }
        guard let url = components.url else { throw APIError.invalidURL(path) }
        return url
    }

    @discardableResult
    func request(
        _ method: String,
        _ path: String,
        query: [String: String]? = nil,
        json: [String: Any]? = nil,
        form: [String: String]? = nil
    ) async throws -> JSON {
        let url = try absoluteURL(path, query: query)
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.setValue("mcmusic-ios/4.3.2", forHTTPHeaderField: "User-Agent")
        if let form {
            request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
            let pairs = form.map { key, value in
                "\(Self.encode(key))=\(Self.encode(value))"
            }
            request.httpBody = pairs.joined(separator: "&").data(using: .utf8)
        } else if let json {
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try? JSONSerialization.data(withJSONObject: json)
        }

        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await session.data(for: request)
        } catch {
            // Normalise transport failures so the outbox can recognise them.
            throw APIError.status(0, error.localizedDescription)
        }
        let status = (response as? HTTPURLResponse)?.statusCode ?? 0
        let body = try? JSON(data)
        if !(200..<300).contains(status) {
            let message = body?["error"]?.string
                ?? body?["message"]?.string
                ?? String(data: data, encoding: .utf8)?.prefix(200).description
                ?? "Request failed"
            throw APIError.status(status, String(message))
        }
        return body ?? .null
    }

    func get(_ path: String, query: [String: String]? = nil) async throws -> JSON {
        try await request("GET", path, query: query)
    }

    func post(_ path: String, json: [String: Any]? = nil, form: [String: String]? = nil) async throws -> JSON {
        try await request("POST", path, json: json, form: form)
    }

    func put(_ path: String, json: [String: Any]? = nil) async throws -> JSON {
        try await request("PUT", path, json: json)
    }

    func delete(_ path: String) async throws -> JSON {
        try await request("DELETE", path)
    }

    /// Download a track through the signed-in session, then hand a local file
    /// to AVFoundation. AVPlayer does not use HTTPCookieStorage on its own.
    func download(to url: URL, from path: String) async throws {
        let remote = try absoluteURL(path)
        let (data, response) = try await session.data(from: remote)
        let status = (response as? HTTPURLResponse)?.statusCode ?? 0
        guard (200..<300).contains(status) else {
            throw APIError.status(status, "Could not load audio")
        }
        try data.write(to: url)
    }

    func artworkURL(_ value: Any?) -> URL? {
        let text: String?
        switch value {
        case let string as String: text = string
        case let json as JSON: text = json.string
        default: text = nil
        }
        guard let text, !text.isEmpty else { return nil }
        if text.hasPrefix("http://") || text.hasPrefix("https://") {
            return URL(string: text)
        }
        return try? absoluteURL(text)
    }

    private static func encode(_ value: String) -> String {
        value.addingPercentEncoding(withAllowedCharacters: .alphanumerics) ?? value
    }
}
