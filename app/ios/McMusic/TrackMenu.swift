import SwiftUI

/// The same track actions the Qt desktop client exposes, attached to every
/// track row across the app.
struct TrackMenu: View {
    @EnvironmentObject private var app: AppState
    @Environment(\.mcTokens) private var tokens
    let track: JSON
    let tracks: [JSON]
    var playlistID: Int?
    var onAlbum: ((String) -> Void)?
    var onArtist: ((String) -> Void)?

    @State private var showPlaylists = false
    @State private var showLyrics = false
    @State private var showInfo = false
    @State private var lyrics: JSON?
    @State private var info: JSON?
    @State private var sources: [JSON] = []
    @State private var showSources = false
    @State private var playlists: [JSON] = []

    var body: some View {
        Menu {
            Button { Task { await app.player.play(track: track, from: tracks) } } label: {
                menuLabel("Play now", icon: "play")
            }
            Button { app.player.append([track], playNext: true) } label: {
                menuLabel("Play next", icon: "list-plus")
            }
            Button { app.player.append([track]) } label: {
                menuLabel("Add to queue", icon: "list")
            }
            Button { showPlaylists = true } label: {
                menuLabel("Add to playlist", icon: "folder-plus")
            }
            Button { Task { await radio() } } label: {
                menuLabel("Start radio", icon: "radio")
            }
            Button { Task { await toggleLike() } } label: {
                menuLabel(track["liked"]?.bool == true ? "Unlike" : "Like", icon: "heart")
            }
            if !track.albumName.isEmpty {
                Button { onAlbum?(track.albumName) } label: {
                    menuLabel("Go to album", icon: "library")
                }
            }
            Button { onArtist?(track.artistName) } label: {
                menuLabel("Go to artist", icon: "user")
            }
            Button { Task { await loadLyrics() } } label: {
                menuLabel("Lyrics", icon: "message-circle")
            }
            Button { Task { await loadInfo() } } label: {
                menuLabel("Track info", icon: "info")
            }
            Button { Task { await loadSources() } } label: {
                menuLabel("Sources", icon: "link")
            }
            if let playlistID {
                Button(role: .destructive) { Task { await removeFromPlaylist(playlistID) } } label: {
                    menuLabel("Remove from playlist", icon: "trash-2")
                }
            }
            if app.isAdmin {
                Button { Task { await toggleExplicit() } } label: {
                    menuLabel(track["explicit"]?.bool == true ? "Clear explicit flag" : "Mark explicit",
                              icon: "shield-alert")
                }
            }
        } label: {
            LucideIcon(name: "more-horizontal", size: 18, color: tokens.dim)
        }
        .sheet(isPresented: $showPlaylists) { playlistPicker }
        .sheet(isPresented: $showLyrics) {
            DetailText(title: "Lyrics", text: lyrics?["lyrics"]?.string
                       ?? lyrics?["text"]?.string ?? "No lyrics yet.")
        }
        .sheet(isPresented: $showInfo) {
            DetailText(title: track.title, text: infoText)
        }
        .sheet(isPresented: $showSources) {
            NavigationStack {
                List(sources, id: \.id) { source in
                    VStack(alignment: .leading, spacing: 2) {
                        Text(source["title"]?.string ?? source["yt_id"]?.string ?? "Source")
                        if let raw = source["url"]?.string, let url = URL(string: raw) {
                            Link(raw, destination: url)
                                .font(.caption)
                        }
                    }
                }
                .navigationTitle("Sources")
                .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { showSources = false } } }
            }
        }
    }

    private func menuLabel(_ title: String, icon: String) -> some View {
        Label {
            Text(title)
        } icon: {
            LucideIcon(name: icon, size: 18)
        }
    }

    private var infoText: String {
        guard let info else { return "Loading…" }
        let keys = ["title", "artist", "album", "genre", "year", "duration",
                    "yt_channel", "yt_likes", "yt_views", "yt_date", "added", "lyrics_source"]
        return keys.compactMap { key in
            guard let value = info[key], !value.isNull else { return nil }
            return "\(key): \(value.string ?? "")"
        }.joined(separator: "\n")
    }

    private var playlistPicker: some View {
        NavigationStack {
            List {
                if playlists.isEmpty {
                    StateView(text: "No playlists yet", icon: "list-music")
                }
                ForEach(playlists, id: \.trackID) { list in
                    Button {
                        Task {
                            try? await app.client.addToPlaylist(list.trackID, trackID: track.trackID)
                            showPlaylists = false
                            app.show("Added to \(list.title)")
                        }
                    } label: {
                        HStack {
                            Text(list.title)
                            Spacer()
                            Text("\(list.itemCount)").foregroundStyle(tokens.dim)
                        }
                    }
                }
            }
            .navigationTitle("Add to playlist")
            .toolbar { ToolbarItem(placement: .cancellationAction) { Button("Done") { showPlaylists = false } } }
            .task { playlists = (try? await app.client.playlists()) ?? [] }
        }
    }

    private func radio() async {
        do {
            let songs = try await app.client.radio(track.trackID)
            if !songs.isEmpty { await app.player.playQueue(songs) }
            else { app.show("No radio tracks available") }
        } catch { app.show(error) }
    }

    private func toggleLike() async {
        do {
            _ = try await app.client.like(track.trackID)
        } catch { app.show(error) }
    }

    private func loadLyrics() async {
        do { lyrics = try await app.client.lyrics(track.trackID); showLyrics = true }
        catch { app.show(error) }
    }

    private func loadInfo() async {
        do { info = try await app.client.trackInfo(track.trackID); showInfo = true }
        catch { app.show(error) }
    }

    private func loadSources() async {
        do {
            sources = try await app.client.trackSources(track.trackID)
            showSources = true
        } catch { app.show(error) }
    }

    private func toggleExplicit() async {
        do { try await app.client.setExplicit(track.trackID, explicit: track["explicit"]?.bool != true) }
        catch { app.show(error) }
    }

    private func removeFromPlaylist(_ id: Int) async {
        do { try await app.client.removeFromPlaylist(id, trackID: track.trackID) }
        catch { app.show(error) }
    }
}

struct DetailText: View {
    let title: String
    let text: String

    var body: some View {
        NavigationStack {
            ScrollView {
                Text(text).frame(maxWidth: .infinity, alignment: .leading).padding()
            }
            .navigationTitle(title)
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } } }
        }
    }

    @Environment(\.dismiss) private var dismiss
}
