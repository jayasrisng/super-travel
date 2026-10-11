import Foundation

/// Events streamed from the concierge while it works on a request.
enum AgentEvent {
    case plan([AgentStep])
    case update(stepID: Int, state: AgentStep.State, detail: String?)
    /// The agent pauses on this step until `answer(_:)` is called.
    case ask(stepID: Int, question: AgentQuestion)
    case message(String)
    case proposal(Trip)
    /// The request wasn't a trip after all; remove the planning card.
    case discardPlan
}

/// The planning brain behind the Concierge tab.
///
/// `WonderConciergeAgent` asks Gemini to read the request and tailor the trip, then
/// runs the booking steps on-device. In production the Gemini call and the bookings
/// (GDS, hotel channel managers, ground transport, payments) belong on Wonder's
/// backend, so no model or supplier keys ship inside the app.
protocol ConciergeAgent {
    func respond(to request: String) -> AsyncStream<AgentEvent>
    /// Resumes planning after an `.ask` event.
    func answer(_ yes: Bool)
    /// Forgets the conversation (new chat).
    func reset()
}

struct TravelBrief {
    var destination: Destination
    var travelers: Int
    var nights: Int
    var business: Bool
    var start: Date
}

final class WonderConciergeAgent: ConciergeAgent {
    private var lastBrief: TravelBrief?
    private var pendingAnswer: CheckedContinuation<Bool, Never>?
    private let planner: GeminiPlanner?
    private let profile: () -> UserProfile

    init(planner: GeminiPlanner? = GeminiPlanner(), profile: @escaping () -> UserProfile) {
        self.planner = planner
        self.profile = profile
    }

    var usesGemini: Bool { planner != nil }

    func reset() {
        lastBrief = nil
        planner?.reset()
    }

    /// Gemini when available; the on-device keyword reader if it isn't (no key, offline, error).
    private func interpret(_ request: String) async -> Interpretation {
        if let planner {
            do {
                return try await planner.interpret(request, profile: profile())
            } catch {
                print("Wonder: Gemini unavailable, planning on-device (\(error))")
            }
        }
        return .plan(TripPlan(
            brief: parse(request), stayIndex: 0, experiences: [], title: nil, summary: nil,
            reply: nil, tailoring: [], offerDinner: true
        ))
    }

    func answer(_ yes: Bool) {
        pendingAnswer?.resume(returning: yes)
        pendingAnswer = nil
    }

    /// Suspends planning until the traveler answers; cancelling planning counts as "no".
    private func waitForAnswer() async -> Bool {
        await withTaskCancellationHandler {
            await withCheckedContinuation { pendingAnswer = $0 }
        } onCancel: {
            Task { @MainActor in self.answer(false) }
        }
    }

    private static let stepTitles = [
        "Understanding your brief",
        "Searching flights",
        "Shortlisting stays",
        "Arranging transfers",
        "Curating experiences",
        "Reserving dinner",
        "Checking documents",
    ]

    func respond(to request: String) -> AsyncStream<AgentEvent> {
        AsyncStream { continuation in
            let task = Task {
                continuation.yield(.plan(Self.stepTitles.enumerated().map {
                    AgentStep(id: $0.offset, title: $0.element, detail: "", state: .pending)
                }))
                try? await Task.sleep(for: .milliseconds(300))
                continuation.yield(.update(stepID: 0, state: .running, detail: "Reading your request…"))

                switch await interpret(request) {
                case .reply(let text):
                    continuation.yield(.discardPlan)
                    continuation.yield(.message(text))
                case .plan(let plan):
                    lastBrief = plan.brief
                    await run(plan, continuation: continuation)
                }
                continuation.finish()
            }
            continuation.onTermination = { _ in task.cancel() }
        }
    }

