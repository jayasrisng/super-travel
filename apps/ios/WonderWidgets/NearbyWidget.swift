import WidgetKit
import SwiftUI
import AppIntents
import CoreLocation
import MapKit

// MARK: - State

/// The category the widget is showing. Widget buttons run in this extension's
/// process, so the extension's own defaults are the right home for it.
enum NearbyWidgetState {
    private static let key = "nearby.widget.category"

    static var category: NearbyCategory {
        get { UserDefaults.standard.string(forKey: key).flatMap(NearbyCategory.init(rawValue:)) ?? .food }
        set { UserDefaults.standard.set(newValue.rawValue, forKey: key) }
    }
}

struct SelectNearbyCategoryIntent: AppIntent {
    static let title: LocalizedStringResource = "Show nearby category"
    static let isDiscoverable = false

    @Parameter(title: "Category")
    var category: NearbyCategory

    init() {}

    init(category: NearbyCategory) {
        self.category = category
    }

    func perform() async throws -> some IntentResult {
        NearbyWidgetState.category = category
        return .result()
    }
}

// MARK: - Timeline

struct NearbyEntry: TimelineEntry {
    enum Status { case ready, noLocation, nothingFound }

    let date: Date
    let category: NearbyCategory
    let status: Status
    let locality: String?
    let picks: [NearbyPick]
    let backdrop: UIImage?

    var top: NearbyPick? { picks.first }

    static func preview(_ category: NearbyCategory = .food) -> NearbyEntry {
        let others = NearbyCategory.allCases.filter { $0 != category }.map(NearbyFinder.preview)
        return NearbyEntry(
            date: .now, category: category, status: .ready, locality: "Bellagio",
            picks: [NearbyFinder.preview(category)] + others, backdrop: nil
        )
    }
}

struct NearbyProvider: TimelineProvider {
    func placeholder(in context: Context) -> NearbyEntry { .preview() }

    func getSnapshot(in context: Context, completion: @escaping (NearbyEntry) -> Void) {
        if context.isPreview {
            completion(.preview(NearbyWidgetState.category))
            return
        }
        Task { completion(await load(size: context.displaySize)) }
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<NearbyEntry>) -> Void) {
        Task {
            let entry = await load(size: context.displaySize)
            // Places change as the traveler moves; refresh regularly.
            completion(Timeline(entries: [entry], policy: .after(.now.addingTimeInterval(15 * 60))))
        }
    }

    private func load(size: CGSize) async -> NearbyEntry {
        let category = NearbyWidgetState.category
        // Prefer a fresh fix; fall back to where the app last saw the traveler.
        var live: CLLocation?
        if CLLocationManager().isAuthorizedForWidgetUpdates {
            live = await CurrentLocation.fetch(timeout: .seconds(5))
        }
        guard let location = live ?? SharedLocation.load() else {
            return NearbyEntry(date: .now, category: category, status: .noLocation, locality: nil, picks: [], backdrop: nil)
        }
        let result = await NearbyFinder.search(near: location, category: category, limit: 4)
        let backdrop = await MapBackdrop.snapshot(around: result.top?.coordinate ?? location.coordinate, size: size)
        return NearbyEntry(
            date: .now,
            category: category,
            status: result.picks.isEmpty ? .nothingFound : .ready,
            locality: result.locality,
            picks: result.picks,
            backdrop: backdrop
        )
    }
}

/// Satellite view of the neighbourhood, used as the widget's background photograph.
enum MapBackdrop {
    static func snapshot(around center: CLLocationCoordinate2D, size: CGSize) async -> UIImage? {
        let options = MKMapSnapshotter.Options()
        options.camera = MKMapCamera(lookingAtCenter: center, fromDistance: 900, pitch: 45, heading: 15)
        options.size = CGSize(width: max(size.width, 120), height: max(size.height, 120))
        options.preferredConfiguration = MKImageryMapConfiguration(elevationStyle: .realistic)
        return try? await MKMapSnapshotter(options: options).start().image
    }
}

// MARK: - Widget

struct NearbyWidget: Widget {
    let kind = "WonderNearby"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: NearbyProvider()) { entry in
            NearbyWidgetView(entry: entry)
        }
        .configurationDisplayName("Wonder Nearby")
        .description("Your agent’s pick around you, by food, social, hospitality or shop.")
        .supportedFamilies([.systemSmall, .systemMedium, .systemLarge, .accessoryRectangular, .accessoryInline])
        .contentMarginsDisabled()
    }
}

struct NearbyWidgetView: View {
    @Environment(\.widgetFamily) private var family
    let entry: NearbyEntry

    var body: some View {
        switch family {
        case .accessoryRectangular: rectangular
        case .accessoryInline: inline
        default: system
        }
    }

    // Home Screen

    private var system: some View {
        VStack(alignment: .leading, spacing: 0) {
            header
            Spacer(minLength: 6)
            recommendation
            if family == .systemLarge, entry.picks.count > 1 {
                alsoNearby.padding(.top, 14)
            }
            if family != .systemSmall {
                Spacer(minLength: 10)
                CategoryButtons(selected: entry.category) { SelectNearbyCategoryIntent(category: $0) }
            }
        }
        .padding(family == .systemSmall ? 14 : 16)
        .foregroundStyle(.white)
        .containerBackground(for: .widget) { background }
        .widgetURL(URL(string: "wonder://nearby"))
    }

