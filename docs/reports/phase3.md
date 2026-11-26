# mcmusic 4.2.0 — Phase 3 report

Branch: `design-4.2.0`. Parent commit: `8525e52` (Phase 2). This phase is the iOS client only; no version bump or release action is included.

## What changed

- Added authored `Design.swift`, mirroring `design/tokens.json` for the 4/8/12/16/28/36 shape scale, 20–28pt covers, 28pt cards, 36pt hero corners, a 48pt touch target and the Material 3 type scale. iOS keeps the system rounded design face, so no new font binary or remote font request was introduced.
- Added authored `Motion.swift`: one shared environment value combining the local `playfulMotion` switch (default on) with `\.accessibilityReduceMotion`, medium 0.7-damped springs, a 0.96 press scale, standard UIKit selection/impact haptics, a pill-to-squircle play/pause morph, a wavy progress line only while playing and a 48pt drag seek. Paused or reduced-motion progress is one flat bar; reduced motion removes springs, morphs, waves and haptics.
- Reworked `Components.swift` around the flat tonal language. `CoverView` now renders deterministic Lucide placeholders (circle, squircle, cookie, flower, pentagon) in a tonal container and shows real artwork untouched; rows, shelves and fields use 28/36pt containers, 48pt targets, pill inputs and `M3Type`. Small covers use 20pt corners and large covers 28pt.
- Rebuilt the mini player and `NowPlayingView` with the shared pill transport, morph play/pause, wavy seek, 48pt icon buttons, 36pt hero artwork, pill control groups and accessible labels. The mini player opens Now Playing from its cover/title button, so transport taps no longer open the sheet by accident.
- Updated navigation, Home, Search, Library, Listening and Profile surfaces to the shared shape/type tokens, deterministic cover seeds, pill button press treatment and 48pt rows. The Listening tab uses the headphones glyph instead of the radio glyph; it is a listening-activity view, not a fabricated Radio destination.
- Kept the Lyric Visualizer deterministic and pure: every frame is a function of playback progress, playing state and active synced line. Motion is disabled by the shared switch/Reduce Motion, and the three flat modes are Bars, Wave and Rings. “Sing along” highlighting appears only for genuine LRC timestamps parsed locally from the stored lyrics; plain-text lyrics stay read-only.
- Added the local `Playful motion` switch to Settings with copy explaining that Reduce Motion wins. It is stored only in `UserDefaults` under `playfulMotion`; no server settings key or schema was touched.
- Preserved all five palette ids and displayed family names and all legacy aliases. `Theme.swift`'s generated palette marker block and `Lucide.swift`'s generated icon marker block were not edited. iOS stays on static family palettes; no cover-derived dynamic colour was added in this phase.
- Kept feature truth: no Dolby/Spatial labels, no fake Lossless badge, no invented `E` badge, no Mix chips, no curated Radio/Mixes destination and no fabricated Charts. The existing `Start radio` action still points at the real `/api/radio/<tid>` endpoint.

## What was run

- `node scripts/gen-tokens.mjs --check && node scripts/gen-lucide.mjs --check` — pass; no token or icon source changed in this phase.
- `.venv/bin/python -m pytest tests/test_no_gradients.py tests/test_contrast.py tests/test_generated_fresh.py -q` — 3 passed; this includes the no-allowlist flatness scan over `app/ios/McMusic`.
- `.venv/bin/python -m pytest tests -q` with the same Qt/widget/update exclusions CI uses — 95 passed, 1 skipped, 2 subtests passed.
- `bash tests/test_check_versions.sh` — 4 checks passed; `bash scripts/check-versions.sh` — all carriers still agree at 4.1.0.
- `git diff --check` — pass.
- Tool probe: `swiftc`, `xcodegen` and `xcodebuild` are unavailable in this Linux workspace, so no local iOS compile was attempted. CI runs the unsigned Simulator build and XCTest action.
- CI is triggered by pushing this separate phase commit to `design-4.2.0`; no CI result is claimed in this pre-push report.

## What was not done and why

- No version bump or release publication: Phase 5 owns that, after Phases 3–4 are CI-green.
- No web, Android or Qt redesign in this commit: those are Phases 1, 2 and 4. No shared token or generated icon source was changed here.
- No cover-derived dynamic colour on iOS: the written 4.2.0 contract keeps iOS on static family palettes.
- No device rendering, screenshot comparison or visual verification: no Apple toolchain, simulator or mockup is available locally. CI covers compilation and the existing XCTest suite; the written M3 Expressive contract is the only visual specification.
- No new remote network call, CDN font, tracker or analytics: `ImageCache` reads the same cover URLs the previous `AsyncImage` view displayed, and no external font or effect asset was added.
- No server settings, live database, branch sync, redeploy or secret rotation: the new motion switch is a local `UserDefaults` value and those operations require explicit permission.
- No fake Mix/Radio/Chart, Dolby/Spatial label, fake lossless badge or fabricated explicit badge: the feature-truth audit and real endpoints remain unchanged.
- No generated blocks were hand-edited. Generated palettes stay inside `Theme.swift`'s marker block and generated Lucide ids stay inside `Lucide.swift`'s marker block.

## Full authored file contents

The files below are reproduced in full. Generated marker blocks are shown only as context in the authored files that contain them; no generated output was changed in this phase.

### `app/ios/McMusic/Design.swift`

```swift
import SwiftUI

/// Authored 4.2.0 shape, spacing and type values mirrored from
/// `design/tokens.json`. Colours remain in `Theme.swift`'s generated block;
/// these constants are the iOS half of the single-source token contract.
enum M3Shape {
    static let xs: CGFloat = 4
    static let sm: CGFloat = 8
    static let md: CGFloat = 12
    static let lg: CGFloat = 16
    static let xl: CGFloat = 28
    static let xxl: CGFloat = 36
    static let pill: CGFloat = 999

    static let coverSmall: CGFloat = 20
    static let coverLarge: CGFloat = 28
    static let card: CGFloat = 28
    static let hero: CGFloat = 36
    static let touch: CGFloat = 48
}

enum M3Space {
    static let unit: CGFloat = 4
}

/// Material 3 type scale. Lexend stays the web face; iOS uses the system
/// rounded design so the native client matches the friendly 4.2.0 voice
/// without adding a downloaded font.
enum M3Type {
    static let display = Font.system(size: 36, weight: .bold, design: .rounded)
    static let headline = Font.system(size: 28, weight: .bold, design: .rounded)
    static let title = Font.system(size: 22, weight: .bold, design: .rounded)
    static let body = Font.system(size: 16, weight: .regular, design: .rounded)
    static let label = Font.system(size: 14, weight: .semibold, design: .rounded)

    static let displayLine: CGFloat = 44
    static let headlineLine: CGFloat = 36
    static let titleLine: CGFloat = 28
    static let bodyLine: CGFloat = 24
    static let labelLine: CGFloat = 20
}
```

