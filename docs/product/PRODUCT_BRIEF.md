# Super Travel
### Less searching. More experiencing.
**Product Vision, Architecture & Engineering Brief**

**Repository:** https://github.com/jayasrisng/super-travel  
**Product:** B2C Travel Super-App  
**Platforms:** Web, iOS, iMessage, Home-Screen Widgets  
**Team:** 5 developers  
**Stage:** MVP / Early Development

---

# 1. What Is Super Travel?

Super Travel is a personalized, AI-powered travel companion designed to simplify the entire travel experience, from deciding where to go to returning home.

Today, planning even a short trip involves switching between numerous applications:

- Google Flights or Skyscanner to find flights.
- Booking.com or Airbnb to find accommodation.
- Google Maps to discover places.
- Instagram, Reddit and TikTok for recommendations.
- Eventbrite, Luma, Meetup and Partiful to discover events.
- Notes, spreadsheets and reminders to organize everything.
- WhatsApp or iMessage to coordinate with friends.
- Splitwise to manage group expenses.
- Shopping platforms to purchase travel essentials.
- Airline apps to track flights and boarding information.

The problem isn't that these applications are individually bad.

**The problem is that none of them understands the complete context of a person's trip or helps them move efficiently from one decision to the next.**

Users spend significant time searching, comparing, switching applications, remembering information and figuring out what to do next.

Super Travel aims to eliminate that fragmentation.

Rather than making users navigate dozens of features, Super Travel presents one intelligent, personalized checklist that continuously adapts to the traveler, their destination, their companions and the current stage of their trip.

**Our fundamental product promise:**

> Tell us what you're trying to do. We'll help you find the best available options, decide faster and take the next action.

We are not building another itinerary generator.

We are building a travel assistant that connects discovery, planning, preparation, booking, coordination, experiences and trip management.

---

# 2. Why Are We Building This?

## 2.1 Travel planning is fragmented

Travelers currently have to manage multiple disconnected workflows.

A flight booking doesn't automatically update a packing list. A restaurant reservation doesn't necessarily account for transportation time. An event recommendation might conflict with an existing itinerary.

A traveler shouldn't have to manually connect all these details.

Super Travel should maintain a shared understanding of the trip so that every feature works with the same information.

## 2.2 Finding the best option takes too long

Travel discovery often involves scrolling through hundreds of results.

Most users don't want hundreds of options. They want a few good options that match their needs.

For example:

"I have two hours before my flight. I'm vegetarian, I have luggage, and I don't want to spend more than $40. What can I do nearby?"

A conventional search engine may return restaurants, attractions and articles independently.

Super Travel should consider available time, travel time, preferences, operating hours, cost and the user's next commitment before suggesting realistic options.

The objective isn't simply to provide more information.

**The objective is to reduce time to useful action.**

## 2.3 Different travelers have different needs

A mother traveling with an infant has different requirements from a solo traveler, a couple or a group of friends.

A generic travel checklist is insufficient.

Super Travel should generate personalized workflows based on who is traveling, without forcing users into rigid demographic categories.

## 2.4 Plans change constantly

Travel is unpredictable.

Flights get delayed. People cancel. Weather changes. Restaurants close. Friends join trips late. Bookings get modified.

A static itinerary cannot handle these situations effectively.

Super Travel should recognize changes, explain their consequences and help users recover quickly.

## 2.5 Travel should be about experiences, not administration

The less time someone spends organizing a trip, the more time they have to experience it.

That's why our positioning is:

**Less searching. More experiencing.**

---

# 3. Product Philosophy

Super Travel follows five fundamental principles.

### 3.1 One simple interface, many powerful capabilities

The product may contain dozens of capabilities internally, but users should not be forced to navigate dozens of tabs.

The primary interface is a contextual checklist.

Each checklist item connects to the appropriate tool or agent.

### 3.2 Personalization happens per trip

A user might travel solo to San Francisco, with family to Tokyo and with friends to New York.

Each trip must maintain its own traveler configuration, participants, preferences, itinerary, expenses and progress.

Global user preferences may provide defaults, but trip-specific information takes precedence.

### 3.3 Users can access one feature independently

Not everyone wants to plan an entire trip.

Someone may open Super Travel only to generate a packing list, find a restaurant, check travel requirements or discover something to do nearby.

