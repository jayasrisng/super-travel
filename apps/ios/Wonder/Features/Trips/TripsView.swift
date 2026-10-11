import SwiftUI

struct TripsView: View {
    @Environment(WonderStore.self) private var store
    @State private var reviewing: AgentAlert?

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 0) {
                    VStack(alignment: .leading, spacing: 0) {
                        header

                        ForEach(store.alerts) { alert in
                            AlertCard(alert: alert) { reviewing = alert }
                                .padding(.horizontal, 20)
                                .padding(.top, 20)
                                .transition(.move(edge: .top).combined(with: .opacity))
                        }

                        Spacer(minLength: 24)

                        if let next = store.upcomingTrips.first {
                            NavigationLink(value: next.id) { NextTripCard(trip: next) }
                                .buttonStyle(PressableStyle())
                                .padding(.horizontal, 20)
                        }
                    }
                    .containerRelativeFrame(.vertical) { height, _ in height - 24 }

                    if store.upcomingTrips.count > 1 {
                        SectionHeader(title: "Ahead")
                        VStack(spacing: 12) {
                            ForEach(store.upcomingTrips.dropFirst()) { trip in
                                NavigationLink(value: trip.id) { TripRow(trip: trip) }
                                    .buttonStyle(PressableStyle())
                            }
                        }
                        .padding(.horizontal, 20)
                    }

                    SectionHeader(title: "What your agent did", eyebrow: "Concierge log")
                    ActivityLog(items: store.activity)
                        .padding(.horizontal, 20)

                    if !store.pastTrips.isEmpty {
                        SectionHeader(title: "Remembered", eyebrow: "Past journeys")
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 14) {
                                ForEach(store.pastTrips) { trip in
                                    NavigationLink(value: trip.id) { PastTripTile(trip: trip) }
                                        .buttonStyle(PressableStyle())
                                }
                            }
                            .padding(.horizontal, 20)
                        }
                        .scrollClipDisabled()
                    }
                }
                .padding(.bottom, 40)
            }
            .statusBarScrim(.black.opacity(0.25))
            .background { Backdrop(photo: store.upcomingTrips.first?.destination.hero ?? Pic.wing, veil: 0.4) }
            .toolbar(.hidden, for: .navigationBar)
            .navigationDestination(for: UUID.self) { id in
                TripDetailView(tripID: id)
            }
            .sheet(item: $reviewing) { alert in
                FlightChangeSheet(alert: alert)
                    .presentationDetents([.large])
                    .presentationCornerRadius(32)
            }
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 8) {
            WonderLogo(height: 22)
            Text("Journeys")
                .font(WFont.display(40))
                .foregroundStyle(Color.ink)
                .padding(.top, 18)
            HStack(spacing: 10) {
                Label("\(store.upcomingTrips.count) ahead", systemImage: "suitcase")
                Text("·")
                Label("\(store.hoursSaved) hours saved", systemImage: "clock.arrow.circlepath")
            }
            .font(WFont.body(13))
            .foregroundStyle(Color.textSoft)
        }
        .legible()
        .padding(.horizontal, 24)
        .padding(.top, 8)
    }
}

struct AlertCard: View {
    let alert: AgentAlert
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 14) {
                MonogramTile(size: 42)
                VStack(alignment: .leading, spacing: 3) {
                    Text(alert.headline)
                        .font(WFont.body(15, weight: .medium))
                        .foregroundStyle(Color.ink)
                    Text("Review your new flight option.")
                        .font(WFont.body(13))
                        .foregroundStyle(Color.textSoft)
                }
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundStyle(Color.textSoft)
            }
            .padding(14)
            .glassPanel(cornerRadius: 20)
        }
        .buttonStyle(PressableStyle())
    }
}

/// Glass caption for the next journey, shown over that place's photograph.
struct NextTripCard: View {
    let trip: Trip

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack(alignment: .top) {
                Eyebrow("Next up · \(trip.destination.country)", color: .textSoft)
                Spacer()
                VStack(alignment: .trailing, spacing: 0) {
                    Text("\(max(trip.daysUntil, 0))")
                        .font(WFont.display(30))
                        .foregroundStyle(Color.ink)
                    Text("DAYS")
                        .font(.system(size: 8.5, weight: .semibold))
                        .tracking(1.6)
                        .foregroundStyle(Color.textSoft)
                }
            }
            Text(trip.title)
                .font(WFont.display(30))
                .foregroundStyle(Color.ink)
                .padding(.top, -6)
            Text("\(Fmt.dateRange(trip.startDate, nights: trip.nights)) · \(trip.nights) nights · \(trip.travelers) guests")
                .font(WFont.body(13))
                .foregroundStyle(Color.textSoft)
                .padding(.top, 4)

            Hairline().padding(.vertical, 16)

            HStack(spacing: 0) {
                ForEach(trip.components) { c in
                    VStack(spacing: 6) {
                        Image(systemName: c.isComplete ? "checkmark.circle.fill" : c.icon)
                            .font(.system(size: 14))
                            .foregroundStyle(c.isComplete ? Color.verified : Color.ink)
                        Text(c.status)
                            .font(WFont.body(10.5, weight: c.isComplete ? .semibold : .medium))
                            .foregroundStyle(c.isComplete ? Color.verified : Color.textSoft)
                            .lineLimit(1)
                    }
                    .frame(maxWidth: .infinity)
                }
            }
        }
        .padding(20)
        .glassPanel(cornerRadius: 28)
    }
}

