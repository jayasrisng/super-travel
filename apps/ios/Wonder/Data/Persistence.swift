import Foundation

/// Everything Wonder knows about the member.
struct UserProfile: Codable, Equatable {
    var firstName: String
    var fullName: String
    var company: String
    var memberSince: Int
    var hasOnboarded: Bool
    var travelStyles: [String]

    // Agent preferences
    var autonomy: AgentAutonomy
    var spendingLimit: Double
    var proactiveRebooking: Bool
    var upgradeWatch: Bool
    var quietHours: Bool

    // Learned preferences
    var cabin: String
    var seat: String
    var hotelStyle: String
    var dining: String
    var loyalty: [String]

    static let sample = UserProfile(
        firstName: "Alexandra",
        fullName: "Alexandra Mercer",
        company: "Mercer Capital",
        memberSince: 2024,
        hasOnboarded: false,
        travelStyles: ["Slow & restorative", "Culture & cuisine"],
        autonomy: .withinPreferences,
        spendingLimit: 40_000,
        proactiveRebooking: true,
        upgradeWatch: true,
        quietHours: true,
        cabin: "First",
        seat: "Window",
        hotelStyle: "Small, quiet, with a view",
        dining: "Pescatarian · no shellfish",
        loyalty: ["Aman", "Delta Diamond", "Star Gold"]
    )
}

/// The member's journeys, plus what the agent has done and wants to do about them.
struct TripsFile: Codable {
    var trips: [Trip]
    var alerts: [AgentAlert]
    var activity: [AgentActivity]
}

/// Reads and writes Wonder's JSON files in the app's Documents folder
/// (visible in Files › On My iPhone › Wonder).
enum Persistence {
    static let profileFile = "profile.json"
    static let tripsFile = "trips.json"

    static var directory: URL {
        URL.documentsDirectory
    }

    static func url(_ name: String) -> URL {
        directory.appending(path: name)
    }

    private static let encoder: JSONEncoder = {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]
        encoder.dateEncodingStrategy = .iso8601
        return encoder
    }()

    private static let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }()

    static func load<T: Decodable>(_ type: T.Type, from name: String) -> T? {
        guard let data = try? Data(contentsOf: url(name)) else { return nil }
        do {
            return try decoder.decode(type, from: data)
        } catch {
            // Keep the unreadable file for inspection rather than silently overwriting it.
            let backup = url(name + ".unreadable")
            try? FileManager.default.removeItem(at: backup)
            try? FileManager.default.moveItem(at: url(name), to: backup)
            print("Wonder: couldn’t read \(name): \(error)")
            return nil
        }
    }

    static func save<T: Encodable>(_ value: T, to name: String) {
        do {
            let data = try encoder.encode(value)
            try data.write(to: url(name), options: [.atomic, .completeFileProtection])
        } catch {
            print("Wonder: couldn’t save \(name): \(error)")
        }
    }

    static func delete(_ name: String) {
        try? FileManager.default.removeItem(at: url(name))
    }
}