The application must support both:

- **Complete Trip Mode:** A connected travel experience with a master checklist.
- **Single Feature Mode:** Direct access to one capability without unnecessary onboarding.

### 3.4 Recommendations must lead to action

Every useful recommendation should have a clear next step.

Depending on the feature, that might be booking, navigating, saving, comparing, sharing, inviting, purchasing or adding an item to the itinerary.

A recommendation is not a confirmed booking. The product must distinguish suggestions, availability checks, reservation requests and completed transactions.

### 3.5 Automate complexity without removing user control

AI should help with research, prioritization and coordination.

Users must retain control over purchases, bookings, sensitive information, itinerary changes and communications.

The system should explain important recommendations and request confirmation before consequential actions.

---

# 4. The Five Core Product Systems

These are internal product domains, not necessarily five visible navigation tabs.

## System 1: Plan & Book

**Purpose:** Help users move from an idea to an organized, bookable trip.

Capabilities:

- Destination discovery.
- Travel date recommendations.
- Budget planning.
- Flight discovery and comparison.
- Accommodation discovery and comparison.
- Travel document and entry-requirement guidance.
- Itinerary generation.
- Transportation planning.
- Booking links and confirmation tracking.
- Multi-destination planning.
- Personalized recommendations based on traveler profiles.

Example:

"Plan a five-day Tokyo trip for two friends under $2,000, prioritizing food, art and unusual local experiences."

The agent should produce a practical plan with budget estimates, destination information, suggested flights and stays, and an actionable checklist.

## System 2: Pack & Shop

**Purpose:** Make travel preparation faster and reduce forgotten essentials.

Capabilities:

- Personalized packing lists.
- Destination weather considerations.
- Trip duration and activity-based packing.
- Airline baggage restrictions.
- Infant and family-specific essentials.
- Medication and travel document reminders.
- Shared packing lists.
- Purchased, packed and missing item tracking.
- Product recommendations.
- Shopping links.
- Last-minute purchase suggestions.

Example:

"I'm going to Iceland for seven days in November, traveling with a carry-on."

The system should create an appropriate packing checklist and identify important missing items.

Shopping should be useful, not intrusive.

## System 3: Explore & Experience

**Purpose:** Help users discover worthwhile experiences and act on them quickly.

Capabilities:

- Restaurants and cafes.
- Local events and meetups.
- Attractions.
- Museums and cultural experiences.
- Outdoor activities.
- Local transportation.
- Tours and workshops.
- Last-minute experiences.
- Business offers and availability.
- Experience booking and reservation links.
- Personalized discovery based on interests.
- Time-aware recommendations.

This system includes our flagship feature: **Magic**.

### Magic: What Can I Do Right Now?

Magic is a context-aware discovery assistant.

Users provide:

1. How much time they have.
2. Where they are or where they want to explore.
3. Their interests, preferences or mood.
4. An optional budget.

Magic recommends a small, ranked selection of realistic activities.

It should consider:

- Actual travel time.
- Available time before the next commitment.
- Operating hours.
- Event start and end times.
- Booking availability where verifiable.
- Cost.
- Accessibility and relevant travel constraints.
- Traveler preferences.
- Group composition.
- Weather where relevant.

Magic should work even when the user isn't traveling.

A person living in San Francisco could use Magic on a normal weekday to discover a workshop, cafe, community event or interesting activity.

Potential discovery sources include event platforms, public event feeds, local businesses, venue websites, tourism providers and booking partners, subject to available APIs, permissions and commercial agreements.

We should not assume every platform provides an unrestricted API.

### Business Marketplace

Businesses may eventually manage:

- Upcoming events.
- Special experiences.
- Last-minute openings.
- Limited-time offers.
- Available reservations.
- Workshops and classes.

Businesses could pay for completed transactions, subscription tools or clearly labeled promotions.

Organic recommendation quality must remain independent of undisclosed payments.

## System 4: Travel Essentials

**Purpose:** Help travelers feel prepared and informed.

Capabilities:

- Passport and visa checklists.
- Travel insurance.
- Currency and payment guidance.
- eSIM and mobile connectivity.
- Health preparation.
- Safety information.
- Emergency contacts.
- Local laws and customs.
- Language assistance.
- Accessibility information.
- Offline access to critical trip information.

