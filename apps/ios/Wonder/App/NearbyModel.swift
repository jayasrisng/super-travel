import SwiftUI
import CoreLocation
import WidgetKit

/// Live-location recommendations: drives the in-app card, the Lock Screen Live Activity
/// and the "found something nearby" notification.
@Observable
final class NearbyModel {
    static let shared = NearbyModel()

    enum Status: Equatable { case idle, locating, searching, ready, empty, needsPermission, denied }

    var status: Status = .idle
    var category: NearbyCategory = .food
    var result: NearbyResult?
    var isOnLockScreen = NearbyLiveActivity.isRunning

    private var location: CLLocation?
    private var session: CLServiceSession?
    private var observer: NSObjectProtocol?

    private init() {
        // The Lock Screen buttons switch category from an intent; keep the app in step.
        observer = NotificationCenter.default.addObserver(forName: .nearbyCategoryChanged, object: nil, queue: .main) { note in
            guard let raw = note.userInfo?["category"] as? String,
                  let category = NearbyCategory(rawValue: raw) else { return }
            MainActor.assumeIsolated {
                NearbyModel.shared.category = category
                Task { await NearbyModel.shared.refresh(updateLiveActivity: false) }
            }
        }
    }

    var top: NearbyPick? { result?.top }

    var liveState: NearbyActivityAttributes.ContentState {
        .init(category: category, pick: top, locality: result?.locality, updated: .now)
    }

    /// Asks for location (once) and runs the first search.
    func start() async {
        guard status == .idle || status == .needsPermission else { return }
        let auth = CLLocationManager().authorizationStatus
        if auth == .denied || auth == .restricted {
            status = .denied
            return
        }
        session = CLServiceSession(authorization: .whenInUse)
        status = .locating
        location = await CurrentLocation.fetch(timeout: .seconds(15))
        guard location != nil else {
            let auth = CLLocationManager().authorizationStatus
            status = (auth == .denied || auth == .restricted) ? .denied : .needsPermission
            return
        }
        await refresh()
    }

    func select(_ category: NearbyCategory) {
        guard category != self.category || status == .empty else { return }
        self.category = category
        Task { await refresh() }
    }

    func refresh(updateLiveActivity: Bool = true) async {
        if location == nil { location = await CurrentLocation.fetch() }
        guard let location else { return }
        SharedLocation.save(location)
        status = .searching
        let found = await NearbyFinder.search(near: location, category: category, limit: 4)
        result = found
        status = found.picks.isEmpty ? .empty : .ready
        WidgetCenter.shared.reloadTimelines(ofKind: "WonderNearby")
        if updateLiveActivity, NearbyLiveActivity.isRunning {
            await NearbyLiveActivity.show(liveState)
        }
    }

    /// Pins the pick to the Lock Screen and sends the notification.
    func showOnLockScreen() async {
        isOnLockScreen = await NearbyLiveActivity.show(liveState)
        if let top {
            await NearbyNotifier.shared.notify(pick: top, locality: result?.locality, delay: 4)
        }
    }

    func removeFromLockScreen() async {
        await NearbyLiveActivity.end()
        isOnLockScreen = false
    }

    /// A category tapped on the notification: find that kind of place and notify again.
    func handleNotificationAction(_ category: NearbyCategory) async {
        self.category = category
        await refresh()
        if let top {
            await NearbyNotifier.shared.notify(pick: top, locality: result?.locality, delay: 1)
        }
    }
}
