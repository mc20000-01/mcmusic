import SwiftUI

struct RequestsView: View {
    @EnvironmentObject private var app: AppState
    @State private var rows: [JSON] = []
    @State private var showingNew = false
    @State private var url = ""

    var body: some View {
        NavigationStack {
            Group {
                if rows.isEmpty {
                    StateView(text: "No download requests", systemImage: "arrow.down.circle")
                } else {
                    List {
                        ForEach(Array(rows.enumerated()), id: \.offset) { _, row in
                            VStack(alignment: .leading, spacing: 6) {
                                Text(row["url"]?.string ?? "").font(.subheadline)
                                HStack {
                                    Label(row["status"]?.string ?? "pending", systemImage: "clock")
                                        .font(.caption).foregroundStyle(.secondary)
                                    if let user = row["username"]?.string {
                                        Text("by \(user)").font(.caption).foregroundStyle(.secondary)
                                    }
                                }
                                if let log = row["log"]?.string, !log.isEmpty {
                                    Text(log).font(.caption2).foregroundStyle(.secondary).lineLimit(3)
                                }
                                if app.isAdmin {
                                    HStack {
                                        Button("Approve") { Task { await act(row, "approve") } }
                                            .buttonStyle(.borderedProminent)
                                        Button("Reject", role: .destructive) { Task { await act(row, "reject") } }
                                            .buttonStyle(.bordered)
                                    }
                                }
                            }
                            .padding(.vertical, 4)
                        }
                    }
                    .listStyle(.plain)
                }
            }
            .navigationTitle("Requests")
            .toolbar {
                Button { showingNew = true } label: { Image(systemName: "plus") }
            }
            .sheet(isPresented: $showingNew) {
                NavigationStack {
                    Form {
                        TextField("YouTube URL", text: $url)
                            .textInputAutocapitalization(.never)
                            .keyboardType(.URL)
                    }
                    .navigationTitle("Request a track")
                    .toolbar {
                        ToolbarItem(placement: .cancellationAction) { Button("Cancel") { showingNew = false } }
                        ToolbarItem(placement: .confirmationAction) {
                            Button("Send") { Task { await send() } }
                        }
                    }
                }
            }
            .refreshable { await load() }
        }
        .task { await load() }
    }

    private func load() async {
        rows = (try? await app.client.requests()["requests"]?.array) ?? []
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
        do {
            try await app.client.requestAct(row.trackID, action: action)
            await load()
        } catch { app.show(error) }
    }
}