Requirements involving immigration, health or safety should use authoritative sources, display freshness and avoid presenting uncertain information as definitive.

## System 5: Manage & Recover

**Purpose:** Handle coordination, disruptions and the less glamorous parts of travel.

Capabilities:

- Flight delays and cancellations.
- Missed connections.
- Lost baggage.
- Booking changes.
- Refund tracking.
- Emergency replanning.
- Home preparation.
- Post-trip tasks.
- Group expense management.
- Split payments.
- Trip coordination.
- Expense reconciliation.
- Shared responsibilities.
- Trip history.

A key feature is group coordination.

Users should be able to see who paid, who participated, what remains owed and which plans changed.

---

# 5. User Personalization

During trip creation, Super Travel should ask a small number of meaningful questions.

### Who is traveling?

Examples:

- Solo traveler.
- Female solo traveler.
- Couple.
- Two friends.
- Friends group.
- Parent with an infant.
- Family with children.
- Multigenerational family.
- Business traveler.
- Mixed group.

These are flexible trip templates rather than fixed user identities.

A traveler should be able to modify the template and enable or disable recommendations.

### What is the trip?

- Destination.
- Dates.
- Number of travelers.
- Approximate budget.
- Travel purpose.
- Interests.
- Relevant constraints.

### What do you need?

- Plan everything.
- Pack bags.
- Find flights.
- Find accommodation.
- Discover experiences.
- Manage an existing trip.
- Use Magic.

Avoid collecting information that isn't necessary for the requested feature.

---

# 6. Multiple Trips and Group Travel

One account can manage several trips simultaneously.

For example:

**Trip A: Tokyo**
- Family vacation.
- November 12–19.
- Parent and infant.
- Family-specific checklist.

**Trip B: New York**
- Friends getaway.
- December 4–8.
- Four participants.
- Shared expenses and activities.

**Trip C: Bali**
- Solo trip.
- January 10–17.
- Independent itinerary and packing list.

Each trip maintains independent state.

## Trip segments

A trip may contain several destinations or time periods.

For example:

Italy trip:
- Rome: June 1–4.
- Florence: June 4–7.
- Venice: June 7–10.

Some friends may participate only in Rome, while others join in Venice.

The system must support participation at trip, segment, booking and activity levels.

## Shared expenses

Every expense should record:

- Description.
- Amount and currency.
- Who paid.
- Who participated.
- Split method.
- Amount owed by each participant.
- Refunds or adjustments.
- Settlement status.

Support equal, custom amount, percentage and weighted splits over time.

Do not assume that every traveler shares every expense.

A participant should be able to join a trip without creating an account initially, using an invitation or guest representation.

Permissions should distinguish organizers, editors, participants and read-only guests.

---

# 7. The Super Travel Homepage

The homepage should not resemble a conventional booking marketplace.

It should answer three questions:

**Where am I going?**

**What is missing?**

**What should I do next?**

Suggested structure:

### Active Trips

Show upcoming, ongoing and recently completed trips.

Each card displays:
- Destination.
- Dates.
- Traveler group.
- Checklist progress.
- Important alerts.
- Next action.

### Master Checklist

Tasks are grouped internally by the five systems but displayed in order of relevance and urgency.

Examples:

- Confirm accommodation.
- Check travel document requirements.
- Pack winter clothing.
- Download an eSIM.
- Reserve airport transportation.

### Magic

A prominent action:

**Got some time? Find something worth doing.**

### Travel Passport

Access personal travel history, statistics, achievements and shareable memories.

The homepage should remain useful even if the user has no active trips.

---

# 8. Travel Passport: Identity, Memories and Sharing

Super Travel should help users remember their experiences, not just organize them.

Travel Passport is an optional personal travel profile.

Potential features:

- Countries visited.
- Cities explored.
- Trips completed.
- Experiences attended.
- Personal travel map.
- Favorite places.
- Travel milestones.
- Yearly travel recaps.
- Shareable trip cards.
- Custom themes.
- Animated travel stories.
- Group travel memories.

The system may use completed trip data and explicitly saved experiences to create visual recaps.

Do not assume a person visited a place merely because they planned or booked it.

Users should be able to control what is private, shared with a group or public.

