import SwiftUI

struct SearchView: View {
    @EnvironmentObject private var app: AppState
    @Environment(\.mcTokens) private var tokens
    @State private var query = ""
    @State private var results: JSON?
    @State private var searching = false

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                HStack {
                    LucideIcon(name: "search", size: 18, color: tokens.dim)
                    TextField("Songs, albums, artists", text: $query)
                        .onSubmit { Task { await search() } }
                    if !query.isEmpty {
                        Button { query = ""; results = nil } label: {
                            LucideIcon(name: "x-circle", size: 18, color: tokens.dim)
                        }
                    }
                }
                .padding(10)
                .background(tokens.surface.opacity(0.6))

                if searching {
                    ProgressView().frame(maxWidth: .infinity)
                } else if let results {
                    List {
                        let tracks = results["tracks"]?.array ?? []
                        if !tracks.isEmpty {
                            Section("Songs (\(tracks.count))") {
                                ForEach(Array(tracks.enumerated()), id: \.offset) { _, track in
                                    HStack {
                                        TrackRow(track: track, onPlay: {
                                            Task { await app.player.play(track: track, from: tracks) }
                                        })
                                        TrackMenu(track: track, tracks: tracks)
                                    }
                                }
                            }
                        }
                        let albums = results["albums"]?.array ?? []
                        if !albums.isEmpty {
                            Section("Albums (\(albums.count))") {
                                ForEach(Array(albums.enumerated()), id: \.offset) { _, album in
                                    NavigationLink(value: Detail.album(album["album"]?.string ?? "")) {
                                        HStack {
                                            CoverView(url: app.client.coverURL(album["cover_id"]), size: 44)
                                            VStack(alignment: .leading) {
                                                Text(album["album"]?.string ?? "Album")
                                                Text(album["artist"]?.string ?? "")
                                                    .font(.caption).foregroundStyle(tokens.dim)
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        let artists = results["artists"]?.array ?? []
                        if !artists.isEmpty {
                            Section("Artists (\(artists.count))") {
                                ForEach(Array(artists.enumerated()), id: \.offset) { _, artist in
                                    NavigationLink(value: Detail.artist(artist["artist"]?.string ?? "")) {
                                        Label {
                                            Text(artist["artist"]?.string ?? "Artist")
                                        } icon: {
                                            LucideIcon(name: "user", size: 18)
                                        }
                                    }
                                }
                            }
                        }
                        if tracks.isEmpty && albums.isEmpty && artists.isEmpty {
                            StateView(text: "No results for “\(query)”", icon: "search")
                        }
                    }
                    .listStyle(.plain)
                } else {
                    StateView(text: "Search your library", icon: "search")
                }
            }
            .navigationTitle("Search")
            .mcmusicNavigation()
        }
        .task {
            // `/` focuses search on the web; on iOS the field is already visible.
        }
    }

    private func search() async {
        guard !query.trimmingCharacters(in: .whitespaces).isEmpty else { return }
        searching = true
        defer { searching = false }
        do { results = try await app.client.search(query) }
        catch { app.show(error) }
    }
}
