import SwiftUI

@main
struct McMusicApp: App {
    @StateObject private var app = AppState()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(app)
        }
    }
}

struct RootView: View {
    @EnvironmentObject private var app: AppState

    var body: some View {
        Group {
            if app.booting {
                BootView()
            } else if app.signedIn {
                MainTabs()
            } else {
                SignInView()
            }
        }
        .mcmusicPalette()
        .mcmusicMotion()
        .alert("mcmusic", isPresented: $app.showingMessage) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(app.message ?? "")
        }
    }
}

/// Child of the palette wrapper, so the boot screen reads the same tokens as
/// the signed-in UI instead of a hard-coded legacy ink colour.
private struct BootView: View {
    @Environment(\.mcTokens) private var tokens

    var body: some View {
        ZStack {
            tokens.bg.ignoresSafeArea()
            ProgressView("Connecting…")
                .foregroundStyle(tokens.dim)
        }
    }
}

struct MainTabs: View {
    @EnvironmentObject private var app: AppState
    @Environment(\.mcTokens) private var tokens
    @State private var showingNowPlaying = false

    var body: some View {
        TabView {
            HomeView().tabItem { tabLabel("Home", icon: "home") }
            SearchView().tabItem { tabLabel("Search", icon: "search") }
            LibraryView().tabItem { tabLabel("Library", icon: "library") }
            ListeningView().tabItem { tabLabel("Listening", icon: "headphones") }
            DownloadsView().tabItem { tabLabel("Downloads", icon: "download") }
            PlaylistsView().tabItem { tabLabel("Playlists", icon: "list-music") }
            RequestsView().tabItem { tabLabel("Requests", icon: "inbox") }
            DevicesView().tabItem { tabLabel("Devices", icon: "monitor") }
            SettingsView().tabItem { tabLabel("Settings", icon: "settings") }
            if app.isAdmin {
                AdminView().tabItem { tabLabel("Admin", icon: "shield") }
            }
        }
        .safeAreaInset(edge: .bottom) { miniPlayer }
        .sheet(isPresented: $showingNowPlaying) { NowPlayingView() }
    }

    private func tabLabel(_ title: String, icon: String) -> some View {
        Label {
            Text(title)
        } icon: {
            LucideIcon(name: icon, size: 20)
        }
    }

    private var miniPlayer: some View {
        VStack(spacing: M3Shape.sm) {
            HStack(spacing: M3Shape.md) {
                Button { showingNowPlaying = true } label: {
                    HStack(spacing: M3Shape.md) {
                        CoverView(url: app.client.coverURL(app.player.current?.coverID),
                                  seed: app.player.currentTitle,
                                  size: 44,
                                  radius: M3Shape.coverSmall)
                        VStack(alignment: .leading, spacing: M3Shape.xs) {
                            Text(app.player.currentTitle)
                                .font(M3Type.label)
                                .lineLimit(1)
                            Text(app.player.currentArtist)
                                .font(.caption)
                                .foregroundStyle(tokens.dim)
                                .lineLimit(1)
                        }
                    }
                    .frame(minHeight: M3Shape.touch)
                }
                .buttonStyle(PlayfulButtonStyle(haptic: false))
                .accessibilityLabel("Open now playing")

                Spacer(minLength: 0)
                PlayPauseButton(playing: app.player.isPlaying, size: 48) {
                    app.player.toggle()
                }
                PlayfulIconButton(icon: "skip-forward", size: 20,
                                  tint: tokens.fg, label: "Next track") {
                    app.player.next()
                }
            }

            PlayfulProgress(fraction: app.player.duration > 0
                            ? app.player.progress / app.player.duration : 0,
                            playing: app.player.isPlaying)
        }
        .padding(.horizontal, M3Shape.lg)
        .padding(.vertical, M3Shape.md)
        .background(
            RoundedRectangle(cornerRadius: M3Shape.card, style: .continuous)
                .fill(tokens.surfaceContainerLow)
        )
    }
}
