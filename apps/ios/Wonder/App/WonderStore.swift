import SwiftUI

enum AppTab: Hashable {
    case discover, concierge, trips, profile
}

enum AgentAutonomy: String, CaseIterable, Identifiable, Codable {
    case ask = "Ask me first"
    case withinPreferences = "Within my preferences"
    case full = "Full autonomy"

    var id: String { rawValue }

    var detail: String {
        switch self {
        case .ask: "Wonder proposes; nothing is booked without your approval."
        case .withinPreferences: "Books and rebooks freely within your budget and preferences."
        case .full: "Handles everything end to end. You’ll get a summary."
        }
    }
}

@Observable
final class WonderStore {
    // Saved to profile.json
    var profile: UserProfile {
        didSet { if profile != oldValue { scheduleSave(profile: true) } }
    }

    // Saved to trips.json
    var trips: [Trip] { didSet { scheduleSave(trips: true) } }
    var alerts: [AgentAlert] { didSet { scheduleSave(trips: true) } }
    var activity: [AgentActivity] { didSet { scheduleSave(trips: true) } }

    // Session
    var selectedTab: AppTab = .discover
    /// Bumped when a widget or the Lock Screen asks to show the nearby card.
    var nearbyFocusRequests = 0

    // Concierge conversation
    var messages: [ChatMessage] = []
    var isAgentWorking = false
    var presentedTrip: Trip?

    @ObservationIgnored private lazy var agent: ConciergeAgent = WonderConciergeAgent { [unowned self] in self.profile }
    private var pendingSave: Task<Void, Never>?
    private var saveProfile = false
    private var saveTrips = false

    init() {
        if let saved = Persistence.load(UserProfile.self, from: Persistence.profileFile) {
            profile = saved
        } else {
            var fresh = UserProfile.sample
            // Carry over onboarding from before profiles were stored as JSON.
            fresh.hasOnboarded = UserDefaults.standard.bool(forKey: "hasOnboarded")
            profile = fresh
            Persistence.save(fresh, to: Persistence.profileFile)
        }

        if let saved = Persistence.load(TripsFile.self, from: Persistence.tripsFile) {
            trips = saved.trips
            alerts = saved.alerts
            activity = saved.activity
        } else {
            let seed = SampleData.trips
            trips = seed
            alerts = Self.makeAlerts(for: seed)
            activity = SampleData.activity
            Persistence.save(TripsFile(trips: trips, alerts: alerts, activity: activity), to: Persistence.tripsFile)
        }
    }

    // MARK: - Profile shortcuts (bindable from views)

    var hasOnboarded: Bool {
        get { profile.hasOnboarded }
        set { profile.hasOnboarded = newValue }
    }
    var travelStyles: Set<String> {
        get { Set(profile.travelStyles) }
        set { profile.travelStyles = newValue.sorted() }
    }
    var memberName: String { profile.firstName }
    var memberFullName: String { profile.fullName }
    var company: String { profile.company }
    var autonomy: AgentAutonomy {
        get { profile.autonomy }
        set { profile.autonomy = newValue }
    }
    var spendingLimit: Double {
        get { profile.spendingLimit }
        set { profile.spendingLimit = newValue }
    }
    var proactiveRebooking: Bool {
        get { profile.proactiveRebooking }
        set { profile.proactiveRebooking = newValue }
    }
    var upgradeWatch: Bool {
        get { profile.upgradeWatch }
        set { profile.upgradeWatch = newValue }
    }
    var quietHours: Bool {
        get { profile.quietHours }
        set { profile.quietHours = newValue }
    }
    var cabin: String {
        get { profile.cabin }
        set { profile.cabin = newValue }
    }
    var seat: String {
        get { profile.seat }
        set { profile.seat = newValue }
    }

    // MARK: - Saving

    /// Coalesces bursts of changes (a slider drag, an approval) into one write per file.
    private func scheduleSave(profile: Bool = false, trips: Bool = false) {
        saveProfile = saveProfile || profile
        saveTrips = saveTrips || trips
        pendingSave?.cancel()
        pendingSave = Task {
            try? await Task.sleep(for: .milliseconds(400))
            guard !Task.isCancelled else { return }
            saveNow()
        }
    }

    /// Writes pending changes immediately (also called when the app leaves the foreground).
    func saveNow() {
        pendingSave?.cancel()
        if saveProfile {
            Persistence.save(profile, to: Persistence.profileFile)
            saveProfile = false
        }
        if saveTrips {
            Persistence.save(TripsFile(trips: trips, alerts: alerts, activity: activity), to: Persistence.tripsFile)
            saveTrips = false
        }
    }

    private static func makeAlerts(for trips: [Trip]) -> [AgentAlert] {
        if let italy = trips.first(where: { $0.title == "Your Italian escape" }) {
            var better = italy.flight
            better.number = "AZ 611"
            better.departs = "21:05"
            better.arrives = "10:15"
            better.duration = "7h 10m"
            better.stops = "Nonstop"
            return [AgentAlert(
                tripID: italy.id,
                headline: "A better connection, found.",
                message: "A new nonstop to Naples opened in Business. Same seat, no connection in Rome.",
                newFlight: better,
                benefit: "Saves 1h 40m · no change fee"
            )]
        }
        return []
    }

