import Foundation

/// Composes a complete, bookable trip from a destination and a brief.
enum TripPlanner {
    private struct Route {
        let carrier: String
        let number: String
        let cabin: String
        let departs: String
        let arrives: String
        let duration: String
        let stops: String
        /// Where the member flies from; New York unless the trip is to New York itself.
        var fromCode = "JFK"
        var fromCity = "New York"
    }

    private static let routes: [String: Route] = [
        "amalfi": Route(carrier: "ITA Airways", number: "AZ 609", cabin: "Business", departs: "17:10", arrives: "08:00", duration: "8h 50m", stops: "Via Rome"),
        "newyork": Route(carrier: "American Airlines", number: "AA 4", cabin: "Flagship First", departs: "08:00", arrives: "16:35", duration: "5h 35m", stops: "Nonstop", fromCode: "LAX", fromCity: "Los Angeles"),
        "sanfrancisco": Route(carrier: "JetBlue", number: "B6 415", cabin: "Mint Studio", departs: "08:15", arrives: "11:45", duration: "6h 30m", stops: "Nonstop"),
        "chicago": Route(carrier: "United", number: "UA 1197", cabin: "Polaris Business", departs: "09:00", arrives: "10:45", duration: "2h 45m", stops: "Nonstop"),
        "como": Route(carrier: "ITA Airways", number: "AZ 603", cabin: "Business", departs: "17:30", arrives: "07:50", duration: "8h 20m", stops: "Nonstop to Milan"),
        "santorini": Route(carrier: "Delta One", number: "DL 166", cabin: "Delta One Suite", departs: "17:45", arrives: "14:55", duration: "12h 10m", stops: "Via Athens"),
        "kyoto": Route(carrier: "Japan Airlines", number: "JL 5", cabin: "First", departs: "13:25", arrives: "17:30", duration: "14h 05m", stops: "Nonstop · rail to Kyoto"),
        "zermatt": Route(carrier: "SWISS", number: "LX 17", cabin: "First", departs: "18:45", arrives: "08:50", duration: "8h 05m", stops: "Nonstop · heli onward"),
        "maldives": Route(carrier: "Emirates", number: "EK 202", cabin: "First Suite", departs: "11:05", arrives: "11:35", duration: "18h 30m", stops: "Via Dubai · seaplane"),
        "dolomites": Route(carrier: "Delta One", number: "DL 250", cabin: "Delta One Suite", departs: "17:30", arrives: "07:25", duration: "8h 55m", stops: "Nonstop"),
        "paris": Route(carrier: "Air France", number: "AF 11", cabin: "La Première", departs: "19:30", arrives: "08:45", duration: "7h 15m", stops: "Nonstop"),
        "iceland": Route(carrier: "Icelandair", number: "FI 614", cabin: "Saga Premium", departs: "20:15", arrives: "06:00", duration: "5h 40m", stops: "Nonstop"),
        "bali": Route(carrier: "Singapore Airlines", number: "SQ 23", cabin: "Suites", departs: "23:35", arrives: "11:15", duration: "21h 40m", stops: "Via Singapore"),
        "dubai": Route(carrier: "Emirates", number: "EK 202", cabin: "First Suite", departs: "11:05", arrives: "07:35", duration: "12h 30m", stops: "Nonstop"),
        "seychelles": Route(carrier: "Qatar Airways", number: "QR 702", cabin: "Qsuite", departs: "21:50", arrives: "16:10", duration: "19h 20m", stops: "Via Doha"),
    ]

    private static let dinners = [
        ("Dinner on the terrace", "Table for the sunset, held under your name"),
        ("Chef’s table", "Tasting menu, pairings arranged"),
        ("An evening unplanned", "Your agent keeps tonight open — just ask"),
        ("Dinner in the village", "A family trattoria the guidebooks miss"),
    ]

    static func flight(for destination: Destination) -> Flight {
        let r = routes[destination.id] ?? routes["amalfi"]!
        return Flight(
            carrier: r.carrier, number: r.number, cabin: r.cabin, seat: "2A",
            fromCode: r.fromCode, fromCity: r.fromCity,
            toCode: destination.airport, toCity: destination.airportCity,
            departs: r.departs, arrives: r.arrives, duration: r.duration, stops: r.stops
        )
    }

    static func makeTrip(
        destination: Destination,
        start: Date,
        nights: Int,
        travelers: Int,
        business: Bool = false,
        status: TripStatus,
        stayIndex: Int = 0,
        title: String? = nil,
        reservation: Reservation? = nil,
        experiences chosen: [Experience]? = nil,
        tailoring: [String]? = nil
    ) -> Trip {
        let stay = destination.stays[min(stayIndex, destination.stays.count - 1)]
        let flight = flight(for: destination)
        let rooms = max(1, Int((Double(travelers) / 2).rounded(.up)))
        let total = stay.nightly * nights * rooms + 6_400 * travelers + 850 * nights * travelers
        let pool = (chosen?.isEmpty == false ? chosen! : destination.experiences)
        let planned = min(pool.count, max(2, nights - 2))

        let confirmed = status != .proposal
        var components = [
            TripComponent(kind: .flights, title: "Flights", status: confirmed ? "Confirmed" : "On hold"),
            TripComponent(kind: .stay, title: "Accommodation", status: confirmed ? "Confirmed" : "On hold"),
            TripComponent(kind: .transfers, title: "Private transfers", status: confirmed ? "Confirmed" : "Arranged"),
            TripComponent(kind: .experiences, title: "Experiences", status: "\(planned) planned"),
        ]
        if reservation != nil {
            // The agent already called and secured it, so it's booked even on a proposal.
            components.append(TripComponent(kind: .dining, title: "Dinner reservation", status: "Booked"))
        }

        return Trip(
            id: UUID(),
            title: title ?? defaultTitle(destination, business: business),
            destination: destination,
            startDate: start,
            nights: nights,
            travelers: travelers,
            isBusiness: business,
            stay: stay,
            flight: flight,
            components: components,
            days: itinerary(experiences: pool, stay: stay, flight: flight, nights: nights, business: business, planned: planned, reservation: reservation),
            status: status,
            total: total,
            hoursSaved: 14 + nights * 3 + travelers * 2 + (reservation == nil ? 0 : 1),
            reservation: reservation,
            tailoring: tailoring
        )
    }

