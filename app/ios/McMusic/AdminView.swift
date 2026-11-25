import SwiftUI

struct AdminView: View {
    @EnvironmentObject private var app: AppState
    @Environment(\.mcTokens) private var tokens
    @State private var stats: JSON?
    @State private var algo: JSON?
    @State private var users: [JSON] = []
    @State private var invites: [JSON] = []
    @State private var requests: [JSON] = []
    @State private var devices: [JSON] = []
    @State private var rooms: [JSON] = []
    @State private var channels: [JSON] = []
    @State private var log: JSON?
    @State private var showChannel = false
    @State private var channelName = ""

    var body: some View {
        NavigationStack {
            List {
                Section("Overview") {
                    if let stats {
                        stat("Users", stats["users"]?.int ?? 0)
                        stat("Admins", stats["admins"]?.int ?? 0)
                        stat("Tracks", stats["tracks"]?.int ?? 0)
                        stat("Albums", stats["albums"]?.int ?? 0)
                        stat("Playlists", stats["playlists"]?.int ?? 0)
                        stat("Plays", stats["plays"]?.int ?? 0)
                        stat("Requests", requestsCount)
                        stat("Rooms", stats["rooms"]?.int ?? 0)
                        stat("Queue", stats["queue"]?.int ?? 0)
                        LabeledContent("Uptime", value: uptime(stats["uptime"]?.double ?? 0))
                    } else {
                        ProgressView()
                    }
                    if let algo {
                        Button("Learning model") {
                            log = .object(["log": .string(pretty(algo))])
                        }
                        .buttonStyle(.borderless)
                    }
                }

                Section("Library jobs") {
                    Button("Rescan library") { Task { await scan() } }
                    Button("Run metadata enrichment") { Task { await run { try await app.client.adminRunEnrich() } } }
                    Button("Fetch missing lyrics") { Task { await run { try await app.client.adminRunLyrics() } } }
                }

                Section("Users") {
                    ForEach(users, id: \.id) { user in
                        HStack {
                            VStack(alignment: .leading) {
                                Text(user["username"]?.string ?? "User")
                                Text("\(user["plays"]?.int ?? 0) plays · \(user["likes"]?.int ?? 0) likes")
                                    .font(.caption).foregroundStyle(tokens.dim)
                            }
                            Spacer()
                            Toggle("Admin", isOn: Binding(
                                get: { user["is_admin"]?.bool ?? false },
                                set: { value in Task { await setAdmin(user, value) } }
                            ))
                            .labelsHidden()
                            Button("Delete", role: .destructive) { Task { await deleteUser(user.trackID) } }
                                .buttonStyle(.borderless)
                        }
                    }
                }

                Section("Invites") {
                    Button("Create invite code") {
                        Task { await run { _ = try await app.client.adminCreateInvite() } }
                    }
                    ForEach(invites, id: \.id) { invite in
                        HStack {
                            Text(invite["code"]?.string ?? "")
                            Spacer()
                            Text("\(invite["uses"]?.int ?? 0)/\(invite["max_uses"]?.int ?? 0)")
                                .font(.caption).foregroundStyle(tokens.dim)
                            Button("Revoke", role: .destructive) { Task { await revokeInvite(invite.trackID) } }
                                .buttonStyle(.borderless)
                        }
                    }
                }

                Section("Request queue") {
                    ForEach(requests, id: \.id) { row in
                        VStack(alignment: .leading, spacing: 4) {
                            Text(row["url"]?.string ?? "").font(.caption).lineLimit(1)
                            HStack {
                                Text(row["status"]?.string ?? "").font(.caption2).foregroundStyle(tokens.dim)
                                Spacer()
                                if ["pending", "failed"].contains(row["status"]?.string ?? "") {
                                    Button("Approve") { Task { await requestAction(row.trackID, "approve") } }
                                        .buttonStyle(.borderless)
                                    Button("Reject", role: .destructive) { Task { await requestAction(row.trackID, "reject") } }
                                        .buttonStyle(.borderless)
                                }
                                Button("Log") { Task { await openLog(row.trackID) } }
                                    .buttonStyle(.borderless)
                            }
                        }
                    }
                }

                Section("Devices") {
                    ForEach(devices, id: \.id) { device in
                        HStack {
                            LucideIcon(name: device["is_active"]?.bool == true ? "volume-2" : "volume-1",
                                       size: 18,
                                       color: device["is_active"]?.bool == true ? tokens.accent : tokens.dim)
                            VStack(alignment: .leading) {
                                Text(device["name"]?.string ?? "Device")
                                Text(device["username"]?.string ?? "")
                                    .font(.caption).foregroundStyle(tokens.dim)
                            }
                        }
                    }
                }

                Section("Rooms") {
                    ForEach(rooms, id: \.id) { room in
                        HStack {
                            Text(room["code"]?.string ?? "")
                            Spacer()
                            Text(room["host"]?.string ?? "")
                                .font(.caption).foregroundStyle(tokens.dim)
                            Button("Close", role: .destructive) { Task { await closeRoom(room["code"]?.string ?? "") } }
                                .buttonStyle(.borderless)
                        }
                    }
                }

                Section("Channels") {
                    Button("Add channel") { showChannel = true }
                    ForEach(channels, id: \.id) { channel in
                        HStack {
                            Text(channel["name"]?.string ?? "Channel")
                            Spacer()
                            Button("Delete", role: .destructive) { Task { await deleteChannel(channel.trackID) } }
                                .buttonStyle(.borderless)
                        }
                    }
                }
            }
            .navigationTitle("Admin")
            .refreshable { await load() }
            .sheet(item: $log) { value in
                DetailText(title: "Details", text: value["log"]?.string ?? "")
            }
            .sheet(isPresented: $showChannel) {
                NavigationStack {
                    Form { TextField("Channel name", text: $channelName) }
                        .navigationTitle("New channel")
                        .toolbar {
                            ToolbarItem(placement: .cancellationAction) { Button("Cancel") { showChannel = false } }
                            ToolbarItem(placement: .confirmationAction) {
                                Button("Add") {
                                    Task {
                                        await run { _ = try await app.client.createChannel(name: channelName) }
                                        channelName = ""
                                        showChannel = false
                                    }
                                }
                            }
                        }
                }
            }
        }
        .task { await load() }
    }

