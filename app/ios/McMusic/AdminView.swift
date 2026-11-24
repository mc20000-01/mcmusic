import SwiftUI

struct AdminView: View {
    @EnvironmentObject private var app: AppState
    @State private var stats: JSON?
    @State private var users: [JSON] = []

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
                        stat("Requests", stats["requests"]?.int ?? 0)
                        stat("Rooms", stats["rooms"]?.int ?? 0)
                        stat("Queue", stats["queue"]?.int ?? 0)
                        LabeledContent("Uptime", value: uptime(stats["uptime"]?.double ?? 0))
                    } else {
                        ProgressView()
                    }
                }

                Section("Library") {
                    Button("Rescan library") { Task { await scan() } }
                }

                Section("Users") {
                    ForEach(Array(users.enumerated()), id: \.offset) { _, user in
                        HStack {
                            VStack(alignment: .leading) {
                                Text(user["username"]?.string ?? "User")
                                Text("\(user["plays"]?.int ?? 0) plays · \(user["likes"]?.int ?? 0) likes")
                                    .font(.caption).foregroundStyle(.secondary)
                            }
                            Spacer()
                            Toggle("Admin", isOn: Binding(
                                get: { user["is_admin"]?.bool ?? false },
                                set: { value in
                                    Task { await setAdmin(user, value) }
                                }
                            ))
                            .labelsHidden()
                        }
                    }
                }
            }
            .navigationTitle("Admin")
            .refreshable { await load() }
        }
        .task { await load() }
    }

    private func stat(_ label: String, _ value: Int) -> some View {
        LabeledContent(label, value: "\(value)")
    }

    private func uptime(_ seconds: Double) -> String {
        let minutes = Int(seconds) / 60
        if minutes < 60 { return "\(minutes)m" }
        return "\(minutes / 60)h \(minutes % 60)m"
    }

    private func load() async {
        do {
            stats = try await app.client.adminStats()
            users = try await app.client.adminUsers()
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
        do { try await app.client.adminSetAdmin(user.trackID, isAdmin: value); await load() }
        catch { app.show(error) }
    }
}