    var upcomingTrips: [Trip] {
        trips.filter { $0.status == .confirmed }.sorted { $0.startDate < $1.startDate }
    }

    var pastTrips: [Trip] {
        trips.filter { $0.status == .completed }.sorted { $0.startDate > $1.startDate }
    }

    var hoursSaved: Int { trips.reduce(0) { $0 + $1.hoursSaved } }

    // MARK: - Concierge

    func ask(_ text: String) {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty, !isAgentWorking else { return }
        selectedTab = .concierge
        messages.append(ChatMessage(kind: .user(trimmed)))
        isAgentWorking = true

        Task {
            var workID: UUID?
            for await event in agent.respond(to: trimmed) {
                withAnimation(.spring(duration: 0.45)) {
                    switch event {
                    case .plan(let steps):
                        let message = ChatMessage(kind: .work(steps))
                        workID = message.id
                        messages.append(message)
                    case .update(let stepID, let state, let detail):
                        updateStep(stepID, in: workID) { step in
                            step.state = state
                            step.question = nil
                            if let detail { step.detail = detail }
                        }
                    case .ask(let stepID, let question):
                        updateStep(stepID, in: workID) { step in
                            step.state = .waiting
                            step.question = question
                        }
                    case .message(let text):
                        messages.append(ChatMessage(kind: .agent(text)))
                    case .proposal(let trip):
                        messages.append(ChatMessage(kind: .proposal(trip)))
                    case .discardPlan:
                        messages.removeAll { $0.id == workID }
                        workID = nil
                    }
                }
            }
            isAgentWorking = false
        }
    }

    private func updateStep(_ stepID: Int, in workID: UUID?, _ change: (inout AgentStep) -> Void) {
        guard let workID, let i = messages.firstIndex(where: { $0.id == workID }),
              case .work(var steps) = messages[i].kind,
              let s = steps.firstIndex(where: { $0.id == stepID }) else { return }
        change(&steps[s])
        messages[i].kind = .work(steps)
    }

    /// The traveler's yes/no to the agent's waiting question.
    func answer(_ yes: Bool, step stepID: Int, in workID: UUID) {
        withAnimation(.spring(duration: 0.4)) {
            updateStep(stepID, in: workID) { step in
                step.question = nil
                step.state = .running
                step.detail = yes ? "Calling now…" : "No problem"
            }
        }
        agent.answer(yes)
    }

    func approve(_ proposal: Trip) {
        var trip = proposal
        trip.status = .confirmed
        if trips.contains(where: { $0.id != trip.id && $0.title == trip.title }) {
            trip.title = "\(trip.destination.name) · \(trip.startDate.formatted(.dateTime.month(.wide).year()))"
        }
        trip.components = trip.components.map { c in
            var c = c
            if c.kind != .experiences { c.status = "Confirmed" }
            return c
        }
        withAnimation(.spring(duration: 0.5)) {
            trips.removeAll { $0.id == trip.id }
            trips.append(trip)
            for i in messages.indices {
                if case .proposal(let p) = messages[i].kind, p.id == trip.id {
                    messages[i].kind = .proposal(trip)
                }
            }
            messages.append(ChatMessage(kind: .confirmation(trip)))
            activity.insert(AgentActivity(
                icon: "checkmark.seal",
                title: "Booked \(trip.title.lowercased().hasPrefix("your") ? trip.destination.name : trip.title)",
                detail: "\(trip.components.count) suppliers confirmed · \(Fmt.money(trip.total))",
                date: .now
            ), at: 0)
        }
    }

    func trip(id: UUID) -> Trip? { trips.first { $0.id == id } }

    /// Starts a fresh conversation with the concierge.
    func newConversation() {
        guard !isAgentWorking else { return }
        withAnimation(.spring(duration: 0.4)) { messages.removeAll() }
        agent.reset()
    }

    // MARK: - Agent alerts

    func accept(_ alert: AgentAlert) {
        guard let i = trips.firstIndex(where: { $0.id == alert.tripID }) else { return }
        withAnimation(.spring(duration: 0.5)) {
            trips[i].flight = alert.newFlight
            alerts.removeAll { $0.id == alert.id }
            activity.insert(AgentActivity(
                icon: "airplane",
                title: "Switched to \(alert.newFlight.carrier) \(alert.newFlight.number)",
                detail: alert.benefit,
                date: .now
            ), at: 0)
        }
    }

    func dismiss(_ alert: AgentAlert) {
        withAnimation(.spring(duration: 0.4)) { alerts.removeAll { $0.id == alert.id } }
    }

    /// Starts over from the sample member and journeys, rewriting both JSON files.
    func resetDemo() {
        trips = SampleData.trips
        alerts = Self.makeAlerts(for: trips)
        activity = SampleData.activity
        messages = []
        profile = .sample
        selectedTab = .discover
        saveNow()
    }
}
