import Foundation

/// A replay-safe write kept while the server is unreachable. Only the same
/// idempotent/toggle writes the web and Qt clients queue go in here.
struct OutboxEntry: Codable, Identifiable {
    let id: String
    let method: String
    let path: String
    let payload: String?
    let toggle: Bool

    var body: [String: Any]? {
        guard let payload, let data = payload.data(using: .utf8),
              let value = try? JSONSerialization.jsonObject(with: data),
              let dict = value as? [String: Any] else { return nil }
        return dict
    }
}

final class Outbox {
    static let shared = Outbox()
    static let changed = Notification.Name("mcmusic.outbox.changed")

    private let defaults: UserDefaults
    private let key = "mcmusic.outbox.v1"
    private let lock = NSLock()
    private var entries: [OutboxEntry] = []

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        load()
    }

    var count: Int {
        lock.lock()
        defer { lock.unlock() }
        return entries.count
    }

    func enqueue(_ method: String, _ path: String, json: [String: Any]? = nil, toggle: Bool = false) {
        let payload: String?
        if let json, let data = try? JSONSerialization.data(withJSONObject: json) {
            payload = String(data: data, encoding: .utf8)
        } else {
            payload = nil
        }
        let entry = OutboxEntry(
            id: UUID().uuidString,
            method: method,
            path: path,
            payload: payload,
            toggle: toggle
        )
        lock.lock()
        entries.append(entry)
        persistLocked()
        lock.unlock()
        notify()
    }

    /// Replays in order and keeps anything that failed for the next sync.
    @discardableResult
    func replay(client: APIClient) async -> Int {
        let snapshot: [OutboxEntry] = {
            lock.lock()
            defer { lock.unlock() }
            return entries
        }()
        guard !snapshot.isEmpty else { return 0 }

        var remaining = snapshot
        var sent = 0
        for entry in snapshot {
            do {
                try await client.request(entry.method, entry.path, json: entry.body)
                remaining.removeAll { $0.id == entry.id }
                sent += 1
            } catch {
                // An HTTP error is kept too: the next sync should retry it
                // after the user fixes the cause (for example a removed song).
            }
        }
        lock.lock()
        entries = remaining
        persistLocked()
        lock.unlock()
        notify()
        return sent
    }

    func clear() {
        lock.lock()
        entries = []
        persistLocked()
        lock.unlock()
        notify()
    }

    private func load() {
        guard let data = defaults.data(forKey: key),
              let decoded = try? JSONDecoder().decode([OutboxEntry].self, from: data) else { return }
        entries = decoded
    }

    private func persistLocked() {
        guard let data = try? JSONEncoder().encode(entries) else { return }
        defaults.set(data, forKey: key)
    }

    private func notify() {
        NotificationCenter.default.post(name: Self.changed, object: self)
    }
}
