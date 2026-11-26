import SwiftUI

struct NowPlayingView: View {
    @EnvironmentObject private var app: AppState
    @Environment(\.mcTokens) private var tokens
    @Environment(\.playfulMotion) private var motion
    @Environment(\.dismiss) private var dismiss
    @State private var showQueue = false
    @State private var showLyrics = false
    @State private var lyricsText = "Loading…"

    private var player: Player { app.player }

    var body: some View {
        NavigationStack {
            VStack(spacing: M3Shape.lg) {
                CoverView(url: app.client.coverURL(player.current?.coverID),
                          seed: player.currentTitle,
                          size: 280,
                          radius: M3Shape.hero)
                    .padding(.top, M3Shape.sm)

                VStack(spacing: M3Shape.xs) {
                    Text(player.currentTitle)
                        .font(M3Type.headline)
                        .multilineTextAlignment(.center)
                    Text(player.currentArtist)
                        .font(M3Type.body)
                        .foregroundStyle(tokens.dim)
                }

                VStack(spacing: 0) {
                    PlayfulSeek(value: player.progress,
                                duration: player.duration,
                                playing: player.isPlaying) { seconds in
                        player.seek(to: seconds)
                    }
                    HStack {
                        Text(time(player.progress))
                        Spacer()
                        Text(time(player.duration))
                    }
                    .font(M3Type.label)
                    .foregroundStyle(tokens.dim)
                }

                HStack(spacing: M3Shape.sm) {
                    PlayfulIconButton(icon: "shuffle", size: 20,
                                      tint: player.shuffle ? tokens.primary : tokens.dim,
                                      label: player.shuffle ? "Turn shuffle off" : "Turn shuffle on") {
                        player.shuffle.toggle()
                    }
                    PlayfulIconButton(icon: "skip-back", size: 24,
                                      tint: tokens.fg, label: "Previous track") {
                        player.previous()
                    }
                    PlayPauseButton(playing: player.isPlaying, size: 64) {
                        player.toggle()
                    }
                    PlayfulIconButton(icon: "skip-forward", size: 24,
                                      tint: tokens.fg, label: "Next track") {
                        player.next()
                    }
                    PlayfulIconButton(icon: player.repeatMode == 2 ? "repeat-1" : "repeat",
                                      size: 20,
                                      tint: player.repeatMode > 0 ? tokens.primary : tokens.dim,
                                      label: "Change repeat mode") {
                        cycleRepeat()
                    }
                }
                .padding(.horizontal, M3Shape.sm)
                .padding(.vertical, M3Shape.xs)
                .background(Capsule().fill(tokens.surfaceContainerHigh))

                HStack(spacing: M3Shape.md) {
                    PlayfulIconButton(icon: app.player.volume > 0 ? "volume-2" : "volume-x",
                                      size: 20, tint: tokens.dim, label: "Mute") {
                        app.player.volume = app.player.volume > 0 ? 0 : 0.8
                    }
                    Slider(value: Binding(
                        get: { Double(app.player.volume) },
                        set: { app.player.volume = Float($0) }
                    ), in: 0...1)
                    .tint(tokens.primary)
                    LucideIcon(name: "volume-2", size: 20, color: tokens.dim)
                        .frame(width: M3Shape.touch, height: M3Shape.touch)
                }
                .padding(.horizontal, M3Shape.sm)
                .background(Capsule().fill(tokens.surfaceContainerLow))

                Spacer(minLength: 0)
            }
            .padding(.horizontal, M3Shape.lg)
            .navigationTitle("Now playing")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    HStack(spacing: 0) {
                        PlayfulIconButton(icon: "message-circle", size: 20,
                                          tint: tokens.primary, label: "Lyrics") {
                            Task { await loadLyrics() }
                        }
                        Menu {
                            Button("Sleep timer: off") { player.setSleepTimer(minutes: 0) }
                            ForEach([5, 15, 30, 45, 60], id: \.self) { minutes in
                                Button("Sleep timer: \(minutes) min") {
                                    player.setSleepTimer(minutes: minutes)
                                }
                            }
                            if player.sleepMinutes > 0 {
                                Button("Stop timer (\(player.sleepRemaining / 60)m left)", role: .destructive) {
                                    player.cancelSleepTimer()
                                }
                            }
                        } label: {
                            LucideIcon(name: "moon", size: 20,
                                       color: player.sleepMinutes > 0 ? tokens.primary : tokens.dim)
                                .frame(width: M3Shape.touch, height: M3Shape.touch)
                                .contentShape(Capsule())
                        }
                        PlayfulIconButton(icon: "list", size: 20,
                                          tint: tokens.primary, label: "Queue") {
                            showQueue = true
                        }
                    }
                }
                ToolbarItem(placement: .cancellationAction) {
                    Button("Close") { dismiss() }
                        .buttonStyle(PlayfulButtonStyle())
                }
            }
            .sheet(isPresented: $showQueue) { queueView }
            .sheet(isPresented: $showLyrics) {
                LyricSheet(text: lyricsText,
                           progress: player.progress,
                           duration: player.duration,
                           isPlaying: player.isPlaying)
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
                    .foregroundStyle(index == player.index ? tokens.primary : tokens.fg)
                    .scaleEffect(index == player.index && motion ? 1.01 : 1)
                    .animation(motion ? Playful.spring : nil, value: index == player.index)
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
            .navigationTitle("Up next")
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
        guard let id = player.currentTrackID else {
            lyricsText = "Nothing playing."
            showLyrics = true
            return
        }
        do {
            let value = try await app.client.lyrics(id)
            lyricsText = value["lyrics"]?.string ?? value["text"]?.string ?? "No lyrics yet."
        } catch {
            lyricsText = "No lyrics yet."
        }
        showLyrics = true
    }
}
