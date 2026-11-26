import SwiftUI

/// Download requests + local audio cache management, matching web "Downloads".
struct DownloadsView: View {
    @EnvironmentObject private var app: AppState
    @Environment(\.mcTokens) private var tokens
    @State private var rows: [JSON] = []
    @State private var showingNew = false
    @State private var url = ""
    @State private var log: JSON?
    @State private var cacheBytes: Int64 = 0
    @State private var tab = 0

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                Picker("Downloads", selection: $tab) {
                    Text("Requests").tag(0)
                    Text("Your downloads").tag(1)
                }
                .pickerStyle(.segmented)
                .padding()

                List {
                    if tab == 1 {
                        Section("Your downloads") {
                            LabeledContent("Cached audio", value: byteCount(cacheBytes))
                            Text("Saved tracks play offline and stay in sync with this device's queue.")
                                .font(.caption).foregroundStyle(tokens.dim)
                            Button("Clear audio cache", role: .destructive) { clearCache() }
                        }
                    } else {
                        Section("Requests") {
                            if rows.isEmpty {
                                StateView(text: "No download requests", icon: "download")
                            } else {
                                ForEach(rows, id: \.id) { row in
                                    VStack(alignment: .leading, spacing: 6) {
                                        Text(row["url"]?.string ?? "")
                                            .font(.subheadline)
                                            .textSelection(.enabled)
                                        HStack {
                                            Label {
                                                Text(row["status"]?.string ?? "pending")
                                            } icon: {
                                                LucideIcon(name: "clock", size: 13, color: tokens.dim)
                                            }
                                            .font(.caption).foregroundStyle(tokens.dim)
                                            if let user = row["username"]?.string {
                                                Text("by \(user)").font(.caption).foregroundStyle(tokens.dim)
                                            }
                                        }
                                        if let preview = row["log"]?.string, !preview.isEmpty {
                                            Text(preview).font(.caption2).foregroundStyle(tokens.dim).lineLimit(2)
                                        }
                                        HStack(spacing: 8) {
                                            if app.isAdmin {
                                                if ["pending", "failed"].contains(row["status"]?.string ?? "") {
                                                    Button("Approve") { Task { await act(row, "approve") } }.buttonStyle(.borderedProminent)
                                                    Button("Reject", role: .destructive) { Task { await act(row, "reject") } }.buttonStyle(.bordered)
                                                }
                                                if ["pending", "running", "approved"].contains(row["status"]?.string ?? "") {
                                                    Button("Cancel", role: .destructive) { Task { await adminAct(row.trackID, action: "cancel") } }.buttonStyle(.bordered)
                                                }
                                                if ["failed", "rejected", "cancelled"].contains(row["status"]?.string ?? "") {
                                                    Button("Retry") { Task { await adminAct(row.trackID, action: "retry") } }.buttonStyle(.bordered)
                                                }
                                                Button("Log") { Task { await openLog(row.trackID) } }.buttonStyle(.borderless)
                                                Button("Delete", role: .destructive) { Task { await adminAct(row.trackID, action: "delete") } }.buttonStyle(.borderless)
                                            } else if ["pending"].contains(row["status"]?.string ?? "") {
                                                Button("Cancel request", role: .destructive) { Task { await act(row, "reject") } }.buttonStyle(.bordered)
                                            }
                                        }
                                    }
                                    .padding(.vertical, 4)
                                }
                            }
                        }
                    }
                }
            }
            .navigationTitle("Downloads")
            .toolbar { Button { showingNew = true } label: { LucideIcon(name: "plus", size: 20, color: tokens.accent) } }
            .sheet(isPresented: $showingNew) { newSheet }
            .sheet(item: $log) { value in
                DetailText(title: "Download log", text: value["log"]?.string ?? "No log available.")
            }
            .refreshable { await load() }
        }
        .task { await load() }
    }

    private var newSheet: some View {
        NavigationStack {
            Form {
                TextField("YouTube URL", text: $url)
                    .mcTextField()
                    .textInputAutocapitalization(.never)
                    .keyboardType(.URL)
            }
            .navigationTitle("Request a track")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancel") { showingNew = false } }
                ToolbarItem(placement: .confirmationAction) { Button("Send") { Task { await send() } } }
            }
        }
    }

    private func load() async {
        cacheBytes = Player.audioCacheBytes()
        do {
            rows = app.isAdmin ? try await app.client.adminRequests() : try await app.client.requests()["requests"]?.array ?? []
        } catch { app.show(error) }
    }

    private func send() async {
        do {
            let status = try await app.client.requestAdd(url)
            app.show(status.isEmpty ? "Request sent" : status)
            url = ""
            showingNew = false
            await load()
        } catch { app.show(error) }
    }

    private func act(_ row: JSON, _ action: String) async {
        do { try await app.client.requestAct(row.trackID, action: action); await load() }
        catch { app.show(error) }
    }

    private func adminAct(_ id: Int, action: String) async {
        do {
            switch action {
            case "cancel": try await app.client.adminRequestCancel(id)
            case "retry": try await app.client.adminRequestRetry(id)
            case "delete": try await app.client.adminRequestDelete(id)
            default: try await app.client.requestAct(id, action: action)
            }
            await load()
        } catch { app.show(error) }
    }

    private func openLog(_ id: Int) async {
        do { log = try await app.client.adminRequestLog(id) }
        catch { app.show(error) }
    }

    private func clearCache() {
        Player.clearAudioCache()
        cacheBytes = 0
        app.show("Audio cache cleared")
    }

    private func byteCount(_ bytes: Int64) -> String {
        let formatter = ByteCountFormatter()
        formatter.countStyle = .file
        return formatter.string(fromByteCount: bytes)
    }
}
