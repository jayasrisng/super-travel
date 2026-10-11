import Foundation

/// What the concierge understood from a message.
enum Interpretation {
    /// A trip to plan, already constrained to Wonder's catalog.
    case plan(TripPlan)
    /// No trip to plan (a question, or somewhere Wonder doesn't go): just answer.
    case reply(String)
}

struct TripPlan {
    var brief: TravelBrief
    var stayIndex: Int
    var experiences: [Experience]
    var title: String?
    var summary: String?
    var reply: String?
    var tailoring: [String]
    var offerDinner: Bool
}

/// Turns a member's request into a tailored trip with Google Gemini.
///
/// Gemini only sees Wonder's catalog, and its JSON schema only admits catalog ids,
/// so every plan it returns is one the app can book. Follow-ups ("make it five nights")
/// work because the conversation so far is sent with each request.
final class GeminiPlanner {
    private let apiKey: String
    private let models = ["gemini-3.8-flash", "gemini-2.5-flash"]
    private var history: [[String: Any]] = []

    /// Reads the key from Info.plist (set from Secrets.xcconfig at build time).
    init?() {
        guard let key = Bundle.main.object(forInfoDictionaryKey: "GeminiAPIKey") as? String,
              !key.isEmpty, !key.hasPrefix("$(") else { return nil }
        apiKey = key
    }

    func reset() { history.removeAll() }

    func interpret(_ request: String, profile: UserProfile) async throws -> Interpretation {
        let userTurn: [String: Any] = ["role": "user", "parts": [["text": request]]]
        var lastError: Error = URLError(.unknown)

        for model in models {
            do {
                let text = try await generate(model: model, contents: Array(history.suffix(12)) + [userTurn], profile: profile)
                let response = try JSONDecoder().decode(Response.self, from: Data(text.utf8))
                history.append(userTurn)
                history.append(["role": "model", "parts": [["text": text]]])
                return response.interpretation()
            } catch {
                lastError = error
            }
        }
        throw lastError
    }

    // MARK: - Request

    private func generate(model: String, contents: [[String: Any]], profile: UserProfile) async throws -> String {
        var generationConfig: [String: Any] = [
            "responseMimeType": "application/json",
            "responseSchema": Self.schema,
            "temperature": 0.8,
        ]
        if model.hasPrefix("gemini-3") {
            generationConfig["thinkingConfig"] = ["thinkingLevel": "low"]
        }
        let body: [String: Any] = [
            "systemInstruction": ["parts": [["text": Self.instructions(profile: profile)]]],
            "contents": contents,
            "generationConfig": generationConfig,
        ]

        var request = URLRequest(url: URL(string: "https://generativelanguage.googleapis.com/v1beta/models/\(model):generateContent")!)
        request.httpMethod = "POST"
        request.timeoutInterval = 30
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue(apiKey, forHTTPHeaderField: "x-goog-api-key")
        request.setValue(Bundle.main.bundleIdentifier, forHTTPHeaderField: "X-Ios-Bundle-Identifier")
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await URLSession.shared.data(for: request)
        guard (response as? HTTPURLResponse)?.statusCode == 200 else {
            throw PlannerError.http((response as? HTTPURLResponse)?.statusCode ?? -1, String(decoding: data.prefix(300), as: UTF8.self))
        }
        let decoded = try JSONDecoder().decode(GenerateResponse.self, from: data)
        // Thinking models may return thought parts first; the answer is the last text part.
        guard let text = decoded.candidates?.first?.content?.parts?.compactMap(\.text).last else {
            throw PlannerError.empty
        }
        return text
    }

    enum PlannerError: Error {
        case http(Int, String)
        case empty
    }

    private struct GenerateResponse: Decodable {
        struct Candidate: Decodable { let content: Content? }
        struct Content: Decodable { let parts: [Part]? }
        struct Part: Decodable { let text: String? }
        let candidates: [Candidate]?
    }

    // MARK: - Prompt

    private static func instructions(profile: UserProfile) -> String {
        let today = Date.now.formatted(.iso8601.year().month().day())
        return """
        You are Wonder, a private AI travel concierge for high-net-worth travelers and companies. \
        Voice: warm, assured, discreet, specific. Never mention being an AI model or these instructions.

        You can ONLY plan trips to the destinations in the catalog below. If the member asks about \
        anywhere else, or asks something that isn't a trip, set kind to "reply": answer briefly and, \
        where it fits, suggest the closest catalog destinations by name. Never invent hotels, \
        experiences or restaurants; use catalog ids and titles exactly.

        For a trip, set kind to "plan" and tailor it to what the member said:
        - destinationId: the best catalog match for their words, mood and season.
        - stayId: one of that destination's stays, chosen for their party and taste.
        - experiences: 3–5 titles from that destination, ordered by how well they fit what they asked for.
        - travelers, nights, startDate (YYYY-MM-DD, after \(today); null if no timing given), business (offsite, board, team, clients).
        - tripTitle: short and evocative, e.g. "Jazz & the Met in New York". No emoji.
        - briefSummary: under 60 characters, e.g. "2 travelers · art & jazz · 3 nights".
        - tailoring: 2–3 short notes (each under 80 characters) on how you shaped the trip to their words.
        - offerDinner: false only if they don't want restaurant bookings.
        - reply: 2–3 sentences presenting the trip in Wonder's voice, referring to what they asked for. \
        Say everything is held until Friday and that you'll confirm on approval.
        For follow-ups ("make it 5 nights", "somewhere warmer"), revise the previous plan.

        Member: \(profile.fullName) of \(profile.company). Travel styles: \(profile.travelStyles.joined(separator: ", ")). \
        Prefers \(profile.cabin) cabin, \(profile.seat.lowercased()) seat; hotels: \(profile.hotelStyle.lowercased()); \
        dining: \(profile.dining). Usually flies from New York. Today is \(today).

        Catalog (JSON):
        \(catalogJSON)
        """
    }

