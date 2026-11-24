import Foundation
import SwiftUI

/// Session, cached account, preferences and the shared player.
@MainActor
final class AppState: ObservableObject {
    @Published var me: JSON?
    @Published var signedIn = false
    @Published var booting = true
    @Published var settings: JSON?
    @Published var message: String?
    @Published var showingMessage = false

    let client = APIClient.shared
    let player: Player

    private var presenceTimer: Timer?

    init() {
        player = Player(client: client)
        if let raw = UserDefaults.standard.string(forKey: "cached_me"),
           let data = raw.data(using: .utf8),
           let cached = try? JSON(data) {
            me = cached
            signedIn = true
        }
        Task { await restore() }
    }

    var username: String {
        me?["username"]?.string ?? ""
    }

    var isAdmin: Bool {
        me?["is_admin"]?.bool ?? false
    }

    var deviceHash: String {
        let key = "device_hash"
        if let existing = UserDefaults.standard.string(forKey: key), !existing.isEmpty {
            return existing
        }
        let value = UIDevice.current.identifierForVendor?.uuidString
            .replacingOccurrences(of: "-", with: "") ?? UUID().uuidString.replacingOccurrences(of: "-", with: "")
        let hash = String(value.prefix(32))
        UserDefaults.standard.set(hash, forKey: key)
        return hash
    }

    var deviceName: String {
        "\(UIDevice.current.name) · iOS"
    }

    func restore() async {
        booting = true
        defer { booting = false }
        guard client.isSignedIn else {
            signedIn = false
            me = nil
            return
        }
        do {
            let value = try await client.me()
            applyMe(value)
            await loadSettings()
            startPresence()
        } catch {
            // A transient network failure must not throw away a verified
            // session; keep the cached identity and retry on next launch.
            if me != nil { signedIn = true }
        }
    }

    private func applyMe(_ value: JSON) {
        me = value
        signedIn = true
        if let data = try? JSONSerialization.data(withJSONObject: value.anyValue),
           let text = String(data: data, encoding: .utf8) {
            UserDefaults.standard.set(text, forKey: "cached_me")
        }
    }

    func signIn(username: String, password: String) async throws {
        let key = username.contains("@") ? "email" : "username"
        let value = try await client.post("login", json: [key: username, "password": password])
        applyMe(value)
        await loadSettings()
        startPresence()
    }

    func register(username: String, password: String, invite: String) async throws {
        applyMe(try await client.register(username: username, password: password, invite: invite))
        await loadSettings()
        startPresence()
    }

    func signOut() async {
        await client.logout()
        me = nil
        signedIn = false
        settings = nil
        UserDefaults.standard.removeObject(forKey: "cached_me")
        presenceTimer?.invalidate()
        presenceTimer = nil
        player.clear()
    }

    func loadSettings() async {
        settings = try? await client.settings()
    }

    func saveSettings(_ values: [String: Any]) async {
        do {
            try await client.saveSettings(values)
            settings = try await client.settings()
        } catch { show(error) }
    }

    func show(_ error: Error) {
        message = error.localizedDescription
        showingMessage = true
    }

    func show(_ text: String) {
        message = text
        showingMessage = true
    }

    private func startPresence() {
        presenceTimer?.invalidate()
        presenceTimer = Timer.scheduledTimer(withTimeInterval: 15, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in
                guard let self, self.signedIn else { return }
                let trackID = Int(player.current?.first("id")?.string ?? "")
                await client.heartbeat(
                    deviceHash: deviceHash, name: deviceName, trackID: trackID,
                    position: player.progress, paused: !player.isPlaying
                )
                await client.publishPlayback(
                    trackID: trackID, position: player.progress, duration: player.duration,
                    playing: player.isPlaying,
                    queue: player.queue.compactMap { Int($0.first("id")?.string ?? "") }
                )
            }
        }
    }
}
