import Foundation
import UIKit

/// Endpoint map matching the server routes and `Repo` in the desktop client.
/// Every path is relative to `/api/`; APIClient prefixes it and sends the
/// session cookie. Replay-safe writes fall back to the local outbox offline.
extension APIClient {
    private func isOffline(_ error: Error) -> Bool {
        (error as? APIError)?.status == 0
    }

    @discardableResult
    func syncOutbox() async -> Int {
        await outbox.replay(client: self)
    }

    func coverURL(_ trackID: Int?) -> URL? {
        guard let trackID, trackID > 0 else { return nil }
        return try? absoluteURL("tracks/\(trackID)/cover")
    }

    func coverURL(_ value: JSON?) -> URL? {
        guard let value, !value.isNull else { return nil }
        if let id = value.int { return coverURL(id) }
        if let text = value.string { return artworkURL(text) }
        return nil
    }

    // MARK: - authentication and account

    func me() async throws -> JSON { try await get("me") }

    func login(username: String, password: String) async throws -> JSON {
        try await post("login", json: ["username": username, "password": password])
    }

    func register(username: String, password: String, invite: String) async throws -> JSON {
        try await post("register", json: ["username": username, "password": password, "invite": invite])
    }

    func logout() async {
        try? await post("logout")
        clearCookies()
    }

    func changePassword(old: String, new: String) async throws {
        try await post("password", json: ["old": old, "new": new])
    }

    func setEmail(_ email: String) async throws {
        try await post("auth/email", json: ["email": email])
    }

    func requestPasswordReset(email: String) async throws {
        try await post("auth/reset/request", json: ["email": email])
    }

    func checkReset(token: String) async throws {
        try await post("auth/reset/check", json: ["token": token])
    }

    func confirmReset(token: String, password: String) async throws {
        try await post("auth/reset/confirm", json: ["token": token, "password": password])
    }

    func roturStatus() async throws -> JSON { try await get("auth/rotur/status") }
    func roturKey() async throws -> JSON { try await get("auth/rotur/key") }
    func roturAuthorize() async throws -> JSON { try await get("auth/rotur/authorize") }
    func roturClaim(code: String) async throws -> JSON {
        try await post("auth/rotur/claim", json: ["code": code, "name": UIDevice.current.name])
    }
    func roturLink(token: String) async throws -> JSON {
        try await post("auth/rotur/link", json: ["token": token])
    }
    func unlinkRotur() async throws { try await post("auth/rotur/unlink") }
    func roturActivity(trackID: Int?, position: Double, playing: Bool) async {
        try? await post("auth/rotur/activity", json: [
            "track_id": trackID as Any,
            "position": position,
            "playing": playing
        ])
    }

    func discordStatus() async throws -> JSON { try await get("auth/discord/status") }
    func discordAuthorize() async throws -> JSON { try await get("auth/discord/authorize") }
    func unlinkDiscord() async throws { try await post("auth/discord/unlink") }
    func discordActivity(trackID: Int?, position: Double, playing: Bool) async {
        try? await post("auth/discord/activity", json: [
            "track_id": trackID as Any,
            "position": position,
            "playing": playing
        ])
    }

    // MARK: - settings

    func settings() async throws -> JSON { try await get("settings") }

    func saveSettings(_ values: [String: Any]) async throws {
        do {
            try await put("settings", json: values)
        } catch {
            if isOffline(error) {
                outbox.enqueue("PUT", "settings", json: values)
                return
            }
            throw error
        }
    }

    // MARK: - library

    func home() async throws -> JSON { try await get("home") }

    func tracks(query: String = "", limit: Int = 2000) async throws -> [JSON] {
        var params = ["limit": String(limit)]
        if !query.isEmpty { params["q"] = query }
        return try await get("tracks", query: params)["tracks"]?.array ?? []
    }

    func search(_ query: String) async throws -> JSON {
        try await get("search", query: ["q": query])
    }

    func albums() async throws -> [JSON] { try await get("albums")["albums"]?.array ?? [] }

    func album(_ name: String) async throws -> [JSON] {
        try await get("album", query: ["name": name])["tracks"]?.array ?? []
    }

    func artists() async throws -> [JSON] { try await get("artists")["artists"]?.array ?? [] }

