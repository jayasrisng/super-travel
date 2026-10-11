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
    private var autoTask: Task<Void, Never>?
    private var lastDelivered: String?

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

    /// (Re)starts the timer that fetches new suggestions every N seconds. Runs while the app
    /// is alive; iOS suspends it in the background.
    func configureAutoRefresh() {
        autoTask?.cancel()
        autoTask = nil
        let seconds = NearbyAlertSettings.shared.intervalSeconds
        guard seconds > 0 else { return }
        autoTask = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(seconds))
                if Task.isCancelled { break }
                await self?.tick()
            }
        }
    }

    private func tick() async {
        if status == .idle || status == .needsPermission { await start() }
        guard status != .denied, status != .locating, status != .searching else { return }
        if let fresh = await CurrentLocation.fetch(timeout: .seconds(10)) { location = fresh }
        await refresh()
        guard NearbyAlertSettings.shared.alertsEnabled, let top, top.id != lastDelivered else { return }
        await deliver(top)
    }

    /// Sends the pick over the channel the user chose; a failed text falls back to a notification.
    func deliver(_ pick: NearbyPick) async {
        lastDelivered = pick.id
        let settings = NearbyAlertSettings.shared
        if settings.channel == .text {
            let place = result?.locality.map { " in \($0)" } ?? ""
            let body = "Wonder found something nearby\(place): \(pick.name) · \(pick.walkText). \(pick.note)"
            if await NearbyTexter.send(body) { return }
        }
        await NearbyNotifier.shared.notify(pick: pick, locality: result?.locality, delay: 1)
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
