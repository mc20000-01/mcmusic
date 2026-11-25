import SwiftUI

/// Server version/build metadata and the same download list the web exposes.
struct BuildsView: View {
    @EnvironmentObject private var app: AppState
    @State private var version: JSON?
    @State private var ping: JSON?
    @State private var builds: [JSON] = []
    @State private var emailKind = ""
    @State private var emailAddress = ""
    @State private var showingEmail = false

    var body: some View {
        List {
            Section("Server") {
                LabeledContent("Build", value: version?["build"]?.string ?? "—")
                LabeledContent("Client", value: version?["shell"]?.string ?? "—")
                LabeledContent("Ping", value: ping?["status"]?.string ?? ping?["ok"]?.bool.map { $0 ? "OK" : "Down" } ?? "—")
                Button("Refresh") { Task { await load() } }
            }

            Section("Downloads") {
                if builds.isEmpty {
                    StateView(text: "No builds published", icon: "download")
                }
                ForEach(builds, id: \.id) { build in
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Text(build["label"]?.string ?? build["name"]?.string ?? "Build")
                            Spacer()
                            if let version = build["version"]?.string {
                                Text(version).font(.caption).foregroundStyle(.secondary)
                            }
                        }
                        Text(build["note"]?.string ?? build["hint"]?.string ?? "")
                            .font(.caption).foregroundStyle(.secondary)
                        if let path = build["url"]?.string,
                           let url = URL(string: path.hasPrefix("/") ? app.client.baseURL + path : path) {
                            Link(build["available"]?.bool == true ? "Download" : "Unavailable",
                                 destination: url)
                                .disabled(build["available"]?.bool != true)
                        }
                        Button("Email me a link") {
                            emailKind = build["kind"]?.string ?? ""
                            showingEmail = true
                        }
                        .font(.caption)
                    }
                    .padding(.vertical, 4)
                }
            }
        }
        .navigationTitle("Builds")
        .task { await load() }
        .refreshable { await load() }
        .sheet(isPresented: $showingEmail) {
            NavigationStack {
                Form {
                    TextField("Email address", text: $emailAddress)
                        .textInputAutocapitalization(.never)
                        .keyboardType(.emailAddress)
                }
                .navigationTitle("Send download link")
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) { Button("Cancel") { showingEmail = false } }
                    ToolbarItem(placement: .confirmationAction) {
                        Button("Send") { Task { await send() } }
                            .disabled(emailAddress.isEmpty || emailKind.isEmpty)
                    }
                }
            }
        }
    }

    private func load() async {
        do {
            version = try await app.client.version()
            ping = try? await app.client.ping()
            builds = try await app.client.builds()["builds"]?.array ?? []
        } catch { app.show(error) }
    }

    private func send() async {
        do {
            try await app.client.emailBuild(emailKind, email: emailAddress)
            showingEmail = false
            app.show("Download link sent")
        } catch { app.show(error) }
    }
}
