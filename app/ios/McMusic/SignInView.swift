import SwiftUI

struct SignInView: View {
    @EnvironmentObject private var app: AppState
    @Environment(\.mcTokens) private var tokens
    @State private var mode = 0
    @State private var server = UserDefaults.standard.string(forKey: "server_url") ?? "http://127.0.0.1:8000"
    @State private var username = ""
    @State private var password = ""
    @State private var invite = ""
    @State private var busy = false
    @State private var showingForgot = false
    @State private var forgotEmail = ""

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                Spacer(minLength: 40)
                LucideIcon(name: "music-note", size: 52, color: tokens.accent)
                Text("mcmusic").font(.largeTitle.bold())
                Text("Your library, your playlists, your rules.")
                    .font(.subheadline).foregroundStyle(tokens.dim)

                Picker("Mode", selection: $mode) {
                    Text("Sign in").tag(0)
                    Text("Create account").tag(1)
                }
                .pickerStyle(.segmented)

                VStack(spacing: 12) {
                    field("Server", text: $server, icon: "server")
                        .textInputAutocapitalization(.never)
                        .keyboardType(.URL)
                    field("Username or email", text: $username, icon: "user")
                        .textInputAutocapitalization(.never)
                    SecureField("Password", text: $password)
                        .mcTextField()
                    if mode == 0 {
                        Button("Forgot password?") { showingForgot = true }
                            .font(.caption)
                            .foregroundStyle(tokens.dim)
                    }
                    if mode == 1 {
                        field("Invite code", text: $invite, icon: "key")
                            .textInputAutocapitalization(.never)
                    }
                }

                Button {
                    Task { await submit() }
                } label: {
                    if busy { ProgressView() } else { Text(mode == 0 ? "Sign in" : "Create account") }
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.large)
                .disabled(busy || username.isEmpty || password.isEmpty)

                Text("Point this at the same server your other mcmusic clients use. Plain http:// works for a LAN server.")
                    .font(.caption).foregroundStyle(tokens.dim).multilineTextAlignment(.center)
                Spacer(minLength: 40)
            }
            .padding(24)
        }
        .sheet(isPresented: $showingForgot) {
            NavigationStack {
                Form {
                    TextField("Email address", text: $forgotEmail)
                        .textInputAutocapitalization(.never)
                        .keyboardType(.emailAddress)
                    Button("Send reset link") { Task { await sendReset() } }
                }
                .navigationTitle("Reset password")
                .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { showingForgot = false } } }
            }
        }
    }

    private func field(_ title: String, text: Binding<String>, icon: String) -> some View {
        HStack {
            LucideIcon(name: icon, size: 20, color: tokens.dim).frame(width: 20)
            TextField(title, text: text).mcTextField()
        }
    }

    private func sendReset() async {
        do {
            try await app.client.requestPasswordReset(email: forgotEmail)
            app.show("If that address is registered, a reset link is on its way")
            showingForgot = false
            forgotEmail = ""
        } catch { app.show(error) }
    }

    private func submit() async {
        if mode == 1 && password.count < 6 {
            app.show("Password must be at least 6 characters")
            return
        }
        busy = true
        defer { busy = false }
        app.client.setBaseURL(server)
        do {
            if mode == 0 {
                try await app.signIn(username: username, password: password)
            } else {
                try await app.register(username: username, password: password, invite: invite)
            }
        } catch {
            app.show(error)
        }
    }
}
