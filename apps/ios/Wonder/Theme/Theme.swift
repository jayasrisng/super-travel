import SwiftUI

// MARK: - Palette
//
// Wonder is monochrome: black, white and translucent white Liquid Glass. Colour comes
// only from the photography of the places themselves.
//
// Type is adaptive: white directly on photography (the app runs in dark appearance),
// black inside glass (every glass surface switches its content to light appearance).

extension Color {
    init(hex: UInt32, opacity: Double = 1) {
        self.init(
            .sRGB,
            red: Double((hex >> 16) & 0xFF) / 255,
            green: Double((hex >> 8) & 0xFF) / 255,
            blue: Double(hex & 0xFF) / 255,
            opacity: opacity
        )
    }

    /// Primary type and solid controls: white on photography, black on glass.
    static let ink = Color.primary
    /// Secondary text.
    static let textSoft = Color.primary.opacity(0.62)
    /// Tertiary text and inactive controls.
    static let textFaint = Color.primary.opacity(0.36)
    /// Quiet fill for icon wells.
    static let well = Color.primary.opacity(0.07)
    /// Completion green: confirmed bookings, finished steps, verified documents.
    static let verified = Color(hex: 0x1F9D55)
}

/// Solid black or white, chosen by appearance: black inside glass, white on photography.
/// Unlike `Color.ink`, it is never rendered with the glass's translucent vibrancy,
/// so buttons and badges stay truly solid.
struct SolidInk: ShapeStyle {
    var inverse = false

    func resolve(in environment: EnvironmentValues) -> Color {
        (environment.colorScheme == .dark) != inverse ? .white : .black
    }
}

extension ShapeStyle where Self == SolidInk {
    static var solidInk: SolidInk { SolidInk() }
    static var solidInkInverse: SolidInk { SolidInk(inverse: true) }
}

// MARK: - Typography

enum WFont {
    /// The Didone wordmark face.
    static func wordmark(_ size: CGFloat) -> Font { .custom("Didot", size: size) }
    /// Editorial serif for headlines (New York).
    static func display(_ size: CGFloat, weight: Font.Weight = .regular) -> Font {
        .system(size: size, weight: weight, design: .serif)
    }
    static func body(_ size: CGFloat = 15, weight: Font.Weight = .regular) -> Font {
        .system(size: size, weight: weight)
    }
    static func mono(_ size: CGFloat = 11) -> Font {
        .system(size: size, weight: .medium, design: .monospaced)
    }
}

/// Small, widely tracked uppercase label — "ITALY", "FOR YOU".
struct Eyebrow: View {
    let text: String
    var color: Color = .ink
    var size: CGFloat = 10.5

    init(_ text: String, color: Color = .ink, size: CGFloat = 10.5) {
        self.text = text
        self.color = color
        self.size = size
    }

    var body: some View {
        Text(text.uppercased())
            .font(.system(size: size, weight: .semibold))
            .tracking(2.2)
            .foregroundStyle(color)
    }
}

struct Hairline: View {
    var color: Color = .primary.opacity(0.12)
    var body: some View {
        Rectangle().fill(color).frame(height: 0.5)
    }
}

// MARK: - Backdrop

/// Full-screen photograph of a place, veiled in black so glass and white type read on top.
/// Content scrolls over it; the backdrop stays put and cross-fades when the place changes.
struct Backdrop: View {
    let photo: String
    /// Strength of the top and bottom shading; the middle of the photo stays clear.
    var veil: Double = 0.45

    var body: some View {
        GeometryReader { geo in
            ZStack {
                Photo(id: photo, width: 1400)
                    .frame(width: geo.size.width, height: geo.size.height)
                    .id(photo)
                    .transition(.opacity)
                LinearGradient(
                    stops: [
                        .init(color: .black.opacity(veil * 0.7), location: 0),
                        .init(color: .black.opacity(veil * 0.12), location: 0.3),
                        .init(color: .black.opacity(veil * 0.05), location: 0.55),
                        .init(color: .black.opacity(veil * 0.85), location: 1),
                    ],
                    startPoint: .top, endPoint: .bottom
                )
            }
            .animation(.easeInOut(duration: 0.7), value: photo)
        }
        .ignoresSafeArea()
    }
}

// MARK: - Surfaces

