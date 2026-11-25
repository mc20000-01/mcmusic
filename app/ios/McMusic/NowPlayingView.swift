import SwiftUI

struct NowPlayingView: View {
    @EnvironmentObject private var app: AppState
    @Environment(\.mcTokens) private var tokens
    @Environment(\.dismiss) private var dismiss
    @State private var showQueue = false
    @State private var showLyrics = false
    @State private var lyricsText = "Loading…"

    private var player: Player { app.player }

    var body: some View {
        NavigationStack {
            VStack(spacing: 22) {
                CoverView(url: app.client.coverURL(player.current?.coverID), size: 280)
                    .padding(.top, 12)

                VStack(spacing: 4) {
                    Text(player.currentTitle).font(.title2.bold()).multilineTextAlignment(.center)
                    Text(player.currentArtist).font(.subheadline).foregroundStyle(tokens.dim)
                }

                VStack(spacing: 2) {
                    Slider(value: Binding(
                        get: { player.progress },
                        set: { player.seek(to: $0) }
                    ), in: 0...max(player.duration, 1))
                    HStack {
                        Text(time(player.progress))
                        Spacer()
                        Text(time(player.duration))
                    }
                    .font(.caption).foregroundStyle(tokens.dim)
                }

                HStack(spacing: 28) {
                    Button { player.shuffle.toggle() } label: {
                        LucideIcon(name: "shuffle", size: 22,
                                   color: player.shuffle ? tokens.accent : tokens.dim)
                    }
                    Button { player.previous() } label: {
                        LucideIcon(name: "skip-back", size: 26, color: tokens.fg)
                    }
                    Button { player.toggle() } label: {
                        LucideIcon(name: player.isPlaying ? "pause" : "play",
                                   size: 48, color: tokens.accent)
                    }
                    Button { player.next() } label: {
                        LucideIcon(name: "skip-forward", size: 26, color: tokens.fg)
                    }
                    Button { cycleRepeat() } label: {
                        LucideIcon(name: player.repeatMode == 2 ? "repeat-1" : "repeat",
                                   size: 22,
                                   color: player.repeatMode > 0 ? tokens.accent : tokens.dim)
                    }
                }

                HStack {
                    Button {
                        app.player.volume = app.player.volume > 0 ? 0 : 0.8
                    } label: {
                        LucideIcon(name: app.player.volume > 0 ? "volume-2" : "volume-x",
                                   size: 20, color: tokens.dim)
                    }
                    Slider(value: Binding(
                        get: { Double(app.player.volume) },
                        set: { app.player.volume = Float($0) }
                    ), in: 0...1)
                    LucideIcon(name: "volume-2", size: 20, color: tokens.dim)
                }
                .padding(.horizontal)

                Spacer(minLength: 0)
            }
            .padding(.horizontal, 24)
            .navigationTitle("Now playing")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    HStack {
                        Button { Task { await loadLyrics() } } label: {
                            LucideIcon(name: "message-circle", size: 20, color: tokens.accent)
                        }
                        Menu {
                            Button("Sleep timer: off") { player.setSleepTimer(minutes: 0) }
                            ForEach([5, 15, 30, 45, 60], id: \.self) { minutes in
                                Button("Sleep timer: \(minutes) min") { player.setSleepTimer(minutes: minutes) }
                            }
                            if player.sleepMinutes > 0 {
                                Button("Stop timer (\(player.sleepRemaining / 60)m left)", role: .destructive) {
                                    player.cancelSleepTimer()
                                }
                            }
                        } label: {
                            LucideIcon(name: "moon", size: 20,
                                       color: player.sleepMinutes > 0 ? tokens.accent : tokens.dim)
                        }
                        Button { showQueue = true } label: {
                            LucideIcon(name: "list", size: 20, color: tokens.accent)
                        }
                    }
                }
                ToolbarItem(placement: .cancellationAction) {
                    Button("Close") { dismiss() }
                }
            }
            .sheet(isPresented: $showQueue) { queueView }
            .sheet(isPresented: $showLyrics) {
                LyricSheet(text: lyricsText, progress: player.progress, duration: player.duration, isPlaying: player.isPlaying)
            }
        }
    }

    private var queueView: some View {
        NavigationStack {
            List {
                ForEach(Array(player.queue.enumerated()), id: \.offset) { index, song in
                    HStack {
                        TrackRow(track: song, number: index + 1, onPlay: {
                            Task { await app.player.play(track: song, from: player.queue) }
                        })
                        TrackMenu(track: song, tracks: player.queue)
                    }
                    .foregroundStyle(index == player.index ? tokens.accent : tokens.fg)
                }
                .onMove { source, destination in
                    for offset in source.indices {
                        player.move(from: source[offset], to: destination)
                    }
                }
                .onDelete { offsets in
                    for offset in offsets.sorted(by: >) { player.remove(at: offset) }
                }
            }
            .listStyle(.plain)
            .navigationTitle("Queue")
            .toolbar { EditButton() }
        }
    }

    private func cycleRepeat() {
        player.repeatMode = (player.repeatMode + 1) % 3
        if player.repeatMode != 0 { player.shuffle = false }
    }

    private func time(_ seconds: Double) -> String {
        let value = max(0, Int(seconds))
        return "\(value / 60):\(String(format: "%02d", value % 60))"
    }

    private func loadLyrics() async {
        guard let id = player.currentTrackID else { lyricsText = "Nothing playing."; showLyrics = true; return }
        do {
            let value = try await app.client.lyrics(id)
            lyricsText = value["lyrics"]?.string ?? value["text"]?.string ?? "No lyrics yet."
        } catch {
            lyricsText = "No lyrics yet."
        }
        showLyrics = true
    }
}
