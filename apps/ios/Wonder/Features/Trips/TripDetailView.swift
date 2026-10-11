import SwiftUI

struct TripDetailView: View {
    @Environment(WonderStore.self) private var store
    @Environment(\.dismiss) private var dismiss

    let tripID: UUID
    var proposal: Trip? = nil

    @State private var expandedDay: Int? = 1
    @State private var approved = false

    private var trip: Trip? { store.trip(id: tripID) ?? proposal }
    private var isSheet: Bool { proposal != nil }

    var body: some View {
        Group {
            if let trip {
                content(trip)
            } else {
                Text("This journey is no longer available.")
                    .foregroundStyle(Color.textSoft)
            }
        }
        .background { Backdrop(photo: trip?.destination.hero ?? Pic.wing, veil: 0.4) }
        .navigationBarTitleDisplayMode(.inline)
        .toolbarBackground(.hidden, for: .navigationBar)
        .toolbar {
            if isSheet {
                ToolbarItem(placement: .topBarLeading) {
                    Button { dismiss() } label: { Image(systemName: "xmark") }
                        .tint(Color.ink)
                }
            }
        }
        .sensoryFeedback(.success, trigger: approved)
        .toolbar(.hidden, for: .tabBar)
    }

    private func content(_ trip: Trip) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                summaryCard(trip)
                    .padding(.top, 230)

                SectionHeader(title: "Getting there", eyebrow: "Flight").padding(.horizontal, -20)
                BoardingPass(flight: trip.flight)

                SectionHeader(title: "Day by day", eyebrow: "Itinerary").padding(.horizontal, -20)
                itinerary(trip)

                SectionHeader(title: "Where you’ll be", eyebrow: trip.stay.location).padding(.horizontal, -20)
                SatelliteMap(coordinate: trip.destination.coordinate, title: trip.destination.name, distance: 9_000)
                    .frame(height: 260)
                    .clipShape(.rect(cornerRadius: 22))