    func artist(_ name: String) async throws -> [JSON] {
        try await get("artist", query: ["name": name])["tracks"]?.array ?? []
    }

    func lyrics(_ trackID: Int) async throws -> JSON { try await get("tracks/\(trackID)/lyrics") }

    func likes() async throws -> [JSON] { try await get("likes")["tracks"]?.array ?? [] }

    func like(_ trackID: Int) async throws -> Bool {
        do {
            return try await post("like/\(trackID)")["liked"]?.bool ?? false
        } catch {
            if isOffline(error) {
                outbox.enqueue("POST", "like/\(trackID)", toggle: true)
                return true
            }
            throw error
        }
    }

    func reportPlay(_ trackID: Int, completed: Bool) async {
        try? await post("plays", json: ["track_id": trackID, "completed": completed])
    }

    func setExplicit(_ trackID: Int, explicit: Bool) async throws {
        try await request("PATCH", "tracks/\(trackID)", json: ["explicit": explicit])
    }

    func radio(_ trackID: Int) async throws -> [JSON] {
        try await get("radio/\(trackID)")["tracks"]?.array ?? []
    }

    func trackInfo(_ trackID: Int) async throws -> JSON { try await get("tracks/\(trackID)") }

    func trackSources(_ trackID: Int) async throws -> [JSON] {
        try await get("tracks/\(trackID)/sources")["sources"]?.array ?? []
    }

    // MARK: - playlists

    func playlists() async throws -> [JSON] { try await get("playlists")["playlists"]?.array ?? [] }

    func playlist(_ id: Int) async throws -> JSON { try await get("playlists/\(id)") }

    func createPlaylist(_ name: String) async throws -> Int {
        try await post("playlists", json: ["name": name])["id"]?.int ?? 0
    }

    func renamePlaylist(_ id: Int, name: String) async throws {
        do {
            try await request("PATCH", "playlists/\(id)", json: ["name": name])
        } catch {
            if isOffline(error) { outbox.enqueue("PATCH", "playlists/\(id)", json: ["name": name]) }
            else { throw error }
        }
    }

    func deletePlaylist(_ id: Int) async throws {
        do {
            try await delete("playlists/\(id)")
        } catch {
            if isOffline(error) { outbox.enqueue("DELETE", "playlists/\(id)") }
            else { throw error }
        }
    }

    func addToPlaylist(_ id: Int, trackID: Int) async throws {
        let body = ["track_id": trackID]
        do {
            try await post("playlists/\(id)/tracks", json: body)
        } catch {
            if isOffline(error) { outbox.enqueue("POST", "playlists/\(id)/tracks", json: body) }
            else { throw error }
        }
    }

    func removeFromPlaylist(_ id: Int, trackID: Int) async throws {
        do {
            try await delete("playlists/\(id)/tracks/\(trackID)")
        } catch {
            if isOffline(error) { outbox.enqueue("DELETE", "playlists/\(id)/tracks/\(trackID)") }
            else { throw error }
        }
    }

    // MARK: - download requests

    func requests() async throws -> JSON { try await get("requests") }

    func requestAdd(_ url: String) async throws -> String {
        try await post("requests", json: ["url": url])["status"]?.string ?? ""
    }

    func requestAct(_ id: Int, action: String) async throws {
        try await post("requests/\(id)/\(action)")
    }

    func adminRequests() async throws -> [JSON] { try await get("admin/requests")["requests"]?.array ?? [] }
    func adminRequestLog(_ id: Int) async throws -> JSON { try await get("admin/requests/\(id)/log") }
    func adminRequestCancel(_ id: Int) async throws { try await post("admin/requests/\(id)/cancel") }
    func adminRequestRetry(_ id: Int) async throws { try await post("admin/requests/\(id)/retry") }
    func adminRequestDelete(_ id: Int) async throws { try await delete("admin/requests/\(id)") }

    // MARK: - admin

    func adminStats() async throws -> JSON { try await get("admin/stats") }
    func adminUsers() async throws -> [JSON] { try await get("admin/users")["users"]?.array ?? [] }

    func adminSetAdmin(_ userID: Int, isAdmin: Bool) async throws {
        try await post("admin/users/\(userID)/admin", json: ["is_admin": isAdmin])
    }

