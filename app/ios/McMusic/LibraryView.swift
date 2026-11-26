import SwiftUI

struct LibraryView: View {
    @EnvironmentObject private var app: AppState
    @State private var tab = 0
    @State private var tracks: [JSON] = []
    @State private var albums: [JSON] = []
    @State private var artists: [JSON] = []
    @State private var liked: [JSON] = []
    @State private var playlists: [JSON] = []
    @State private var loading = true

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                Picker("Library", selection: $tab) {
                    Text("Songs").tag(0)
                    Text("Albums").tag(1)
                    Text("Artists").tag(2)
                    Text("Playlists").tag(3)
                    Text("Liked").tag(4)
                }
                .pickerStyle(.segmented)
                .padding()

                if loading {
                    ProgressView().frame(maxWidth: .infinity)
                } else {
                    switch tab {
                    case 0: trackList(tracks)
                    case 1: albumGrid(albums)
                    case 2: artistList(artists)
                    case 3: playlistList(playlists)
                    default: trackList(liked)
                    }
                }
            }
            .navigationTitle("Library")
            .refreshable { await load() }
            .mcmusicNavigation()
        }
        .task { await load() }
    }

    private func trackList(_ songs: [JSON]) -> some View {
        List {
            ForEach(Array(songs.enumerated()), id: \.offset) { index, song in
                HStack {
                    TrackRow(track: song, number: index + 1, onPlay: {
                        Task { await app.player.play(track: song, from: songs) }
                    })
                    TrackMenu(track: song, tracks: songs)
                }
            }
        }
        .listStyle(.plain)
        .overlay {
            if songs.isEmpty { StateView(text: "Nothing here yet", icon: "music-note") }
        }
    }

    private func albumGrid(_ rows: [JSON]) -> some View {
        ScrollView {
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 140))], spacing: 18) {
                ForEach(Array(rows.enumerated()), id: \.offset) { _, row in
                    NavigationLink(value: Detail.album(row["album"]?.string ?? "")) {
                        CoverTile(title: row["album"]?.string ?? "Album",
                                  subtitle: row["artist"]?.string ?? "",
                                  cover: app.client.coverURL(row["cover_id"]))
                    }
                    .buttonStyle(PlayfulButtonStyle())
                }
            }
            .padding()
        }
    }

    private func artistList(_ rows: [JSON]) -> some View {
        List {
            ForEach(Array(rows.enumerated()), id: \.offset) { _, row in
                NavigationLink(value: Detail.artist(row["artist"]?.string ?? "")) {
                    HStack {
                        CoverView(url: app.client.coverURL(row["cover_id"]),
                                  seed: row["artist"]?.string ?? "Artist",
                                  size: 44)
                        VStack(alignment: .leading) {
                            Text(row["artist"]?.string ?? "Artist")
                            Text("\(row.itemCount) songs · \(row["albums"]?.int ?? 0) albums")
                                .font(.caption).foregroundStyle(.secondary)
                        }
                    }
                    .frame(minHeight: M3Shape.touch)
                }
            }
        }
        .listStyle(.plain)
    }

    private func playlistList(_ rows: [JSON]) -> some View {
        List {
            ForEach(Array(rows.enumerated()), id: \.offset) { _, row in
                NavigationLink(value: Detail.playlist(row["id"]?.int ?? 0)) {
                    HStack {
                        CoverView(url: app.client.coverURL(row["cover_id"]),
                                  seed: row["name"]?.string ?? "Playlist",
                                  size: 44)
                        VStack(alignment: .leading) {
                            Text(row["name"]?.string ?? "Playlist")
                            Text("\(row["count"]?.int ?? 0) songs")
                                .font(.caption).foregroundStyle(.secondary)
                        }
                    }
                    .frame(minHeight: M3Shape.touch)
                }
            }
        }
        .listStyle(.plain)
        .overlay {
            if rows.isEmpty { StateView(text: "No playlists yet", icon: "list-music") }
        }
    }

    private func load() async {
        loading = true
        defer { loading = false }
        do {
            tracks = try await app.client.tracks()
            albums = try await app.client.albums()
            artists = try await app.client.artists()
            liked = try await app.client.likes()
            playlists = try await app.client.playlists()
        } catch { app.show(error) }
    }
}

struct AlbumView: View {
    @EnvironmentObject private var app: AppState
    let name: String
    @State private var songs: [JSON] = []

    var body: some View {
        List {
            ForEach(Array(songs.enumerated()), id: \.offset) { index, song in
                HStack {
                    TrackRow(track: song, number: song["track_no"]?.int ?? index + 1, onPlay: {
                        Task { await app.player.play(track: song, from: songs) }
                    })
                    TrackMenu(track: song, tracks: songs, onAlbum: nil, onArtist: nil)
                }
            }
        }
        .listStyle(.plain)
        .navigationTitle(name)
        .toolbar {
            if !songs.isEmpty {
                Button("Play all") { Task { await app.player.playQueue(songs) } }
            }
        }
        .task { songs = (try? await app.client.album(name)) ?? [] }
    }
}

struct ArtistView: View {
    @EnvironmentObject private var app: AppState
    let name: String
    @State private var songs: [JSON] = []

    var body: some View {
        List {
            ForEach(Array(songs.enumerated()), id: \.offset) { index, song in
                HStack {
                    TrackRow(track: song, number: index + 1, onPlay: {
                        Task { await app.player.play(track: song, from: songs) }
                    })
                    TrackMenu(track: song, tracks: songs, onAlbum: nil, onArtist: nil)
                }
            }
        }
        .listStyle(.plain)
        .navigationTitle(name)
        .toolbar {
            if !songs.isEmpty {
                Button("Play all") { Task { await app.player.playQueue(songs) } }
            }
        }
        .task { songs = (try? await app.client.artist(name)) ?? [] }
    }
}