                details(trip).padding(.top, 24)
            }
            .padding(.horizontal, 18)
            .padding(.bottom, 24)
        }
        .safeAreaInset(edge: .bottom) { actionBar(trip) }
    }

    /// The white glass card from the brand board: title, stay and booking status in one place.
    private func summaryCard(_ trip: Trip) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            Eyebrow(trip.isBusiness ? "\(trip.destination.country) · Business" : trip.destination.country, color: .textSoft)
            Text(trip.title)
                .font(WFont.display(32))
                .foregroundStyle(Color.ink)
                .padding(.top, 8)
            Text("\(Fmt.dateRange(trip.startDate, nights: trip.nights)) · \(trip.nights) nights · \(trip.travelers) \(trip.travelers == 1 ? "guest" : "guests")")
                .font(WFont.body(14))
                .foregroundStyle(Color.textSoft)
                .padding(.top, 4)

            if let notes = trip.tailoring, !notes.isEmpty {
                TailoringNotes(notes: notes)
                    .padding(.top, 14)
            }

            Photo(id: trip.stay.photo, width: 1200)
                .frame(height: 180)
                .clipShape(.rect(cornerRadius: 16))
                .padding(.top, 18)

            HStack {
                VStack(alignment: .leading, spacing: 3) {
                    Text(trip.stay.name)
                        .font(WFont.display(19))
                        .foregroundStyle(Color.ink)
                    Text("\(trip.stay.location) · \(trip.stay.note)")
                        .font(WFont.body(13))
                        .foregroundStyle(Color.textSoft)
                        .lineLimit(1)
                }
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundStyle(Color.textSoft)
            }
            .padding(.vertical, 14)

            Hairline()
            components(trip)
        }
        .padding(20)
        .glassPanel(cornerRadius: 30)
    }

    private func components(_ trip: Trip) -> some View {
        VStack(spacing: 0) {
            ForEach(Array(trip.components.enumerated()), id: \.element.id) { index, c in
                HStack(spacing: 14) {
                    Image(systemName: c.icon)
                        .font(.system(size: 14))
                        .foregroundStyle(Color.ink)
                        .frame(width: 34, height: 34)
                        .background(Color.well, in: .circle)
                    Text(c.title)
                        .font(WFont.body(15))
                        .foregroundStyle(Color.ink)
                    Spacer()
                    StatusLabel(text: c.status, complete: c.isComplete, size: 13)
                    Image(systemName: "chevron.right")
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundStyle(Color.textSoft.opacity(0.5))
                }
                .padding(.vertical, 11)
                if index < trip.components.count - 1 {
                    Hairline().padding(.leading, 48)
                }
            }
        }
    }

    private func itinerary(_ trip: Trip) -> some View {
        VStack(spacing: 10) {
            ForEach(trip.days) { day in
                let open = expandedDay == day.day
                VStack(alignment: .leading, spacing: 0) {
                    Button {
                        withAnimation(.spring(duration: 0.4)) { expandedDay = open ? nil : day.day }
                    } label: {
                        HStack(spacing: 14) {
                            VStack(spacing: 0) {
                                Text("DAY").font(.system(size: 8, weight: .semibold)).tracking(1.5)
                                Text("\(day.day)").font(WFont.display(18))
                            }
                            .foregroundStyle(SolidInk(inverse: open))
                            .frame(width: 44, height: 44)
                            .background(open ? AnyShapeStyle(.solidInk) : AnyShapeStyle(Color.well), in: .rect(cornerRadius: 12))
                            VStack(alignment: .leading, spacing: 2) {
                                Text(day.title)
                                    .font(WFont.body(15, weight: .medium))
                                    .foregroundStyle(Color.ink)
                                    .multilineTextAlignment(.leading)
                                Text(dayDate(trip, day.day))
                                    .font(WFont.body(12))
                                    .foregroundStyle(Color.textSoft)
                            }
                            Spacer()
                            Image(systemName: "chevron.down")
                                .font(.system(size: 11, weight: .semibold))
                                .foregroundStyle(Color.textSoft)
                                .rotationEffect(.degrees(open ? 180 : 0))
                        }
                        .padding(12)
                        .contentShape(.rect)
                    }
                    .buttonStyle(.plain)

                    if open {
                        VStack(alignment: .leading, spacing: 0) {
                            ForEach(day.items) { item in
                                HStack(alignment: .top, spacing: 14) {
                                    Text(item.time)
                                        .font(WFont.mono(11))
                                        .foregroundStyle(Color.textSoft)
                                        .frame(width: 44, alignment: .leading)
                                        .padding(.top, 2)
                                    Image(systemName: item.icon)
                                        .font(.system(size: 12))
                                        .foregroundStyle(Color.ink)
                                        .frame(width: 16)
                                        .padding(.top, 2)
                                    VStack(alignment: .leading, spacing: 2) {
                                        Text(item.title)
                                            .font(WFont.body(14, weight: .medium))
                                            .foregroundStyle(Color.ink)
                                        Text(item.detail)
                                            .font(WFont.body(12))
                                            .foregroundStyle(Color.textSoft)
                                    }
                                    Spacer(minLength: 0)
                                }
                                .padding(.vertical, 9)
                            }
                        }
                        .padding(.horizontal, 16)
                        .padding(.bottom, 10)
                        .transition(.opacity.combined(with: .move(edge: .top)))
                    }
                }
                .glassPanel(cornerRadius: 18)
            }
        }
    }

    private func dayDate(_ trip: Trip, _ day: Int) -> String {
        let date = Calendar.current.date(byAdding: .day, value: day - 1, to: trip.startDate) ?? trip.startDate
        return date.formatted(.dateTime.weekday(.wide).month(.abbreviated).day())
    }

    private func details(_ trip: Trip) -> some View {
        VStack(spacing: 0) {
            detailRow("person.text.rectangle", "Travel documents", "Verified for \(trip.travelers)")
            Hairline().padding(.leading, 50)
            detailRow("shield.lefthalf.filled", "Travel protection", "Included")
            Hairline().padding(.leading, 50)
            detailRow("clock.arrow.circlepath", "Planning time saved", "\(trip.hoursSaved) hours")
            if trip.isBusiness {
                Hairline().padding(.leading, 50)
                detailRow("building.2", "Invoiced to", store.company)
            }
        }
        .glassPanel(cornerRadius: 20)
    }

    private func detailRow(_ icon: String, _ title: String, _ value: String) -> some View {
        HStack(spacing: 14) {
            Image(systemName: icon)
                .font(.system(size: 14))
                .foregroundStyle(Color.ink)
                .frame(width: 22)
            Text(title).font(WFont.body(14)).foregroundStyle(Color.ink)
            Spacer()
            Text(value).font(WFont.body(13)).foregroundStyle(Color.textSoft)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 14)
    }

    @ViewBuilder
    private func actionBar(_ trip: Trip) -> some View {
        VStack(spacing: 0) {
            if trip.status == .proposal {
                Button {
                    store.approve(trip)
                    approved = true
                    Task {
                        try? await Task.sleep(for: .milliseconds(450))
                        dismiss()
                    }
                } label: {
                    HStack {
                        Text("Approve & book")
                        Text("·").opacity(0.5)
                        Text(Fmt.money(trip.total))
                    }
                }
                .buttonStyle(PrimaryButtonStyle())
                Text("Held until Friday · free cancellation for 48 hours")
                    .font(WFont.body(11))
                    .foregroundStyle(Color.textSoft)
                    .padding(.top, 6)
            } else if trip.status == .confirmed {
                Button {
                    store.selectedTab = .concierge
                    if isSheet { dismiss() }
                } label: {
                    HStack(spacing: 8) {
                        Text("Ask your concierge")
                        Image(systemName: "arrow.right").font(.system(size: 12, weight: .semibold))
                    }
                }
                .buttonStyle(PrimaryButtonStyle())
            } else {
                Button {
                    store.ask("Plan something like \(trip.title) in \(trip.destination.name) again, \(trip.nights) nights for \(trip.travelers)")
                } label: {
                    Text("Plan it again")
                }
                .buttonStyle(PrimaryButtonStyle())
            }
        }
        .padding(10)
        .padding(.bottom, trip.status == .proposal ? 4 : 0)
        .glassPanel(cornerRadius: 34)
        .padding(.horizontal, 14)
        .padding(.bottom, 4)
    }
}

