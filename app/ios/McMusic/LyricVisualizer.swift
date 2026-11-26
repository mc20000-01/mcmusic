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
