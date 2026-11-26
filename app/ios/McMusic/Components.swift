import SwiftUI
import UIKit

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

/// Deterministic flat cover placeholders. Real artwork is never recoloured;
/// these glyphs appear only when there is no decoded image to show.
enum CoverPlaceholder {
    static let glyphs = ["circle", "squircle", "cookie", "flower", "pentagon"]

    static func index(for seed: String) -> Int {
        var hash: UInt64 = 1_469_598_103_934_665_603
        for byte in seed.utf8 {
            hash ^= UInt64(byte)
            hash = hash &* 1_099_511_628_211
        }
        return Int(hash % UInt64(glyphs.count))
    }

    static func glyph(for seed: String) -> String { glyphs[index(for: seed)] }
}

struct CoverView: View {
    let url: URL?
    var seed: String? = nil
    var size: CGFloat = 48
    var radius: CGFloat? = nil
    @Environment(\.mcTokens) private var tokens
    @State private var image: UIImage?

    private var cornerRadius: CGFloat {
        radius ?? (size <= 64 ? M3Shape.coverSmall : M3Shape.coverLarge)
    }

    private var placeholderSeed: String {
        seed ?? url?.absoluteString ?? "cover"
    }

    var body: some View {
        Group {
            if let image {
                Image(uiImage: image)
                    .resizable()
                    .scaledToFill()
            } else {
                ZStack {
                    RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                        .fill(tokens.primaryContainer)
                    LucideIcon(name: CoverPlaceholder.glyph(for: placeholderSeed),
                               size: max(16, min(size * 0.42, 56)),
                               color: tokens.onPrimaryContainer)
                }
            }
        }
        .frame(width: size, height: size)
        .clipShape(RoundedRectangle(cornerRadius: cornerRadius, style: .continuous))
        .task(id: url?.absoluteString) {
            image = nil
            if let url { image = await ImageCache.shared.image(for: url) }
        }
    }
}

struct TrackRow: View {
    let track: JSON
    let number: Int?
    let onPlay: () -> Void
    let onMenu: (() -> Void)?
    @Environment(\.mcTokens) private var tokens
    @Environment(\.playfulMotion) private var motion

    init(track: JSON, number: Int? = nil, onPlay: @escaping () -> Void, onMenu: (() -> Void)? = nil) {
        self.track = track
        self.number = number
        self.onPlay = onPlay
        self.onMenu = onMenu
    }

    private var title: String { track.first("title", "name", "song")?.string ?? "Untitled" }

    var body: some View {
        HStack(spacing: M3Shape.sm) {
            if let number {
                Text("\(number)")
                    .font(M3Type.label.monospacedDigit())
                    .foregroundStyle(tokens.dim)
                    .frame(width: 24)
            }
            CoverView(url: APIClient.shared.artworkURL(track.first("cover", "art", "image", "thumbnail")?.string),
                      seed: title, size: 44)
            VStack(alignment: .leading, spacing: M3Shape.xs) {
                Text(title)
                    .font(M3Type.label)
                    .lineLimit(1)
                Text(track.first("artist", "artist_name", "author")?.string ?? "Unknown artist")
                    .font(.caption)
                    .foregroundStyle(tokens.dim)
                    .lineLimit(1)
            }
            Spacer()
            if let likes = track.first("likes", "like_count")?.int {
                HStack(spacing: M3Shape.xs) {
                    LucideIcon(name: "heart", size: 12, color: tokens.dim)
                    Text("\(likes)")
                }
                .font(.caption)
                .foregroundStyle(tokens.dim)
            }
            if let onMenu {
                Button(action: onMenu) {
                    LucideIcon(name: "more-horizontal", size: 18, color: tokens.dim)
                        .frame(width: M3Shape.touch, height: M3Shape.touch)
                        .contentShape(Capsule())
                }
                .buttonStyle(PlayfulButtonStyle())
                .accessibilityLabel("More options")
            }
        }
        .frame(minHeight: M3Shape.touch)
        .contentShape(Rectangle())
        .onTapGesture {
            if motion { PlayfulHaptic.selection() }
            onPlay()
        }
    }
}

struct Shelf<Content: View>: View {
    let title: String
    let subtitle: String?
    let hero: Bool
    let content: Content
    @Environment(\.mcTokens) private var tokens

    init(_ title: String, subtitle: String? = nil, hero: Bool = false,
         @ViewBuilder content: () -> Content) {
        self.title = title
        self.subtitle = subtitle
        self.hero = hero
        self.content = content()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: M3Shape.md) {
            HStack(alignment: .firstTextBaseline) {
                VStack(alignment: .leading, spacing: M3Shape.xs) {
                    Text(title)
                        .font(hero ? M3Type.headline : M3Type.title)
                    if let subtitle {
                        Text(subtitle)
                            .font(.caption)
                            .foregroundStyle(tokens.dim)
                    }
                }
                Spacer()
            }
            content
        }
        .padding(M3Shape.lg)
        .background(
            RoundedRectangle(cornerRadius: hero ? M3Shape.hero : M3Shape.card,
                             style: .continuous)
                .fill(tokens.surfaceContainerLow)
        )
    }
}

/// Flat input surface: generous radius and one quiet hairline, no glass.
private struct MCFieldBackground: View {
    @Environment(\.mcTokens) private var tokens

    var body: some View {
        RoundedRectangle(cornerRadius: M3Shape.lg, style: .continuous)
            .fill(tokens.surfaceContainerLow)
            .overlay(
                RoundedRectangle(cornerRadius: M3Shape.lg, style: .continuous)
                    .stroke(tokens.outlineVariant, lineWidth: 1)
            )
    }
}

extension View {
    func mcTextField() -> some View {
        self
            .textFieldStyle(.plain)
            .padding(M3Shape.md)
            .frame(minHeight: M3Shape.touch)
            .background(MCFieldBackground())
    }
}

struct StateView: View {
    let text: String
    var icon: String = "music"
    var retry: (() -> Void)?
    @Environment(\.mcTokens) private var tokens

    var body: some View {
        VStack(spacing: M3Shape.md) {
            LucideIcon(name: icon, size: 34, color: tokens.dim)
            Text(text)
                .font(M3Type.body)
                .foregroundStyle(tokens.dim)
                .multilineTextAlignment(.center)
            if let retry {
                Button("Try again", action: retry)
                    .buttonStyle(PlayfulProminentButtonStyle())
            }
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, M3Shape.xl * 2)
    }
}
