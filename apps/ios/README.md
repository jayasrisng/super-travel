# Wonder — iOS

Premium AI travel concierge for high-net-worth travelers and companies. SwiftUI, iOS 18+ (Liquid Glass on iOS 26).

## Run

Open `Wonder.xcodeproj` in Xcode 26 and run the **Wonder** scheme on an iPhone simulator, or:

```bash
xcodebuild -project Wonder.xcodeproj -scheme Wonder -destination 'platform=iOS Simulator,name=iPhone 17 Pro' build
```

Photography loads from Unsplash at runtime, so the simulator needs network access.

### On your iPhone

The project signs automatically with the Personal Team `H52YW64K38` (sacquah05@icloud.com). To run it, plug in the phone, choose it as the run destination in Xcode and press Run. From the terminal:

```bash
xcodebuild -project Wonder.xcodeproj -scheme Wonder -destination 'platform=iOS,name=iPhone (7)' -derivedDataPath build/DeviceData -allowProvisioningUpdates build
xcrun devicectl device install app --device "iPhone (7)" build/DeviceData/Build/Products/Debug-iphoneos/Wonder.app
```

Free (Personal Team) accounts have these limits:
- **Expiry:** apps stop opening after 7 days. Run again from Xcode to re-sign them.
- **Install limit:** each phone can hold at most 3 self-signed apps.
- **No App Groups:** the widget gets location from its own permission ("While Using the App or Widgets") rather than sharing the app's.

With a paid Apple Developer Program team, re-add an App Group entitlement (`group.com.wonder.concierge`) to both targets so the widget can fall back to the app's last location.

## What's in it

| Tab | What it shows |
| --- | --- |
| **Discover** | Editorial destinations by mood (coastal, cities, alpine…), a live "your agent is working" card, iconic stays, Wonder for Business. Destination pages include a 3D satellite map. |
| **Concierge** | Chat with the agent (Gemini). It tailors the trip to what you say, streams its planning steps, asks before booking dinner, then proposes a fully costed trip on hold. You approve it to book. |
| **Journeys** | Upcoming and past trips, a day-by-day itinerary, boarding passes, and the agent's log. The agent also raises proactive alerts here, e.g. a better flight to switch to. |
| **Profile** | Membership, agent autonomy and the auto-approve limit, learned preferences, business account and documents. |

## Saved data

The member's profile and trips are stored as readable JSON in the app's Documents folder. To view them on the phone, open **Files › On My iPhone › Wonder**.

- `profile.json`: name, company, onboarding, travel styles, agent autonomy and spending limit, cabin and seat, and other learned preferences.
- `trips.json`: every journey, including ones the concierge plans and you approve. It also holds the agent's pending alerts and activity log. Each trip stores its destination as a catalog id such as `"como"`.

Changes save automatically shortly after they happen, and immediately when the app goes to the background. If a file can't be read, it's renamed `*.unreadable` and the app starts from the sample data. **Profile › Replay introduction** resets both files.

## The concierge (Google Gemini)

The Concierge tab uses **Gemini** (`gemini-3.8-flash`, falling back to `gemini-2.5-flash`) to read each request and tailor the trip. The code is in `Wonder/Agent/GeminiPlanner.swift`.

- **Limited to Wonder's destinations:** Gemini sees only Wonder's 15 destinations (New York, San Francisco, Chicago and the 12 international ones), with their stays, experiences and restaurants. Its JSON response schema only accepts catalog ids, so it can't return a hotel or place Wonder doesn't offer. When asked about somewhere else, it replies and suggests the closest catalog options.
- **What it chooses:** destination, hotel, party size, nights, dates, business or leisure, which experiences to prioritise, a trip title, a one-line brief summary, up to three "Tailored for you" notes, and the message presenting the trip.
- **Follow-ups:** they work ("make it five nights"). The new-chat button resets the conversation.
- **Fallback:** if there's no key, no network or an error, the on-device keyword planner takes over, so the concierge always answers.

**API key:** it lives in `Secrets.xcconfig` (git-ignored; see `Secrets.example.xcconfig`) and reaches the app through `GeminiAPIKey` in Info.plist. Anything shipped inside an app can be extracted, so:
- In Google Cloud Console, restrict the key to the Generative Language API and to the iOS bundle ID `com.wonder.concierge`.
- Before release, move the Gemini call to Wonder's own backend.

## Dinner reservations while planning

While building a plan, the agent stops at **Reserving dinner** and asks whether to book the destination's signature restaurant for the first night, with the restaurant, time and party size. It says it will call them **using Dial**, and planning waits for **Yes, call** or **No thanks**.
- **Yes:** the call is shown stage by stage. The table then appears in the proposal as **Dining · Booked** and in the day 1 itinerary, with a reference number.
- **No:** the step is marked skipped.

The call is scripted in `WonderConciergeAgent.callRestaurant`. A production build would hand it to a phone-calling service.

## Nearby recommendations

Wonder uses the traveler's live location to recommend places around them in four categories: **Food, Social, Hospitality, Shop**. The agent's main pick always sits above the category buttons.

| Surface | Where | Notes |
| --- | --- | --- |
| **Around you** card | Discover tab | Has a **Show on Lock Screen** button. |
| **Wonder Nearby** widget | Home Screen (S/M/L) and Lock Screen (rectangular/inline) | Category buttons switch the pick in place, over a satellite view of the neighbourhood. |
| **Live Activity** | Lock Screen and Dynamic Island | The category buttons work while the phone is locked. |
| **Notification** | "Your agent found something nearby" | Food · Social · Hospitality · Shop are its quick actions. |

Places come from MapKit points of interest (`Shared/Nearby.swift`), so no API key is needed. Code shared by the app and the `WonderWidgets` extension lives in `Shared/`.

If widgets aren't allowed to use location, the widget falls back to the location the app last saw. The two share it through an App Group, which needs a paid developer team (see above).

## Architecture

```
Wonder/
  App/        WonderApp, WonderStore (@Observable app state)
  Agent/      ConciergeAgent protocol, WonderConciergeAgent, GeminiPlanner
  Data/       Catalog (destinations, stays, experiences), TripPlanner, sample trips
  Models/     Destination, Trip, Flight, AgentStep, ChatMessage…
  Theme/      Black, white and white Liquid Glass; adaptive ink; Backdrop; WonderLogo (vector globe mark)
  Components/ Photo (cached remote images), SatelliteMap
  Features/   Onboarding, Discover, Concierge, Trips, Profile
Shared/       Nearby search, Live Activity attributes and intents, WonderMark (app + widgets)
WonderWidgets/ Home/Lock Screen widget and the Lock Screen Live Activity
```

The concierge is behind the `ConciergeAgent` protocol, which streams `AgentEvent`s. To go to production, implement it against a Wonder backend. That backend should own the LLM, the supplier integrations (GDS/NDC flights, hotel channel managers, ground transport) and payments. Keep model and supplier keys out of the app.

State is in-memory for now. Approved trips reset when the app relaunches.
