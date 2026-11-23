import Foundation

/// Endpoint map matching `Repo` in app/linux/mcmusic_linux/api.py. Every path
/// is relative to `/api/`; APIClient adds the prefix and the session cookie.
extension APIClient {
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

    // auth
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
    func roturStatus() async throws -> JSON { try await get("auth/rotur/status") }
    func unlinkRotur() async throws { try await post("auth/rotur/unlink") }

    // settings
    func settings() async throws -> JSON { try await get("settings") }
    func saveSettings(_ values: [String: Any]) async throws { try await put("settings", json: values) }

    // library
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
        try await post("like/\(trackID)")["liked"]?.bool ?? false
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

    // playlists
    func playlists() async throws -> [JSON] { try await get("playlists")["playlists"]?.array ?? [] }
    func playlist(_ id: Int) async throws -> JSON { try await get("playlists/\(id)") }
    func createPlaylist(_ name: String) async throws -> Int {
        try await post("playlists", json: ["name": name])["id"]?.int ?? 0
    }
    func renamePlaylist(_ id: Int, name: String) async throws {
        try await request("PATCH", "playlists/\(id)", json: ["name": name])
    }
    func deletePlaylist(_ id: Int) async throws { try await delete("playlists/\(id)") }
    func addToPlaylist(_ id: Int, trackID: Int) async throws {
        try await post("playlists/\(id)/tracks", json: ["track_id": trackID])
    }
    func removeFromPlaylist(_ id: Int, trackID: Int) async throws {
        try await delete("playlists/\(id)/tracks/\(trackID)")
    }

    // requests
    func requests() async throws -> JSON { try await get("requests") }
    func requestAdd(_ url: String) async throws -> String {
        try await post("requests", json: ["url": url])["status"]?.string ?? ""
    }
    func requestAct(_ id: Int, action: String) async throws {
        try await post("requests/\(id)/\(action)")
    }

    // admin
    func adminStats() async throws -> JSON { try await get("admin/stats") }
    func adminUsers() async throws -> [JSON] { try await get("admin/users")["users"]?.array ?? [] }
    func adminSetAdmin(_ userID: Int, isAdmin: Bool) async throws {
        try await post("admin/users/\(userID)/admin", json: ["is_admin": isAdmin])
    }
    func adminScan() async throws -> JSON { try await post("admin/scan") }

    // device / playback registry
    func heartbeat(deviceHash: String, name: String, trackID: Int?, position: Double, paused: Bool) async {
        try? await post("devices/heartbeat", json: [
            "device_hash": deviceHash,
            "name": name,
            "track_id": trackID as Any,
            "position": position,
            "paused": paused
        ])
    }
    func publishPlayback(trackID: Int?, position: Double, duration: Double, playing: Bool, queue: [Int]) async {
        try? await post("playback", json: [
            "track_id": trackID as Any,
            "position": position,
            "duration": duration,
            "playing": playing,
            "queue": queue
        ])
    }
}
