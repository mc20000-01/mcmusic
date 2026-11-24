import SwiftUI

struct HomeView: View {
    @EnvironmentObject private var app: AppState
    @State private var home: JSON?
    @State private var loading = true

    var body: some View {
        NavigationStack {
            Group {
                if loading {
                    ProgressView("Loading your library…").frame(maxWidth: .infinity)
                } else if let home {
                    ScrollView {
                        VStack(alignment: .leading, spacing: 24) {
                            ForEach(Array((home["sections"]?.array ?? []).enumerated()), id: \.offset) { _, section in
                                let title = section["title"]?.string ?? "Music"
                                let songs = section["tracks"]?.array ?? []
                                Shelf(title) {
                                    ScrollView(.horizontal) {
                                        HStack(spacing: 12) {
                                            ForEach(Array(songs.enumerated()), id: \.offset) { _, song in
                                                NavigationLink(value: Detail.album(song.albumName)) {
                                                    CoverTile(title: song.title,
                                                              subtitle: song.artistName,
                                                              cover: app.client.coverURL(song.coverID))
                                                }
                                                .buttonStyle(.plain)
                                            }
                                        }
                                        .padding(.horizontal, 16)
                                    }
                                }
                                .padding(.horizontal, 16)

                                if !songs.isEmpty {
                                    VStack(spacing: 0) {
                                        ForEach(Array(songs.prefix(5).enumerated()), id: \.offset) { _, song in
                                            trackRow(song, in: songs)
                                        }
                                    }
                                    .padding(.horizontal, 16)
                                }
                            }

                            let albums = home["albums"]?.array ?? []
                            if !albums.isEmpty {
                                Shelf("Albums") {
                                    ScrollView(.horizontal) {
                                        HStack(spacing: 12) {
                                            ForEach(Array(albums.enumerated()), id: \.offset) { _, album in
                                                NavigationLink(value: Detail.album(album["album"]?.string ?? "")) {
                                                    CoverTile(title: album["album"]?.string ?? "Album",
                                                              subtitle: album["artist"]?.string ?? "",
                                                              cover: app.client.coverURL(album["cover_id"]))
                                                }
                                                .buttonStyle(.plain)
                                            }
                                        }
                                        .padding(.horizontal, 16)
                                    }
                                }
                                .padding(.horizontal, 16)
                            }
                        }
                        .padding(.top, 8)
                    }
                } else {
                    StateView(text: "Could not load home", systemImage: "wifi.exclamationmark") {
                        Task { await load() }
                    }
                }
            }
            .navigationTitle("Home")
            .refreshable { await load() }
            .mcmusicNavigation()
        }
        .task { await load() }
    }

    private func trackRow(_ song: JSON, in songs: [JSON]) -> some View {
        HStack {
            TrackRow(track: song, onPlay: {
                Task { await app.player.play(track: song, from: songs) }
            }, onMenu: nil)
            TrackMenu(track: song, tracks: songs)
        }
    }

    private func load() async {
        loading = true
        defer { loading = false }
        do { home = try await app.client.home() }
        catch { app.show(error) }
    }
}
