import SwiftUI
import MapKit

/// Photoreal 3D satellite view of a place, with cartographic annotations.
struct SatelliteMap: View {
    let coordinate: CLLocationCoordinate2D
    var title: String
    var distance: Double = 14_000
    var pitch: Double = 58
    var heading: Double = 25
    var interactive = false

    var body: some View {
        Map(
            initialPosition: .camera(MapCamera(centerCoordinate: coordinate, distance: distance, heading: heading, pitch: pitch)),
            interactionModes: interactive ? .all : []
        ) {
            Annotation("", coordinate: coordinate, anchor: .center) {
                ZStack {
                    PulseRing(style: Color.white.opacity(0.8), lineWidth: 1, from: 0.6, to: 1.6, duration: 2)
                        .frame(width: 44, height: 44)
                    Circle().fill(Color.white).frame(width: 10, height: 10)
                    Circle().stroke(Color.black, lineWidth: 2).frame(width: 10, height: 10)
                }
            }
        }
        .mapStyle(.imagery(elevation: .realistic))
        .mapControlVisibility(.hidden)
        .overlay {
            LinearGradient(colors: [.black.opacity(0.45), .clear, .clear, .black.opacity(0.55)], startPoint: .top, endPoint: .bottom)
                .allowsHitTesting(false)
        }
        .overlay(alignment: .topLeading) {
            VStack(alignment: .leading, spacing: 4) {
                Text(title.uppercased())
                    .font(WFont.mono(11))
                    .tracking(2)
                Rectangle().fill(Color.white.opacity(0.6)).frame(width: 28, height: 0.5)
            }
            .foregroundStyle(Color.white)
            .padding(16)
            .allowsHitTesting(false)
        }
        .overlay(alignment: .bottomTrailing) {
            Text(Fmt.coordinate(coordinate.latitude, coordinate.longitude))
                .font(WFont.mono(10))
                .foregroundStyle(Color.white.opacity(0.85))
                .padding(16)
                .allowsHitTesting(false)
        }
    }
}