### `app/ios/McMusic/Motion.swift`

```swift
import Foundation
import SwiftUI
import UIKit

/// Authored 4.2.0 motion values mirrored from `design/tokens.json`.
/// Every animation here is flat and short; there are no decorative shadows.
enum Playful {
    static let pressScale: CGFloat = 0.96
    static let damping: Double = 0.7
    static let response: Double = 0.32
    static let spring = Animation.spring(response: response, dampingFraction: damping)
    static let morph = Animation.spring(response: response, dampingFraction: damping)
    static let waveHz: Double = 0.55
    static let wavePx: CGFloat = 3
    static let settingsKey = "playfulMotion"
}

/// Standard UIKit feedback generators only: no custom waveform and no
/// continuous feedback. Callers honour the local switch and Reduce Motion.
enum PlayfulHaptic {
    static func selection() {
        let generator = UISelectionFeedbackGenerator()
        generator.prepare()
        generator.selectionChanged()
    }

    static func impact(_ style: UIImpactFeedbackGenerator.FeedbackStyle = .light) {
        let generator = UIImpactFeedbackGenerator(style: style)
        generator.prepare()
        generator.impactOccurred()
    }

    static func notice(_ type: UINotificationFeedbackGenerator.FeedbackType) {
        let generator = UINotificationFeedbackGenerator()
        generator.prepare()
        generator.notificationOccurred(type)
    }
}

private struct PlayfulMotionKey: EnvironmentKey {
    static let defaultValue = true
}

extension EnvironmentValues {
    /// True only when the local "Playful motion" switch is on and the platform
    /// Reduce Motion setting is off. Views read this instead of querying
    /// UserDefaults directly.
    var playfulMotion: Bool {
        get { self[PlayfulMotionKey.self] }
        set { self[PlayfulMotionKey.self] = newValue }
    }
}

private struct PlayfulMotionModifier: ViewModifier {
    @AppStorage("playfulMotion") private var enabled = true
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    func body(content: Content) -> some View {
        content.environment(\.playfulMotion, enabled && !reduceMotion)
    }
}

extension View {
    func mcmusicMotion() -> some View {
        modifier(PlayfulMotionModifier())
    }
}

/// Shared press treatment: 0.96 scale on a medium spring and one standard
/// selection click on press. Set `haptic: false` when a control supplies its
/// own transport-specific feedback.
struct PlayfulButtonStyle: ButtonStyle {
    var haptic: Bool = true

    @Environment(\.playfulMotion) private var motion

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed && motion ? Playful.pressScale : 1)
            .animation(motion ? Playful.spring : nil, value: configuration.isPressed)
            .onChange(of: configuration.isPressed) { _, pressed in
                if pressed && haptic && motion { PlayfulHaptic.selection() }
            }
    }
}

/// Pill-shaped filled action used for primary settings and retry actions.
struct PlayfulProminentButtonStyle: ButtonStyle {
    @Environment(\.playfulMotion) private var motion
    @Environment(\.mcTokens) private var tokens

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(M3Type.label)
            .foregroundStyle(tokens.onPrimary)
            .frame(minHeight: M3Shape.touch)
            .padding(.horizontal, M3Shape.lg)
            .background(Capsule().fill(tokens.primary))
            .scaleEffect(configuration.isPressed && motion ? Playful.pressScale : 1)
            .animation(motion ? Playful.spring : nil, value: configuration.isPressed)
            .onChange(of: configuration.isPressed) { _, pressed in
                if pressed && motion { PlayfulHaptic.impact() }
            }
    }
}

/// Lucide icon button with a 48pt hit target. It is the only icon-button
/// treatment used by the redesigned shell and player.
struct PlayfulIconButton: View {
    let icon: String
    var size: CGFloat = 20
    var tint: Color?
    let label: String
    let action: () -> Void

    @Environment(\.mcTokens) private var tokens

    var body: some View {
        Button(action: action) {
            LucideIcon(name: icon, size: size, color: tint ?? tokens.dim)
                .frame(width: M3Shape.touch, height: M3Shape.touch)
                .contentShape(Capsule())
        }
        .buttonStyle(PlayfulButtonStyle())
        .accessibilityLabel(label)
    }
}

/// Play/pause control with the 4.2.0 pill-to-squircle morph. Paused is a
/// capsule, playing is a 16pt squircle, and the glyph turns a quarter turn.
/// Reduced motion or the local switch keeps a fixed squircle.
struct PlayPauseButton: View {
    let playing: Bool
    var size: CGFloat = 58
    let action: () -> Void

    @Environment(\.playfulMotion) private var motion
    @Environment(\.mcTokens) private var tokens

    private var cornerRadius: CGFloat {
        motion && !playing ? size / 2 : M3Shape.lg
    }

    var body: some View {
        Button {
            if motion { PlayfulHaptic.impact(.medium) }
            action()
        } label: {
            ZStack {
                RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                    .fill(tokens.primary)
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

/// Flat progress line. It waves only while playing and only when playful
/// motion is available; paused or reduced motion is one flat bar.
struct PlayfulProgress: View {
    let fraction: Double
    let playing: Bool

    @Environment(\.playfulMotion) private var motion
    @Environment(\.mcTokens) private var tokens

    var body: some View {
        TimelineView(.animation(minimumInterval: 1.0 / 30.0,
                                paused: !playing || !motion)) { timeline in
            Canvas { context, size in
                let filled = min(max(CGFloat(fraction), 0), 1) * size.width
                guard filled > 0, size.height > 0 else { return }
                let middle = size.height / 2
                var path = Path()
                if !playing || !motion {
                    path.move(to: CGPoint(x: 0, y: middle))
                    path.addLine(to: CGPoint(x: filled, y: middle))
                } else {
                    let phase = timeline.date.timeIntervalSinceReferenceDate
                        * Playful.waveHz * 2 * .pi
                    let steps = max(2, Int(filled / 4))
                    for step in 0...steps {
                        let unit = CGFloat(step) / CGFloat(steps)
                        let envelope = sin(.pi * unit)
                        let y = middle
                            + sin(unit * .pi * 4 + CGFloat(phase))
                            * Playful.wavePx * envelope
                        let point = CGPoint(x: filled * unit, y: y)
                        if step == 0 { path.move(to: point) } else { path.addLine(to: point) }
                    }
                }
                context.stroke(
                    path,
                    with: .color(tokens.primary),
                    style: StrokeStyle(lineWidth: 2, lineCap: .round, lineJoin: .round)
                )
            }
        }
        .frame(height: 6)
        .background(Capsule().fill(tokens.outlineVariant.opacity(tokens.isDark ? 0.5 : 0.35)))
        .clipShape(Capsule())
    }
}

/// A 48pt touch target carrying the flat/wavy progress line. A single
/// selection click fires when a drag ends; there is no continuous feedback.
struct PlayfulSeek: View {
    let value: Double
    let duration: Double
    let playing: Bool
    let onSeek: (Double) -> Void

    @Environment(\.playfulMotion) private var motion

    var body: some View {
        GeometryReader { geometry in
            PlayfulProgress(fraction: duration > 0 ? value / duration : 0,
                            playing: playing)
                .frame(maxWidth: .infinity)
                .contentShape(Rectangle())
                .gesture(
                    DragGesture(minimumDistance: 0)
                        .onChanged { gesture in
                            let ratio = min(max(0, gesture.location.x / max(geometry.size.width, 1)), 1)
                            onSeek(ratio * duration)
                        }
                        .onEnded { _ in
                            if motion { PlayfulHaptic.selection() }
                        }
                )
        }
        .frame(height: M3Shape.touch)
    }
}
```

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
```

### `app/ios/McMusic/McMusicApp.swift`

```swift
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
```

### `app/ios/McMusic/Navigation.swift`

```swift
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
        VStack(alignment: .leading, spacing: M3Shape.sm) {
            CoverView(url: cover, seed: title, size: 140, radius: M3Shape.coverLarge)
            Text(title)
                .font(M3Type.label)
                .lineLimit(1)
            Text(subtitle)
                .font(.caption)
                .foregroundStyle(.secondary)
                .lineLimit(1)
        }
        .frame(width: 140)
    }
}
```

### `app/ios/McMusic/HomeView.swift`

```swift
import SwiftUI

