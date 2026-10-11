import Foundation
import Observation

/// Text delivery opens the system composer; the user must tap Send.
enum AlertChannel: String, CaseIterable, Identifiable {
    case push, text
    var id: String { rawValue }
    var title: String { self == .push ? "Notification" : "Text draft" }
}

@Observable
final class NearbyAlertSettings {
    static let shared = NearbyAlertSettings()
    static let intervals: [(label: String, seconds: Int)] = [
        ("30 sec", 30), ("1 min", 60), ("5 min", 300), ("15 min", 900), ("Off", 0)
    ]
    var alertsEnabled: Bool { didSet { defaults.set(alertsEnabled, forKey: "alerts.enabled") } }
    var channel: AlertChannel { didSet { defaults.set(channel.rawValue, forKey: "alerts.channel") } }
    var phone: String { didSet { defaults.set(phone, forKey: "alerts.phone") } }
    var intervalSeconds: Int { didSet { defaults.set(intervalSeconds, forKey: "alerts.interval") } }
    private let defaults = UserDefaults.standard

    private init() {
        alertsEnabled = defaults.bool(forKey: "alerts.enabled")
        channel = AlertChannel(rawValue: defaults.string(forKey: "alerts.channel") ?? "") ?? .push
        phone = defaults.string(forKey: "alerts.phone") ?? ""
        let saved = defaults.object(forKey: "alerts.interval") as? Int ?? 300
        intervalSeconds = NearbyAlertPolicy.allowedIntervals.contains(saved) ? saved : 0
    }
    var e164Phone: String? { NearbyAlertPolicy.phone(phone) }
}