    private var requestsCount: Int {
        if let count = stats?["requests"]?["pending"]?.int {
            return count
        }
        return stats?["requests"]?.int ?? requests.count
    }

    private func stat(_ label: String, _ value: Int) -> some View {
        LabeledContent(label, value: "\(value)")
    }

    private func uptime(_ seconds: Double) -> String {
        let minutes = Int(seconds) / 60
        if minutes < 60 { return "\(minutes)m" }
        return "\(minutes / 60)h \(minutes % 60)m"
    }

    private func pretty(_ value: JSON) -> String {
        guard let data = try? JSONSerialization.data(withJSONObject: value.anyValue, options: [.prettyPrinted]),
              let text = String(data: data, encoding: .utf8) else { return "No details" }
        return text
    }

    private func load() async {
        do {
            stats = try await app.client.adminStats()
            algo = try? await app.client.adminAlgo()
            users = try await app.client.adminUsers()
            invites = try await app.client.adminInvites()
            requests = try await app.client.adminRequests()
            devices = try await app.client.adminDevices()
            rooms = try await app.client.adminRooms()
            channels = try await app.client.channels()
        } catch { app.show(error) }
    }

    private func run(_ action: () async throws -> Void) async {
        do {
            try await action()
            await load()
        } catch { app.show(error) }
    }

    private func scan() async {
        do {
            let result = try await app.client.adminScan()
            app.show("Scanned \(result["tracks"]?.int ?? 0) tracks, \(result["albums"]?.int ?? 0) albums")
            await load()
        } catch { app.show(error) }
    }

    private func setAdmin(_ user: JSON, _ value: Bool) async {
        await run { try await app.client.adminSetAdmin(user.trackID, isAdmin: value) }
    }

    private func deleteUser(_ id: Int) async {
        await run { try await app.client.adminDeleteUser(id) }
    }

    private func revokeInvite(_ id: Int) async {
        await run { try await app.client.adminDeleteInvite(id) }
    }

    private func requestAction(_ id: Int, _ action: String) async {
        await run { try await app.client.requestAct(id, action: action) }
    }

    private func openLog(_ id: Int) async {
        do { log = try await app.client.adminRequestLog(id) }
        catch { app.show(error) }
    }

    private func closeRoom(_ code: String) async {
        guard !code.isEmpty else { return }
        await run { try await app.client.adminCloseRoom(code) }
    }

    private func deleteChannel(_ id: Int) async {
        await run { try await app.client.deleteChannel(id) }
    }
}
