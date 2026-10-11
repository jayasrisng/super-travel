import Foundation
import CoreLocation

enum TravelCategory: String, CaseIterable, Identifiable, Codable {
    case forYou = "For You"
    case coastal = "Coastal"
    case cities = "Cities"
    case nature = "Nature"
    case alpine = "Alpine"
    case islands = "Islands"

    var id: String { rawValue }
}

struct Experience: Hashable, Codable {
    let title: String
    let detail: String
    let icon: String
}

struct Stay: Identifiable, Hashable, Codable {
    let id: String
    let name: String
    let location: String
    let photo: String
    let nightly: Int
    let note: String
}

struct Destination: Identifiable, Hashable {
    let id: String
    let name: String
    let country: String
    let adjective: String          // "Italian"
    let tagline: String
    let summary: String
    let categories: Set<TravelCategory>
    let hero: String
    let gallery: [String]
    let latitude: Double
    let longitude: Double
    let bestSeason: String
    let airport: String            // IATA
    let airportCity: String
    let flightTime: String
    let fromPrice: Int
    let stays: [Stay]
    let experiences: [Experience]
    /// The table the agent offers to book while planning.
    let dinner: Restaurant

    var coordinate: CLLocationCoordinate2D { .init(latitude: latitude, longitude: longitude) }
}

/// Saved as its catalog id (`"como"`), so stored trips stay small and pick up catalog updates.
extension Destination: Codable {
    struct UnknownDestination: Error { let id: String }

    init(from decoder: Decoder) throws {
        let id = try decoder.singleValueContainer().decode(String.self)
        guard let destination = Catalog.destination(id: id) else { throw UnknownDestination(id: id) }
        self = destination
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        try container.encode(id)
    }
}

struct Restaurant: Hashable, Codable {
    let name: String
    let cuisine: String
    let time: String
}

/// A table the agent booked by phone.
struct Reservation: Hashable, Codable {
    let restaurant: Restaurant
    let guests: Int
    let day: Int
    let reference: String
}

struct Flight: Hashable, Codable {
    var carrier: String
    var number: String
    var cabin: String
    var seat: String
    var fromCode: String
    var fromCity: String
    var toCode: String
    var toCity: String
    var departs: String
    var arrives: String
    var duration: String
    var stops: String
}

struct TripComponent: Identifiable, Hashable, Codable {
    enum Kind: String, Codable { case flights, stay, transfers, experiences, dining }

    let kind: Kind
    var title: String
    var status: String

    var id: String { kind.rawValue }

    /// Completed components get the green check.
    var isComplete: Bool { status == "Confirmed" || status == "Booked" }

    var icon: String {
        switch kind {
        case .flights: "airplane"
        case .stay: "bed.double"
        case .transfers: "car"
        case .experiences: "binoculars"
        case .dining: "fork.knife"
        }
    }
}

struct ItineraryItem: Identifiable, Hashable, Codable {
    var id = UUID()
    let time: String
    let title: String
    let detail: String
    let icon: String
}

struct ItineraryDay: Identifiable, Hashable, Codable {
    let day: Int
    let title: String
    let items: [ItineraryItem]
    var id: Int { day }
}

enum TripStatus: String, Codable {
    case proposal = "Proposal"
    case confirmed = "Confirmed"
    case completed = "Completed"
}

struct Trip: Identifiable, Hashable, Codable {
    let id: UUID
    var title: String
    var destination: Destination
    var startDate: Date
    var nights: Int
    var travelers: Int
    var isBusiness: Bool
    var stay: Stay
    var flight: Flight
    var components: [TripComponent]
    var days: [ItineraryDay]
    var status: TripStatus
    var total: Int
    var hoursSaved: Int
    var reservation: Reservation? = nil
    /// How the concierge shaped this trip around what the member asked for.
    var tailoring: [String]? = nil

    var endDate: Date {
        Calendar.current.date(byAdding: .day, value: nights, to: startDate) ?? startDate
    }

    var daysUntil: Int {
        Calendar.current.dateComponents([.day], from: .now, to: startDate).day ?? 0
    }

    static func == (lhs: Trip, rhs: Trip) -> Bool {
        lhs.id == rhs.id && lhs.status == rhs.status && lhs.flight == rhs.flight && lhs.reservation == rhs.reservation
    }
    func hash(into hasher: inout Hasher) { hasher.combine(id) }
}

// MARK: - Agent

struct AgentStep: Identifiable, Hashable {
    enum State { case pending, running, waiting, done, skipped }

    let id: Int
    let title: String
    var detail: String
    var state: State
    /// Set while the agent is waiting on the traveler (`state == .waiting`).
    var question: AgentQuestion? = nil
}

/// A yes/no the agent needs answered before it can carry on planning.
struct AgentQuestion: Hashable {
    let prompt: String
    let note: String
    let yes: String
    let no: String
}

struct ChatMessage: Identifiable {
    enum Kind {
        case user(String)
        case agent(String)
        case work([AgentStep])
        case proposal(Trip)
        case confirmation(Trip)
    }

    let id = UUID()
    var kind: Kind
}

struct AgentActivity: Identifiable, Hashable, Codable {
    var id = UUID()
    let icon: String
    let title: String
    let detail: String
    let date: Date

    var time: String {
        if date.timeIntervalSinceNow > -60 { return "Just now" }
        return date.formatted(.relative(presentation: .named, unitsStyle: .abbreviated))
    }
}

/// A change the agent wants the traveler to approve.
struct AgentAlert: Identifiable, Hashable, Codable {
    var id = UUID()
    let tripID: UUID
    let headline: String
    let message: String
    let newFlight: Flight
    let benefit: String
}
