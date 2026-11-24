import SwiftUI

/// Public listening directory and profile peek, matching the web/Android home
/// listener cards without embedding any web content.
struct ListeningView: View {
    @EnvironmentObject private var app: AppState
    @State private var listeners: [JSON] = []
    @State private var profile: JSON?
    @State private var profileName = ""

    var body: some View {
        NavigationStack {
            Group {
                if listeners.isEmpty {
                    StateView(text: "Nobody is listening right now", systemImage: "antenna.radiowaves.left.and.right")
                } else {
                    List(listeners, id: \.id) { listener in
                        Button {
                            profileName = listener["username"]?.string ?? ""
                            profile = listener
                            Task { await loadProfile(profileName) }
                        } label: {
                            HStack(spacing: 12) {
                                AsyncImage(url: URL(string: listener["cover_url"]?.string ?? "")) { image in
                                    image.resizable().scaledToFill()
                                } placeholder: {
                                    RoundedRectangle(cornerRadius: 10).fill(Color(hex: "241A38"))
                                }
                                .frame(width: 44, height: 44)
                                .clipShape(RoundedRectangle(cornerRadius: 10))

                                VStack(alignment: .leading, spacing: 2) {
                                    Text(listener["username"]?.string ?? "Listener")
                                        .foregroundStyle(.primary)
                                    if let track = listener["track"] {
                                        Text("\(track["title"]?.string ?? "Unknown") — \(track["artist"]?.string ?? "")")
                                            .font(.caption)
                                            .foregroundStyle(.secondary)
                                            .lineLimit(1)
                                    } else {
                                        Text(listener["listening"]?.bool == true ? "Listening" : "Paused")
                                            .font(.caption).foregroundStyle(.secondary)
                                    }
                                }
                                Spacer()
                                if listener["listening"]?.bool == true {
                                    Image(systemName: "waveform")
                                        .foregroundStyle(Theme.violet)
                                }
                            }
                        }
                        .buttonStyle(.plain)
                    }
                    .listStyle(.plain)
                }
            }
            .navigationTitle("Listening")
            .refreshable { await load() }
            .sheet(item: $profile) { listener in
                NavigationStack {
                    ScrollView {
                        VStack(alignment: .leading, spacing: 12) {
                            Text(listener["username"]?.string ?? profileName)
                                .font(.title2.bold())
                            if let track = listener["track"] ?? profile?["track"] {
                                LabeledContent("Now playing", value: track["title"]?.string ?? "Unknown")
                                LabeledContent("Artist", value: track["artist"]?.string ?? "")
                                LabeledContent("Album", value: track["album"]?.string ?? "")
                            } else {
                                Text("Not playing anything right now.")
                                    .foregroundStyle(.secondary)
                            }
                            if let url = listener["profile_url"]?.string ?? profile?["profile_url"]?.string {
                                if let link = URL(string: url) {
                                Link("Open profile", destination: link)
                                    .buttonStyle(.bordered)
                            }
                            }
                        }
                        .padding()
                    }
                    .navigationTitle("Profile")
                    .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { profile = nil } } }
                }
            }
        }
        .task { await load() }
    }

    private func load() async {
        do { listeners = try await app.client.publicListening() }
        catch { app.show(error) }
    }

    private func loadProfile(_ name: String) async {
        guard !name.isEmpty else { return }
        do {
            let value = try await app.client.publicNow(name)
            var merged = profile?.object ?? [:]
            for (key, item) in value.object ?? [:] { merged[key] = item }
            profile = .object(merged)
        } catch { app.show(error) }
    }
}
