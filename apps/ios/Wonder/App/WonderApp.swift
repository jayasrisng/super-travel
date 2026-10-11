import SwiftUI

@main
struct WonderApp: App {
    @UIApplicationDelegateAdaptor private var appDelegate: AppDelegate
    @State private var store = WonderStore()
    @Environment(\.scenePhase) private var scenePhase

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(store)
                .onOpenURL { url in
                    // Widgets and the Live Activity link to wonder://nearby.
                    guard url.scheme == "wonder", url.host == "nearby" else { return }
                    store.selectedTab = .discover
                    store.nearbyFocusRequests += 1
                }
        }
        .onChange(of: scenePhase) { _, phase in
            if phase != .active { store.saveNow() }
        }
    }
}

final class AppDelegate: NSObject, UIApplicationDelegate {
    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil) -> Bool {
        // Set up before any notification action is delivered, including background launches.
        NearbyNotifier.shared.configure()
        return true
    }
}

struct RootView: View {
    @Environment(WonderStore.self) private var store

    var body: some View {
        ZStack {
            if store.hasOnboarded {
                MainTabView()
                    .transition(.opacity)
            } else {
                OnboardingView()
                    .transition(.opacity)
            }
        }
        .animation(.easeInOut(duration: 0.6), value: store.hasOnboarded)
        .onAppear {
            NearbyModel.shared.configureAutoRefresh()
            ImagePipeline.shared.prefetch(Catalog.all.map(\.hero))
        }
    }
}

struct MainTabView: View {
    @Environment(WonderStore.self) private var store

    var body: some View {
        @Bindable var store = store
        TabView(selection: $store.selectedTab) {
            Tab("Discover", systemImage: "globe.europe.africa", value: AppTab.discover) {
                DiscoverView()
            }
            Tab("Concierge", systemImage: "sparkles", value: AppTab.concierge) {
                ConciergeView()
            }
            Tab("Journeys", systemImage: "suitcase", value: AppTab.trips) {
                TripsView()
            }
            .badge(store.alerts.count)
            Tab("Profile", systemImage: "person.crop.circle", value: AppTab.profile) {
                ProfileView()
            }
        }
        .tint(.ink)
        .preferredColorScheme(.dark)
        .sheet(item: $store.presentedTrip) { trip in
            NavigationStack {
                TripDetailView(tripID: trip.id, proposal: trip)
            }
            .preferredColorScheme(.dark)
        }
    }
}