struct HomeView: View {
    @EnvironmentObject private var app: AppState
    @Environment(\.mcTokens) private var tokens
    @State private var home: JSON?
    @State private var loading = true

    var body: some View {
        NavigationStack {
            Group {
                if loading {
                    ProgressView("Loading your library…")
                        .foregroundStyle(tokens.dim)
                        .frame(maxWidth: .infinity)
                } else if let home {
                    ScrollView {
                        VStack(alignment: .leading, spacing: M3Shape.xl) {
                            ForEach(Array((home["sections"]?.array ?? []).enumerated()), id: \.offset) { index, section in
                                let title = section["title"]?.string ?? "Music"
                                let songs = section["tracks"]?.array ?? []
                                Shelf(title, hero: index == 0) {
                                    ScrollView(.horizontal) {
                                        HStack(spacing: M3Shape.md) {
                                            ForEach(Array(songs.enumerated()), id: \.offset) { _, song in
                                                NavigationLink(value: Detail.album(song.albumName)) {
                                                    CoverTile(title: song.title,
                                                              subtitle: song.artistName,
                                                              cover: app.client.coverURL(song.coverID))
                                                }
                                                .buttonStyle(PlayfulButtonStyle())
                                            }
                                        }
                                        .padding(.horizontal, M3Shape.sm)
                                    }
                                }
                                .padding(.horizontal, M3Shape.lg)

                                if !songs.isEmpty {
                                    VStack(spacing: 0) {
                                        ForEach(Array(songs.prefix(5).enumerated()), id: \.offset) { _, song in
                                            trackRow(song, in: songs)
                                        }
                                    }
                                    .padding(.horizontal, M3Shape.lg)
                                }
                            }

                            let albums = home["albums"]?.array ?? []
                            if !albums.isEmpty {
                                Shelf("Albums") {
                                    ScrollView(.horizontal) {
                                        HStack(spacing: M3Shape.md) {
                                            ForEach(Array(albums.enumerated()), id: \.offset) { _, album in
                                                NavigationLink(value: Detail.album(album["album"]?.string ?? "")) {
                                                    CoverTile(title: album["album"]?.string ?? "Album",
                                                              subtitle: album["artist"]?.string ?? "",
                                                              cover: app.client.coverURL(album["cover_id"]))
                                                }
                                                .buttonStyle(PlayfulButtonStyle())
                                            }
                                        }
                                        .padding(.horizontal, M3Shape.sm)
                                    }
                                }
                                .padding(.horizontal, M3Shape.lg)
                            }
                        }
                        .padding(.top, M3Shape.sm)
                    }
                } else {
                    StateView(text: "Could not load home", icon: "wifi-off") {
                        Task { await load() }
                    }
                }
            }
            .navigationTitle("Home")
            .refreshable { await load() }
            .mcmusicNavigation()
        }
        .task { await load() }
    }

    private func trackRow(_ song: JSON, in songs: [JSON]) -> some View {
        HStack {
            TrackRow(track: song, onPlay: {
                Task { await app.player.play(track: song, from: songs) }
            }, onMenu: nil)
            TrackMenu(track: song, tracks: songs)
        }
    }

    private func load() async {
        loading = true
        defer { loading = false }
        do { home = try await app.client.home() }
        catch { app.show(error) }
    }
}
```

### `app/ios/McMusic/SearchView.swift`

```swift
import SwiftUI

struct SearchView: View {
    @EnvironmentObject private var app: AppState
    @Environment(\.mcTokens) private var tokens
    @State private var query = ""
    @State private var results: JSON?
    @State private var searching = false

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                HStack(spacing: M3Shape.sm) {
                    LucideIcon(name: "search", size: 18, color: tokens.dim)
                        .frame(width: M3Shape.touch, height: M3Shape.touch)
                    TextField("Songs, albums, artists", text: $query)
                        .font(M3Type.body)
                        .onSubmit { Task { await search() } }
                    if !query.isEmpty {
                        PlayfulIconButton(icon: "x-circle", size: 18,
                                          tint: tokens.dim, label: "Clear search") {
                            query = ""
                            results = nil
                        }
                    }
                }
                .padding(.horizontal, M3Shape.md)
                .frame(minHeight: M3Shape.touch)
                .background(Capsule().fill(tokens.surfaceContainerLow))