Real-time locations, children's details, sensitive travel information and private expenses must never be exposed in public sharing by default.

---

# 9. iMessage and Social Coordination

Super Travel should integrate naturally into how people already coordinate.

The iMessage workstream should explore:

- Trip invitations.
- Sharing itineraries.
- Voting on activities.
- Group reminders.
- Sharing booking details.
- Expense settlement links.
- Activity suggestions.
- Quick access to trip updates.

We should not require every participant to download the app immediately.

Shared web links should provide useful fallback experiences.

Native iMessage capabilities must be implemented within Apple's supported APIs and platform restrictions.

The long-term objective is to make group coordination possible without creating another complicated social network.

---

# 10. iOS App and Widgets

The native iOS application should prioritize speed and contextual usefulness.

Core screens:

- Trip overview.
- Master checklist.
- Magic.
- Focused feature views.
- Travel Passport.
- Account and settings.

### Home-Screen Widget

The widget should show the most relevant information at a glance.

Examples:

Before a trip:
- Packing progress.
- Outstanding travel documents.
- Upcoming flight.

During a trip:
- Next reservation.
- Departure time.
- Important alerts.
- Magic shortcut.

After a trip:
- Unsettled expenses.
- Refund reminders.
- Travel recap.

Widgets should respect iOS update and interaction constraints.

The app should remain functional without a widget.

---

# 11. AI Architecture

Super Travel should use specialized agents coordinated through a shared application backend.

The initial three agents are:

### Agent A: Plan & Book

Inputs:
- Trip context.
- Destination.
- Dates.
- Budget.
- Traveler configuration.
- Preferences.

Outputs:
- Suggested itinerary.
- Budget breakdown.
- Flight and accommodation suggestions.
- Actionable checklist.
- Recommendation reasoning and sources.

### Agent B: Pack & Shop

Inputs:
- Trip context.
- Duration.
- Weather.
- Activities.
- Baggage rules.
- Traveler requirements.

Outputs:
- Categorized packing list.
- Missing essentials.
- Shopping suggestions.
- Preparation reminders.

### Agent C: Explore & Experience

Inputs:
- Location.
- Available time.
- Interests.
- Budget.
- Trip itinerary.
- Traveler configuration.

Outputs:
- Ranked experiences.
- Time feasibility.
- Cost estimates.
- Booking/navigation actions.
- Sources and availability status.

### Agent Orchestration

All agents should receive relevant information through a shared trip-context service.

Agents should not maintain separate authoritative copies of user or trip data.

Use structured outputs with schema validation.

Prefer deterministic application logic for expense calculations, permissions, state transitions and scheduling constraints.

AI should assist with interpretation, discovery, ranking and planning rather than replace predictable business logic.

Third-party data should be treated as untrusted input.

Require explicit confirmation for purchases, cancellations, payments and consequential changes.

---

# 12. Proposed Technology Stack

The following is the recommended starting stack, subject to team agreement.

| Layer | Proposed technology | Purpose |
|---|---|---|
| Web | Next.js, React, TypeScript | Responsive web application |
| Styling | Tailwind CSS, shadcn/ui | Reusable interface components |
| iOS | Swift, SwiftUI | Native application |
| Widgets | WidgetKit, App Intents | iOS home-screen experiences |
| iMessage | Swift, supported Apple messaging extensions and share links | Group coordination |
| Backend | Python, FastAPI | APIs and agent execution |
| Database | PostgreSQL via Supabase | Shared persistent data |
| Authentication | Supabase Auth | User accounts and access |
| Realtime | Supabase Realtime | Collaborative trip updates |
| AI | Model-provider abstraction with structured outputs | Reasoning and recommendations |
| Agent orchestration | Python services; LangGraph if needed | Multi-step agent workflows |
| Maps | MapKit or Google Maps Platform | Location, routing and maps |
| Places and events | Provider adapters | Discovery integrations |
| Storage | Supabase Storage | User-uploaded media and documents |
| Background jobs | Managed job queue / scheduler | Reminders, refreshes and asynchronous work |
| Observability | Sentry, structured logs, tracing | Error monitoring and debugging |
| Analytics | PostHog or equivalent | Product metrics |
| Testing | Pytest, Vitest, Playwright, XCTest | Backend, web and iOS validation |
| CI/CD | GitHub Actions | Automated checks and deployments |

