import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var app: AppState
    @AppStorage("palette") private var palette = "dusk"
    @AppStorage("accent") private var accent = ""

    @State private var server = UserDefaults.standard.string(forKey: "server_url") ?? "http://127.0.0.1:8000"
    @State private var density = "comfy"
    @State private var material = "plane"
    @State private var realGlass = "auto"
    @State private var covers = true
    @State private var autoplay = true
    @State private var hideExplicit = false
    @State private var isPrivate = false
    @State private var ytStats = true
    @State private var rememberVolume = true
    @State private var prefetch = true
    @State private var offlineAudio = true
    @State private var roturActivity = false
    @State private var discordActivity = false
    @State private var showRoomURL = false
    @State private var volume = 0.8

    @State private var rotur: JSON?
    @State private var discord: JSON?
    @State private var roturURL = ""
    @State private var discordURL = ""
    @State private var roturCode = ""
    @State private var showingPassword = false
    @State private var oldPassword = ""
    @State private var newPassword = ""
    @State private var showingEmail = false
    @State private var email = ""
    @State private var showingReset = false
    @State private var resetEmail = ""
    @State private var resetToken = ""
    @State private var resetPassword = ""

    private let guideURL = URL(string: "https://github.com/mc20000-01/mcmusic/blob/main/docs/selfhost.md")!

    var body: some View {
        NavigationStack {
            Form {
                Section("Account") {
                    LabeledContent("Signed in as", value: app.username)
                    TextField("Server", text: $server)
                        .textInputAutocapitalization(.never)
                        .keyboardType(.URL)
                    if app.isAdmin { LabeledContent("Role", value: "Admin") }
                    Link("Self-hosting guide", destination: guideURL)
                    NavigationLink("Builds and updates") { BuildsView() }
                    Button("Change email") { showingEmail = true }
                    Button("Change password") { showingPassword = true }
                    Button("Forgot password") { showingReset = true }
                    Button("Sign out", role: .destructive) { Task { await app.signOut() } }
                }

                Section("Offline") {
                    LabeledContent("Queued changes", value: "\(app.pendingCount)")
                    Button("Sync now") { Task { await app.syncOutbox() } }
                        .disabled(app.pendingCount == 0)
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
                    Picker("Material", selection: $material) {
                        ForEach(["plane", "glass", "liquid"], id: \.self) { Text($0).tag($0) }
                    }
                    Picker("Glass effect", selection: $realGlass) {
                        ForEach(["auto", "on", "off"], id: \.self) { Text($0).tag($0) }
                    }
                    Toggle("Cover art", isOn: $covers)
                    Toggle("Show room link", isOn: $showRoomURL)
                }

                Section("Playback") {
                    Toggle("Autoplay radio", isOn: $autoplay)
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
                    Toggle("Rotur activity", isOn: $roturActivity)
                    if let ready = rotur?["activity"]?["ready"]?.bool ?? rotur?["ready"]?.bool {
                        LabeledContent("Rotur", value: ready ? "Linked" : "Not linked")
                    }
                    if let reason = rotur?["activity"]?["reason"]?.string ?? rotur?["reason"]?.string {
                        Text(reason).font(.caption).foregroundStyle(.secondary)
                    }
                    if let url = URL(string: roturURL) {
                        Link("Sign in with Rotur", destination: url)
                    }
                    SecureField("Rotur claim code", text: $roturCode)
                        .textInputAutocapitalization(.never)
                    Button("Claim Rotur code") { Task { await claimRotur() } }
                        .disabled(roturCode.isEmpty)
                    Button("Unlink Rotur", role: .destructive) { Task { await run { try await app.client.unlinkRotur() } } }

                    Toggle("Discord activity", isOn: $discordActivity)
                    if let name = discord?["user"]?["username"]?.string ?? discord?["username"]?.string {
                        LabeledContent("Discord", value: name)
                    }
                    if let url = URL(string: discordURL) {
                        Link("Link Discord", destination: url)
                    }
                    Button("Unlink Discord", role: .destructive) { Task { await run { try await app.client.unlinkDiscord() } } }
                }

                Section {
                    Button("Save settings") { Task { await save() } }
                        .buttonStyle(.borderedProminent)
                }
            }
            .navigationTitle("Settings")
            .sheet(isPresented: $showingPassword) { passwordSheet }
            .sheet(isPresented: $showingEmail) { emailSheet }
            .sheet(isPresented: $showingReset) { resetSheet }
        }
        .task { await load() }
    }

    private var passwordSheet: some View {
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

    private var emailSheet: some View {
        NavigationStack {
            Form {
                TextField("Email address", text: $email)
                    .textInputAutocapitalization(.never)
                    .keyboardType(.emailAddress)
            }
            .navigationTitle("Change email")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancel") { showingEmail = false } }
                ToolbarItem(placement: .confirmationAction) { Button("Save") { Task { await changeEmail() } } }
            }
        }
    }

    private var resetSheet: some View {
        NavigationStack {
            Form {
                Section("1. Send a link") {
                    TextField("Email address", text: $resetEmail)
                        .textInputAutocapitalization(.never)
                        .keyboardType(.emailAddress)
                    Button("Send reset link") { Task { await sendReset() } }
                }
                Section("2. Use the token from your email") {
                    SecureField("Reset token", text: $resetToken)
                        .textInputAutocapitalization(.never)
                    Button("Check token") { Task { await checkReset() } }
                    SecureField("New password", text: $resetPassword)
                    Button("Set new password") { Task { await confirmReset() } }
                        .disabled(resetToken.isEmpty || resetPassword.isEmpty)
                }
            }
            .navigationTitle("Reset password")
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { showingReset = false } } }
        }
    }

    private func load() async {
        let values = app.settings ?? (try? await app.client.settings())
        density = values?["density"]?.string ?? density
        material = values?["material"]?.string ?? material
        realGlass = values?["real_glass"]?.string ?? realGlass
        covers = values?["covers"]?.bool ?? covers
        autoplay = values?["autoplay"]?.bool ?? autoplay
        hideExplicit = values?["hide_explicit"]?.bool ?? hideExplicit
        isPrivate = values?["private"]?.bool ?? isPrivate
        ytStats = values?["yt_stats"]?.bool ?? ytStats
        rememberVolume = values?["remember_volume"]?.bool ?? rememberVolume
        prefetch = values?["prefetch"]?.bool ?? prefetch
        offlineAudio = values?["offline_audio"]?.bool ?? offlineAudio
        roturActivity = values?["rotur_activity"]?.bool ?? roturActivity
        discordActivity = values?["discord_activity"]?.bool ?? discordActivity
        showRoomURL = values?["show_room_url"]?.bool ?? showRoomURL
        volume = values?["volume"]?.double ?? volume
        if let theme = values?["theme"]?.string { palette = theme }
        if let color = values?["accent"]?.string, !color.isEmpty { accent = color }
        async let roturStatus = try? await app.client.roturStatus()
        async let discordStatus = try? await app.client.discordStatus()
        async let roturAuth = try? await app.client.roturAuthorize()
        async let discordAuth = try? await app.client.discordAuthorize()
        rotur = await roturStatus
        discord = await discordStatus
        let roturAuthValue = await roturAuth
        let discordAuthValue = await discordAuth
        roturURL = roturAuthValue?["url"]?.string ?? ""
        discordURL = discordAuthValue?["url"]?.string ?? ""
    }

    private func save() async {
        app.client.setBaseURL(server)
        await app.saveSettings([
            "theme": palette,
            "accent": accent,
            "density": density,
            "material": material,
            "real_glass": realGlass,
            "covers": covers,
            "autoplay": autoplay,
            "hide_explicit": hideExplicit,
            "private": isPrivate,
            "yt_stats": ytStats,
            "remember_volume": rememberVolume,
            "volume": volume,
            "prefetch": prefetch,
            "offline_audio": offlineAudio,
            "rotur_activity": roturActivity,
            "discord_activity": discordActivity,
            "show_room_url": showRoomURL
        ])
        app.player.volume = Float(volume)
        app.show("Settings saved")
    }

    private func run(_ action: () async throws -> Void) async {
        do {
            try await action()
            await load()
        } catch { app.show(error) }
    }

    private func claimRotur() async {
        await run {
            let result = try await app.client.roturClaim(code: roturCode)
            if let message = result["error"]?.string { app.show(message) }
            roturCode = ""
        }
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

    private func changeEmail() async {
        do {
            try await app.client.setEmail(email)
            showingEmail = false
            app.show("Email updated")
        } catch { app.show(error) }
    }

    private func sendReset() async {
        do {
            try await app.client.requestPasswordReset(email: resetEmail)
            app.show("If that address is registered, a reset link is on its way")
        } catch { app.show(error) }
    }

    private func checkReset() async {
        do {
            try await app.client.checkReset(token: resetToken)
            app.show("Reset token is valid")
        } catch { app.show(error) }
    }

    private func confirmReset() async {
        do {
            try await app.client.confirmReset(token: resetToken, password: resetPassword)
            showingReset = false
            resetToken = ""
            resetPassword = ""
            app.show("Password reset")
        } catch { app.show(error) }
    }
}