                if searching {
                    ProgressView().frame(maxWidth: .infinity)
                } else if let results {
                    List {
                        let tracks = results["tracks"]?.array ?? []
                        if !tracks.isEmpty {
                            Section("Songs (\(tracks.count))") {
                                ForEach(Array(tracks.enumerated()), id: \.offset) { _, track in
                                    HStack {
                                        TrackRow(track: track, onPlay: {
                                            Task { await app.player.play(track: track, from: tracks) }
                                        })
                                        TrackMenu(track: track, tracks: tracks)
                                    }
                                }
                            }
                        }
                        let albums = results["albums"]?.array ?? []
                        if !albums.isEmpty {
                            Section("Albums (\(albums.count))") {
                                ForEach(Array(albums.enumerated()), id: \.offset) { _, album in
                                    NavigationLink(value: Detail.album(album["album"]?.string ?? "")) {
                                        HStack {
                                            CoverView(url: app.client.coverURL(album["cover_id"]),
                                                      seed: album["album"]?.string ?? "Album",
                                                      size: 44)
                                            VStack(alignment: .leading) {
                                                Text(album["album"]?.string ?? "Album")
                                                Text(album["artist"]?.string ?? "")
                                                    .font(.caption).foregroundStyle(tokens.dim)
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        let artists = results["artists"]?.array ?? []
                        if !artists.isEmpty {
                            Section("Artists (\(artists.count))") {
                                ForEach(Array(artists.enumerated()), id: \.offset) { _, artist in
                                    NavigationLink(value: Detail.artist(artist["artist"]?.string ?? "")) {
                                        Label {
                                            Text(artist["artist"]?.string ?? "Artist")
                                        } icon: {
                                            LucideIcon(name: "user", size: 18)
                                        }
                                        .frame(minHeight: M3Shape.touch)
                                    }
                                }
                            }
                        }
                        if tracks.isEmpty && albums.isEmpty && artists.isEmpty {
                            StateView(text: "No results for “\(query)”", icon: "search")
                        }
                    }
                    .listStyle(.plain)
                } else {
                    StateView(text: "Search your library", icon: "search")
                }
            }
            .navigationTitle("Search")
            .mcmusicNavigation()
        }
        .task {
            // `/` focuses search on the web; on iOS the field is already visible.
        }
    }

    private func search() async {
        guard !query.trimmingCharacters(in: .whitespaces).isEmpty else { return }
        searching = true
        defer { searching = false }
        do { results = try await app.client.search(query) }
        catch { app.show(error) }
    }
}
```

### `app/ios/McMusic/LibraryView.swift`

```swift
import SwiftUI

struct LibraryView: View {
    @EnvironmentObject private var app: AppState
    @State private var tab = 0
    @State private var tracks: [JSON] = []
    @State private var albums: [JSON] = []
    @State private var artists: [JSON] = []
    @State private var liked: [JSON] = []
    @State private var playlists: [JSON] = []
    @State private var loading = true

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                Picker("Library", selection: $tab) {
                    Text("Songs").tag(0)
                    Text("Albums").tag(1)
                    Text("Artists").tag(2)
                    Text("Playlists").tag(3)
                    Text("Liked").tag(4)
                }
                .pickerStyle(.segmented)
                .padding()

                if loading {
                    ProgressView().frame(maxWidth: .infinity)
                } else {
                    switch tab {
                    case 0: trackList(tracks)
                    case 1: albumGrid(albums)
                    case 2: artistList(artists)
                    case 3: playlistList(playlists)
                    default: trackList(liked)
                    }
                }
            }
            .navigationTitle("Library")
            .refreshable { await load() }
            .mcmusicNavigation()
        }
        .task { await load() }
    }

    private func trackList(_ songs: [JSON]) -> some View {
        List {
            ForEach(Array(songs.enumerated()), id: \.offset) { index, song in
                HStack {
                    TrackRow(track: song, number: index + 1, onPlay: {
                        Task { await app.player.play(track: song, from: songs) }
                    })
                    TrackMenu(track: song, tracks: songs)
                }
            }
        }
        .listStyle(.plain)
        .overlay {
            if songs.isEmpty { StateView(text: "Nothing here yet", icon: "music-note") }
        }
    }

    private func albumGrid(_ rows: [JSON]) -> some View {
        ScrollView {
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 140))], spacing: 18) {
                ForEach(Array(rows.enumerated()), id: \.offset) { _, row in
                    NavigationLink(value: Detail.album(row["album"]?.string ?? "")) {
                        CoverTile(title: row["album"]?.string ?? "Album",
                                  subtitle: row["artist"]?.string ?? "",
                                  cover: app.client.coverURL(row["cover_id"]))
                    }
                    .buttonStyle(PlayfulButtonStyle())
                }
            }
            .padding()
        }
    }

    private func artistList(_ rows: [JSON]) -> some View {
        List {
            ForEach(Array(rows.enumerated()), id: \.offset) { _, row in
                NavigationLink(value: Detail.artist(row["artist"]?.string ?? "")) {
                    HStack {
                        CoverView(url: app.client.coverURL(row["cover_id"]),
                                  seed: row["artist"]?.string ?? "Artist",
                                  size: 44)
                        VStack(alignment: .leading) {
                            Text(row["artist"]?.string ?? "Artist")
                            Text("\(row.itemCount) songs · \(row["albums"]?.int ?? 0) albums")
                                .font(.caption).foregroundStyle(.secondary)
                        }
                    }
                    .frame(minHeight: M3Shape.touch)
                }
            }
        }
        .listStyle(.plain)
    }

    private func playlistList(_ rows: [JSON]) -> some View {
        List {
            ForEach(Array(rows.enumerated()), id: \.offset) { _, row in
                NavigationLink(value: Detail.playlist(row["id"]?.int ?? 0)) {
                    HStack {
                        CoverView(url: app.client.coverURL(row["cover_id"]),
                                  seed: row["name"]?.string ?? "Playlist",
                                  size: 44)
                        VStack(alignment: .leading) {
                            Text(row["name"]?.string ?? "Playlist")
                            Text("\(row["count"]?.int ?? 0) songs")
                                .font(.caption).foregroundStyle(.secondary)
                        }
                    }
                    .frame(minHeight: M3Shape.touch)
                }
            }
        }
        .listStyle(.plain)
        .overlay {
            if rows.isEmpty { StateView(text: "No playlists yet", icon: "list-music") }
        }
    }

    private func load() async {
        loading = true
        defer { loading = false }
        do {
            tracks = try await app.client.tracks()
            albums = try await app.client.albums()
            artists = try await app.client.artists()
            liked = try await app.client.likes()
            playlists = try await app.client.playlists()
        } catch { app.show(error) }
    }
}

struct AlbumView: View {
    @EnvironmentObject private var app: AppState
    let name: String
    @State private var songs: [JSON] = []

    var body: some View {
        List {
            ForEach(Array(songs.enumerated()), id: \.offset) { index, song in
                HStack {
                    TrackRow(track: song, number: song["track_no"]?.int ?? index + 1, onPlay: {
                        Task { await app.player.play(track: song, from: songs) }
                    })
                    TrackMenu(track: song, tracks: songs, onAlbum: nil, onArtist: nil)
                }
            }
        }
        .listStyle(.plain)
        .navigationTitle(name)
        .toolbar {
            if !songs.isEmpty {
                Button("Play all") { Task { await app.player.playQueue(songs) } }
            }
        }
        .task { songs = (try? await app.client.album(name)) ?? [] }
    }
}

