import SwiftUI

struct PlaylistsView: View {
    @EnvironmentObject private var app: AppState
    @Environment(\.mcTokens) private var tokens
    @State private var playlists: [JSON] = []
    @State private var showingNew = false
    @State private var newName = ""

    var body: some View {
        NavigationStack {
            Group {
                if playlists.isEmpty {
                    StateView(text: "No playlists yet", icon: "list-music")
                } else {
                    List {
                        ForEach(Array(playlists.enumerated()), id: \.offset) { _, item in
                            NavigationLink(value: Detail.playlist(item.trackID)) {
                                HStack {
                                    CoverView(url: app.client.coverURL(item["cover_id"]), size: 48)
                                    VStack(alignment: .leading) {
                                        Text(item.title)
                                        Text("\(item.itemCount) songs").font(.caption).foregroundStyle(tokens.dim)
                                    }
                                }
                            }
                        }
                    }
                    .listStyle(.plain)
                }
            }
            .navigationTitle("Playlists")
            .toolbar {
                Button { showingNew = true } label: { LucideIcon(name: "plus", size: 20, color: tokens.accent) }
            }
            .sheet(isPresented: $showingNew) {
                NavigationStack {
                    Form {
                        TextField("Playlist name", text: $newName)
                    }
                    .navigationTitle("New playlist")
                    .toolbar {
                        ToolbarItem(placement: .cancellationAction) {
                            Button("Cancel") { showingNew = false }
                        }
                        ToolbarItem(placement: .confirmationAction) {
                            Button("Create") { Task { await create() } }
                        }
                    }
                }
            }
            .refreshable { await load() }
            .mcmusicNavigation()
        }
        .task { await load() }
    }

    private func load() async { playlists = (try? await app.client.playlists()) ?? [] }

    private func create() async {
        guard !newName.isEmpty else { return }
        do {
            _ = try await app.client.createPlaylist(newName)
            newName = ""
            showingNew = false
            await load()
        } catch { app.show(error) }
    }
}

struct PlaylistView: View {
    @EnvironmentObject private var app: AppState
    @Environment(\.mcTokens) private var tokens
    let id: Int
    @State private var name = "Playlist"
    @State private var songs: [JSON] = []
    @State private var showingRename = false
    @State private var renameText = ""

    var body: some View {
        List {
            ForEach(Array(songs.enumerated()), id: \.offset) { _, song in
                HStack {
                    TrackRow(track: song, onPlay: {
                        Task { await app.player.play(track: song, from: songs) }
                    })
                    TrackMenu(track: song, tracks: songs, playlistID: id)
                }
            }
        }
        .listStyle(.plain)
        .navigationTitle(name)
        .toolbar {
            Button("Play all") { Task { await app.player.playQueue(songs) } }
            Button { renameText = name; showingRename = true } label: {
                LucideIcon(name: "pencil", size: 20, color: tokens.accent)
            }
            Button(role: .destructive) { Task { await delete() } } label: {
                LucideIcon(name: "trash-2", size: 20, color: tokens.fg)
            }
        }
        .sheet(isPresented: $showingRename) {
            NavigationStack {
                Form { TextField("Name", text: $renameText) }
                    .navigationTitle("Rename playlist")
                    .toolbar {
                        ToolbarItem(placement: .confirmationAction) {
                            Button("Save") { Task { await rename() } }
                        }
                    }
            }
        }
        .task { await load() }
    }

    private func load() async {
        do {
            let detail = try await app.client.playlist(id)
            name = detail["name"]?.string ?? "Playlist"
            songs = detail["tracks"]?.array ?? []
        } catch { app.show(error) }
    }

    private func rename() async {
        do {
            try await app.client.renamePlaylist(id, name: renameText)
            showingRename = false
            await load()
        } catch { app.show(error) }
    }

    private func delete() async {
        do {
            try await app.client.deletePlaylist(id)
        } catch { app.show(error) }
    }
}
