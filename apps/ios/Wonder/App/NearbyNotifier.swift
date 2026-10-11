import UserNotifications

/// "Your agent found something nearby": the pick as the notification, with
/// Food · Social · Hospitality · Shop as actions on it.
final class NearbyNotifier: NSObject, UNUserNotificationCenterDelegate {
    static let shared = NearbyNotifier()
    static let categoryID = "WONDER_NEARBY"

    func configure() {
        let center = UNUserNotificationCenter.current()
        center.delegate = self
        let actions = NearbyCategory.allCases.map { category in
            UNNotificationAction(
                identifier: category.rawValue,
                title: category.title,
                options: [],
                icon: UNNotificationActionIcon(systemImageName: category.symbol)
            )
        }
        center.setNotificationCategories([
            UNNotificationCategory(identifier: Self.categoryID, actions: actions, intentIdentifiers: [])
        ])
    }

    @discardableResult
    func notify(pick: NearbyPick, locality: String?, delay: TimeInterval, identifier: String = "nearby") async -> Bool {
        let center = UNUserNotificationCenter.current()
        guard (try? await center.requestAuthorization(options: [.alert, .sound])) == true else { return false }

        guard !Task.isCancelled else { return false }
        let content = UNMutableNotificationContent()
        content.title = "Your agent found something nearby"
        content.subtitle = [pick.name, pick.walkText].joined(separator: " · ")
        content.body = pick.note
        content.categoryIdentifier = Self.categoryID
        content.threadIdentifier = "nearby"
        content.relevanceScore = 0.8
        if let locality { content.targetContentIdentifier = locality }

        let trigger = UNTimeIntervalNotificationTrigger(timeInterval: max(delay, 1), repeats: false)
        do {
            try await center.add(UNNotificationRequest(identifier: identifier, content: content, trigger: trigger))
            guard !Task.isCancelled else {
                center.removePendingNotificationRequests(withIdentifiers: [identifier])
                return false
            }
            return true
        } catch { return false }
    }

    func cancelAutomaticRequests() {
        UNUserNotificationCenter.current().removePendingNotificationRequests(withIdentifiers: ["nearby-auto"])
    }

    nonisolated func userNotificationCenter(_ center: UNUserNotificationCenter, didReceive response: UNNotificationResponse) async {
        guard let category = NearbyCategory(rawValue: response.actionIdentifier) else { return }
        await NearbyModel.shared.handleNotificationAction(category)
    }

    nonisolated func userNotificationCenter(_ center: UNUserNotificationCenter, willPresent notification: UNNotification) async -> UNNotificationPresentationOptions {
        [.banner, .list, .sound]
    }
}
