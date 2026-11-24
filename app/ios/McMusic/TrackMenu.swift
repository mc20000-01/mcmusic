import SwiftUI

/// The same track actions the Qt desktop client exposes, attached to every
/// track row across the app.
struct TrackMenu: View {
    @EnvironmentObject private var app: AppState
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
                Label("Play now", systemImage: "play.fill")
            }
            Button { app.player.append([track], playNext: true) } label: {
                Label("Play next", systemImage: "text.insert")
            }
            Button { app.player.append([track]) } label: {
                Label("Add to queue", systemImage: "list.bullet")
            }
            Button { showPlaylists = true } label: {
                Label("Add to playlist", systemImage: "plus.rectangle.on.folder")
            }
            Button { Task { await radio() } } label: {
                Label("Start radio", systemImage: "antenna.radiowaves.left.and.right")
            }
            Button { Task { await toggleLike() } } label: {
                Label(track["liked"]?.bool == true ? "Unlike" : "Like", systemImage: "heart")
            }
            if !track.albumName.isEmpty {
                Button { onAlbum?(track.albumName) } label: {
                    Label("Go to album", systemImage: "square.stack")
                }
            }
            Button { onArtist?(track.artistName) } label: {
                Label("Go to artist", systemImage: "person")
            }
            Button { Task { await loadLyrics() } } label: {
                Label("Lyrics", systemImage: "quote.bubble")
            }
            Button { Task { await loadInfo() } } label: {
                Label("Track info", systemImage: "info.circle")
            }
            Button { Task { await loadSources() } } label: {
                Label("Sources", systemImage: "link")
            }
            if let playlistID {
                Button(role: .destructive) { Task { await removeFromPlaylist(playlistID) } } label: {
                    Label("Remove from playlist", systemImage: "trash")
                }
            }
            if app.isAdmin {
                Button { Task { await toggleExplicit() } } label: {
                    Label(track["explicit"]?.bool == true ? "Clear explicit flag" : "Mark explicit",
                          systemImage: "exclamationmark.shield")
                }
            }
        } label: {
            Image(systemName: "ellipsis").foregroundStyle(.secondary)
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
                    StateView(text: "No playlists yet", systemImage: "music.note.list")
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
                            Text("\(list.itemCount)").foregroundStyle(.secondary)
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
