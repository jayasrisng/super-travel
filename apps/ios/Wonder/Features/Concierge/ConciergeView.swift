import SwiftUI

struct ConciergeView: View {
    @Environment(WonderStore.self) private var store
    @State private var draft = ""
    @FocusState private var focused: Bool

    private let suggestions: [(String, String)] = [
        ("water.waves", "A quiet week by the sea"),
        ("snowflake", "Ski week in Zermatt for a family of 4"),
        ("briefcase", "Board offsite in Kyoto for 12 executives"),
        ("sun.max", "Somewhere warm in December, just the two of us"),
    ]

    private var greeting: String {
        let hour = Calendar.current.component(.hour, from: .now)
        let part = hour < 12 ? "morning" : hour < 18 ? "afternoon" : "evening"
        return "Good \(part), \(store.memberName)."
    }

    var body: some View {
        VStack(spacing: 0) {
            header
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 18) {
                        if store.messages.isEmpty {
                            emptyState
                        }
                        ForEach(store.messages) { message in
                            MessageView(message: message)
                                .id(message.id)
                                .transition(.asymmetric(insertion: .move(edge: .bottom).combined(with: .opacity), removal: .opacity))
                        }
                        Color.clear.frame(height: 1).id("bottom")
                    }
                    .padding(.horizontal, 20)
                    .padding(.top, 8)
                    .padding(.bottom, 16)
                }
                .scrollDismissesKeyboard(.interactively)
                .mask(
                    LinearGradient(stops: [.init(color: .clear, location: 0), .init(color: .black, location: 0.035)], startPoint: .top, endPoint: .bottom)
                )
                .onChange(of: store.messages.count) { scrollToBottom(proxy) }
                .onChange(of: workSignature) { scrollToBottom(proxy) }
                .onAppear { proxy.scrollTo("bottom") }
            }
        }
        .background(background)
        .safeAreaInset(edge: .bottom) { composer }
    }

    /// Changes whenever a planning step moves on or asks a question, to keep it in view.
    private var workSignature: Int {
        var hasher = Hasher()
        for message in store.messages {
            if case .work(let steps) = message.kind {
                for step in steps {
                    hasher.combine(step.state)
                    hasher.combine(step.question)
                }
            }
        }
        return hasher.finalize()
    }

    private func scrollToBottom(_ proxy: ScrollViewProxy) {
        withAnimation(.spring(duration: 0.5)) { proxy.scrollTo("bottom", anchor: .bottom) }
    }

    /// The backdrop follows the conversation: the latest place proposed, or the open sky.
    private var backdropPhoto: String {
        for message in store.messages.reversed() {
            switch message.kind {
            case .proposal(let trip), .confirmation(let trip): return trip.destination.hero
            default: continue
            }
        }
        return Pic.wing
    }

    private var background: some View {
        Backdrop(photo: backdropPhoto, veil: 0.55)
    }

    private var header: some View {
        HStack(spacing: 12) {
            AgentAvatar(size: 38, working: store.isAgentWorking)
            VStack(alignment: .leading, spacing: 2) {
                Text("Concierge")
                    .font(WFont.display(20))
                    .foregroundStyle(Color.ink)
                HStack(spacing: 6) {
                    Circle().fill(store.isAgentWorking ? AnyShapeStyle(Color.ink.opacity(0.5)) : AnyShapeStyle(Color.verified))
                        .frame(width: 6, height: 6)
                    Text(store.isAgentWorking ? "Working on it…" : "Your agent · always on")
                        .font(WFont.body(12))
                        .foregroundStyle(Color.ink.opacity(0.6))
                        .contentTransition(.opacity)
                }
            }
            Spacer()
            if !store.messages.isEmpty {
                Button {
                    store.newConversation()
                } label: {
                    Image(systemName: "square.and.pencil")
                        .font(.system(size: 15, weight: .medium))
                        .foregroundStyle(Color.ink)
                        .frame(width: 40, height: 40)
                        .glassCapsule()
                }
                .disabled(store.isAgentWorking)
            }
        }
        .padding(.horizontal, 20)
        .padding(.top, 6)
        .padding(.bottom, 10)
    }

    private var emptyState: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text(greeting)
                .font(WFont.display(34))
                .foregroundStyle(Color.ink)
                .legible()
                .padding(.top, 36)
            Text("Tell me where you’d like to wake up. I’ll find the flights, hold the suite, arrange the car and quietly watch over every detail.")
                .font(WFont.body(15))
                .foregroundStyle(Color.ink.opacity(0.85))
                .lineSpacing(4)
                .legible()
                .padding(.top, 14)

            Eyebrow("Try asking", color: .textSoft)
                .legible()
                .padding(.top, 36)
                .padding(.bottom, 12)

            VStack(spacing: 10) {
                ForEach(suggestions, id: \.1) { icon, text in
                    Button {
                        store.ask(text)
                    } label: {
                        HStack(spacing: 14) {
                            Image(systemName: icon)
                                .font(.system(size: 14))
                                .foregroundStyle(Color.ink)
                                .frame(width: 22)
                            Text(text)
                                .font(WFont.body(15))
                                .foregroundStyle(Color.ink)
                                .multilineTextAlignment(.leading)
                            Spacer(minLength: 0)
                            Image(systemName: "arrow.up.right")
                                .font(.system(size: 11, weight: .semibold))
                                .foregroundStyle(Color.ink.opacity(0.4))
                        }
                        .padding(.horizontal, 18)
                        .padding(.vertical, 16)
                        .glassPanel(cornerRadius: 18)
                    }
                    .buttonStyle(PressableStyle())
                }
            }

            HStack(spacing: 0) {
                ForEach(["Flights", "Stays", "Transfers", "Dining", "Visas", "Rebooking"], id: \.self) { item in
                    Text(item)
                        .font(WFont.body(11))
                        .foregroundStyle(Color.ink.opacity(0.45))
                    if item != "Rebooking" {
                        Text(" · ").font(WFont.body(11)).foregroundStyle(Color.ink.opacity(0.25))
                    }
                }
            }
            .frame(maxWidth: .infinity)
            .padding(.top, 28)
        }
    }

    private var composer: some View {
        HStack(alignment: .bottom, spacing: 10) {
            TextField(
                "",
                text: $draft,
                prompt: Text(store.isAgentWorking ? "Wonder is planning…" : "Where to next?").foregroundStyle(Color.ink.opacity(0.5)),
                axis: .vertical
            )
            .font(WFont.body(15))
            .foregroundStyle(Color.ink)
            .lineLimit(1...4)
            .focused($focused)
            .padding(.vertical, 15)
            .submitLabel(.send)
            .onSubmit(send)

            Button(action: send) {
                Image(systemName: "arrow.up")
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundStyle(.solidInkInverse)
                    .frame(width: 38, height: 38)
                    .background(.solidInk.opacity(canSend ? 1 : 0.3), in: .circle)
            }
            .disabled(!canSend)
            .padding(.bottom, 7)
        }
        .padding(.leading, 20)
        .padding(.trailing, 7)
        .glassPanel(cornerRadius: 26)
        .padding(.horizontal, 16)
        .padding(.bottom, 8)
    }

    private var canSend: Bool {
        !draft.trimmingCharacters(in: .whitespaces).isEmpty && !store.isAgentWorking
    }

    private func send() {
        guard canSend else { return }
        store.ask(draft)
        draft = ""
    }
}