struct ArtistView: View {
    @EnvironmentObject private var app: AppState
    let name: String
    @State private var songs: [JSON] = []

    var body: some View {
        List {
            ForEach(Array(songs.enumerated()), id: \.offset) { index, song in
                HStack {
                    TrackRow(track: song, number: index + 1, onPlay: {
                        Task { await app.player.play(track: song, from: songs) }
                    })
                    TrackMenu(track: song, tracks: songs, onAlbum: nil, onArtist: nil)
                }
            }
        }
        .listStyle(.plain)
        .navigationTitle(name)
        .toolbar {
            if !songs.isEmpty {
                Button("Play all") { Task { await app.player.playQueue(songs) } }
            }
        }
        .task { songs = (try? await app.client.artist(name)) ?? [] }
    }
}
```

### `app/ios/McMusic/ListeningView.swift`

```swift
import SwiftUI

/// Public listening directory and profile peek, matching the web/Android home
/// listener cards without embedding any web content.
struct ListeningView: View {
    @EnvironmentObject private var app: AppState
    @Environment(\.mcTokens) private var tokens
    @State private var listeners: [JSON] = []

    var body: some View {
        NavigationStack {
            Group {
                if listeners.isEmpty {
                    StateView(text: "Nobody is listening right now", icon: "radio")
                } else {
                    List(listeners, id: \.id) { listener in
                        NavigationLink(value: Detail.profile(listener["username"]?.string ?? "")) {
                            HStack(spacing: 12) {
                                CoverView(url: URL(string: listener["cover_url"]?.string ?? ""),
                                          seed: listener["username"]?.string ?? "Listener",
                                          size: 44,
                                          radius: M3Shape.coverSmall)

                                VStack(alignment: .leading, spacing: 2) {
                                    Text(listener["username"]?.string ?? "Listener")
                                        .foregroundStyle(.primary)
                                    if let track = listener["track"] {
                                        Text("\(track["title"]?.string ?? "Unknown") — \(track["artist"]?.string ?? "")")
                                            .font(.caption)
                                            .foregroundStyle(tokens.dim)
                                            .lineLimit(1)
                                    } else {
                                        Text(listener["listening"]?.bool == true ? "Listening" : "Paused")
                                            .font(.caption).foregroundStyle(tokens.dim)
                                    }
                                }
                                Spacer()
                                if listener["listening"]?.bool == true {
                                    LucideIcon(name: "audio-lines", size: 18, color: tokens.accent)
                                }
                            }
                            .frame(minHeight: M3Shape.touch)
                        }
                        .buttonStyle(.plain)
                    }
                    .listStyle(.plain)
                }
            }
            .navigationTitle("Listening")
            .refreshable { await load() }
            .mcmusicNavigation()
            .task { await load() }
        }
    }

    private func load() async {
        do { listeners = try await app.client.publicListening() }
        catch { app.show(error) }
    }

}
```

### `app/ios/McMusic/ProfileView.swift`

```swift
import SwiftUI

/// Public profile/listening view, equivalent to web `/u/:username`.
struct ProfileView: View {
    @EnvironmentObject private var app: AppState
    @Environment(\.mcTokens) private var tokens
    let username: String
    @State private var profile: JSON?
    @State private var loading = true

    var body: some View {
        Group {
            if loading {
                ProgressView().frame(maxWidth: .infinity)
            } else if let profile {
                ScrollView {
                    VStack(alignment: .leading, spacing: M3Shape.lg) {
                        HStack(spacing: M3Shape.md) {
                            CoverView(url: URL(string: profile["cover_url"]?.string ?? ""),
                                      seed: profile["username"]?.string ?? username,
                                      size: 88,
                                      radius: M3Shape.coverLarge)
                            VStack(alignment: .leading, spacing: M3Shape.xs) {
                                Text(profile["username"]?.string ?? username)
                                    .font(M3Type.title)
                                Text(profile["listening"]?.bool == true ? "Listening now" : "Not listening")
                                    .font(M3Type.body)
                                    .foregroundStyle(tokens.dim)
                            }
                        }

                        if let track = profile["track"], !track.isNull {
                            VStack(alignment: .leading, spacing: M3Shape.sm) {
                                Text("Now playing")
                                    .font(M3Type.label)
                                TrackRow(track: track) {
                                    Task { await app.player.play(track: track) }
                                }
                            }
                            .padding(M3Shape.lg)
                            .background(
                                RoundedRectangle(cornerRadius: M3Shape.card, style: .continuous)
                                    .fill(tokens.surfaceContainerLow)
                            )
                        }

                        if let url = profile["profile_url"]?.string, let link = URL(string: url) {
                            Link("Open public profile", destination: link)
                                .buttonStyle(PlayfulProminentButtonStyle())
                        }
                    }
                    .padding()
                }
            } else {
                StateView(text: "Could not load profile", icon: "circle-alert") {
                    Task { await load() }
                }
            }
        }
        .navigationTitle(username)
        .task { await load() }
        .refreshable { await load() }
    }

    private func load() async {
        loading = true
        defer { loading = false }
        do { profile = try await app.client.publicNow(username) }
        catch { app.show(error) }
    }
}
```

### `app/ios/McMusic/NowPlayingView.swift`

```swift
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
```

### `app/ios/McMusic/LyricVisualizer.swift`

```swift
import SwiftUI

/// One time-synced lyric line. Plain lyrics never produce this type.
struct LyricLine {
    let time: Double
    let text: String
}

/// Minimal LRC reader used only to decide whether a lyrics copy is genuinely
/// time-synced. It does not fetch anything and never invents timestamps.
enum LyricParser {
    static func parse(_ text: String) -> [LyricLine]? {
        var lines: [LyricLine] = []
        for raw in text.components(separatedBy: .newlines) {
            let trimmed = raw.trimmingCharacters(in: .whitespaces)
            guard trimmed.hasPrefix("["), let close = trimmed.firstIndex(of: "]") else { continue }
            let stamp = String(trimmed[trimmed.index(after: trimmed.startIndex)..<close])
            let body = String(trimmed[trimmed.index(after: close)...])
                .trimmingCharacters(in: .whitespaces)
            guard let time = seconds(from: stamp) else { continue }
            lines.append(LyricLine(time: time, text: body))
        }
        return lines.isEmpty ? nil : lines
    }

    private static func seconds(from stamp: String) -> Double? {
        let pieces = stamp.split(separator: ":")
        guard pieces.count >= 2,
              let minutes = Double(pieces[0]),
              let seconds = Double(pieces[1]) else { return nil }
        return minutes * 60 + seconds
    }
}

