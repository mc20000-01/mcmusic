# mcmusic 4.3.0 — Phase 3 report

Branch: `design-4.3.0`, based on the CI-green Android phase (`7c19d88`). iOS-only phase: no version bump and no release action.

## What changed

- Added `BlobShape.swift`: a dependency-free parser for the five generated normalised 100×100 blob paths. It supports the absolute M/H/V/C/Q/A/L/Z commands emitted by the generator, converts arcs to ≤90° cubic Béziers, exposes true bounds for tests, and scales the resulting `CGPath` into any SwiftUI rect. `blobId(for:)` maps a seed string deterministically onto one of the generated ids.
- `CoverView` now renders a flat `primaryContainer` blob with a single `outlineVariant` hairline for missing artwork. Real downloaded artwork is clipped to the existing continuous rounded rectangle; the frame itself no longer clips the placeholder, so the blob silhouette is visible.
- Replaced the Now Playing play/pause control with `MorphingPlayPauseButton`: a capsule becomes the generated squircle blob while playing, using the shared morph spring only when playful motion is enabled, with the existing haptic and VoiceOver semantics preserved.
- Rebuilt the Now Playing details area as a segmented `Lyrics | Up next` pill inside the scroll view. Lyrics reuse the existing `LyricParser` and `LyricVisualizer` (genuine LRC only, raw text otherwise); Up next reuses the same queue rows as the full queue sheet, including the existing skip/remove/move calls. The toolbar Lyrics and Queue buttons now select the matching segment in addition to opening their sheets.
- Added two XCTests: every generated blob path parses to sane bounds inside the 100×100 canvas, and the seed→blob mapping is deterministic and always chooses a generated id.
- Left the five palette ids/aliases, `playfulMotion` storage key, Reduce Motion handling, Dynamic Type sizes, local fonts, cleartext policy and signing setup untouched.

## What was run

- `node scripts/gen-tokens.mjs --check` and `node scripts/gen-lucide.mjs --check` — no drift.
- `.venv/bin/python -m pytest tests/test_no_gradients.py tests/test_contrast.py tests/test_generated_fresh.py tests/test_blobs.py tests/test_font_bundling.py tests/test_lucide_paths.py -q` — 9 passed.
- `git diff --check` — no whitespace errors.
- Swift compilation and XCTest cannot run in this Linux workspace (no Xcode/Simulator). CI's unsigned Simulator build job is the authoritative compile gate, and its result is recorded in the CI log for this push.

### Local gate tail

```
    .........                                                                [100%]
    9 passed in 12.98s
```

## What was not done and why

- No new iOS screen or navigation destination was added. The compact shell, flat tonal chrome, haptics, Reduce Motion and Dynamic Type work shipped in 4.2.0; this phase changes the geometry and the details-panel interaction only.
- No Mixes tab, global Charts, codec/lossless badge, Dolby/Spatial label or word-level karaoke was added. The feature-truth audit in `docs/design-4.3.md` records why each lacks a real source; Sing Mode remains gated on genuine LRC line timings.
- No new network request, CDN font, tracker or storage key was introduced. Blob paths are generated locally; lyrics and queue data are the existing local fetches.
- No on-device appearance claim is made: no mockup was supplied and there is no simulator in this workspace. CI's Simulator build verifies compilation, not pixel fidelity.
- No Android/Qt/web code or version carrier was touched in this commit.

## Full authored file contents

Every authored file in this phase is reproduced below in full. Generated blob modules from Phase 0 are unchanged.


### `app/ios/McMusic/Components.swift`

```swift
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

    private var placeholderBlob: String { blobId(for: placeholderSeed) }

    var body: some View {
        Group {
            if let image {
                Image(uiImage: image)
                    .resizable()
                    .scaledToFill()
                    .clipShape(RoundedRectangle(cornerRadius: cornerRadius,
                                                style: .continuous))
            } else {
                ZStack {
                    BlobShape(id: placeholderBlob)
                        .fill(tokens.primaryContainer)
                        .overlay(
                            BlobShape(id: placeholderBlob)
                                .stroke(tokens.outlineVariant, lineWidth: 1)
                        )
                    LucideIcon(name: CoverPlaceholder.glyph(for: placeholderSeed),
                               size: max(16, min(size * 0.42, 56)),
                               color: tokens.onPrimaryContainer)
                }
            }
        }
        .frame(width: size, height: size)
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
```


### `app/ios/McMusic/NowPlayingView.swift`

