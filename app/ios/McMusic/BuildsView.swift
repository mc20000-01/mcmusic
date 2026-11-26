import SwiftUI

/// Server version/build metadata and the same download list the web exposes.
struct BuildsView: View {
    @EnvironmentObject private var app: AppState
    @Environment(\.mcTokens) private var tokens
    @State private var version: JSON?
    @State private var ping: JSON?
    @State private var builds: [JSON] = []
    @State private var emailKind = ""
    @State private var emailAddress = ""
    @State private var showingEmail = false
    @State private var updateBuild: JSON?
    @State private var updateURL: URL?
    @State private var showingUpdate = false
    @State private var promptedForUpdate = false

    private var currentVersion: AppVersion { AppVersion.current }

    var body: some View {
        List {
            Section("Update") {
                if let build = updateBuild, let url = updateURL {
                    HStack(alignment: .top, spacing: 10) {
                        LucideIcon(name: "download", size: 20,
                                   color: tokens.accent)
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Version \(build["version"]?.string ?? "new") is available")
                            Text("Installed: \(currentVersion.description)")
                                .font(.caption).foregroundStyle(.secondary)
                            Link("Open download page", destination: url)
                            Text("iOS cannot replace an app from a downloaded build. Open the page in Safari and use the build channel you distribute.")
                                .font(.caption).foregroundStyle(.secondary)
                        }
                    }
                    Button("Dismiss") { updateBuild = nil }
                        .font(.caption)
                } else {
                    StateView(text: "Up to date (\(currentVersion.description))",
                              icon: "check")
                }
            }

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
                        if let url = downloadURL(for: build) {
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
        .sheet(isPresented: $showingUpdate) {
            NavigationStack {
                VStack(spacing: 16) {
                    LucideIcon(name: "download", size: 44, color: tokens.accent)
                    Text("Update available").font(.title3.weight(.semibold))
                    Text("Version \(updateBuild?["version"]?.string ?? "new") is published. Installed: \(currentVersion.description).")
                        .multilineTextAlignment(.center)
                    Text("iOS cannot replace an installed app from a downloaded build. Open the public page in Safari for the build channel you distribute.")
                        .font(.caption).foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                    if let url = updateURL {
                        Link("Open download page", destination: url)
                            .buttonStyle(.borderedProminent)
                    }
                    Button("Later") { showingUpdate = false }
                }
                .padding(24)
                .navigationTitle("Update")
                .toolbar {
                    ToolbarItem(placement: .confirmationAction) {
                        Button("Done") { showingUpdate = false }
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
            checkForUpdate(builds)
        } catch { app.show(error) }
    }

    private func downloadURL(for build: JSON) -> URL? {
        guard let path = build["url"]?.string else { return nil }
        return URL(string: path.hasPrefix("/") ? app.client.baseURL + path : path)
    }

    private func checkForUpdate(_ rows: [JSON]) {
        let installed = AppVersion.current
        let found = rows.first { row in
            guard row["kind"]?.string == "ios",
                  row["available"]?.bool == true else { return false }
            let published = AppVersion(row["version"]?.string)
            return published.isValid && published > installed
        }
        guard let found else {
            updateBuild = nil
            updateURL = nil
            promptedForUpdate = false
            return
        }
        updateBuild = found
        updateURL = downloadURL(for: found)
            ?? URL(string: "https://mcmusic.sdisk.us/downloads")
        if !promptedForUpdate {
            promptedForUpdate = true
            showingUpdate = true
        }
    }

    private func send() async {
        do {
            try await app.client.emailBuild(emailKind, email: emailAddress)
            showingEmail = false
            app.show("Download link sent")
        } catch { app.show(error) }
    }
}
