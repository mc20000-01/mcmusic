import SwiftUI

/// Compact, dependency-free lyric visualizer used by the lyrics sheet.
///
/// Every frame is a pure function of `progress`, `isPlaying` and `activeLine`:
/// no timers, no random state and no wall-clock phase. Pausing playback freezes
/// the picture exactly where it is, and seeking always redraws the same frame.
/// Only SwiftUI/Canvas APIs are used, so the drawing code is portable.
struct LyricVisualizer: View {
    enum Mode: String, CaseIterable, Identifiable {
        case bars, wave, glow

        var id: String { rawValue }

        var label: String {
            switch self {
            case .bars: return "Bars"
            case .wave: return "Wave"
            case .glow: return "Glow"
            }
        }
    }

    var progress: Double
    var isPlaying: Bool
    var activeLine: Int? = nil
    var mode: Mode = .bars

    var body: some View {
        Canvas { context, size in
            guard size.width > 0, size.height > 0 else { return }
            let t = CGFloat(progress.isFinite ? max(0, progress) : 0)
            let energy: CGFloat = (isPlaying ? 1 : 0.5) + (activeLine == nil ? 0 : 0.06)
            switch mode {
            case .bars: drawBars(&context, size, t, energy)
            case .wave: drawWave(&context, size, t, energy)
            case .glow: drawGlow(&context, size, t, energy)
            }
        }
        .accessibilityHidden(true) // decorative; the mode picker is the control
    }

    // MARK: - Modes

    private func drawBars(_ context: inout GraphicsContext, _ size: CGSize, _ t: CGFloat, _ energy: CGFloat) {
        let count = 32
        let spacing: CGFloat = 3
        let width = max(2, (size.width - spacing * CGFloat(count - 1)) / CGFloat(count))
        let middle = size.height / 2
        for i in 0..<count {
            let seed = CGFloat(i) * 0.62
            let motion = 0.5 + 0.5 * sin(t * 1.35 + seed)
            let shimmer = 0.5 + 0.5 * sin(t * 0.8 - seed * 1.7)
            let height = max(3, size.height * (0.12 + 0.62 * motion * shimmer) * energy)
            let rect = CGRect(
                x: CGFloat(i) * (width + spacing),
                y: middle - height / 2,
                width: width,
                height: height
            )
            context.fill(
                Path(roundedRect: rect, cornerRadius: width / 2),
                with: .color(Theme.violet.opacity(0.4 + 0.6 * motion))
            )
        }
    }

    private func drawWave(_ context: inout GraphicsContext, _ size: CGSize, _ t: CGFloat, _ energy: CGFloat) {
        let middle = size.height / 2
        let steps = max(24, Int(size.width / 4))
        for layer in 0..<3 {
            var path = Path()
            let amplitude = size.height * (0.14 + CGFloat(layer) * 0.06) * energy
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
                with: .color(Theme.violet.opacity(opacity)),
                style: StrokeStyle(lineWidth: layer == 0 ? 3 : 1.5, lineCap: .round, lineJoin: .round)
            )
        }
    }

    private func drawGlow(_ context: inout GraphicsContext, _ size: CGSize, _ t: CGFloat, _ energy: CGFloat) {
        let center = CGPoint(x: size.width / 2, y: size.height / 2)
        let radius = min(size.width, size.height) * 0.48
        let pulse = 0.5 + 0.5 * sin(t * 1.1)
        let rings = 7
        for i in stride(from: rings, through: 1, by: -1) {
            let fraction = CGFloat(i) / CGFloat(rings)
            let r = radius * (0.18 + fraction * 0.82) * (0.92 + 0.1 * pulse) * energy
            let rect = CGRect(x: center.x - r, y: center.y - r, width: r * 2, height: r * 2)
            context.fill(
                Path(ellipseIn: rect),
                with: .color(Theme.violet.opacity(Double(1 - fraction) * 0.3 + 0.02))
            )
        }
        let core = radius * (0.14 + 0.05 * pulse) * energy
        context.fill(
            Path(ellipseIn: CGRect(x: center.x - core, y: center.y - core, width: core * 2, height: core * 2)),
            with: .color(Theme.textBright.opacity(0.85))
        )
    }
}

/// Lyrics sheet: the visualizer, an accessible mode picker, then the lyrics
/// text exactly as loaded by NowPlayingView (including its error strings).
struct LyricSheet: View {
    let text: String
    let progress: Double
    let duration: Double
    let isPlaying: Bool

    @Environment(\.dismiss) private var dismiss
    @State private var mode: LyricVisualizer.Mode = .bars

    private var lines: [String] { text.components(separatedBy: .newlines) }

    private var activeLine: Int? {
        guard lines.count > 1, duration.isFinite, duration > 0, progress.isFinite else { return nil }
        return min(lines.count - 1, max(0, Int(progress / duration * Double(lines.count))))
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 12) {
                LyricVisualizer(progress: progress, isPlaying: isPlaying, activeLine: activeLine, mode: mode)
                    .frame(height: 170)
                    .padding(.horizontal, 8)

                Picker("Visualizer mode", selection: $mode) {
                    ForEach(LyricVisualizer.Mode.allCases) { option in
                        Text(option.label).tag(option).accessibilityLabel(option.label)
                    }
                }
                .pickerStyle(.segmented)
                .padding(.horizontal)
                .frame(minHeight: 44)
                .accessibilityLabel("Visualizer mode")
                .accessibilityHint("Choose how the lyrics are visualized")
                .accessibilityIdentifier("lyricVisualizerMode")

                ScrollView {
                    VStack(alignment: .leading, spacing: 12) {
                        ForEach(Array(lines.enumerated()), id: \.offset) { index, line in
                            Text(line.isEmpty ? " " : line)
                                .font(.body)
                                .foregroundStyle(index == activeLine ? Theme.violet : Theme.text)
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }
                    }
                    .padding()
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
            }
            .padding(.top, 8)
            .background(Theme.ink.ignoresSafeArea())
            .navigationTitle("Lyrics")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } }
            }
        }
    }
}