    /// Works through the booking steps for a plan, pausing for the dinner question.
    private func run(_ plan: TripPlan, continuation: AsyncStream<AgentEvent>.Continuation) async {
        let brief = plan.brief
        let d = brief.destination
        let draft = TripPlanner.makeTrip(
            destination: d, start: brief.start, nights: brief.nights, travelers: brief.travelers,
            business: brief.business, status: .proposal, stayIndex: plan.stayIndex, experiences: plan.experiences
        )
        let dinner = d.dinner
        let routings = 600 + (d.name.count * 97) % 900
        let carriers = 5 + d.name.count % 6
        let planned = draft.components.first { $0.kind == .experiences }?.status ?? "4 planned"
        let people = brief.travelers == 1 ? "1 traveler" : "\(brief.travelers) travelers"
        let party = brief.travelers == 1 ? "one" : brief.travelers > 6 ? "\(brief.travelers) — a private room" : "\(brief.travelers)"
        let firstNight = brief.start.formatted(.dateTime.weekday(.wide))

        let experienceLine: String
        if plan.experiences.isEmpty {
            experienceLine = "\(planned.prefix(1).uppercased() + planned.dropFirst()), timed to the season"
        } else {
            let names = plan.experiences.prefix(2).map(\.title).joined(separator: ", ")
            experienceLine = plan.experiences.count > 2 ? "\(names) +\(plan.experiences.count - 2) more" : names
        }
        let details: [Int: String] = [
            0: plan.summary ?? "\(people) · \(brief.nights) nights · from \(draft.flight.fromCity)",
            1: "Compared \(routings.formatted()) routings across \(carriers) carriers",
            2: "Holding \(draft.stay.name) · \(draft.stay.note)",
            3: "Private driver from \(d.airport), meet and greet",
            4: experienceLine,
            6: d.country == "United States" ? "IDs verified · domestic travel" : "Passports valid · no visa required",
        ]
        let question = AgentQuestion(
            prompt: "Shall I book \(dinner.name) for your first night?",
            note: "\(dinner.cuisine) · \(firstNight) \(dinner.time) · table for \(party). I’ll call them for you using Dial.",
            yes: "Yes, call",
            no: "No thanks"
        )

        var reservation: Reservation?
        for index in Self.stepTitles.indices {
            if index > 0 {
                try? await Task.sleep(for: .milliseconds(350))
                if Task.isCancelled { return }
                continuation.yield(.update(stepID: index, state: .running, detail: nil))
            }

            if index == 5 {
                guard plan.offerDinner else {
                    try? await Task.sleep(for: .milliseconds(500))
                    continuation.yield(.update(stepID: index, state: .skipped, detail: "Not needed this time"))
                    continue
                }
                try? await Task.sleep(for: .milliseconds(700))
                continuation.yield(.ask(stepID: index, question: question))
                // Planning waits here for the traveler.
                if await waitForAnswer() {
                    reservation = await callRestaurant(dinner, guests: brief.travelers, step: index, continuation: continuation)
                } else {
                    try? await Task.sleep(for: .milliseconds(400))
                    continuation.yield(.update(stepID: index, state: .skipped, detail: "Skipped · I’ll keep your first evening open"))
                }
                continue
            }

            try? await Task.sleep(for: .milliseconds(index == 0 ? 400 : index == 1 ? 1300 : 750))
            continuation.yield(.update(stepID: index, state: .done, detail: details[index]))
        }

        let trip = TripPlanner.makeTrip(
            destination: d, start: brief.start, nights: brief.nights, travelers: brief.travelers,
            business: brief.business, status: .proposal, stayIndex: plan.stayIndex, title: plan.title,
            reservation: reservation, experiences: plan.experiences,
            tailoring: plan.tailoring.isEmpty ? nil : plan.tailoring
        )

        let dinnerLine = reservation.map { " Dinner at \($0.restaurant.name) is booked for your first night." } ?? ""
        let reply: String
        if let written = plan.reply {
            reply = written + dinnerLine
        } else if brief.business {
            reply = "Here’s the plan for your team. \(trip.stay.name) for \(brief.nights) nights, a private salon for working sessions, group transfers, and one consolidated invoice to your company account.\(dinnerLine) Everything else is on hold until Friday."
        } else {
            reply = "I’ve found something I think you’ll love: \(trip.stay.name) in \(trip.stay.location.components(separatedBy: ",")[0]), with flights, transfers and \(planned.replacingOccurrences(of: " planned", with: "")) experiences arranged around it.\(dinnerLine) It’s all on hold until Friday; approve and I’ll confirm everything."
        }

        try? await Task.sleep(for: .milliseconds(500))
        continuation.yield(.message(reply))
        try? await Task.sleep(for: .milliseconds(400))
        continuation.yield(.proposal(trip))
    }