    func adminDeleteUser(_ userID: Int) async throws { try await delete("admin/users/\(userID)") }
    func adminScan() async throws -> JSON { try await post("admin/scan") }
    func adminAlgo() async throws -> JSON { try await get("admin/algo") }

    func adminInvites() async throws -> [JSON] { try await get("admin/invite-codes")["codes"]?.array ?? [] }
    func adminCreateInvite() async throws -> JSON { try await post("admin/invite-codes") }
    func adminDeleteInvite(_ id: Int) async throws { try await delete("admin/invite-codes/\(id)") }

    func adminDevices() async throws -> [JSON] { try await get("admin/devices")["devices"]?.array ?? [] }
    func adminRooms() async throws -> [JSON] { try await get("admin/rooms")["rooms"]?.array ?? [] }
    func adminCloseRoom(_ code: String) async throws {
        try await request("DELETE", "admin/rooms/\(code.addingPercentEncoding(withAllowedCharacters: .alphanumerics) ?? code)")
    }

    func channels() async throws -> [JSON] { try await get("channels")["channels"]?.array ?? [] }
    func createChannel(name: String) async throws -> JSON { try await post("channels", json: ["name": name]) }
    func deleteChannel(_ id: Int) async throws { try await delete("channels/\(id)") }

    func adminEnrich() async throws -> JSON { try await get("admin/enrich") }
    func adminRunEnrich() async throws -> JSON { try await post("admin/enrich") }
    func adminLyrics() async throws -> JSON { try await get("admin/lyrics") }
    func adminRunLyrics() async throws -> JSON { try await post("admin/lyrics") }

    // MARK: - devices, listening and playback sync

    func devices() async throws -> [JSON] { try await get("devices")["devices"]?.array ?? [] }

    func activateDevice(_ id: Int) async throws { try await post("devices/\(id)/activate") }

    func renameDevice(_ id: Int, name: String) async throws {
        try await request("PATCH", "devices/\(id)", json: ["name": name])
    }

    func forgetDevice(_ id: Int) async throws { try await delete("devices/\(id)") }
    func cleanupDevices() async throws { try await post("devices/cleanup") }
    func clearDevices() async throws { try await post("devices/clear") }
    func deviceSync() async throws -> JSON { try await get("devices/sync") }
    func pairCode() async throws -> JSON { try await post("devices/code") }
    func claimPairCode(_ code: String) async throws -> JSON {
        try await post("devices/claim", json: [
            "code": code,
            "name": UIDevice.current.name,
            "device_hash": AppState.deviceHashValue
        ])
    }
    func deviceTokens() async throws -> [JSON] { try await get("devices/tokens")["tokens"]?.array ?? [] }
    func revokeDeviceToken(_ id: Int) async throws { try await post("devices/tokens/\(id)/revoke") }

    func publicListening() async throws -> [JSON] { try await get("public/listening")["users"]?.array ?? [] }
    func publicNow(_ username: String) async throws -> JSON {
        let encoded = username.addingPercentEncoding(withAllowedCharacters: .alphanumerics) ?? username
        return try await get("public/now/\(encoded)")
    }

    func playback(device: String? = nil) async throws -> JSON {
        var query: [String: String]? = nil
        if let device { query = ["device": device] }
        return try await get("playback", query: query)
    }

    func heartbeat(deviceHash: String, name: String, trackID: Int?, position: Double, paused: Bool) async {
        try? await post("devices/heartbeat", json: [
            "device_hash": deviceHash,
            "name": name,
            "track_id": trackID as Any,
            "position": position,
            "paused": paused
        ])
    }

    func publishPlayback(device: String? = nil, trackID: Int?, position: Double,
                         duration: Double, playing: Bool, queue: [Int]) async {
        var body: [String: Any] = [
            "track_id": trackID as Any,
            "position": position,
            "duration": duration,
            "playing": playing,
            "queue": queue
        ]
        if let device { body["device"] = device }
        try? await post("playback", json: body)
    }

    // MARK: - builds and server metadata

    func ping() async throws -> JSON { try await get("ping") }
    func version() async throws -> JSON { try await get("version") }
    func builds() async throws -> JSON { try await get("builds") }
    func emailBuild(_ kind: String, email: String) async throws {
        try await post("builds/email", json: ["kind": kind, "email": email])
    }
}