/// Compact, dependency-free lyric visualizer used by the lyrics sheet.
///
/// Every frame is a pure function of `progress`, `isPlaying` and `activeLine`:
/// no timers, no random state and no wall-clock phase. Pausing playback freezes
/// the picture exactly where it is, and seeking always redraws the same frame.
/// Reduced motion and the local switch flatten the bars and waves.
struct LyricVisualizer: View {
    enum Mode: String, CaseIterable, Identifiable {
        case bars, wave, rings

        var id: String { rawValue }

        var label: String {
            switch self {
            case .bars: return "Bars"
            case .wave: return "Wave"
            case .rings: return "Rings"
            }
        }
    }

    var progress: Double
    var isPlaying: Bool
    var activeLine: Int? = nil
    var mode: Mode = .bars
    @Environment(\.mcTokens) private var tokens
    @Environment(\.playfulMotion) private var motion

    var body: some View {
        Canvas { context, size in
            guard size.width > 0, size.height > 0 else { return }
            let t = CGFloat(progress.isFinite ? max(0, progress) : 0)
            let energy: CGFloat = (isPlaying ? 1 : 0.5) + (activeLine == nil ? 0 : 0.06)
            switch mode {
            case .bars: drawBars(&context, size, t, energy, tokens.primary, motion)
            case .wave: drawWave(&context, size, t, energy, tokens.primary, motion)
            case .rings: drawRings(&context, size, t, energy, tokens.primary, tokens.fg, motion)
            }
        }
        .accessibilityHidden(true) // decorative; the mode picker is the control
    }

    // MARK: - Modes

    private func drawBars(_ context: inout GraphicsContext, _ size: CGSize, _ t: CGFloat,
                          _ energy: CGFloat, _ accent: Color, _ motion: Bool) {
        let count = 32
        let spacing: CGFloat = 3
        let width = max(2, (size.width - spacing * CGFloat(count - 1)) / CGFloat(count))
        let middle = size.height / 2
        for i in 0..<count {
            let seed = CGFloat(i) * 0.62
            let wobble = motion ? 0.5 + 0.5 * sin(t * 1.35 + seed) : 0.5
            let beat = motion ? 0.5 + 0.5 * sin(t * 0.8 - seed * 1.7) : 1
            let height = max(3, size.height * (0.12 + 0.62 * wobble * beat) * energy)
            let rect = CGRect(
                x: CGFloat(i) * (width + spacing),
                y: middle - height / 2,
                width: width,
                height: height
            )
            context.fill(
                Path(roundedRect: rect, cornerRadius: width / 2),
                with: .color(accent.opacity(motion ? 0.4 + 0.6 * wobble : 0.8))
            )
        }
    }

    private func drawWave(_ context: inout GraphicsContext, _ size: CGSize, _ t: CGFloat,
                          _ energy: CGFloat, _ accent: Color, _ motion: Bool) {
        let middle = size.height / 2
        let steps = max(24, Int(size.width / 4))
        for layer in 0..<3 {
            var path = Path()
            let amplitude = motion ? size.height * (0.14 + CGFloat(layer) * 0.06) * energy : 0
            let frequency: CGFloat = 1.5 + CGFloat(layer) * 0.6
            for step in 0...steps {
                let x = size.width * CGFloat(step) / CGFloat(steps)
                let u = x / max(size.width, 1) * .pi * 2 * frequency
                let y = middle
                    + sin(u + t * (1 + CGFloat(layer) * 0.25) + CGFloat(layer)) * amplitude
                    + sin(u * 2.3 - t * 0.8) * amplitude * 0.25
                let point = CGPoint(x: x, y: y)
                if step == 0 { path.move(to: point) } else { path.addLine(to: point) }
            }
            let opacity: Double = layer == 0 ? 0.95 : 0.4 - Double(layer) * 0.12
            context.stroke(
                path,
                with: .color(accent.opacity(opacity)),
                style: StrokeStyle(lineWidth: layer == 0 ? 3 : 1.5, lineCap: .round, lineJoin: .round)
            )
        }
    }

    private func drawRings(_ context: inout GraphicsContext, _ size: CGSize, _ t: CGFloat,
                          _ energy: CGFloat, _ accent: Color, _ foreground: Color,
                          _ motion: Bool) {
        let center = CGPoint(x: size.width / 2, y: size.height / 2)
        let radius = min(size.width, size.height) * 0.48
        let pulse = motion ? 0.5 + 0.5 * sin(t * 1.1) : 0.5
        let rings = 7
        for i in stride(from: rings, through: 1, by: -1) {
            let fraction = CGFloat(i) / CGFloat(rings)
            let r = radius * (0.18 + fraction * 0.82) * (0.92 + 0.1 * pulse) * energy
            let rect = CGRect(x: center.x - r, y: center.y - r, width: r * 2, height: r * 2)
            context.fill(
                Path(ellipseIn: rect),
                with: .color(accent.opacity(Double(1 - fraction) * 0.3 + 0.02))
            )
        }
        let core = radius * (0.14 + 0.05 * pulse) * energy
        context.fill(
            Path(ellipseIn: CGRect(x: center.x - core, y: center.y - core, width: core * 2, height: core * 2)),
            with: .color(foreground.opacity(0.85))
        )
    }
}

/// Lyrics sheet: the visualizer, an accessible mode picker, then the lyrics.
/// Only a real LRC copy gets a highlighted "Sing along" line; plain text stays
/// a read-only sheet with no fabricated timing.
struct LyricSheet: View {
    let text: String
    let progress: Double
    let duration: Double
    let isPlaying: Bool

    @Environment(\.dismiss) private var dismiss
    @Environment(\.mcTokens) private var tokens
    @State private var mode: LyricVisualizer.Mode = .bars

    private var syncedLines: [LyricLine]? { LyricParser.parse(text) }
    private var displayLines: [String] {
        syncedLines?.map(\.text) ?? text.components(separatedBy: .newlines)
    }

