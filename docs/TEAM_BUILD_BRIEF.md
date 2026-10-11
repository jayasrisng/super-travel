# Super Travel — Team Build Brief

**Positioning:** Less searching. More experiencing. One personalized checklist, with the next best action a tap away.

## Five owners
1. **Agents & shared API (project lead):** Plan & Book, Pack & Shop, Explore & Experience / Magic. Own shared data contracts and integration decisions.
2. **iMessage:** Trip invite links, itinerary sharing, group polls, reminders, expense updates. Use supported platform methods; provide fallback share links.
3. **Essentials & Recovery:** Travel documents, payments, connectivity, health/safety, disruptions, home prep, refunds and post-trip tasks.
4. **Web:** Landing page, onboarding, trips dashboard, personalized checklist, single-feature mode, Travel Passport.
5. **iOS:** Native screens, active-trip checklist, Magic entry point, notifications and compact home-screen widget.

## MVP user journeys
- Create multiple independent trips; set persona per trip (solo, family, infant, friends, etc.).
- Open a trip to see the next actionable checklist item; optionally enter one feature directly.
- Invite people who participate only in selected trip segments.
- Record shared expenses: paid by, participants, split rules, refunds and balances.
- Ask Magic for nearby experiences based on available time, travel time, area, budget and interests.
- Export/share an opt-in Travel Passport recap.

## Shared models (draft)
User, Trip, TripSegment, TripParticipant, Task, Booking, Expense, ExpenseSplit, Experience, Recommendation, ActivityLog.
Every trip-related record must have a trip ID. Participants have their own joined dates/segments and permissions. Use source attribution and timestamps on recommendations.

## API proposal (draft; finalize before implementation)
GET/POST /trips; GET /trips/:id; GET/PATCH /trips/:id/tasks
POST /agents/plan; POST /agents/pack; POST /agents/explore
GET/POST /trips/:id/participants; GET/POST /trips/:id/expenses
POST /magic/recommend; GET /trips/:id/summary
Return typed, versioned JSON with clear loading/error states. Mock integrations where third-party access is unavailable, and label mock data.

## Repo collaboration
Separate feature branches and pull requests. Don't push directly to main. Document environment setup and API changes. No secrets or personal travel documents in Git. Unit tests for split math and trip isolation; integration tests for checklist persistence; basic privacy and accessibility review.

## Demonstration target
A user creates a Tokyo family trip and an overlapping friends trip; gets distinct checklists; invites a partial-trip participant; records a group taxi payment; opens Magic for a 90-minute activity; sees the same trip state on web and iOS.

## Five-day prototype plan
Day 1 contracts and skeleton; Days 2–3 parallel feature demos; Day 4 integration; Day 5 end-to-end validation. Booking/payments and live event availability should not be represented as real unless integrations are operational.
