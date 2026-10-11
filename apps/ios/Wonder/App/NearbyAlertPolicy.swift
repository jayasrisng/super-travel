import Foundation

/// Pure consent and formatting rules shared by the UI and refresh loop.
nonisolated enum NearbyAlertPolicy {
    static let allowedIntervals = [0, 30, 60, 300, 900]

    static func canRefresh(enabled: Bool, interval: Int, foreground: Bool) -> Bool {
        enabled && foreground && interval > 0 && allowedIntervals.contains(interval)
    }

    static func phone(_ raw: String) -> String? {
        let value = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        let formatting = CharacterSet(charactersIn: "0123456789+()- .")
        guard value.unicodeScalars.allSatisfy({ formatting.contains($0) }) else { return nil }
        let digits = value.filter { $0 >= "0" && $0 <= "9" }
        if value.hasPrefix("+") {
            guard value.filter({ $0 == "+" }).count == 1,
                  (8...15).contains(digits.count), digits.first != "0" else { return nil }
            return "+" + digits
        }
        guard !value.contains("+") else { return nil }
        if digits.count == 10, let first = digits.first, first >= "2" { return "+1" + digits }
        if digits.count == 11, digits.hasPrefix("1") { return "+" + digits }
        return nil
    }
}

/// Only successful notification scheduling counts as delivery; failures remain retryable.
nonisolated struct NearbyDeliveryLedger {
    private(set) var lastDelivered: String?
    func shouldDeliver(_ identifier: String) -> Bool { identifier != lastDelivered }
    mutating func record(_ identifier: String, succeeded: Bool) {
        if succeeded { lastDelivered = identifier }
    }
}