struct TripRow: View {
    let trip: Trip

    var body: some View {
        HStack(spacing: 14) {
            Photo(id: trip.destination.hero, width: 400)
                .frame(width: 76, height: 76)
                .clipShape(.rect(cornerRadius: 14))
            VStack(alignment: .leading, spacing: 4) {
                Eyebrow(trip.isBusiness ? "\(trip.destination.country) · Business" : trip.destination.country, color: .textSoft, size: 9)
                Text(trip.title)
                    .font(WFont.display(18))
                    .foregroundStyle(Color.ink)
                Text("\(Fmt.dateRange(trip.startDate, nights: trip.nights)) · \(trip.travelers) guests")
                    .font(WFont.body(12))
                    .foregroundStyle(Color.textSoft)
            }
            Spacer()
            Image(systemName: "chevron.right")
                .font(.system(size: 12, weight: .semibold))
                .foregroundStyle(Color.textSoft.opacity(0.6))
        }
        .padding(10)
        .glassPanel(cornerRadius: 20)
    }
}

struct PastTripTile: View {
    let trip: Trip

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Photo(id: trip.destination.hero, width: 600)
                .frame(width: 180, height: 130)
                .clipShape(.rect(cornerRadius: 18))
            Text(trip.title)
                .font(WFont.display(16))
                .foregroundStyle(Color.ink)
            Text(trip.startDate.formatted(.dateTime.month(.wide).year()))
                .font(WFont.body(12))
                .foregroundStyle(Color.textSoft)
        }
        .frame(width: 180, alignment: .leading)
    }
}

struct ActivityLog: View {
    let items: [AgentActivity]

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            ForEach(Array(items.prefix(5).enumerated()), id: \.element.id) { index, item in
                HStack(alignment: .top, spacing: 14) {
                    VStack(spacing: 0) {
                        let done = item.icon.hasPrefix("checkmark")
                        Image(systemName: item.icon)
                            .font(.system(size: 12, weight: .medium))
                            .foregroundStyle(done ? Color.verified : Color.ink)
                            .frame(width: 30, height: 30)
                            .background(done ? Color.verified.opacity(0.14) : Color.well, in: .circle)
                        if index < min(items.count, 5) - 1 {
                            Rectangle().fill(Color.ink.opacity(0.18)).frame(width: 1).frame(maxHeight: .infinity)
                        }
                    }
                    VStack(alignment: .leading, spacing: 3) {
                        HStack {
                            Text(item.title)
                                .font(WFont.body(14, weight: .medium))
                                .foregroundStyle(Color.ink)
                            Spacer()
                            Text(item.time)
                                .font(WFont.body(11))
                                .foregroundStyle(Color.textSoft)
                        }
                        Text(item.detail)
                            .font(WFont.body(12))
                            .foregroundStyle(Color.textSoft)
                    }
                    .padding(.bottom, 18)
                }
            }
        }
        .padding(18)
        .glassPanel(cornerRadius: 22)
    }
}

struct FlightChangeSheet: View {
    @Environment(WonderStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    let alert: AgentAlert

    var body: some View {
        let current = store.trip(id: alert.tripID)?.flight
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                MonogramTile(size: 46)
                Text(alert.headline)
                    .font(WFont.display(30))
                    .foregroundStyle(Color.ink)
                    .padding(.top, 18)
                Text(alert.message)
                    .font(WFont.body(15))
                    .foregroundStyle(Color.textSoft)
                    .lineSpacing(3)
                    .padding(.top, 8)

                if let current {
                    Eyebrow("Current", color: .textSoft)
                        .padding(.top, 28)
                        .padding(.bottom, 10)
                    BoardingPass(flight: current, compact: true)
                        .opacity(0.6)
                }
                Eyebrow("Proposed", color: .ink)
                    .padding(.top, 20)
                    .padding(.bottom, 10)
                BoardingPass(flight: alert.newFlight, compact: true)

                Label(alert.benefit, systemImage: "sparkles")
                    .font(WFont.body(14, weight: .medium))
                    .foregroundStyle(Color.ink)
                    .padding(.top, 16)

                Button {
                    store.accept(alert)
                    dismiss()
                } label: {
                    Text("Switch my flight")
                }
                .buttonStyle(PrimaryButtonStyle())
                .padding(.top, 28)

                Button {
                    store.dismiss(alert)
                    dismiss()
                } label: {
                    Text("Keep current flight")
                        .font(WFont.body(14))
                        .foregroundStyle(Color.textSoft)
                        .frame(maxWidth: .infinity)
                        .frame(height: 44)
                }
                .padding(.top, 6)
            }
            .padding(22)
            .glassPanel(cornerRadius: 32)
            .padding(.horizontal, 14)
            .padding(.top, 150)
            .padding(.bottom, 24)
        }
        .background { Backdrop(photo: Pic.wing, veil: 0.35) }
        .presentationBackground(.clear)
        .preferredColorScheme(.dark)
    }
}
