import Foundation
import CoreLocation
import MapKit
import AppIntents

// Shared by the app and the widget extension: what "nearby" means, and how the
// agent finds and picks a place around the traveler's live location.

nonisolated enum NearbyCategory: String, Codable, CaseIterable, Hashable, AppEnum {
    case food, social, hospitality, shop

    static let typeDisplayRepresentation: TypeDisplayRepresentation = "Nearby category"
    static let caseDisplayRepresentations: [NearbyCategory: DisplayRepresentation] = [
        .food: "Food", .social: "Social", .hospitality: "Hospitality", .shop: "Shop",
    ]

    var title: String {
        switch self {
        case .food: "Food"
        case .social: "Social"
        case .hospitality: "Hospitality"
        case .shop: "Shop"
        }
    }

    /// Shorter label for tight layouts (widgets, Dynamic Island).
    var shortTitle: String { self == .hospitality ? "Stay" : title }

    var symbol: String {
        switch self {
        case .food: "fork.knife"
        case .social: "person.2"
        case .hospitality: "bed.double"
        case .shop: "bag"
        }
    }

    var pointsOfInterest: [MKPointOfInterestCategory] {
        switch self {
        case .food: [.restaurant, .cafe, .bakery, .winery, .brewery, .foodMarket]
        case .social: [.nightlife, .musicVenue, .theater, .museum, .park, .beach, .marina]
        case .hospitality: [.hotel, .spa]
        case .shop: [.store]
        }
    }
}

/// A place the agent recommends, small enough to travel in a Live Activity update.
nonisolated struct NearbyPick: Codable, Hashable, Identifiable {
    var name: String
    var category: NearbyCategory
    var kind: String
    var distanceMeters: Double
    var note: String
    var latitude: Double
    var longitude: Double

    var id: String { "\(name)-\(latitude)-\(longitude)" }

    /// Walking at roughly 80 m a minute, never less than a minute.
    var walkMinutes: Int { max(1, Int((distanceMeters / 80).rounded())) }

    var walkText: String { "\(walkMinutes) min walk" }

    var coordinate: CLLocationCoordinate2D { .init(latitude: latitude, longitude: longitude) }
}

/// What the agent found around one location for one category.
nonisolated struct NearbyResult: Hashable {
    var locality: String?
    var picks: [NearbyPick]

    var top: NearbyPick? { picks.first }
}