    private var header: some View {
        HStack(spacing: 6) {
            WonderMark(color: .white)
                .frame(width: 26, height: 16)
            Text(family == .systemSmall ? "NEARBY" : ["NEARBY", entry.locality?.uppercased()].compactMap { $0 }.joined(separator: " · "))
                .font(.system(size: 9.5, weight: .semibold))
                .tracking(1.6)
                .lineLimit(1)
                .opacity(0.85)
            Spacer(minLength: 0)
            if family == .systemSmall {
                Image(systemName: entry.category.symbol)
                    .font(.system(size: 11, weight: .semibold))
                    .opacity(0.85)
            }
        }
    }

    @ViewBuilder
    private var recommendation: some View {
        switch entry.status {
        case .ready:
            if let pick = entry.top {
                VStack(alignment: .leading, spacing: 3) {
                    Text("AGENT’S PICK · \(entry.category.title.uppercased())")
                        .font(.system(size: 8.5, weight: .semibold))
                        .tracking(1.4)
                        .opacity(0.7)
                    Text(pick.name)
                        .font(.system(size: family == .systemLarge ? 26 : family == .systemSmall ? 17 : 20, design: .serif))
                        .lineLimit(family == .systemSmall ? 2 : 1)
                        .minimumScaleFactor(0.8)
                    Text("\(pick.kind) · \(pick.walkText)")
                        .font(.system(size: 12, weight: .medium))
                        .opacity(0.8)
                    if family == .systemLarge {
                        Text(pick.note)
                            .font(.system(size: 13))
                            .opacity(0.85)
                            .lineLimit(2)
                            .padding(.top, 4)
                    }
                }
            }
        case .noLocation:
            message("Share your location", "Open Wonder and allow location to see what’s around you.")
        case .nothingFound:
            message("Nothing close by", "Try another category — or ask your concierge.")
        }
    }

    private func message(_ title: String, _ detail: String) -> some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(title).font(.system(size: 17, design: .serif))
            Text(detail).font(.system(size: 11)).opacity(0.75).lineLimit(2)
        }
    }

    private var alsoNearby: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("ALSO NEARBY")
                .font(.system(size: 8.5, weight: .semibold))
                .tracking(1.4)
                .opacity(0.7)
            ForEach(entry.picks.dropFirst().prefix(3)) { pick in
                HStack {
                    Text(pick.name).font(.system(size: 13, weight: .medium)).lineLimit(1)
                    Spacer()
                    Text("\(pick.walkMinutes) min").font(.system(size: 12)).opacity(0.75)
                }
            }
        }
        .padding(12)
        .background(.white.opacity(0.14), in: .rect(cornerRadius: 14))
    }

    private var background: some View {
        ZStack {
            Color.black
            if let backdrop = entry.backdrop {
                Image(uiImage: backdrop)
                    .resizable()
                    .scaledToFill()
            }
            LinearGradient(
                stops: [
                    .init(color: .black.opacity(0.55), location: 0),
                    .init(color: .black.opacity(0.15), location: 0.35),
                    .init(color: .black.opacity(0.7), location: 1),
                ],
                startPoint: .top, endPoint: .bottom
            )
        }
    }

    // Lock Screen

    private var rectangular: some View {
        VStack(alignment: .leading, spacing: 1) {
            Label("Wonder · \(entry.category.title)", systemImage: entry.category.symbol)
                .font(.system(size: 11, weight: .semibold))
                .widgetAccentable()
            Text(entry.top?.name ?? (entry.status == .noLocation ? "Share your location" : "Nothing close by"))
                .font(.system(size: 15, weight: .semibold))
                .lineLimit(1)
            if let pick = entry.top {
                Text("\(pick.kind) · \(pick.walkText)")
                    .font(.system(size: 12))
                    .lineLimit(1)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .containerBackground(for: .widget) { Color.clear }
        .widgetURL(URL(string: "wonder://nearby"))
    }

    private var inline: some View {
        Label(entry.top.map { "\($0.name) · \($0.walkMinutes) min" } ?? "Wonder Nearby", systemImage: entry.category.symbol)
            .containerBackground(for: .widget) { Color.clear }
    }
}

/// Food · Social · Hospitality · Shop, used by the widget and the Live Activity.
struct CategoryButtons<Intent: AppIntent>: View {
    let selected: NearbyCategory
    let intent: (NearbyCategory) -> Intent

    var body: some View {
        HStack(spacing: 6) {
            ForEach(NearbyCategory.allCases, id: \.self) { category in
                let isOn = category == selected
                Button(intent: intent(category)) {
                    VStack(spacing: 3) {
                        Image(systemName: category.symbol)
                            .font(.system(size: 12, weight: .semibold))
                        Text(category.title)
                            .font(.system(size: 10, weight: .semibold))
                            .lineLimit(1)
                            .minimumScaleFactor(0.8)
                    }
                    .foregroundStyle(isOn ? .black : .white)
                    .frame(maxWidth: .infinity)
                    .frame(height: 40)
                    .background(isOn ? Color.white : Color.white.opacity(0.18), in: .rect(cornerRadius: 12))
                }
                .buttonStyle(.plain)
            }
        }
    }
}

#Preview("Medium", as: .systemMedium) {
    NearbyWidget()
} timeline: {
    NearbyEntry.preview(.food)
    NearbyEntry.preview(.hospitality)
}