```swift
import SwiftUI

private enum DetailPanel: String, CaseIterable, Identifiable {
    case lyrics
    case upNext

    var id: String { rawValue }
    var label: String { self == .lyrics ? "Lyrics" : "Up next" }
}

struct NowPlayingView: View {
    @EnvironmentObject private var app: AppState
    @Environment(\.mcTokens) private var tokens
    @Environment(\.playfulMotion) private var motion
    @Environment(\.dismiss) private var dismiss
    @State private var showQueue = false
    @State private var showLyrics = false
    @State private var lyricsText = "Loading…"
    @State private var detailPanel: DetailPanel = .lyrics

    private var player: Player { app.player }
    private var lyricLines: [String] {
        LyricParser.parse(lyricsText)?.map(\.text)
            ?? lyricsText.components(separatedBy: .newlines)
    }

    var body: some View {
        NavigationStack {
            ScrollView {
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
                    MorphingPlayPauseButton(playing: player.isPlaying, size: 64) {
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

                Picker("Now playing details", selection: $detailPanel) {
                    ForEach(DetailPanel.allCases) { panel in
                        Text(panel.label).tag(panel).accessibilityLabel(panel.label)
                    }
                }
                .pickerStyle(.segmented)
                .padding(.horizontal, M3Shape.sm)
                .frame(minHeight: M3Shape.touch)
                .accessibilityLabel("Now playing details")
                .accessibilityHint("Show lyrics or the up next queue")

                if detailPanel == .lyrics {
                    lyricsPanel
                } else {
                    upNextPanel
                }

                Spacer(minLength: 0)
            }
            .padding(.horizontal, M3Shape.lg)
            }
            .navigationTitle("Now playing")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    HStack(spacing: 0) {
                        PlayfulIconButton(icon: "message-circle", size: 20,
                                          tint: tokens.primary, label: "Lyrics") {
                            detailPanel = .lyrics
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
                            detailPanel = .upNext
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

    /// Same rows as the full queue sheet, shared by the inline Up next panel.
    private var queueRows: some View {
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

    private var queueView: some View {
        NavigationStack {
            List { queueRows }
                .listStyle(.plain)
                .navigationTitle("Up next")
                .toolbar { EditButton() }
        }
    }

    private var lyricsPanel: some View {
        VStack(alignment: .leading, spacing: M3Shape.sm) {
            LyricVisualizer(progress: player.progress, isPlaying: player.isPlaying)
                .frame(height: 72)
            ForEach(Array(lyricLines.enumerated()), id: \.offset) { _, line in
                Text(line.isEmpty ? " " : line)
                    .font(M3Type.body)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            Button("Open full lyrics") { Task { await loadLyrics() } }
                .buttonStyle(PlayfulButtonStyle())
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .accessibilityLabel("Lyrics")
        .task(id: player.currentTrackID) { await fetchLyrics() }
    }

    private var upNextPanel: some View {
        LazyVStack(spacing: 0) { queueRows }
            .frame(maxWidth: .infinity, alignment: .leading)
            .accessibilityLabel("Up next queue")
    }

    private func cycleRepeat() {
        player.repeatMode = (player.repeatMode + 1) % 3
        if player.repeatMode != 0 { player.shuffle = false }
    }

    private func time(_ seconds: Double) -> String {
        let value = max(0, Int(seconds))
        return "\(value / 60):\(String(format: "%02d", value % 60))"
    }

    private func fetchLyrics() async {
        guard let id = player.currentTrackID else {
            lyricsText = "Nothing playing."
            return
        }
        do {
            let value = try await app.client.lyrics(id)
            lyricsText = value["lyrics"]?.string ?? value["text"]?.string ?? "No lyrics yet."
        } catch {
            lyricsText = "No lyrics yet."
        }
    }

    private func loadLyrics() async {
        await fetchLyrics()
        showLyrics = true
    }
}

/// Transport control in this sheet: a capsule becomes the canonical squircle
/// blob while playing. The shape change uses the shared spring only when
/// playful motion is on; haptics and VoiceOver semantics are unchanged.
private struct MorphingPlayPauseButton: View {
    let playing: Bool
    var size: CGFloat = 64
    let action: () -> Void

    @Environment(\.playfulMotion) private var motion
    @Environment(\.mcTokens) private var tokens

    var body: some View {
        Button {
            if motion { PlayfulHaptic.impact(.medium) }
            action()
        } label: {
            ZStack {
                Group {
                    if playing {
                        BlobShape(id: "blob-2")
                            .fill(tokens.primary)
                    } else {
                        Capsule()
                            .fill(tokens.primary)
                    }
                }
                .animation(motion ? Playful.morph : nil, value: playing)
                LucideIcon(name: playing ? "pause" : "play",
                           size: size * 0.38, color: tokens.onPrimary)
                    .rotationEffect(.degrees(playing && motion ? 90 : 0))
            }
        }
        .buttonStyle(PlayfulButtonStyle(haptic: false))
        .frame(width: size, height: size)
        .animation(motion ? Playful.morph : nil, value: playing)
        .accessibilityLabel(playing ? "Pause" : "Play")
    }
}
```