nonisolated enum NearbyFinder {
    /// Searches points of interest around `location` and ranks them, best first.
    static func search(near location: CLLocation, category: NearbyCategory, limit: Int = 4) async -> NearbyResult {
        let request = MKLocalPointsOfInterestRequest(center: location.coordinate, radius: 1_500)
        request.pointOfInterestFilter = MKPointOfInterestFilter(including: category.pointsOfInterest)

        guard let response = try? await MKLocalSearch(request: request).start() else {
            return NearbyResult(locality: nil, picks: [])
        }

        let ranked = response.mapItems
            .compactMap { item -> (MKMapItem, Double)? in
                guard item.name?.isEmpty == false else { return nil }
                let distance = location.distance(from: CLLocation(latitude: item.placemark.coordinate.latitude, longitude: item.placemark.coordinate.longitude))
                return (item, distance)
            }
            .sorted { score($0.0, distance: $0.1) > score($1.0, distance: $1.1) }
            .prefix(limit)

        let picks = ranked.enumerated().map { index, entry in
            makePick(entry.0, distance: entry.1, category: category, isTop: index == 0)
        }
        return NearbyResult(locality: ranked.first?.0.placemark.locality, picks: picks)
    }

    /// Prefers established places (a website or phone number listed) a short walk away.
    private static func score(_ item: MKMapItem, distance: Double) -> Double {
        var score = 1_000 - min(distance, 1_500) * 0.6
        if item.url != nil { score += 260 }
        if item.phoneNumber != nil { score += 120 }
        if distance < 60 { score -= 150 } // right on top of you is rarely the discovery
        return score
    }

    private static func makePick(_ item: MKMapItem, distance: Double, category: NearbyCategory, isTop: Bool) -> NearbyPick {
        let kind = label(for: item.pointOfInterestCategory, fallback: category)
        let coordinate = item.placemark.coordinate
        return NearbyPick(
            name: item.name ?? kind,
            category: category,
            kind: kind,
            distanceMeters: distance,
            note: note(category: category, kind: kind, minutes: max(1, Int((distance / 80).rounded()))),
            latitude: coordinate.latitude,
            longitude: coordinate.longitude
        )
    }

    static func label(for poi: MKPointOfInterestCategory?, fallback: NearbyCategory) -> String {
        switch poi {
        case .restaurant?: "Restaurant"
        case .cafe?: "Café"
        case .bakery?: "Bakery"
        case .winery?: "Winery"
        case .brewery?: "Brewery"
        case .foodMarket?: "Food market"
        case .nightlife?: "Bar"
        case .musicVenue?: "Live music"
        case .theater?: "Theatre"
        case .museum?: "Museum"
        case .park?: "Park"
        case .beach?: "Beach"
        case .marina?: "Marina"
        case .hotel?: "Hotel"
        case .spa?: "Spa"
        case .store?: "Boutique"
        default: fallback.title
        }
    }

    /// The agent's one-line reason, tuned to the time of day.
    static func note(category: NearbyCategory, kind: String, minutes: Int, date: Date = .now) -> String {
        let hour = Calendar.current.component(.hour, from: date)
        let walk = minutes == 1 ? "a minute away" : "\(minutes) minutes on foot"
        switch category {
        case .food:
            let moment = switch hour {
            case 5..<11: "breakfast"
            case 11..<15: "lunch"
            case 15..<18: "an afternoon break"
            case 18..<22: "dinner"
            default: "a late bite"
            }
            return "My pick for \(moment), \(walk). Want me to hold a table?"
        case .social:
            return hour >= 17 || hour < 3
                ? "Where the evening is tonight, \(walk)."
                : "Worth an hour this afternoon, \(walk)."
        case .hospitality:
            return "A calm place to pause, \(walk). I can arrange a room or a treatment."
        case .shop:
            return "Worth the detour, \(walk). I’ll have anything shipped home."
        }
    }

    /// Illustrative picks for widget previews and the gallery — never shown as real results.
    static func preview(_ category: NearbyCategory) -> NearbyPick {
        let base = (lat: 45.9858, lon: 9.2610)
        return switch category {
        case .food:
            NearbyPick(name: "Bar Rossi", category: .food, kind: "Café", distanceMeters: 320, note: note(category: .food, kind: "Café", minutes: 4), latitude: base.lat, longitude: base.lon)
        case .social:
            NearbyPick(name: "Villa Melzi Gardens", category: .social, kind: "Park", distanceMeters: 900, note: note(category: .social, kind: "Park", minutes: 11), latitude: base.lat, longitude: base.lon)
        case .hospitality:
            NearbyPick(name: "Grand Hotel Villa Serbelloni", category: .hospitality, kind: "Hotel", distanceMeters: 240, note: note(category: .hospitality, kind: "Hotel", minutes: 3), latitude: base.lat, longitude: base.lon)
        case .shop:
            NearbyPick(name: "Pierangelo Masciadri", category: .shop, kind: "Boutique", distanceMeters: 410, note: note(category: .shop, kind: "Boutique", minutes: 5), latitude: base.lat, longitude: base.lon)
        }
    }
}

/// The app's last known location, shared with the widget through an App Group.
/// Widgets may not be allowed to use location themselves, so this is their fallback.
/// App Groups need a paid developer account; without the entitlement this stays empty
/// for the widget and it relies on its own location access instead.
nonisolated enum SharedLocation {
    static let defaults = UserDefaults(suiteName: "group.com.wonder.concierge")

    static func save(_ location: CLLocation) {
        defaults?.set([
            "lat": location.coordinate.latitude,
            "lon": location.coordinate.longitude,
            "time": location.timestamp.timeIntervalSince1970,
        ], forKey: "lastLocation")
    }

    /// Last saved location, if it is recent enough to still be "around you".
    static func load(maxAge: TimeInterval = 6 * 60 * 60) -> CLLocation? {
        guard let dict = defaults?.dictionary(forKey: "lastLocation"),
              let lat = dict["lat"] as? Double, let lon = dict["lon"] as? Double,
              let time = dict["time"] as? Double else { return nil }
        let timestamp = Date(timeIntervalSince1970: time)
        guard timestamp.timeIntervalSinceNow > -maxAge else { return nil }
        return CLLocation(coordinate: .init(latitude: lat, longitude: lon), altitude: 0,
                          horizontalAccuracy: 100, verticalAccuracy: -1, timestamp: timestamp)
    }
}

nonisolated enum CurrentLocation {
    /// The freshest location available without keeping updates running.
    static func fetch(timeout: Duration = .seconds(6)) async -> CLLocation? {
        if let cached = CLLocationManager().location,
           cached.timestamp.timeIntervalSinceNow > -600 {
            return cached
        }
        return await withTaskGroup(of: CLLocation?.self) { group in
            group.addTask {
                do {
                    for try await update in CLLocationUpdate.liveUpdates() {
                        if let location = update.location { return location }
                        if update.authorizationDenied || update.authorizationRestricted { return nil }
                    }
                } catch {}
                return nil
            }
            group.addTask {
                try? await Task.sleep(for: timeout)
                return nil
            }
            let first = await group.next() ?? nil
            group.cancelAll()
            return first ?? CLLocationManager().location
        }
    }
}