// MARK: - Messages

struct AgentAvatar: View {
    var size: CGFloat = 28
    var working = false

    var body: some View {
        ZStack {
            Circle().fill(.solidInk)
            Text("W")
                .font(WFont.wordmark(size * 0.5))
                .foregroundStyle(.solidInkInverse)
            if working {
                SpinningArc(style: .ink)
                    .padding(-4)
            }
        }
        .frame(width: size, height: size)
    }
}

struct MessageView: View {
    let message: ChatMessage

    var body: some View {
        switch message.kind {
        case .user(let text):
            HStack {
                Spacer(minLength: 60)
                Text(text)
                    .font(WFont.body(15))
                    .foregroundStyle(Color.ink)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 12)
                    .glassPanel(cornerRadius: 20)
            }
            .padding(.top, 10)
        case .agent(let text):
            HStack(alignment: .top, spacing: 12) {
                AgentAvatar(size: 26)
                Text(text)
                    .font(WFont.display(16))
                    .foregroundStyle(Color.ink.opacity(0.92))
                    .lineSpacing(4)
                Spacer(minLength: 20)
            }
        case .work(let steps):
            WorkCard(steps: steps, messageID: message.id)
        case .proposal(let trip):
            ProposalCard(trip: trip)
        case .confirmation(let trip):
            ConfirmationCard(trip: trip)
        }
    }
}

struct WorkCard: View {
    @Environment(WonderStore.self) private var store
    let steps: [AgentStep]
    let messageID: UUID