Do not introduce unnecessary infrastructure before the MVP requires it.

Use external provider interfaces so flight, accommodation, event, shopping and payment integrations can be replaced without rewriting the core product.

---

# 13. Suggested Repository Architecture

A monorepo is recommended because five developers will share contracts and data models.

```text
super-travel/
│
├── apps/
│   ├── web/
│   └── ios/
│
├── services/
│   ├── api/
│   ├── agents/
│   │   ├── plan_book/
│   │   ├── pack_shop/
│   │   └── explore_magic/
│   └── integrations/
│
├── packages/
│   ├── contracts/
│   ├── shared-types/
│   └── design-tokens/
│
├── database/
│   ├── migrations/
│   └── seeds/
│
├── docs/
│   ├── architecture/
│   ├── product/
│   ├── api/
│   └── decisions/
│
├── tests/
│
├── .github/
│   └── workflows/
│
├── README.md
├── AGENTS.md
└── .env.example
```

The exact structure should be refined after inspecting the repository and selecting deployment infrastructure.

The iMessage implementation may live inside the iOS project as an extension target.

---

# 14. Shared Data Model

The database should support:

### Identity and trips

- User
- UserPreferences
- Trip
- TripSegment
- TripParticipant
- TripPreference
- TripPermission

### Planning and execution

- ChecklistTask
- ItineraryItem
- Booking
- BookingParticipant
- TransportationLeg
- Notification

### Discovery

- Place
- Experience
- Event
- Recommendation
- SavedExperience
- ProviderSource

### Packing and shopping

- PackingList
- PackingItem
- ShoppingItem
- PurchaseReference

### Group finance

- Expense
- ExpenseSplit
- Settlement
- Refund

### Travel history

- CompletedExperience
- TravelPassport
- TravelMemory
- ShareableRecap

Every trip-owned resource must be scoped by trip ID and protected by appropriate authorization.

Trip participants may belong to different segments or activities.

Booking status, expense status and checklist completion should be explicit state transitions.

---

# 15. Business Model

Super Travel is consumer-first.

The core checklist and essential trip-management features should remain accessible without requiring a subscription.

Potential monetization:

1. Affiliate revenue from travel-related bookings and purchases.
2. Commissions from completed experience bookings.
3. Business subscriptions for managing experiences and offers.
4. Clearly labeled sponsored discovery placements.
5. Premium automation and advanced travel tools.
6. Premium Travel Passport customization and recaps.
7. Optional paid group coordination features.

Monetization should not compromise recommendation quality, safety or user trust.

Initial business validation should focus on whether users return, complete actions and make bookings through the product.

---

# 16. Team Responsibilities

We have five developers.

### Developer 1: AI Agents, Shared APIs and Integration

Responsible for:

- Plan & Book agent.
- Pack & Shop agent.
- Explore & Experience agent.
- Magic recommendation engine.
- Agent API contracts.
- Shared trip context.
- Integration architecture.
- Coordination of remaining backend work.

### Developer 2: iMessage

Responsible for:

- Invitations.
- Trip sharing.
- Group coordination.
- Messaging workflows.
- Polls and reminders.
- Share-link fallbacks.

### Developer 3: Travel Essentials and Manage & Recover

Responsible for:

- Travel essentials dashboard.
- Documents and safety.
- Connectivity and payments guidance.
- Disruption workflows.
- Recovery tasks.
- Home preparation.
- Post-trip tasks.

### Developer 4: Website

Responsible for:

- Marketing website.
- Onboarding.
- Trip dashboard.
- Master checklist.
- Focused feature experiences.
- Travel Passport UI.
- Responsive design.

### Developer 5: iOS

Responsible for:

- Native iOS application.
- Shared trip experiences.
- Native Magic interface.
- Notifications.
- Widgets.
- Native integration.

All developers must coordinate through shared API contracts and pull requests.

---

# 17. MVP Scope

The first release should prove the core product experience rather than attempt to replace every existing travel platform.

### Required MVP

- User authentication.
- Multiple trips per user.
- Per-trip traveler personalization.
- Trip creation and editing.
- Master checklist.
- Three callable AI agents.
- Personalized packing lists.
- Basic itinerary generation.
- Magic discovery with verifiable or clearly labeled mock results.
- Group participants.
- Basic shared expenses.
- Web interface.
- iOS prototype.
- Shareable trip links.
- Basic Travel Passport.
- Simple essentials and recovery dashboard.

