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