    private var finished: Bool { steps.allSatisfy { $0.state == .done || $0.state == .skipped } }
    private var waiting: Bool { steps.contains { $0.state == .waiting } }
    private var completed: Int { steps.filter { $0.state == .done || $0.state == .skipped }.count }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack {
                Eyebrow(finished ? "Plan ready" : waiting ? "Waiting for you" : "Wonder is planning",
                        color: finished ? .verified : .ink, size: 9.5)
                    .contentTransition(.opacity)
                Spacer()
                Text("\(completed)/\(steps.count)")
                    .font(WFont.mono(10))
                    .foregroundStyle(finished ? Color.verified : Color.ink.opacity(0.5))
                    .contentTransition(.numericText())
            }
            .padding(.bottom, 14)

            ForEach(steps) { step in
                HStack(alignment: .top, spacing: 12) {
                    StepIcon(state: step.state)
                        .frame(width: 16, height: 16)
                        .padding(.top, 1)

                    VStack(alignment: .leading, spacing: 3) {
                        Text(step.title)
                            .font(WFont.body(14, weight: .medium))
                            .foregroundStyle(step.state == .pending ? Color.ink.opacity(0.35) : Color.ink)
                        if !step.detail.isEmpty {
                            Text(step.detail)
                                .font(WFont.body(12))
                                .foregroundStyle(Color.ink.opacity(0.55))
                                .contentTransition(.opacity)
                                .transition(.opacity)
                        }
                        if let question = step.question {
                            QuestionPanel(question: question) { yes in
                                store.answer(yes, step: step.id, in: messageID)
                            }
                            .padding(.top, 8)
                            .transition(.opacity.combined(with: .move(edge: .top)))
                        }
                    }
                    Spacer(minLength: 0)
                }
                .padding(.vertical, 7)
            }
        }
        .padding(18)
        .glassPanel(cornerRadius: 22)
    }
}

/// Status glyph for a planning step: green once it's complete.
struct StepIcon: View {
    let state: AgentStep.State

    var body: some View {
        switch state {
        case .pending:
            Circle().strokeBorder(Color.ink.opacity(0.25), lineWidth: 1)
        case .running:
            ProgressView().controlSize(.mini).tint(Color.ink)
        case .waiting:
            Image(systemName: "questionmark.circle.fill")
                .resizable()
                .foregroundStyle(.solidInk)
                .symbolEffect(.pulse, options: .repeating)
        case .done:
            Image(systemName: "checkmark.circle.fill")
                .resizable()
                .foregroundStyle(.white, Color.verified)
                .transition(.scale.combined(with: .opacity))
        case .skipped:
            Image(systemName: "minus.circle")
                .resizable()
                .foregroundStyle(Color.ink.opacity(0.35))
        }
    }
}

/// The agent's yes/no, shown inside the step it belongs to.
struct QuestionPanel: View {
    let question: AgentQuestion
    let onAnswer: (Bool) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(question.prompt)
                .font(WFont.display(17))
                .foregroundStyle(Color.ink)
            HStack(alignment: .top, spacing: 8) {
                Image(systemName: "phone.fill")
                    .font(.system(size: 11))
                    .padding(.top, 2)
                Text(question.note)
                    .font(WFont.body(12))
            }
            .foregroundStyle(Color.textSoft)

            HStack(spacing: 8) {
                Button { onAnswer(false) } label: {
                    Text(question.no)
                        .font(WFont.body(14, weight: .medium))
                        .foregroundStyle(Color.ink)
                        .frame(maxWidth: .infinity)
                        .frame(height: 42)
                        .background(Color.well, in: .capsule)
                }
                Button { onAnswer(true) } label: {
                    Label(question.yes, systemImage: "phone.arrow.up.right")
                        .font(WFont.body(14, weight: .medium))
                        .foregroundStyle(.white)
                        .frame(maxWidth: .infinity)
                        .frame(height: 42)
                        .background(Color.verified, in: .capsule)
                }
            }
            .buttonStyle(PressableStyle())
            .padding(.top, 2)
        }
        .padding(14)
        .background(Color.well, in: .rect(cornerRadius: 16))
    }
}

struct ProposalCard: View {
    @Environment(WonderStore.self) private var store
    let trip: Trip

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            ZStack(alignment: .bottomLeading) {
                Photo(id: trip.stay.photo, width: 1000)
                Scrim(strength: 0.8)
                VStack(alignment: .leading, spacing: 6) {
                    Eyebrow(trip.destination.country, color: .ink.opacity(0.85))
                    Text(trip.title)
                        .font(WFont.display(26))
                        .foregroundStyle(Color.ink)
                }
                .padding(18)
            }
            .frame(height: 200)
            .clipShape(.rect(cornerRadius: 18))
            .overlay(alignment: .topTrailing) {
                Label(trip.status == .confirmed ? "Confirmed" : "On hold · 72h", systemImage: trip.status == .confirmed ? "checkmark" : "clock")
                    .font(WFont.body(11, weight: .semibold))
                    .foregroundStyle(trip.status == .confirmed ? AnyShapeStyle(.white) : AnyShapeStyle(.solidInkInverse))
                    .padding(.horizontal, 10)
                    .frame(height: 26)
                    .background(trip.status == .confirmed ? AnyShapeStyle(Color.verified) : AnyShapeStyle(.solidInk), in: .capsule)
                    .padding(12)
            }
            // Type over the photograph stays white even though the card is light glass.
            .environment(\.colorScheme, .dark)
            .padding([.horizontal, .top], 10)