/// Boarding-pass style flight summary.
struct BoardingPass: View {
    let flight: Flight
    var compact = false

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Text(flight.carrier.uppercased())
                    .font(.system(size: 10, weight: .semibold))
                    .tracking(2)
                Spacer()
                Text("\(flight.number) · \(flight.cabin)")
                    .font(WFont.mono(10))
            }
            .foregroundStyle(Color.ink)

            HStack(alignment: .center) {
                airport(flight.fromCode, flight.fromCity, flight.departs, alignment: .leading)
                Spacer()
                VStack(spacing: 6) {
                    HStack(spacing: 4) {
                        Circle().frame(width: 4, height: 4)
                        Rectangle().frame(height: 0.5)
                        Image(systemName: "airplane").font(.system(size: 13))
                        Rectangle().frame(height: 0.5)
                        Circle().frame(width: 4, height: 4)
                    }
                    .foregroundStyle(Color.ink.opacity(0.6))
                    Text(flight.duration)
                        .font(WFont.mono(10))
                        .foregroundStyle(Color.ink.opacity(0.6))
                }
                .frame(maxWidth: 110)
                Spacer()
                airport(flight.toCode, flight.toCity, flight.arrives, alignment: .trailing)
            }
            .padding(.top, compact ? 14 : 20)

            if !compact {
                DashedLine()
                    .stroke(Color.ink.opacity(0.2), style: StrokeStyle(lineWidth: 1, dash: [4, 4]))
                    .frame(height: 1)
                    .padding(.vertical, 18)
                HStack {
                    passField("Seat", flight.seat)
                    Spacer()
                    passField("Lounge", "Access")
                    Spacer()
                    passField("Routing", flight.stops, trailing: true)
                }
            } else {
                Text(flight.stops)
                    .font(WFont.body(11))
                    .foregroundStyle(Color.ink.opacity(0.6))
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.top, 12)
            }
        }
        .padding(20)
        .background(.black, in: .rect(cornerRadius: 22))
        .environment(\.colorScheme, .dark)
    }

    private func airport(_ code: String, _ city: String, _ time: String, alignment: HorizontalAlignment) -> some View {
        VStack(alignment: alignment, spacing: 2) {
            Text(code).font(WFont.display(compact ? 28 : 34)).foregroundStyle(Color.ink)
            Text(city).font(WFont.body(11)).foregroundStyle(Color.ink.opacity(0.6))
            Text(time).font(WFont.mono(12)).foregroundStyle(Color.ink).padding(.top, 4)
        }
    }

    private func passField(_ label: String, _ value: String, trailing: Bool = false) -> some View {
        VStack(alignment: trailing ? .trailing : .leading, spacing: 4) {
            Text(label.uppercased()).font(.system(size: 8.5, weight: .semibold)).tracking(1.6).foregroundStyle(Color.ink.opacity(0.5))
            Text(value).font(WFont.body(12, weight: .medium)).foregroundStyle(Color.ink)
                .lineLimit(2)
                .multilineTextAlignment(trailing ? .trailing : .leading)
                .frame(maxWidth: 150, alignment: trailing ? .trailing : .leading)
        }
    }
}

struct DashedLine: Shape {
    func path(in rect: CGRect) -> Path {
        var p = Path()
        p.move(to: CGPoint(x: 0, y: rect.midY))
        p.addLine(to: CGPoint(x: rect.width, y: rect.midY))
        return p
    }
}
