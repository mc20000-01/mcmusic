import SwiftUI

struct NowPlayingView: View {
    @EnvironmentObject private var app: AppState
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
                    Text(player.currentArtist).font(.subheadline).foregroundStyle(.secondary)
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
                    .font(.caption).foregroundStyle(.secondary)
                }

                HStack(spacing: 28) {
                    Button { player.shuffle.toggle() } label: {
                        Image(systemName: "shuffle").foregroundStyle(player.shuffle ? Theme.violet : .secondary)
                    }
                    Button { player.previous() } label: {
                        Image(systemName: "backward.fill").font(.title2)
                    }
                    Button { player.toggle() } label: {
                        Image(systemName: player.isPlaying ? "pause.circle.fill" : "play.circle.fill")
                            .font(.system(size: 56))
                            .foregroundStyle(Theme.violet)
                    }
                    Button { player.next() } label: {
                        Image(systemName: "forward.fill").font(.title2)
                    }
                    Button { cycleRepeat() } label: {
                        Image(systemName: player.repeatMode == 2 ? "repeat.1" : "repeat")
                            .foregroundStyle(player.repeatMode > 0 ? Theme.violet : .secondary)
                    }
                }

                HStack {
                    Button {
                        app.player.volume = app.player.volume > 0 ? 0 : 0.8
                    } label: {
                        Image(systemName: app.player.volume > 0 ? "speaker.fill" : "speaker.slash.fill")
                            .foregroundStyle(.secondary)
                    }
                    Slider(value: Binding(
                        get: { Double(app.player.volume) },
                        set: { app.player.volume = Float($0) }
                    ), in: 0...1)
                    Image(systemName: "speaker.wave.3.fill").foregroundStyle(.secondary)
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
                            Image(systemName: "quote.bubble")
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
                            Image(systemName: "moon.zzz")
                                .foregroundStyle(player.sleepMinutes > 0 ? Theme.violet : .secondary)
                        }
                        Button { showQueue = true } label: { Image(systemName: "list.bullet") }
                    }
                }
                ToolbarItem(placement: .cancellationAction) {
                    Button("Close") { dismiss() }
                }
            }
            .sheet(isPresented: $showQueue) { queueView }
            .sheet(isPresented: $showLyrics) { DetailText(title: "Lyrics", text: lyricsText) }
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
                    .foregroundStyle(index == player.index ? Theme.violet : .primary)
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