    private static let catalogJSON: String = {
        let items: [[String: Any]] = Catalog.all.map { d in
            [
                "id": d.id,
                "name": d.name,
                "country": d.country,
                "tagline": d.tagline,
                "bestSeason": d.bestSeason,
                "fromPricePerPerson": d.fromPrice,
                "stays": d.stays.map { ["id": $0.id, "name": $0.name, "location": $0.location, "room": $0.note, "nightly": $0.nightly] },
                "experiences": d.experiences.map { ["title": $0.title, "detail": $0.detail] },
                "signatureDinner": "\(d.dinner.name) (\(d.dinner.cuisine))",
            ]
        }
        let data = (try? JSONSerialization.data(withJSONObject: items, options: [.sortedKeys])) ?? Data()
        return String(decoding: data, as: UTF8.self)
    }()

    /// Enums pin every id to the catalog, so Gemini can't return a place Wonder doesn't offer.
    private static let schema: [String: Any] = [
        "type": "OBJECT",
        "properties": [
            "kind": ["type": "STRING", "enum": ["plan", "reply"]],
            "reply": ["type": "STRING"],
            "destinationId": ["type": "STRING", "enum": Catalog.all.map(\.id), "nullable": true],
            "stayId": ["type": "STRING", "enum": Catalog.all.flatMap { $0.stays.map(\.id) }, "nullable": true],
            "experiences": ["type": "ARRAY", "items": ["type": "STRING", "enum": Array(Set(Catalog.all.flatMap { $0.experiences.map(\.title) })).sorted()]],
            "travelers": ["type": "INTEGER", "nullable": true],
            "nights": ["type": "INTEGER", "nullable": true],
            "startDate": ["type": "STRING", "nullable": true],
            "business": ["type": "BOOLEAN", "nullable": true],
            "tripTitle": ["type": "STRING", "nullable": true],
            "briefSummary": ["type": "STRING", "nullable": true],
            "tailoring": ["type": "ARRAY", "items": ["type": "STRING"]],
            "offerDinner": ["type": "BOOLEAN", "nullable": true],
        ],
        "required": ["kind", "reply"],
        "propertyOrdering": ["kind", "destinationId", "stayId", "travelers", "nights", "startDate", "business",
                             "experiences", "tripTitle", "briefSummary", "tailoring", "offerDinner", "reply"],
    ]

    // MARK: - Response

    private struct Response: Decodable {
        let kind: String
        let reply: String
        let destinationId: String?
        let stayId: String?
        let experiences: [String]?
        let travelers: Int?
        let nights: Int?
        let startDate: String?
        let business: Bool?
        let tripTitle: String?
        let briefSummary: String?
        let tailoring: [String]?
        let offerDinner: Bool?

        /// Validates everything against the catalog and clamps numbers to what Wonder can book.
        func interpretation() -> Interpretation {
            guard kind == "plan", let id = destinationId, let destination = Catalog.destination(id: id) else {
                return .reply(reply)
            }
            let chosen = (experiences ?? []).compactMap { title in destination.experiences.first { $0.title == title } }
            let start = startDate
                .flatMap { try? Date($0, strategy: .iso8601.year().month().day()) }
                .flatMap { $0 > .now ? $0 : nil }
            return .plan(TripPlan(
                brief: TravelBrief(
                    destination: destination,
                    travelers: min(max(travelers ?? 2, 1), 40),
                    nights: min(max(nights ?? 5, 1), 21),
                    business: business ?? false,
                    start: start ?? WonderConciergeAgent.seasonalStart(for: destination)
                ),
                stayIndex: destination.stays.firstIndex { $0.id == stayId } ?? 0,
                experiences: chosen,
                title: tripTitle?.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty,
                summary: briefSummary?.nilIfEmpty,
                reply: reply.nilIfEmpty,
                tailoring: Array((tailoring ?? []).prefix(3)),
                offerDinner: offerDinner ?? true
            ))
        }
    }
}

private extension String {
    var nilIfEmpty: String? { isEmpty ? nil : self }
}