extension View {
    /// Translucent white Liquid Glass panel (iOS 26), light material elsewhere.
    /// Content inside reads in light appearance, so `ink` type turns black.
    @ViewBuilder
    func glassPanel(cornerRadius: CGFloat = 22) -> some View {
        if #available(iOS 26.0, *) {
            self
                .glassEffect(.regular.tint(.white.opacity(0.42)), in: .rect(cornerRadius: cornerRadius))
                .environment(\.colorScheme, .light)
        } else {
            self
                .background(.regularMaterial, in: .rect(cornerRadius: cornerRadius))
                .background(Color.white.opacity(0.35), in: .rect(cornerRadius: cornerRadius))
                .overlay(
                    RoundedRectangle(cornerRadius: cornerRadius)
                        .strokeBorder(.white.opacity(0.6), lineWidth: 0.5)
                )
                .environment(\.colorScheme, .light)
        }
    }

    /// Soft shadow that keeps white type readable directly on photography.
    func legible() -> some View {
        shadow(color: .black.opacity(0.3), radius: 12, y: 1)
    }

    @ViewBuilder
    func glassCapsule(interactive: Bool = false) -> some View {
        if #available(iOS 26.0, *) {
            let glass: Glass = .regular.tint(.white.opacity(0.42))
            self
                .glassEffect(interactive ? glass.interactive() : glass, in: .capsule)
                .environment(\.colorScheme, .light)
        } else {
            self
                .background(.regularMaterial, in: .capsule)
                .background(Color.white.opacity(0.35), in: .capsule)
                .overlay(Capsule().strokeBorder(.white.opacity(0.6), lineWidth: 0.5))
                .environment(\.colorScheme, .light)
        }
    }

    /// Frosted white capsule for small controls. Liquid Glass adapts small elements to
    /// whatever is behind them (turning dark over dark photos); this always stays white.
    func frostedCapsule() -> some View {
        self
            .background(Capsule().fill(.white.opacity(0.55)))
            .background(.ultraThinMaterial, in: .capsule)
            .overlay(Capsule().strokeBorder(.white.opacity(0.7), lineWidth: 0.5))
            .environment(\.colorScheme, .light)
    }

    @ViewBuilder
    func glassCircle() -> some View {
        if #available(iOS 26.0, *) {
            self
                .glassEffect(.regular.tint(.white.opacity(0.42)).interactive(), in: .circle)
                .environment(\.colorScheme, .light)
        } else {
            self
                .background(.regularMaterial, in: .circle)
                .overlay(Circle().strokeBorder(.white.opacity(0.6), lineWidth: 0.5))
                .environment(\.colorScheme, .light)
        }
    }
}

// MARK: - Status

/// A component's status: green with a check once it's complete, quiet otherwise.
struct StatusLabel: View {
    let text: String
    let complete: Bool
    var size: CGFloat = 12

    var body: some View {
        HStack(spacing: 4) {
            if complete {
                Image(systemName: "checkmark.circle.fill")
                    .font(.system(size: size))
                    .symbolRenderingMode(.palette)
                    .foregroundStyle(.white, Color.verified)
            }
            Text(text)
                .font(WFont.body(size, weight: complete ? .semibold : .regular))
                .foregroundStyle(complete ? Color.verified : Color.textSoft)
        }
        .lineLimit(1)
    }
}

/// "Tailored for you": how the concierge shaped a trip around the member's words.
struct TailoringNotes: View {
    let notes: [String]

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Eyebrow("Tailored for you", color: .textSoft, size: 9)
            ForEach(notes, id: \.self) { note in
                HStack(alignment: .firstTextBaseline, spacing: 8) {
                    Image(systemName: "sparkle")
                        .font(.system(size: 9, weight: .semibold))
                    Text(note)
                        .font(WFont.body(13))
                        .fixedSize(horizontal: false, vertical: true)
                }
                .foregroundStyle(Color.ink)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

// MARK: - Buttons

/// The one solid control on a screen: black on glass, white on photography.
struct PrimaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(WFont.body(15, weight: .medium))
            .foregroundStyle(.solidInkInverse)
            .frame(maxWidth: .infinity)
            .frame(height: 54)
            .background(.solidInk, in: .capsule)
            .scaleEffect(configuration.isPressed ? 0.98 : 1)
            .opacity(configuration.isPressed ? 0.9 : 1)
            .animation(.spring(duration: 0.25), value: configuration.isPressed)
    }
}

struct PressableStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.975 : 1)
            .animation(.spring(duration: 0.3), value: configuration.isPressed)
    }
}

// MARK: - Formatting

enum Fmt {
    static func money(_ value: Int, currency: String = "USD") -> String {
        value.formatted(.currency(code: currency).precision(.fractionLength(0)))
    }

    static func dateRange(_ start: Date, nights: Int) -> String {
        let end = Calendar.current.date(byAdding: .day, value: nights, to: start) ?? start
        let sameMonth = Calendar.current.isDate(start, equalTo: end, toGranularity: .month)
        let s = start.formatted(.dateTime.month(.wide).day())
        let e = sameMonth ? end.formatted(.dateTime.day()) : end.formatted(.dateTime.month(.abbreviated).day())
        return "\(s) – \(e)"
    }

    static func coordinate(_ lat: Double, _ lon: Double) -> String {
        let ns = lat >= 0 ? "N" : "S"
        let ew = lon >= 0 ? "E" : "W"
        return String(format: "%.4f° %@   %.4f° %@", abs(lat), ns, abs(lon), ew)
    }
}

extension View {
    /// Fades scrolled content out beneath the status bar.
    func statusBarScrim(_ color: Color) -> some View {
        overlay(alignment: .top) {
            GeometryReader { geo in
                let inset = geo.safeAreaInsets.top
                LinearGradient(
                    stops: [.init(color: color, location: 0), .init(color: color.opacity(0.9), location: 0.55), .init(color: color.opacity(0), location: 1)],
                    startPoint: .top, endPoint: .bottom
                )
                .frame(height: inset + 14)
                .offset(y: -inset)
            }
            .allowsHitTesting(false)
        }
    }
}