### `app/ios/McMusic/BlobShape.swift`

```swift
import SwiftUI

/// Parses the generated normalised 100x100 blob strings into Core Graphics
/// paths. Only the absolute commands emitted by the generator are supported:
/// M, H, V, C, Q, A, L and Z. Arcs are approximated with cubic Béziers.
enum BlobPathParser {
    static let canvas: CGFloat = 100

    static func path(for id: String) -> CGPath? {
        guard let source = BlobShapes.paths[id] else { return nil }
        return parse(source)
    }

    /// Bounds in the same 100x100 coordinate space as the generated strings.
    static func bounds(for id: String) -> CGRect? {
        guard let path = path(for: id) else { return nil }
        let box = path.boundingBoxOfPath
        return box.isNull ? nil : box
    }

    static func parse(_ source: String) -> CGPath {
        let tokens = source.split(whereSeparator: { $0 == "," || $0.isWhitespace })
            .map(String.init)
        let path = CGMutablePath()
        var current = CGPoint.zero
        var subpathStart = CGPoint.zero
        var index = 0

        func number() -> Double {
            guard index < tokens.count, let value = Double(tokens[index]) else { return 0 }
            index += 1
            return value
        }
        func point() -> CGPoint {
            CGPoint(x: CGFloat(number()), y: CGFloat(number()))
        }

        while index < tokens.count {
            let command = tokens[index].uppercased()
            index += 1
            switch command {
            case "M":
                current = point()
                path.move(to: current)
                subpathStart = current
            case "L":
                current = point()
                path.addLine(to: current)
            case "H":
                current = CGPoint(x: CGFloat(number()), y: current.y)
                path.addLine(to: current)
            case "V":
                current = CGPoint(x: current.x, y: CGFloat(number()))
                path.addLine(to: current)
            case "C":
                let c1 = point(), c2 = point(), end = point()
                path.addCurve(to: end, control1: c1, control2: c2)
                current = end
            case "Q":
                let control = point(), end = point()
                path.addQuadCurve(to: end, control: control)
                current = end
            case "A":
                let radiusX = number(), radiusY = number(), rotation = number()
                let largeArc = number(), sweep = number(), end = point()
                appendArc(to: path, from: current, radiusX: radiusX, radiusY: radiusY,
                          rotation: rotation, largeArc: largeArc, sweep: sweep, end: end)
                current = end
            case "Z":
                path.closeSubpath()
                current = subpathStart
            default:
                break
            }
        }
        return path
    }

    /// Endpoint-to-centre conversion followed by 90°-or-smaller cubic arcs.
    private static func appendArc(to path: CGMutablePath, from start: CGPoint,
                                  radiusX: Double, radiusY: Double, rotation: Double,
                                  largeArc: Double, sweep: Double, end: CGPoint) {
        guard abs(radiusX) > 0, abs(radiusY) > 0 else {
            path.addLine(to: end)
            return
        }
        let x1 = Double(start.x), y1 = Double(start.y)
        let x2 = Double(end.x), y2 = Double(end.y)
        let phi = rotation * .pi / 180
        let cosPhi = cos(phi), sinPhi = sin(phi)
        let dx = (x1 - x2) / 2, dy = (y1 - y2) / 2
        let x1r = cosPhi * dx + sinPhi * dy
        let y1r = -sinPhi * dx + cosPhi * dy

        var rx = abs(radiusX), ry = abs(radiusY)
        let lambda = x1r * x1r / (rx * rx) + y1r * y1r / (ry * ry)
        if lambda > 1 {
            let scale = sqrt(lambda)
            rx *= scale
            ry *= scale
        }
        let denominator = rx * rx * y1r * y1r + ry * ry * x1r * x1r
        let numerator = rx * rx * ry * ry - denominator
        let factor = sqrt(max(0, numerator / max(denominator, .ulpOfOne)))
        let sign = (largeArc != 0) == (sweep != 0) ? -1.0 : 1.0
        let cxr = sign * factor * rx * y1r / ry
        let cyr = sign * factor * -ry * x1r / rx
        let cx = cosPhi * cxr - sinPhi * cyr + (x1 + x2) / 2
        let cy = sinPhi * cxr + cosPhi * cyr + (y1 + y2) / 2

        let ux = (x1r - cxr) / rx, uy = (y1r - cyr) / ry
        let vx = (-x1r - cxr) / rx, vy = (-y1r - cyr) / ry
        let startAngle = angle(1, 0, ux, uy)
        var delta = angle(ux, uy, vx, vy)
        if sweep == 0, delta > 0 { delta -= 2 * .pi }
        if sweep != 0, delta < 0 { delta += 2 * .pi }

        let segments = max(1, Int(ceil(abs(delta) / (.pi / 2))))
        let step = delta / Double(segments)
        let handle = (4.0 / 3.0) * tan(step / 4)

        func point(at angle: Double) -> CGPoint {
            let c = cos(angle), s = sin(angle)
            return CGPoint(
                x: CGFloat(cx + rx * c * cosPhi - ry * s * sinPhi),
                y: CGFloat(cy + rx * c * sinPhi + ry * s * cosPhi)
            )
        }
        func tangent(at angle: Double) -> (Double, Double) {
            let c = cos(angle), s = sin(angle)
            return (-rx * s * cosPhi - ry * c * sinPhi,
                    -rx * s * sinPhi + ry * c * cosPhi)
        }

        for segment in 0..<segments {
            let a0 = startAngle + step * Double(segment)
            let a1 = a0 + step
            let p0 = point(at: a0), p1 = point(at: a1)
            let d0 = tangent(at: a0), d1 = tangent(at: a1)
            path.addCurve(
                to: p1,
                control1: CGPoint(x: CGFloat(Double(p0.x) + handle * d0.0),
                                  y: CGFloat(Double(p0.y) + handle * d0.1)),
                control2: CGPoint(x: CGFloat(Double(p1.x) - handle * d1.0),
                                  y: CGFloat(Double(p1.y) - handle * d1.1))
            )
        }
    }

    private static func angle(_ ax: Double, _ ay: Double,
                              _ bx: Double, _ by: Double) -> Double {
        atan2(ax * by - ay * bx, ax * bx + ay * by)
    }
}

/// Flat generated blob, scaled into the proposed rect. No decorative effects.
struct BlobShape: Shape {
    let id: String

    func path(in rect: CGRect) -> Path {
        guard let source = BlobPathParser.path(for: id) else {
            return Path(roundedRect: rect, cornerRadius: min(rect.width, rect.height) / 2)
        }
        var transform = CGAffineTransform(translationX: rect.origin.x, y: rect.origin.y)
            .scaledBy(x: rect.width / BlobPathParser.canvas,
                      y: rect.height / BlobPathParser.canvas)
        guard let scaled = source.copy(using: &transform) else { return Path(source) }
        return Path(scaled)
    }
}

/// Stable per-item blob choice: the same seed always gets the same shape.
func blobId(for seed: String) -> String {
    var hash: UInt64 = 1_469_598_103_934_665_603
    for byte in seed.utf8 {
        hash ^= UInt64(byte)
        hash = hash &* 1_099_511_628_211
    }
    return BlobShapes.ids[Int(hash % UInt64(BlobShapes.ids.count))]
}
```


