import SwiftUI

/// Public listening directory and profile peek, matching the web/Android home
/// listener cards without embedding any web content.
struct ListeningView: View {
    @EnvironmentObject private var app: AppState
    @Environment(\.mcTokens) private var tokens
    @State private var listeners: [JSON] = []

    var body: some View {
        NavigationStack {
            Group {
                if listeners.isEmpty {
                    StateView(text: "Nobody is listening right now", icon: "radio")
                } else {
                    List(listeners, id: \.id) { listener in
                        NavigationLink(value: Detail.profile(listener["username"]?.string ?? "")) {
                            HStack(spacing: 12) {
                                AsyncImage(url: URL(string: listener["cover_url"]?.string ?? "")) { image in
                                    image.resizable().scaledToFill()
                                } placeholder: {
                                    RoundedRectangle(cornerRadius: 10).fill(tokens.surface2)
                                }
                                .frame(width: 44, height: 44)
                                .clipShape(RoundedRectangle(cornerRadius: 10))

                                VStack(alignment: .leading, spacing: 2) {
                                    Text(listener["username"]?.string ?? "Listener")
                                        .foregroundStyle(.primary)
                                    if let track = listener["track"] {
                                        Text("\(track["title"]?.string ?? "Unknown") — \(track["artist"]?.string ?? "")")
                                            .font(.caption)
                                            .foregroundStyle(tokens.dim)
                                            .lineLimit(1)
                                    } else {
                                        Text(listener["listening"]?.bool == true ? "Listening" : "Paused")
                                            .font(.caption).foregroundStyle(tokens.dim)
                                    }
                                }
                                Spacer()
                                if listener["listening"]?.bool == true {
                                    LucideIcon(name: "audio-lines", size: 18, color: tokens.accent)
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
            .mcmusicNavigation()
            .task { await load() }
        }
    }

    private func load() async {
        do { listeners = try await app.client.publicListening() }
        catch { app.show(error) }
    }

}