            VStack(alignment: .leading, spacing: 14) {
                HStack {
                    Text("\(Fmt.dateRange(trip.startDate, nights: trip.nights)) · \(trip.nights) nights · \(trip.travelers) \(trip.travelers == 1 ? "guest" : "guests")")
                        .font(WFont.body(13))
                        .foregroundStyle(Color.ink.opacity(0.7))
                }

                if let notes = trip.tailoring, !notes.isEmpty {
                    TailoringNotes(notes: notes)
                    Hairline()
                }

                VStack(spacing: 10) {
                    ForEach(trip.components) { c in
                        HStack(spacing: 12) {
                            Image(systemName: c.icon)
                                .font(.system(size: 13))
                                .foregroundStyle(Color.ink)
                                .frame(width: 20)
                            Text(componentLine(c))
                                .font(WFont.body(13))
                                .foregroundStyle(Color.ink)
                                .lineLimit(1)
                            Spacer()
                            StatusLabel(text: c.status, complete: c.isComplete)
                        }
                    }
                }

                Hairline(color: .ink.opacity(0.1))

                HStack(alignment: .firstTextBaseline) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(Fmt.money(trip.total))
                            .font(WFont.display(22))
                            .foregroundStyle(Color.ink)
                        Text("all-inclusive · \(trip.hoursSaved)h of planning saved")
                            .font(WFont.body(11))
                            .foregroundStyle(Color.ink.opacity(0.5))
                    }
                    Spacer()
                    Button {
                        store.presentedTrip = trip
                    } label: {
                        HStack(spacing: 6) {
                            Text("Review trip")
                            Image(systemName: "arrow.right").font(.system(size: 11, weight: .semibold))
                        }
                        .font(WFont.body(14, weight: .medium))
                        .foregroundStyle(.solidInkInverse)
                        .padding(.horizontal, 18)
                        .frame(height: 42)
                        .background(.solidInk, in: .capsule)
                    }
                    .buttonStyle(PressableStyle())
                }
            }
            .padding(18)
        }
        .glassPanel(cornerRadius: 24)
        .clipShape(.rect(cornerRadius: 24))
    }

    private func componentLine(_ c: TripComponent) -> String {
        switch c.kind {
        case .flights: "\(trip.flight.carrier) · \(trip.flight.cabin)"
        case .stay: trip.stay.name
        case .transfers: "Private driver · \(trip.destination.airport)"
        case .experiences: trip.destination.experiences.first?.title ?? "Experiences"
        case .dining: trip.reservation.map { "\($0.restaurant.name) · \($0.restaurant.time)" } ?? "Dining"
        }
    }
}

struct ConfirmationCard: View {
    @Environment(WonderStore.self) private var store
    let trip: Trip
    @State private var appeared = false

    var body: some View {
        VStack(spacing: 14) {
            Image(systemName: "checkmark.seal.fill")
                .font(.system(size: 34))
                .symbolRenderingMode(.palette)
                .foregroundStyle(.white, Color.verified)
                .symbolEffect(.bounce, value: appeared)
            Text("Confirmed. Bon voyage.")
                .font(WFont.display(22))
                .foregroundStyle(Color.ink)
            Text("Every booking is confirmed with \(trip.components.count) suppliers. Boarding passes, daily plans and your driver’s details will appear in Journeys — I’ll keep watching for anything better.")
                .font(WFont.body(13))
                .foregroundStyle(Color.ink.opacity(0.65))
                .multilineTextAlignment(.center)
                .lineSpacing(3)
            Button {
                store.selectedTab = .trips
            } label: {
                Text("View in Journeys")
                    .font(WFont.body(14, weight: .medium))
                    .foregroundStyle(.solidInkInverse)
                    .padding(.horizontal, 20)
                    .frame(height: 42)
                    .background(.solidInk, in: .capsule)
            }
            .padding(.top, 4)
        }
        .padding(24)
        .frame(maxWidth: .infinity)
        .glassPanel(cornerRadius: 24)
        .onAppear { appeared = true }
    }
}