    /// Phones the restaurant through Dial and reports each stage of the call.
    /// Scripted here; a production build hands this to Wonder's calling service.
    private func callRestaurant(
        _ restaurant: Restaurant,
        guests: Int,
        step: Int,
        continuation: AsyncStream<AgentEvent>.Continuation
    ) async -> Reservation {
        let stages = [
            "Dialing \(restaurant.name) via Dial…",
            "Connected · asking for a table for \(guests) at \(restaurant.time)",
            "They have it · confirming your name and allergies",
        ]
        for stage in stages {
            continuation.yield(.update(stepID: step, state: .running, detail: stage))
            try? await Task.sleep(for: .milliseconds(1_100))
        }
        let reference = "WD-\(Int.random(in: 1000...9999))"
        continuation.yield(.update(stepID: step, state: .done, detail: "\(restaurant.name) · table for \(guests) at \(restaurant.time) · Ref \(reference)"))
        return Reservation(restaurant: restaurant, guests: guests, day: 1, reference: reference)
    }

    // MARK: - Brief parsing

    private let keywords: [(String, [String])] = [
        ("zermatt", ["ski", "snow", "zermatt", "switzerland", "swiss", "matterhorn", "christmas"]),
        ("kyoto", ["japan", "kyoto", "tokyo", "cherry", "sakura", "tea"]),
        ("santorini", ["greece", "greek", "santorini", "aegean", "mykonos"]),
        ("maldives", ["maldives", "overwater", "honeymoon", "warm", "lagoon", "diving", "snorkel"]),
        ("dolomites", ["dolomites", "hike", "hiking", "mountain"]),
        ("paris", ["paris", "france", "fashion", "louvre", "art"]),
        ("iceland", ["iceland", "aurora", "northern lights", "glacier"]),
        ("bali", ["bali", "ubud", "jungle", "yoga", "wellness", "retreat"]),
        ("dubai", ["dubai", "desert", "uae", "abu dhabi", "roadshow"]),
        ("seychelles", ["seychelles", "family island", "private island", "turtle"]),
        ("como", ["como", "lake", "bellagio", "lakes"]),
        ("newyork", ["new york", "nyc", "manhattan", "broadway", "brooklyn", "big apple"]),
        ("sanfrancisco", ["san francisco", "sf", "bay area", "golden gate", "napa"]),
        ("chicago", ["chicago", "windy city"]),
        ("amalfi", ["amalfi", "italy", "italian", "positano", "ravello", "capri", "sea", "coast", "quiet"]),
    ]

    private let numberWords: [String: Int] = [
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
        "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "fourteen": 14, "twenty": 20,
    ]

