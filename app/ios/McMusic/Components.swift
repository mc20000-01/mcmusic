import SwiftUI

/// Small on-disk/decode cache so cover art does not flash on every scroll.
final class ImageCache {
    static let shared = ImageCache()
    private var cache = NSCache<NSString, UIImage>()

    func image(for url: URL) async -> UIImage? {
        let key = url.absoluteString as NSString
        if let hit = cache.object(forKey: key) { return hit }
        guard let (data, _) = try? await URLSession.shared.data(from: url),
              let image = UIImage(data: data) else { return nil }
        cache.setObject(image, forKey: key)
        return image
    }
}

struct CoverView: View {
    let url: URL?
    var size: CGFloat = 48
    var radius: CGFloat = 10

    var body: some View {
        Group {
            if let url, let image = image {
                Image(uiImage: image)
                    .resizable()
                    .scaledToFill()
            } else {
                ZStack {
                    RoundedRectangle(cornerRadius: radius)
                        .fill(LinearGradient(colors: [.purple.opacity(0.5), .blue.opacity(0.25)],
                                             startPoint: .topLeading, endPoint: .bottomTrailing))
                    Image(systemName: "music.note")
                        .foregroundStyle(.white.opacity(0.8))
                }
            }
        }
        .frame(width: size, height: size)
        .clipShape(RoundedRectangle(cornerRadius: radius))
        .task(id: url?.absoluteString) {
            if let url { image = await ImageCache.shared.image(for: url) }
        }
    }

    @State private var image: UIImage?
}

struct TrackRow: View {
    let track: JSON
    let number: Int?
    let onPlay: () -> Void
    let onMenu: (() -> Void)?
    @Environment(\.mcAccent) private var accent

    init(track: JSON, number: Int? = nil, onPlay: @escaping () -> Void, onMenu: (() -> Void)? = nil) {
        self.track = track
        self.number = number
        self.onPlay = onPlay
        self.onMenu = onMenu
    }

    var body: some View {
        HStack(spacing: 12) {
            if let number {
                Text("\(number)")
                    .font(.caption.monospacedDigit())
                    .foregroundStyle(.secondary)
                    .frame(width: 20)
            }
            CoverView(url: APIClient.shared.artworkURL(track.first("cover", "art", "image", "thumbnail")?.string), size: 44)
            VStack(alignment: .leading, spacing: 2) {
                Text(track.first("title", "name", "song")?.string ?? "Untitled")
                    .font(.subheadline.weight(.medium))
                    .lineLimit(1)
                Text(track.first("artist", "artist_name", "author")?.string ?? "Unknown artist")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
            }
            Spacer()
            if let likes = track.first("likes", "like_count")?.int {
                Label("\(likes)", systemImage: "heart")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            if let onMenu {
                Button(action: onMenu) {
                    Image(systemName: "ellipsis")
                        .foregroundStyle(.secondary)
                }
                .buttonStyle(.plain)
            }
        }
        .contentShape(Rectangle())
        .onTapGesture(perform: onPlay)
    }
}

struct Shelf<Content: View>: View {
    let title: String
    let subtitle: String?
    let content: Content

    init(_ title: String, subtitle: String? = nil, @ViewBuilder content: () -> Content) {
        self.title = title
        self.subtitle = subtitle
        self.content = content()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(alignment: .firstTextBaseline) {
                VStack(alignment: .leading, spacing: 2) {
                    Text(title).font(.title3.weight(.semibold))
                    if let subtitle { Text(subtitle).font(.caption).foregroundStyle(.secondary) }
                }
                Spacer()
            }
            content
        }
        .padding(.vertical, 4)
    }
}

struct StateView: View {
    let text: String
    var systemImage: String = "music.note"
    var retry: (() -> Void)?

    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: systemImage).font(.largeTitle).foregroundStyle(.secondary)
            Text(text).font(.subheadline).foregroundStyle(.secondary).multilineTextAlignment(.center)
            if let retry { Button("Try again", action: retry).buttonStyle(.borderedProminent) }
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 48)
    }
}
