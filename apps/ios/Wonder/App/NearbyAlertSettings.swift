import Foundation

/// How "found something nearby" updates reach the user.
enum AlertChannel: String, CaseIterable, Identifiable {
    case push, text
    var id: String { rawValue }
    var title: String { self == .push ? "Notification" : "Text message" }
}

/// Settings for location-based updates. Stored on device only.
@Observable
final class NearbyAlertSettings {
    static let shared = NearbyAlertSettings()

    /// Seconds between new suggestions; 0 turns auto-refresh off.
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
        // The number comes from the git-ignored Secrets.xcconfig, never from source.
        let fallback = Bundle.main.object(forInfoDictionaryKey: "DefaultAlertPhone") as? String ?? ""
        phone = defaults.string(forKey: "alerts.phone") ?? fallback
        intervalSeconds = defaults.object(forKey: "alerts.interval") as? Int ?? 300
    }

    /// E.164 for US numbers, or nil if the entry isn't a valid number.
    var e164Phone: String? {
        let digits = phone.filter(\.isNumber)
        if digits.count == 10 { return "+1" + digits }
        if digits.count == 11, digits.hasPrefix("1") { return "+" + digits }
        return nil
    }

    var relayURL: URL? {
        guard let raw = Bundle.main.object(forInfoDictionaryKey: "SMSRelayURL") as? String,
              !raw.isEmpty else { return nil }
        return URL(string: raw)
    }
}

/// iOS apps cannot send SMS on their own, so texts go through a small relay
/// (for example a Twilio function) that takes `{"to": "+1…", "body": "…"}`.
enum NearbyTexter {
    static func send(_ body: String) async -> Bool {
        let settings = NearbyAlertSettings.shared
        guard let url = settings.relayURL, let to = settings.e164Phone else { return false }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try? JSONSerialization.data(withJSONObject: ["to": to, "body": body])
        guard let (_, response) = try? await URLSession.shared.data(for: request) else { return false }
        return (response as? HTTPURLResponse).map { (200..<300).contains($0.statusCode) } ?? false
    }
}
