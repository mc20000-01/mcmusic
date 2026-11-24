import SwiftUI

enum Detail: Hashable {
    case album(String)
    case artist(String)
    case playlist(Int)
    case set(String)
    case profile(String)
}

struct DetailNavigation: ViewModifier {
    @EnvironmentObject private var app: AppState

    func body(content: Content) -> some View {
        content.navigationDestination(for: Detail.self) { destination in
            switch destination {
            case .album(let name): AlbumView(name: name)
            case .artist(let name): ArtistView(name: name)
            case .playlist(let id): PlaylistView(id: id)
            case .set(let name): AlbumView(name: name)
            case .profile(let username): ProfileView(username: username)
            }
        }
    }
}

extension View {
    func mcmusicNavigation() -> some View {
        modifier(DetailNavigation())
    }
}

/// A compact cover tile used in shelves throughout the app.
struct CoverTile: View {
    let title: String
    let subtitle: String
    let cover: URL?

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            CoverView(url: cover, size: 140, radius: 12)
            Text(title).font(.subheadline.weight(.medium)).lineLimit(1)
            Text(subtitle).font(.caption).foregroundStyle(.secondary).lineLimit(1)
        }
        .frame(width: 140)
    }
}
