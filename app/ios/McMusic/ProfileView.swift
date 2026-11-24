import SwiftUI

/// Public profile/listening view, equivalent to web `/u/:username`.
struct ProfileView: View {
    @EnvironmentObject private var app: AppState
    let username: String
    @State private var profile: JSON?
    @State private var loading = true

    var body: some View {
        Group {
            if loading {
                ProgressView().frame(maxWidth: .infinity)
            } else if let profile {
                ScrollView {
                    VStack(alignment: .leading, spacing: 16) {
                        HStack(spacing: 14) {
                            AsyncImage(url: URL(string: profile["cover_url"]?.string ?? "")) { image in
                                image.resizable().scaledToFill()
                            } placeholder: {
                                RoundedRectangle(cornerRadius: 12).fill(Color(hex: "241A38"))
                            }
                            .frame(width: 88, height: 88)
                            .clipShape(RoundedRectangle(cornerRadius: 12))
                            VStack(alignment: .leading, spacing: 4) {
                                Text(profile["username"]?.string ?? username).font(.title2.bold())
                                Text(profile["listening"]?.bool == true ? "Listening now" : "Not listening")
                                    .foregroundStyle(.secondary)
                            }
                        }

                        if let track = profile["track"], !track.isNull {
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Now playing").font(.headline)
                                TrackRow(track: track) {
                                    Task { await app.player.play(track: track) }
                                }
                            }
                            .padding(14)
                            .background(RoundedRectangle(cornerRadius: 10).fill(Color(hex: "100C18")))
                            .overlay(RoundedRectangle(cornerRadius: 10).stroke(Color(hex: "2A2040"), lineWidth: 1))
                        }

                        if let url = profile["profile_url"]?.string, let link = URL(string: url) {
                            Link("Open public profile", destination: link)
                                .buttonStyle(.bordered)
                        }
                    }
                    .padding()
                }
            } else {
                StateView(text: "Could not load profile", systemImage: "person.crop.circle.badge.exclamationmark") {
                    Task { await load() }
                }
            }
        }
        .navigationTitle(username)
        .task { await load() }
        .refreshable { await load() }
    }

    private func load() async {
        loading = true
        defer { loading = false }
        do { profile = try await app.client.publicNow(username) }
        catch { app.show(error) }
    }
}
