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
                ZStack {
                    Theme.ink.ignoresSafeArea()
                    ProgressView("Connecting…")
                        .foregroundStyle(.secondary)
                }
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

struct MainTabs: View {
    @EnvironmentObject private var app: AppState
    @State private var showingNowPlaying = false

    var body: some View {
        TabView {
            HomeView().tabItem { Label("Home", systemImage: "house") }
            SearchView().tabItem { Label("Search", systemImage: "magnifyingglass") }
            LibraryView().tabItem { Label("Library", systemImage: "square.stack") }
            PlaylistsView().tabItem { Label("Playlists", systemImage: "music.note.list") }
            RequestsView().tabItem { Label("Requests", systemImage: "arrow.down.circle") }
            SettingsView().tabItem { Label("Settings", systemImage: "gear") }
            if app.isAdmin {
                AdminView().tabItem { Label("Admin", systemImage: "shield") }
            }
        }
        .safeAreaInset(edge: .bottom) { miniPlayer }
        .sheet(isPresented: $showingNowPlaying) { NowPlayingView() }
    }

    private var miniPlayer: some View {
        HStack(spacing: 10) {
            CoverView(url: app.client.coverURL(app.player.current?.coverID), size: 40)
            VStack(alignment: .leading, spacing: 2) {
                Text(app.player.currentTitle).font(.subheadline.weight(.medium)).lineLimit(1)
                Text(app.player.currentArtist).font(.caption).foregroundStyle(.secondary).lineLimit(1)
            }
            Spacer()
            Button { app.player.toggle() } label: {
                Image(systemName: app.player.isPlaying ? "pause.fill" : "play.fill")
            }
            Button { app.player.next() } label: {
                Image(systemName: "forward.fill")
            }
            Button { showingNowPlaying = true } label: {
                Image(systemName: "chevron.up")
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(.ultraThinMaterial)
        .onTapGesture { showingNowPlaying = true }
    }
}
