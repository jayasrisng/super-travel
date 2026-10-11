import SwiftUI

/// The Wonder mark: a globe circled by an orbit swoosh, with a plane trailing off it.
/// Drawn as vectors so it stays crisp at any size and takes any colour.
struct WonderMark: View {
    var color: Color = .primary

    /// Design box the paths are drawn in.
    static let box = CGSize(width: 160, height: 100)

    var body: some View {
        Canvas { ctx, size in
            let scale = min(size.width / Self.box.width, size.height / Self.box.height)
            ctx.translateBy(x: (size.width - Self.box.width * scale) / 2, y: (size.height - Self.box.height * scale) / 2)
            ctx.scaleBy(x: scale, y: scale)
            let ink = GraphicsContext.Shading.color(color)

            ctx.fill(Self.globe, with: ink)

            // Each stroke cuts a hairline gap through what's beneath it, then fills itself.
            for path in [Self.orbit, Self.contrail] {
                ctx.blendMode = .destinationOut
                ctx.stroke(path, with: .color(.black), lineWidth: 4.5)
                ctx.blendMode = .normal
                ctx.fill(path, with: ink)
            }

            if let plane = ctx.resolveSymbol(id: "plane") {
                ctx.translateBy(x: 140, y: 14)
                ctx.rotate(by: .degrees(-22))
                ctx.draw(plane, at: .zero)
            }
        } symbols: {
            Image(systemName: "airplane")
                .font(.system(size: 28, weight: .black))
                .foregroundStyle(color)
                .tag("plane")
        }
    }

    static let globe = Path(ellipseIn: CGRect(x: 40, y: 14, width: 80, height: 80))

    /// Crescent sweeping from under the globe round to the left, tapering at both ends.
    static let orbit: Path = {
        var p = Path()
        p.move(to: CGPoint(x: 150, y: 84))
        p.addCurve(to: CGPoint(x: 4, y: 64), control1: CGPoint(x: 88, y: 116), control2: CGPoint(x: -10, y: 104))
        p.addCurve(to: CGPoint(x: 150, y: 84), control1: CGPoint(x: 16, y: 86), control2: CGPoint(x: 92, y: 98))
        p.closeSubpath()
        return p
    }()

    /// Tapered contrail rising from the orbit across the globe to the plane.
    static let contrail: Path = {
        var p = Path()
        p.move(to: CGPoint(x: 4, y: 64))
        p.addQuadCurve(to: CGPoint(x: 128, y: 20), control: CGPoint(x: 46, y: 26))
        p.addQuadCurve(to: CGPoint(x: 4, y: 64), control: CGPoint(x: 50, y: 34))
        p.closeSubpath()
        return p
    }()
}
