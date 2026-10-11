import SwiftUI

/// An expanding, fading ring that loops forever. The animation is driven by the ring's
/// own keyframes, so it never leaks into the layout of the views around it.
struct PulseRing<S: ShapeStyle>: View {
    var style: S
    var lineWidth: CGFloat? = nil
    var from: CGFloat = 0.9
    var to: CGFloat = 1.3
    var duration: Double = 1.6

    var body: some View {
        Group {
            if let lineWidth {
                Circle().stroke(style, lineWidth: lineWidth)
            } else {
                Circle().fill(style)
            }
        }
        .keyframeAnimator(initialValue: 0.0, repeating: true) { ring, progress in
            ring
                .scaleEffect(from + (to - from) * progress)
                .opacity(1 - progress)
        } keyframes: { _ in
            CubicKeyframe(1, duration: duration)
        }
        .allowsHitTesting(false)
    }
}

/// A short arc that spins forever, scoped to itself.
struct SpinningArc: View {
    var style: Color
    var lineWidth: CGFloat = 1.5

    var body: some View {
        Circle()
            .trim(from: 0, to: 0.3)
            .stroke(style, style: StrokeStyle(lineWidth: lineWidth, lineCap: .round))
            .keyframeAnimator(initialValue: 0.0, repeating: true) { arc, turn in
                arc.rotationEffect(.degrees(turn * 360))
            } keyframes: { _ in
                LinearKeyframe(1, duration: 1)
            }
            .allowsHitTesting(false)
    }
}
