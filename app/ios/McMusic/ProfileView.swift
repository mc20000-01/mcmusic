import SwiftUI

/// Public profile/listening view, equivalent to web `/u/:username`.
struct ProfileView: View {
    @EnvironmentObject private var app: AppState
    @Environment(\.mcTokens) private var tokens
    let username: String
    @State private var profile: JSON?
    @State private var loading = true

    var body: some View {
        Group {
            if loading {
                ProgressView().frame(maxWidth: .infinity)
            } else if let profile {
                ScrollView {
                    VStack(alignment: .leading, spacing: M3Shape.lg) {
                        HStack(spacing: M3Shape.md) {
                            CoverView(url: URL(string: profile["cover_url"]?.string ?? ""),
                                      seed: profile["username"]?.string ?? username,
                                      size: 88,
                                      radius: M3Shape.coverLarge)
                            VStack(alignment: .leading, spacing: M3Shape.xs) {
                                Text(profile["username"]?.string ?? username)
                                    .font(M3Type.title)
                                Text(profile["listening"]?.bool == true ? "Listening now" : "Not listening")
                                    .font(M3Type.body)
                                    .foregroundStyle(tokens.dim)
                            }
                        }

                        if let track = profile["track"], !track.isNull {
                            VStack(alignment: .leading, spacing: M3Shape.sm) {
                                Text("Now playing")
                                    .font(M3Type.label)
                                TrackRow(track: track) {
                                    Task { await app.player.play(track: track) }
                                }
                            }
                            .padding(M3Shape.lg)
                            .background(
                                RoundedRectangle(cornerRadius: M3Shape.card, style: .continuous)
                                    .fill(tokens.surfaceContainerLow)
                            )
                        }

                        if let url = profile["profile_url"]?.string, let link = URL(string: url) {
                            Link("Open public profile", destination: link)
                                .buttonStyle(PlayfulProminentButtonStyle())
                        }
                    }
                    .padding()
                }
            } else {
                StateView(text: "Could not load profile", icon: "circle-alert") {
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