    private var activeLine: Int? {
        guard let syncedLines, duration.isFinite, duration > 0, progress.isFinite else { return nil }
        let position = min(max(progress, 0), duration)
        var active = 0
        for (index, line) in syncedLines.enumerated() {
            if line.time <= position { active = index } else { break }
        }
        return active
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: M3Shape.md) {
                HStack(spacing: M3Shape.xs) {
                    LucideIcon(name: syncedLines == nil ? "message-circle" : "music",
                               size: 16, color: tokens.primary)
                    Text(syncedLines == nil ? "Lyrics" : "Sing along")
                        .font(M3Type.label)
                }
                Text(syncedLines == nil
                     ? "This copy is not time-synced, so it stays read-only."
                     : "Words follow the song as it plays.")
                    .font(.caption)
                    .foregroundStyle(tokens.dim)
                    .frame(maxWidth: .infinity, alignment: .leading)

                LyricVisualizer(progress: progress, isPlaying: isPlaying,
                                activeLine: activeLine, mode: mode)
                    .frame(height: 170)
                    .padding(.horizontal, M3Shape.sm)

                Picker("Visualizer mode", selection: $mode) {
                    ForEach(LyricVisualizer.Mode.allCases) { option in
                        Text(option.label).tag(option).accessibilityLabel(option.label)
                    }
                }
                .pickerStyle(.segmented)
                .padding(.horizontal)
                .frame(minHeight: M3Shape.touch)
                .accessibilityLabel("Visualizer mode")
                .accessibilityHint("Choose how the lyrics are visualized")
                .accessibilityIdentifier("lyricVisualizerMode")

                ScrollView {
                    VStack(alignment: .leading, spacing: M3Shape.md) {
                        ForEach(Array(displayLines.enumerated()), id: \.offset) { index, line in
                            Text(line.isEmpty ? " " : line)
                                .font(M3Type.body)
                                .foregroundStyle(index == activeLine ? tokens.primary : tokens.fg)
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }
                    }
                    .padding()
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
            }
            .padding(.top, M3Shape.sm)
            .background(tokens.bg.ignoresSafeArea())
            .navigationTitle("Lyrics")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                        .buttonStyle(PlayfulButtonStyle())
                }
            }
        }
    }
}
```

### `app/ios/McMusic/SettingsView.swift`

```swift
import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var app: AppState
    @AppStorage("palette") private var palette = "violet"
    @AppStorage("accent") private var accent = ""
    @AppStorage("iconStroke") private var iconStroke = 1.0
    @AppStorage("iconFilled") private var iconFilled = false
    // Local device preference only; the server settings schema has no such key.
    @AppStorage("playfulMotion") private var playfulMotion = true

    @State private var server = UserDefaults.standard.string(forKey: "server_url") ?? "http://127.0.0.1:8000"
    @State private var density = "comfy"
    @State private var material = "plane"
    @State private var realGlass = "auto"
    @State private var covers = true
    @State private var autoplay = true
    @State private var hideExplicit = false
    @State private var isPrivate = false
    @State private var ytStats = true
    @State private var rememberVolume = true
    @State private var prefetch = true
    @State private var offlineAudio = true
    @State private var roturActivity = false
    @State private var discordActivity = false
    @State private var showRoomURL = false
    @State private var volume = 0.8

    @State private var rotur: JSON?
    @State private var discord: JSON?
    @State private var roturURL = ""
    @State private var discordURL = ""
    @State private var roturCode = ""
    @State private var showingPassword = false
    @State private var oldPassword = ""
    @State private var newPassword = ""
    @State private var showingEmail = false
    @State private var email = ""
    @State private var showingReset = false
    @State private var resetEmail = ""
    @State private var resetToken = ""
    @State private var resetPassword = ""

    private let guideURL = URL(string: "https://github.com/mc20000-01/mcmusic/blob/main/docs/selfhost.md")!

    var body: some View {
        NavigationStack {
            Form {
                Section("Account") {
                    LabeledContent("Signed in as", value: app.username)
                    TextField("Server", text: $server)
                        .textInputAutocapitalization(.never)
                        .keyboardType(.URL)
                    if app.isAdmin { LabeledContent("Role", value: "Admin") }
                    Link("Self-hosting guide", destination: guideURL)
                    NavigationLink("Builds and updates") { BuildsView() }
                    Button("Change email") { showingEmail = true }
                    Button("Change password") { showingPassword = true }
                    Button("Forgot password") { showingReset = true }
                    Button("Sign out", role: .destructive) { Task { await app.signOut() } }
                }

                Section("Offline") {
                    LabeledContent("Queued changes", value: "\(app.pendingCount)")
                    Button("Sync now") { Task { await app.syncOutbox() } }
                        .disabled(app.pendingCount == 0)
                }

                Section("Appearance") {
                    // The picker edits only the family; legacy/pinned ids stay
                    // in AppStorage until the user chooses a new family.
                    Picker("Palette", selection: Binding<PaletteID>(
                        get: { PaletteID.resolve(Theme.canonicalID(palette)) },
                        set: { palette = $0.rawValue }
                    )) {
                        ForEach(PaletteID.allCases) { option in
                            Text(option.label).tag(option)
                        }
                    }
                    TextField("Accent (hex)", text: $accent)
                        .textInputAutocapitalization(.never)
                    Picker("Density", selection: $density) {
                        ForEach(["compact", "comfy", "roomy"], id: \.self) { Text($0).tag($0) }
                    }
                    // Server-synced appearance values are read and written back
                    // unchanged, but no translucent effect is exposed in the UI.
                    Picker("Icon width", selection: $iconStroke) {
                        ForEach(Lucide.strokeChoices, id: \.self) { value in
                            Text("\(value.formatted())x").tag(value)
                        }
                    }
                    Toggle("Filled icons", isOn: $iconFilled)
                    Toggle("Cover art", isOn: $covers)
                    Toggle("Show room link", isOn: $showRoomURL)
                    Toggle("Playful motion", isOn: $playfulMotion)
                    Text("Springs, shape morphs and the wavy progress follow this switch. Reduce Motion always wins.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }

                Section("Playback") {
                    Toggle("Autoplay radio", isOn: $autoplay)
                    Toggle("Prefetch tracks", isOn: $prefetch)
                    Toggle("Offline audio cache", isOn: $offlineAudio)
                    Toggle("Remember volume", isOn: $rememberVolume)
                    VStack {
                        Text("Volume \(Int(volume * 100))%")
                        Slider(value: $volume, in: 0...1)
                    }
                }

                Section("Privacy and content") {
                    Toggle("Hide explicit", isOn: $hideExplicit)
                    Toggle("Private profile", isOn: $isPrivate)
                    Toggle("YouTube statistics", isOn: $ytStats)
                }

                Section("Integrations") {
                    Toggle("Rotur activity", isOn: $roturActivity)
                    if let linked = rotur?["linked"]?.bool {
                        LabeledContent("Rotur", value: linked ? "Linked" : "Not linked")
                    }
                    if let reason = rotur?["reason"]?.string {
                        Text(reason).font(.caption).foregroundStyle(.secondary)
                    }
                    if let url = URL(string: roturURL) {
                        Link("Sign in with Rotur", destination: url)
                    }
                    SecureField("Rotur claim code", text: $roturCode)
                        .textInputAutocapitalization(.never)
                    Button("Claim Rotur code") { Task { await claimRotur() } }
                        .disabled(roturCode.isEmpty)
                    Button("Unlink Rotur", role: .destructive) { Task { await run { try await app.client.unlinkRotur() } } }

                    Toggle("Discord activity", isOn: $discordActivity)
                    if let name = discord?["username"]?.string {
                        LabeledContent("Discord", value: name)
                    } else if let linked = discord?["linked"]?.bool {
                        LabeledContent("Discord", value: linked ? "Linked" : "Not linked")
                    }
                    if let reason = discord?["presence"]?["reason"]?.string, discord?["presence"]?["available"]?.bool != true {
                        Text(reason).font(.caption).foregroundStyle(.secondary)
                    }
                    if let url = URL(string: discordURL) {
                        Link("Link Discord", destination: url)
                    }
                    Button("Unlink Discord", role: .destructive) { Task { await run { try await app.client.unlinkDiscord() } } }
                }

                Section {
                    Button("Save settings") { Task { await save() } }
                        .buttonStyle(PlayfulProminentButtonStyle())
                }
            }
            .navigationTitle("Settings")
            .sheet(isPresented: $showingPassword) { passwordSheet }
            .sheet(isPresented: $showingEmail) { emailSheet }
            .sheet(isPresented: $showingReset) { resetSheet }
        }
        .task { await load() }
    }

    private var passwordSheet: some View {
        NavigationStack {
            Form {
                SecureField("Current password", text: $oldPassword)
                SecureField("New password", text: $newPassword)
            }
            .navigationTitle("Change password")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancel") { showingPassword = false } }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") { Task { await changePassword() } }
                }
            }
        }
    }

    private var emailSheet: some View {
        NavigationStack {
            Form {
                TextField("Email address", text: $email)
                    .textInputAutocapitalization(.never)
                    .keyboardType(.emailAddress)
            }
            .navigationTitle("Change email")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancel") { showingEmail = false } }
                ToolbarItem(placement: .confirmationAction) { Button("Save") { Task { await changeEmail() } } }
            }
        }
    }

    private var resetSheet: some View {
        NavigationStack {
            Form {
                Section("1. Send a link") {
                    TextField("Email address", text: $resetEmail)
                        .textInputAutocapitalization(.never)
                        .keyboardType(.emailAddress)
                    Button("Send reset link") { Task { await sendReset() } }
                }
                Section("2. Use the token from your email") {
                    SecureField("Reset token", text: $resetToken)
                        .textInputAutocapitalization(.never)
                    Button("Check token") { Task { await checkReset() } }
                    SecureField("New password", text: $resetPassword)
                    Button("Set new password") { Task { await confirmReset() } }
                        .disabled(resetToken.isEmpty || resetPassword.isEmpty)
                }
            }
            .navigationTitle("Reset password")
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { showingReset = false } } }
        }
    }

    private func load() async {
        let values: JSON?
        if let cached = app.settings {
            values = cached
        } else {
            values = try? await app.client.settings()
        }
        density = values?["density"]?.string ?? density
        material = values?["material"]?.string ?? material
        realGlass = values?["real_glass"]?.string ?? realGlass
        covers = values?["covers"]?.bool ?? covers
        autoplay = values?["autoplay"]?.bool ?? autoplay
        hideExplicit = values?["hide_explicit"]?.bool ?? hideExplicit
        isPrivate = values?["private"]?.bool ?? isPrivate
        ytStats = values?["yt_stats"]?.bool ?? ytStats
        rememberVolume = values?["remember_volume"]?.bool ?? rememberVolume
        prefetch = values?["prefetch"]?.bool ?? prefetch
        offlineAudio = values?["offline_audio"]?.bool ?? offlineAudio
        roturActivity = values?["rotur_activity"]?.bool ?? roturActivity
        discordActivity = values?["discord_activity"]?.bool ?? discordActivity
        showRoomURL = values?["show_room_url"]?.bool ?? showRoomURL
        volume = values?["volume"]?.double ?? volume
        // Preserve the half a legacy server id implied; the picker displays its
        // family without rewriting the stored value.
        if let theme = values?["theme"]?.string { palette = Theme.canonicalID(theme) }
        if let color = values?["accent"]?.string, !color.isEmpty { accent = color }
        if let stroke = values?["iconStroke"]?.double {
            iconStroke = Lucide.nearestStroke(stroke)
        }
        if let filled = values?["iconFilled"]?.bool { iconFilled = filled }
        async let roturStatus = try? await app.client.roturStatus()
        async let discordStatus = try? await app.client.discordStatus()
        async let roturAuth = try? await app.client.roturAuthorize()
        async let discordAuth = try? await app.client.discordAuthorize()
        rotur = await roturStatus
        discord = await discordStatus
        let roturAuthValue = await roturAuth
        let discordAuthValue = await discordAuth
        roturURL = roturAuthValue?["url"]?.string ?? ""
        discordURL = discordAuthValue?["url"]?.string ?? ""
    }

    private func save() async {
        app.client.setBaseURL(server)
        await app.saveSettings([
            "theme": palette,
            "accent": accent,
            "iconStroke": iconStroke,
            "iconFilled": iconFilled,
            "density": density,
            "material": material,
            "real_glass": realGlass,
            "covers": covers,
            "autoplay": autoplay,
            "hide_explicit": hideExplicit,
            "private": isPrivate,
            "yt_stats": ytStats,
            "remember_volume": rememberVolume,
            "volume": volume,
            "prefetch": prefetch,
            "offline_audio": offlineAudio,
            "rotur_activity": roturActivity,
            "discord_activity": discordActivity,
            "show_room_url": showRoomURL
        ])
        app.player.volume = Float(volume)
        app.show("Settings saved")
    }

    private func run(_ action: () async throws -> Void) async {
        do {
            try await action()
            await load()
        } catch { app.show(error) }
    }

    private func claimRotur() async {
        await run {
            let result = try await app.client.roturClaim(code: roturCode)
            if let message = result["error"]?.string { app.show(message) }
            roturCode = ""
        }
    }

    private func changePassword() async {
        do {
            try await app.client.changePassword(old: oldPassword, new: newPassword)
            showingPassword = false
            oldPassword = ""
            newPassword = ""
            app.show("Password changed")
        } catch { app.show(error) }
    }

    private func changeEmail() async {
        do {
            try await app.client.setEmail(email)
            showingEmail = false
            app.show("Email updated")
        } catch { app.show(error) }
    }

    private func sendReset() async {
        do {
            try await app.client.requestPasswordReset(email: resetEmail)
            app.show("If that address is registered, a reset link is on its way")
        } catch { app.show(error) }
    }

    private func checkReset() async {
        do {
            try await app.client.checkReset(token: resetToken)
            app.show("Reset token is valid")
        } catch { app.show(error) }
    }

    private func confirmReset() async {
        do {
            try await app.client.confirmReset(token: resetToken, password: resetPassword)
            showingReset = false
            resetToken = ""
            resetPassword = ""
            app.show("Password reset")
        } catch { app.show(error) }
    }
}
```

