import SwiftUI

struct SignInView: View {
    @EnvironmentObject private var app: AppState
    @State private var mode = 0
    @State private var server = UserDefaults.standard.string(forKey: "server_url") ?? "http://127.0.0.1:8000"
    @State private var username = ""
    @State private var password = ""
    @State private var invite = ""
    @State private var busy = false

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                Spacer(minLength: 40)
                Image(systemName: "music.note.house.fill")
                    .font(.system(size: 52))
                    .foregroundStyle(Theme.violet)
                Text("mcmusic").font(.largeTitle.bold())
                Text("Your library, your playlists, your rules.")
                    .font(.subheadline).foregroundStyle(.secondary)

                Picker("Mode", selection: $mode) {
                    Text("Sign in").tag(0)
                    Text("Create account").tag(1)
                }
                .pickerStyle(.segmented)

                VStack(spacing: 12) {
                    field("Server", text: $server, icon: "server.rack")
                        .textInputAutocapitalization(.never)
                        .keyboardType(.URL)
                    field("Username or email", text: $username, icon: "person")
                        .textInputAutocapitalization(.never)
                    SecureField("Password", text: $password)
                        .textFieldStyle(.roundedBorder)
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
                    .font(.caption).foregroundStyle(.secondary).multilineTextAlignment(.center)
                Spacer(minLength: 40)
            }
            .padding(24)
        }
    }

    private func field(_ title: String, text: Binding<String>, icon: String) -> some View {
        HStack {
            Image(systemName: icon).foregroundStyle(.secondary).frame(width: 20)
            TextField(title, text: text).textFieldStyle(.roundedBorder)
        }
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
