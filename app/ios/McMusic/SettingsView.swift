import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var app: AppState
    @AppStorage("palette") private var palette = "dusk"
    @AppStorage("accent") private var accent = ""

    @State private var density = "comfy"
    @State private var covers = true
    @State private var autoplay = true
    @State private var hideExplicit = false
    @State private var isPrivate = false
    @State private var ytStats = true
    @State private var rememberVolume = true
    @State private var prefetch = true
    @State private var offlineAudio = true
    @State private var volume = 0.8
    @State private var rotur: JSON?
    @State private var showingPassword = false
    @State private var oldPassword = ""
    @State private var newPassword = ""

    private let guideURL = URL(string: "https://github.com/mc20000-01/mcmusic/blob/main/docs/selfhost.md")!

    var body: some View {
        NavigationStack {
            Form {
                Section("Account") {
                    LabeledContent("Signed in as", value: app.username)
                    LabeledContent("Server", value: app.client.baseURL)
                    if app.isAdmin { LabeledContent("Role", value: "Admin") }
                    Link("Self-hosting guide", destination: guideURL)
                    Button("Change password") { showingPassword = true }
                    Button("Sign out", role: .destructive) { Task { await app.signOut() } }
                }

                Section("Appearance") {
                    Picker("Palette", selection: $palette) {
                        ForEach(["dusk", "paper", "ink", "tide", "copper", "forest", "rose"], id: \.self) {
                            Text($0.capitalized).tag($0)
                        }
                    }
                    TextField("Accent (hex)", text: $accent)
                        .textInputAutocapitalization(.never)
                    Picker("Density", selection: $density) {
                        ForEach(["compact", "comfy", "roomy"], id: \.self) { Text($0).tag($0) }
                    }
                    Toggle("Cover art", isOn: $covers)
                }

                Section("Playback") {
                    Toggle("Autoplay", isOn: $autoplay)
                    Toggle("Prefetch tracks", isOn: $prefetch)
                    Toggle("Offline audio cache", isOn: $offlineAudio)
                    Toggle("Remember volume", isOn: $rememberVolume)
                    VStack {
                        Text("Volume \(Int(volume * 100))%")
                        Slider(value: $volume, in: 0...1)
                    }
                }

                Section("Privacy and content") {
                    Toggle("Hide explicit", isOn: $hideExplicit)
                    Toggle("Private profile", isOn: $isPrivate)
                    Toggle("YouTube statistics", isOn: $ytStats)
                }

                Section("Integrations") {
                    if let status = rotur?["activity"]?["ready"]?.bool ?? rotur?["ready"]?.bool {
                        LabeledContent("Rotur activity", value: status ? "Ready" : "Not ready")
                    }
                    if let reason = rotur?["activity"]?["reason"]?.string ?? rotur?["reason"]?.string {
                        Text(reason).font(.caption).foregroundStyle(.secondary)
                    }
                    if let room = app.settings?["room_url"]?.string, !room.isEmpty {
                        LabeledContent("Room link", value: room)
                    }
                }

                Section {
                    Button("Save settings") { Task { await save() } }
                }
            }
            .navigationTitle("Settings")
            .sheet(isPresented: $showingPassword) {
                NavigationStack {
                    Form {
                        SecureField("Current password", text: $oldPassword)
                        SecureField("New password", text: $newPassword)
                    }
                    .navigationTitle("Change password")
                    .toolbar {
                        ToolbarItem(placement: .cancellationAction) { Button("Cancel") { showingPassword = false } }
                        ToolbarItem(placement: .confirmationAction) {
                            Button("Save") { Task { await changePassword() } }
                        }
                    }
                }
            }
        }
        .task { await load() }
    }

    private func load() async {
        guard let values = try? await app.client.settings() else { return }
        density = values["density"]?.string ?? density
        covers = values["covers"]?.bool ?? covers
        autoplay = values["autoplay"]?.bool ?? autoplay
        hideExplicit = values["hide_explicit"]?.bool ?? hideExplicit
        isPrivate = values["private"]?.bool ?? isPrivate
        ytStats = values["yt_stats"]?.bool ?? ytStats
        rememberVolume = values["remember_volume"]?.bool ?? rememberVolume
        prefetch = values["prefetch"]?.bool ?? prefetch
        offlineAudio = values["offline_audio"]?.bool ?? offlineAudio
        volume = values["volume"]?.double ?? volume
        if let theme = values["theme"]?.string { palette = theme }
        if let color = values["accent"]?.string, !color.isEmpty { accent = color }
        rotur = try? await app.client.roturStatus()
    }

    private func save() async {
        await app.saveSettings([
            "theme": palette,
            "accent": accent,
            "density": density,
            "covers": covers,
            "autoplay": autoplay,
            "hide_explicit": hideExplicit,
            "private": isPrivate,
            "yt_stats": ytStats,
            "remember_volume": rememberVolume,
            "volume": volume,
            "prefetch": prefetch,
            "offline_audio": offlineAudio
        ])
        app.player.volume = Float(volume)
        app.show("Settings saved")
    }

    private func changePassword() async {
        do {
            try await app.client.changePassword(old: oldPassword, new: newPassword)
            showingPassword = false
            oldPassword = ""
            newPassword = ""
            app.show("Password changed")
        } catch { app.show(error) }
    }
}