    static func defaultTitle(_ d: Destination, business: Bool) -> String {
        business ? "\(d.name) offsite" : "Your \(d.adjective) escape"
    }

    private static func itinerary(experiences: [Experience], stay: Stay, flight: Flight, nights: Int, business: Bool, planned: Int, reservation: Reservation?) -> [ItineraryDay] {
        var days: [ItineraryDay] = []

        days.append(ItineraryDay(day: 1, title: "Arrival", items: [
            ItineraryItem(time: flight.arrives, title: "Land in \(flight.toCity)", detail: "\(flight.carrier) \(flight.number) · met planeside", icon: "airplane.arrival"),
            ItineraryItem(time: "—", title: "Private transfer", detail: "Driver waiting with your name, luggage handled", icon: "car"),
            ItineraryItem(time: "15:00", title: "Check in · \(stay.name)", detail: stay.note, icon: "key"),
            reservation.map {
                ItineraryItem(time: $0.restaurant.time, title: "Dinner · \($0.restaurant.name)", detail: "Table for \($0.guests), booked by Wonder · Ref \($0.reference)", icon: "fork.knife")
            } ?? ItineraryItem(time: "20:30", title: "Welcome dinner", detail: "A quiet first evening, close to the hotel", icon: "fork.knife"),
        ]))

        let middle = max(0, nights - 1)
        for i in 0..<middle {
            var items: [ItineraryItem] = []
            if business && i < 2 {
                items.append(ItineraryItem(time: "09:00", title: "Working session", detail: "Private salon reserved · AV and catering arranged", icon: "person.3"))
            }
            let title: String
            if i < planned {
                let exp = experiences[i % experiences.count]
                items.append(ItineraryItem(time: business && i < 2 ? "14:30" : "10:00", title: exp.title, detail: exp.detail, icon: exp.icon))
                title = exp.title
            } else {
                items.append(ItineraryItem(time: "—", title: "At leisure", detail: "Spa, pool, or nothing at all", icon: "sun.max"))
                title = "A day of your own"
            }
            let dinner = dinners[i % dinners.count]
            items.append(ItineraryItem(time: "20:00", title: dinner.0, detail: dinner.1, icon: "moon.stars"))
            days.append(ItineraryDay(day: i + 2, title: title, items: items))
        }

        days.append(ItineraryDay(day: nights + 1, title: "Departure", items: [
            ItineraryItem(time: "11:00", title: "Late check-out", detail: "Arranged — no need to rush breakfast", icon: "clock"),
            ItineraryItem(time: "—", title: "Transfer to \(flight.toCode)", detail: "Fast-track security and lounge access", icon: "car"),
        ]))
        return days
    }
}

enum SampleData {
    static func date(_ y: Int, _ m: Int, _ d: Int) -> Date {
        Calendar.current.date(from: DateComponents(year: y, month: m, day: d)) ?? .now
    }

    static let italianEscape = TripPlanner.makeTrip(
        destination: Catalog.amalfi, start: date(2027, 6, 12), nights: 7, travelers: 2,
        status: .confirmed, title: "Your Italian escape"
    )

    static var trips: [Trip] {
        [
            TripPlanner.makeTrip(destination: Catalog.paris, start: date(2026, 11, 17), nights: 3, travelers: 8, business: true, status: .confirmed, title: "Paris board offsite"),
            TripPlanner.makeTrip(destination: Catalog.zermatt, start: date(2026, 12, 19), nights: 8, travelers: 4, status: .confirmed, stayIndex: 1, title: "Christmas in Zermatt"),
            italianEscape,
            TripPlanner.makeTrip(destination: Catalog.kyoto, start: date(2026, 4, 2), nights: 6, travelers: 2, status: .completed, title: "Kyoto in bloom"),
            TripPlanner.makeTrip(destination: Catalog.maldives, start: date(2026, 1, 8), nights: 9, travelers: 2, status: .completed, title: "New Year in Noonu"),
        ]
    }

    static var activity: [AgentActivity] {
        let hour: TimeInterval = 3_600
        return [
            AgentActivity(icon: "arrow.triangle.2.circlepath", title: "Rebooked your Zurich connection", detail: "Earlier arrival, same cabin, no fees", date: .now - 2 * hour),
            AgentActivity(icon: "star", title: "Upgraded to the Matterhorn suite", detail: "Complimentary · Christmas in Zermatt", date: .now - 26 * hour),
            AgentActivity(icon: "fork.knife", title: "Secured Plénitude for 8", detail: "Paris board offsite · Nov 18, 20:00", date: .now - 4 * 24 * hour),
            AgentActivity(icon: "doc.text", title: "Schengen documents checked", detail: "All 8 travelers cleared", date: .now - 6 * 24 * hour),
        ]
    }
}