### Later Releases

- Direct flight and hotel booking.
- Real payment processing.
- Merchant self-service portal.
- Automated refunds and cancellations.
- Advanced flight disruption monitoring.
- Full event-provider aggregation.
- Premium subscription billing.
- Sophisticated social features.
- Advanced group settlement.
- Automated travel memory generation.

A feature should not be described as live, bookable or transactional until the corresponding integration works.

---

# 18. Success Metrics

Our primary metric is:

**Time to Useful Action (TTUA)**

The time between a user expressing a need and successfully taking the next meaningful action.

Examples:

- Time to select a suitable experience.
- Time to generate and accept a packing list.
- Time to identify the next required travel task.
- Time to resolve a group expense.
- Time to recover from a changed itinerary.

Supporting metrics:

- Checklist completion rate.
- Recommendation acceptance rate.
- Magic usage frequency.
- Trip creation completion.
- Booking click-through and confirmed conversion.
- Repeat usage.
- Multi-trip retention.
- Group invitation acceptance.
- User-reported time saved.
- Cost per successful AI-assisted action.

Time-saving claims should be supported by actual measurements.

---

# 19. Engineering Principles

1. **Shared context first.** Every component must work from consistent trip data.
2. **API-first collaboration.** Define contracts before parallel implementation.
3. **Privacy by default.** Protect locations, documents, financial data and travel plans.
4. **Minimal interfaces.** Avoid unnecessary navigation and configuration.
5. **Actionable AI.** Return structured recommendations with clear next steps.
6. **Reliable fallbacks.** Core workflows should function when AI or external APIs fail.
7. **No fabricated availability.** Clearly distinguish verified results, estimates and mocks.
8. **Explicit user control.** Never make purchases or major trip changes without authorization.
9. **Test business logic.** Especially permissions, trip isolation, expense splitting and scheduling.
10. **Ship incrementally.** Deliver one complete journey before expanding breadth.

---

# 20. The First Demonstration

Our initial end-to-end demonstration should follow one user.

The user opens Super Travel and creates a family trip to Tokyo.

They select the traveler configuration, dates, budget and interests.

Super Travel creates a personalized checklist.

The Plan & Book agent proposes an itinerary.

The Pack & Shop agent creates a packing list.

The user then switches to a second trip with friends.

They invite participants, including someone joining only part of the trip.

The group records a shared expense.

Later, the user has 90 minutes free.

They open Magic, provide their location and preferences, and receive feasible experience recommendations with clear next actions.

Finally, the user sees their trip progress on both web and iOS and can access an optional Travel Passport recap.

**The demonstration should prove that the entire product behaves like one connected system.**

---

# 21. What Codex Should Do Next

After reading this document, Codex should:

1. Inspect the existing repository and current files.
2. Identify any existing decisions or architecture constraints.
3. Create a detailed `PLAN.md` with implementation phases, dependencies, milestones and acceptance criteria.
4. Expand `README.md` with product context, architecture, local setup and contributor instructions.
5. Create `AGENTS.md` with repository-wide instructions for coding agents, architecture boundaries, testing requirements and collaboration rules.
6. Define the shared database schema and API contracts.
7. Propose the monorepo structure and local development workflow.
8. Create a clear task breakdown for the five developers.
9. Establish environment variable templates, linting, formatting, testing and CI.
10. Identify external API dependencies, costs, risks and missing credentials.
11. Prioritize the smallest working end-to-end vertical slice.
12. Avoid building unnecessary features or selecting expensive services without justification.

**Do not immediately implement the entire product. First establish a coherent engineering foundation that enables five developers and multiple coding agents to work safely in parallel.**

---

# Final Vision

Super Travel is not trying to become another Google Maps, Booking.com, TripIt, Eventbrite or Splitwise.

It aims to connect the jobs people currently accomplish across those applications into one personalized experience.

The user shouldn't have to think about which app to open, which information to copy or which task comes next.

Super Travel should understand the trip, identify what matters and help the user act.

**Less searching. More experiencing.**

**One trip. One checklist. Everything connected.**