### `app/ios/McMusicTests/McMusicTests.swift`

```swift
import XCTest
@testable import McMusic

final class McMusicTests: XCTestCase {
    func testNormalizeAddsSchemeAndStripsTrailingSlash() {
        XCTAssertEqual(APIClient.normalize("example.com:8000/"), "http://example.com:8000")
        XCTAssertEqual(APIClient.normalize(" https://music.example.com "), "https://music.example.com")
    }

    func testRelativePathsGoThroughTheApiPrefix() throws {
        let client = APIClient(baseURL: "https://music.example.com")
        let url = try client.absoluteURL("tracks/12/stream")
        XCTAssertEqual(url.absoluteString, "https://music.example.com/api/tracks/12/stream")
    }

    func testQueryIsPreserved() throws {
        let client = APIClient(baseURL: "https://music.example.com")
        let url = try client.absoluteURL("search", query: ["q": "hello world"])
        XCTAssertEqual(url.absoluteString, "https://music.example.com/api/search?q=hello%20world")
    }

    func testTolerantJSONParsing() throws {
        let data = Data(#"{"id":"42","title":"Song","liked":true,"extra":null}"#.utf8)
        let json = try JSON(data)
        XCTAssertEqual(json["id"]?.int, 42)
        XCTAssertEqual(json.title, "Song")
        XCTAssertEqual(json["liked"]?.bool, true)
        XCTAssertTrue(json["extra"]?.isNull ?? false)
        XCTAssertNil(json["missing"])
    }

    func testTrackHelpers() throws {
        let json = try JSON(Data(#"{"id":7,"title":"T","artist":"A","cover_id":9}"#.utf8))
        XCTAssertEqual(json.trackID, 7)
        XCTAssertEqual(json.title, "T")
        XCTAssertEqual(json.artistName, "A")
        XCTAssertEqual(json.coverID, 9)
    }

    func testCoverURLUsesTheTrackCoverEndpoint() throws {
        let client = APIClient(baseURL: "https://music.example.com")
        let url = try XCTUnwrap(client.coverURL(9))
        XCTAssertEqual(url.absoluteString, "https://music.example.com/api/tracks/9/cover")
    }

    func testOutboxQueuesAndClearsReplayableWrites() {
        let suite = "McMusicTests"
        let defaults = UserDefaults(suiteName: suite)!
        defaults.removePersistentDomain(forName: suite)
        let outbox = Outbox(defaults: defaults)
        outbox.enqueue("POST", "like/7", toggle: true)
        outbox.enqueue("PUT", "settings", json: ["theme": "dusk"])
        XCTAssertEqual(outbox.count, 2)
        XCTAssertEqual(Outbox(defaults: defaults).count, 2)
        outbox.clear()
        XCTAssertEqual(outbox.count, 0)
    }

    func testAbsoluteURLAcceptsServerBuildPaths() throws {
        let client = APIClient(baseURL: "https://music.example.com")
        let url = try XCTUnwrap(URL(string: client.baseURL + "/apps/macos/mcmusic-4.0.1.dmg"))
        XCTAssertEqual(url.host, "music.example.com")
    }

    func testIconStrokeSnapsToAllowedWidths() {
        XCTAssertEqual(Lucide.nearestStroke(0.2), 1)
        XCTAssertEqual(Lucide.nearestStroke(1.3), 1.5)
        XCTAssertEqual(Lucide.nearestStroke(1.8), 2)
    }

    func testIconStrokeWidthUsesLucideDefaultAt1x() {
        // Lucide's base stroke is `size * scale / 12`; 1x is its default 2-unit
        // stroke. The `size / 6` ceiling keeps 2x from crowding small icons.
        XCTAssertEqual(Lucide.strokeWidth(1, size: 20), 20.0 / 12)
        XCTAssertEqual(Lucide.strokeWidth(1.5, size: 20), 20.0 / 8)
        XCTAssertEqual(Lucide.strokeWidth(2, size: 32), 32.0 / 6)
        XCTAssertEqual(Lucide.strokeWidth(2, size: 52), 52.0 / 6)
        XCTAssertEqual(Lucide.strokeWidth(1, size: 48), 4)
    }

    func testOnlyCirclesAndRectsAreFillable() {
        XCTAssertTrue(Lucide.Primitive.circle(12, 12, 9).isFillable)
        XCTAssertTrue(Lucide.Primitive.rect(3, 4, 18, 13, 2).isFillable)
        XCTAssertFalse(Lucide.Primitive.path("M7 4.5 L19 12 L7 19.5 Z").isFillable)
    }

    func testEveryGeneratedBlobPathHasBoundsInsideTheCanvas() throws {
        XCTAssertFalse(BlobShapes.ids.isEmpty)
        for id in BlobShapes.ids {
            let box = try XCTUnwrap(BlobPathParser.bounds(for: id), "\(id) has no path")
            XCTAssertGreaterThan(box.width, 1, "\(id) width")
            XCTAssertGreaterThan(box.height, 1, "\(id) height")
            XCTAssertGreaterThanOrEqual(box.minX, -1, "\(id) minX")
            XCTAssertGreaterThanOrEqual(box.minY, -1, "\(id) minY")
            XCTAssertLessThanOrEqual(box.maxX, 101, "\(id) maxX")
            XCTAssertLessThanOrEqual(box.maxY, 101, "\(id) maxY")
        }
    }

    func testBlobIdIsDeterministicAndGenerated() {
        let seed = "album/17/song-3"
        let id = blobId(for: seed)
        XCTAssertEqual(id, blobId(for: seed))
        XCTAssertEqual(blobId(for: ""), blobId(for: ""))
        XCTAssertTrue(BlobShapes.ids.contains(id))
    }
}
```
