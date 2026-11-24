import Foundation
import SwiftUI
import UIKit

/// Session, cached account, preferences, sync and the shared player.
@MainActor
final class AppState: ObservableObject {
    @Published var me: JSON?
    @Published var signedIn = false
    @Published var booting = true
    @Published var settings: JSON?
    @Published var pendingCount = Outbox.shared.count
    @Published var message: String?
    @Published var showingMessage = false

    let client = APIClient.shared
    let player: Player

    private var presenceTimer: Timer?
    private var commandTimer: Timer?
    private var outboxObserver: NSObjectProtocol?

    init() {
        player = Player(client: client)
        if let raw = UserDefaults.standard.string(forKey: "cached_me"),
           let data = raw.data(using: .utf8),
           let cached = try? JSON(data) {
            me = cached
            signedIn = true
        }
        outboxObserver = NotificationCenter.default.addObserver(
            forName: Outbox.changed, object: nil, queue: .main
        ) { [weak self] _ in
            Task { @MainActor [weak self] in self?.pendingCount = Outbox.shared.count }
        }
        Task { await restore() }
    }

    static var deviceHashValue: String {
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

    var username: String {
        me?["username"]?.string ?? ""
    }

    var isAdmin: Bool {
        me?["is_admin"]?.bool ?? false
    }

    var deviceHash: String { Self.deviceHashValue }

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
            await player.restoreSnapshot()
            await syncOutbox(announce: false)
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
        await player.restoreSnapshot()
    }

    func register(username: String, password: String, invite: String) async throws {
        applyMe(try await client.register(username: username, password: password, invite: invite))
        await loadSettings()
        startPresence()
        await player.restoreSnapshot()
    }

    func signOut() async {
        await client.logout()
        me = nil
        signedIn = false
        settings = nil
        UserDefaults.standard.removeObject(forKey: "cached_me")
        stopPresence()
        player.clear()
    }

    func loadSettings() async {
        settings = try? await client.settings()
        player.applySettings(settings)
    }

    func saveSettings(_ values: [String: Any]) async {
        await syncOutbox(announce: false)
        var merged = settings?.object?.mapValues { $0.anyValue } ?? [:]
        for (key, value) in values { merged[key] = value }
        do {
            try await client.saveSettings(merged)
            settings = try await client.settings()
            player.applySettings(settings)
        } catch { show(error) }
    }

    @discardableResult
    func syncOutbox(announce: Bool = true) async -> Int {
        let sent = await client.syncOutbox()
        pendingCount = Outbox.shared.count
        if announce && sent > 0 { show("Synced \(sent) queued change\(sent == 1 ? "" : "s")") }
        return sent
    }

    func show(_ error: Error) {
        message = error.localizedDescription
        showingMessage = true
    }

    func show(_ text: String) {
        message = text
        showingMessage = true
    }

    // MARK: - presence and remote commands

    private func startPresence() {
        stopPresence()
        presenceTimer = Timer.scheduledTimer(withTimeInterval: 15, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in
                guard let self, self.signedIn else { return }
                let trackID = player.currentTrackID
                await client.heartbeat(
                    deviceHash: deviceHash, name: deviceName, trackID: trackID,
                    position: player.progress, paused: !player.isPlaying
                )
                await client.publishPlayback(
                    device: deviceHash,
                    trackID: trackID, position: player.progress, duration: player.duration,
                    playing: player.isPlaying,
                    queue: player.queue.compactMap { Int(Player.id($0) ?? "") }
                )
                player.persistQueue()
            }
        }
        commandTimer = Timer.scheduledTimer(withTimeInterval: 3, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in
                guard let self, self.signedIn else { return }
                await pollCommands()
            }
        }
    }

    private func stopPresence() {
        presenceTimer?.invalidate()
        commandTimer?.invalidate()
        presenceTimer = nil
        commandTimer = nil
    }

    private func pollCommands() async {
        guard let payload = try? await client.playback(device: deviceHash) else { return }
        for command in payload["commands"]?.array ?? [] {
            apply(command)
        }
    }

    private func apply(_ command: JSON) {
        let action = command["action"]?.string ?? ""
        let arg = command["arg"] ?? .null
        switch action {
        case "play":
            player.resumePlayback()
        case "pause":
            player.pausePlayback()
        case "toggle":
            player.toggle()
        case "next", "skip":
            player.next()
        case "prev":
            player.previous()
        case "seek":
            if let position = arg["position"]?.double ?? arg["position"]?.int.map({ Double($0) }) {
                player.seek(to: position)
            }
        case "remove":
            if let position = arg["index"]?.int { player.remove(at: position) }
        case "enqueue":
            if let track = arg["track"] { player.append([track]) }
        case "play_track":
            if let track = arg["track"] {
                Task { await player.play(track: track) }
            } else if let id = arg["track_id"]?.int {
                Task { await playRemoteTrack(id) }
            }
        default:
            break
        }
    }

    private func playRemoteTrack(_ id: Int) async {
        do {
            let track = try await client.trackInfo(id)
            await player.play(track: track)
        } catch { show(error) }
    }
}