    func parse(_ raw: String) -> TravelBrief {
        let text = raw.lowercased()
        let words = Set(tokens(text))
        func has(_ w: String) -> Bool {
            w.contains(" ") ? text.contains(w) : (words.contains(w) || words.contains(w + "s"))
        }

        let matched = keywords.first { _, list in list.contains(where: has) }
        let destination = matched.flatMap { Catalog.destination(id: $0.0) }
            ?? lastBrief?.destination
            ?? Catalog.amalfi

        var travelers = lastBrief?.travelers ?? 2
        if let n = number(in: text, before: ["people", "guests", "travelers", "travellers", "executives", "of us", "adults", "colleagues", "partners"])
            ?? number(in: text, after: ["family of", "party of", "team of", "group of", "for"]) {
            travelers = n
        } else if ["solo", "myself", "just me"].contains(where: has) {
            travelers = 1
        } else if ["couple", "honeymoon", "anniversary", "my wife", "my husband", "my partner"].contains(where: has) {
            travelers = 2
        }

        var nights = lastBrief?.nights ?? 7
        if let n = number(in: text, before: ["nights", "night"]) {
            nights = n
        } else if let n = number(in: text, before: ["days", "day"]) {
            nights = max(1, n - 1)
        } else if text.contains("fortnight") || text.contains("two weeks") {
            nights = 14
        } else if text.contains("long weekend") {
            nights = 4
        } else if text.contains("weekend") {
            nights = 3
        } else if text.contains("week") {
            nights = 7
        }

        let businessWords = ["offsite", "off-site", "board", "team", "company", "conference", "roadshow", "clients", "executives", "colleagues", "business"]
        let business = businessWords.contains(where: has) || (lastBrief?.business ?? false && matched == nil)

        return TravelBrief(
            destination: destination,
            travelers: min(max(travelers, 1), 40),
            nights: min(max(nights, 2), 21),
            business: business,
            start: startDate(in: text) ?? (matched == nil ? lastBrief?.start : nil) ?? Self.seasonalStart(for: destination)
        )
    }

    private func tokens(_ text: String) -> [String] {
        text.components(separatedBy: CharacterSet.alphanumerics.inverted).filter { !$0.isEmpty }
    }

    private func value(_ token: String) -> Int? {
        Int(token) ?? numberWords[token]
    }

    /// Finds "<n> <noun>", e.g. "12 guests".
    private func number(in text: String, before nouns: [String]) -> Int? {
        let t = tokens(text)
        for (i, token) in t.enumerated() where i + 1 < t.count {
            guard let n = value(token) else { continue }
            let rest = t[(i + 1)...].prefix(2).joined(separator: " ")
            if nouns.contains(where: { rest.hasPrefix($0) }) { return n }
        }
        return nil
    }

    /// Finds "<phrase> <n>", e.g. "family of 4".
    private func number(in text: String, after phrases: [String]) -> Int? {
        for phrase in phrases {
            guard let range = text.range(of: phrase + " ") else { continue }
            let following = tokens(String(text[range.upperBound...]))
            guard let first = following.first, let n = value(first) else { continue }
            let unit = following.dropFirst().first ?? ""
            if !["night", "nights", "day", "days", "week", "weeks"].contains(unit) { return n }
        }
        return nil
    }

    /// Month each destination is at its best, so open-ended requests land in season.
    private static let peakMonth: [String: Int] = [
        "newyork": 12, "sanfrancisco": 9, "chicago": 6, "como": 5, "amalfi": 6, "santorini": 6, "kyoto": 4, "zermatt": 2, "maldives": 2, "dolomites": 7,
        "paris": 5, "iceland": 2, "bali": 7, "dubai": 1, "seychelles": 4,
    ]

    static func seasonalStart(for destination: Destination) -> Date {
        let cal = Calendar.current
        let soonest = cal.date(byAdding: .day, value: 30, to: .now)!
        guard let month = peakMonth[destination.id] else { return soonest }
        var year = cal.component(.year, from: .now)
        while true {
            if let date = cal.date(from: DateComponents(year: year, month: month, day: 12)), date >= soonest {
                return date
            }
            year += 1
        }
    }

    private func startDate(in text: String) -> Date? {
        let months = Calendar.current.monthSymbols.map { $0.lowercased() }
        guard let index = months.firstIndex(where: { text.contains($0) }) else { return nil }
        let now = Calendar.current.dateComponents([.year, .month], from: .now)
        let month = index + 1
        let year = (now.month ?? 1) >= month ? (now.year ?? 2026) + 1 : (now.year ?? 2026)
        return Calendar.current.date(from: DateComponents(year: year, month: month, day: 12))
    }
}
