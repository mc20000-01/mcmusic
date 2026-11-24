import SwiftUI

struct SearchView: View {
    @EnvironmentObject private var app: AppState
    @State private var query = ""
    @State private var results: JSON?
    @State private var searching = false

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                HStack {
                    Image(systemName: "magnifyingglass").foregroundStyle(.secondary)
                    TextField("Songs, albums, artists", text: $query)
                        .onSubmit { Task { await search() } }
                    if !query.isEmpty {
                        Button { query = ""; results = nil } label: {
                            Image(systemName: "xmark.circle.fill").foregroundStyle(.secondary)
                        }
                    }
                }
                .padding(10)
                .background(Theme.surface.opacity(0.6))

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
                                                    .font(.caption).foregroundStyle(.secondary)
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
                                        Label(artist["artist"]?.string ?? "Artist", systemImage: "person")
                                    }
                                }
                            }
                        }
                        if tracks.isEmpty && albums.isEmpty && artists.isEmpty {
                            StateView(text: "No results for “\(query)”", systemImage: "magnifyingglass")
                        }
                    }
                    .listStyle(.plain)
                } else {
                    StateView(text: "Search your library", systemImage: "magnifyingglass")
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
