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
