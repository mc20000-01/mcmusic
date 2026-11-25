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
            ListeningView().tabItem { tabLabel("Listening", icon: "radio") }
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
        HStack(spacing: 10) {
            CoverView(url: app.client.coverURL(app.player.current?.coverID), size: 40)
            VStack(alignment: .leading, spacing: 2) {
                Text(app.player.currentTitle).font(.subheadline.weight(.medium)).lineLimit(1)
                Text(app.player.currentArtist).font(.caption).foregroundStyle(tokens.dim).lineLimit(1)
            }
            Spacer()
            Button { app.player.toggle() } label: {
                LucideIcon(name: app.player.isPlaying ? "pause" : "play", size: 20, color: tokens.accent)
            }
            Button { app.player.next() } label: {
                LucideIcon(name: "skip-forward", size: 20, color: tokens.fg)
            }
            Button { showingNowPlaying = true } label: {
                LucideIcon(name: "chevron-up", size: 18, color: tokens.dim)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(tokens.surface)
        .overlay(Rectangle().frame(height: 1).foregroundStyle(tokens.line), alignment: .top)
        .onTapGesture { showingNowPlaying = true }
    }
}
