import Foundation
import ActivityKit
import AppIntents

/// The Lock Screen / Dynamic Island card: the agent's pick, plus category buttons.
nonisolated struct NearbyActivityAttributes: ActivityAttributes {
    struct ContentState: Codable, Hashable {
        var category: NearbyCategory
        var pick: NearbyPick?
        var locality: String?
        var updated: Date
    }
}

nonisolated extension Notification.Name {
    /// Posted (in the app process) when the Live Activity switches category.
    static let nearbyCategoryChanged = Notification.Name("WonderNearbyCategoryChanged")
}

nonisolated enum NearbyLiveActivity {
    static var current: Activity<NearbyActivityAttributes>? {
        Activity<NearbyActivityAttributes>.activities.first { $0.activityState == .active || $0.activityState == .stale }
    }

    static var isRunning: Bool { current != nil }

    /// Starts the card, or updates it if one is already showing. Call from the foreground app.
    @discardableResult
    static func show(_ state: NearbyActivityAttributes.ContentState) async -> Bool {
        if let activity = current {
            await activity.update(ActivityContent(state: state, staleDate: nil, relevanceScore: 80))
            return true
        }
        guard ActivityAuthorizationInfo().areActivitiesEnabled else { return false }
        do {
            _ = try Activity.request(
                attributes: NearbyActivityAttributes(),
                content: ActivityContent(state: state, staleDate: nil, relevanceScore: 80)
            )
            return true
        } catch {
            return false
        }
    }

    static func end() async {
        for activity in Activity<NearbyActivityAttributes>.activities {
            await activity.end(nil, dismissalPolicy: .immediate)
        }
    }

    /// Re-runs the search for `category` around the current location and updates the card.
    static func switchCategory(to category: NearbyCategory) async {
        guard let activity = current else { return }
        var state = activity.content.state
        state.category = category
        // Show the selection immediately; the new pick follows when the search returns.
        await activity.update(ActivityContent(state: state, staleDate: nil, relevanceScore: 80))

        if let location = await CurrentLocation.fetch() {
            let result = await NearbyFinder.search(near: location, category: category, limit: 1)
            state.pick = result.top
            state.locality = result.locality ?? state.locality
        } else {
            state.pick = nil
        }
        state.updated = .now
        await activity.update(ActivityContent(state: state, staleDate: nil, relevanceScore: 80))
        NotificationCenter.default.post(name: .nearbyCategoryChanged, object: nil, userInfo: ["category": category.rawValue])
    }
}

/// Category buttons on the Live Activity. Runs in the app's process.
struct NearbyLiveCategoryIntent: LiveActivityIntent {
    static let title: LocalizedStringResource = "Show nearby category"
    static let isDiscoverable = false

    @Parameter(title: "Category")
    var category: NearbyCategory

    init() {}

    init(category: NearbyCategory) {
        self.category = category
    }

    func perform() async throws -> some IntentResult {
        await NearbyLiveActivity.switchCategory(to: category)
        return .result()
    }
}
