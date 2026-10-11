# CODEX TASK: Build Wonder, the Complete Consumer Travel Experience

Repository: https://github.com/jayasrisng/super-travel

You are the principal product engineer, full-stack developer, AI engineer and UX designer responsible for implementing Wonder.

**This is an implementation request, not a documentation or architecture-only task.**

Inspect the repository, existing agent code, FastAPI endpoints, contracts, orchestrator, fixtures and demos before making changes. Reuse working components rather than rebuilding them.

Read the repository's `AGENTS.md`, `README.md`, `ARCHITECTURE.md`, `PLAN.md` and integration status documentation.

The product requirements in this prompt represent the current product-owner direction. Where older documents describe a different priority or user experience, identify the conflict and follow this direction for the consumer application while preserving useful existing infrastructure.

## 1. Product Vision

Wonder is a consumer-first, AI-powered travel super-app.

**Tagline: Less searching. More experiencing.**

The objective is to close the dozens of tabs people open while planning and experiencing travel.

Instead of switching between flights, hotels, maps, event platforms, shopping, itineraries, calendars, packing lists and messaging apps, users should interact with one intelligent application.

The interface must be extremely minimal.

Imagine a beautiful notebook, a handwritten checklist and a calm personal assistant.

The complexity exists behind the interface, not on the screen.

## 2. Visual Design

Design principles:

- Minimalist, editorial, premium, calm.
- Primarily white or warm off-white backgrounds.
- Dark typography.
- Subtle borders and restrained accent colors.
- Excellent typography and spacing.
- Smooth, understated animations.
- Responsive web-first experience.
- Mobile-first layouts.
- Avoid cluttered dashboards, dense cards and excessive navigation.
- Avoid large AI chat interfaces unless the user explicitly opens one.
- Use progressive disclosure: details appear when a task is opened.
- Make the application feel like a personal travel notebook rather than enterprise software.

The core experience should have only a few primary destinations: Home, Trip and Magic. Wardrobe is accessible from packing or the user profile.

## 3. Homepage

The homepage should contain:

- Wonder branding.
- Upcoming and ongoing trips.
- An obvious New Trip action.
- A prominent Magic button.
- The next important task from the active trip.

Each trip should display:

- Destination.
- Dates.
- Traveler count.
- Checklist progress.
- Next required action.

Support multiple independent trips for the same user.

Do not force users to create a trip to access Magic or Wardrobe.

## 4. Trip Onboarding

When creating a trip, ask for:

- Destination or undecided destination.
- Confirmed dates, tentative dates or flexible dates.
- Who is traveling.
- Number of adults and children.
- Relevant ages where necessary.
- Dietary preferences.
- Accessibility and special requirements.
- Approximate budget and currency.
- Interests.
- Travel style.
- Activities they enjoy.
- Existing bookings.

Support solo, couple, friends, family, infant, multigenerational and business-trip contexts.

Do not make traveler identity categories rigid.

Use progressive onboarding, not a long questionnaire.

Store the information per trip and reuse global user preferences where appropriate.

Allow users to skip optional fields and update details later.

## 5. Personalized Master Checklist

After onboarding, create a personalized checklist.

The checklist should be the primary trip interface.

Tasks may include:

- Compare flights.
- Choose accommodation.
- Check passport validity.
- Research visa requirements.
- Prepare required documents.
- Build itinerary.
- Arrange local transportation.
- Reserve experiences.
- Prepare packing list.
- Choose outfits.
- Purchase missing essentials.
- Arrange connectivity.
- Prepare for emergencies.
- Track shared expenses.
- Handle disruptions.
- Complete post-trip tasks.

Show only relevant tasks.

Task states:

- Not started.
- Agent working.
- Needs your input.
- Ready for review.
- Completed.
- Blocked or failed.

Clicking a task opens a minimal detail drawer or panel.

The detail view may include recommendations, sources, comparisons, agent progress, required documents, approval actions and next steps.

Users should be able to edit, dismiss, complete or add tasks.

Tasks must persist.

Do not mark an external action completed unless it actually succeeded.

## 6. Five AI Agents

Integrate the existing agents:

1. Plan & Book.
2. Pack & Shop.
3. Explore & Experience / Magic.
4. Travel Essentials.
5. Manage & Recover.

Use the existing orchestrator and API infrastructure wherever possible.

Agents should:

- Read the authorized trip context.
- Generate structured proposals.
- Suggest checklist tasks.
- Provide explanations and sources where available.
- Identify missing information.
- Request approval before consequential actions.
- Report actual progress and failures.
- Never fabricate bookings, prices, availability or confirmations.

Show agent activity inside relevant checklist items.

Do not build a noisy standalone five-agent dashboard for consumers.

If real booking integrations are unavailable, provide clearly labeled research and booking-link flows rather than pretending to complete transactions.

## 7. Magic Discovery

Magic must work both during travel and in the user's home city.

Inputs:

- Current or manually entered location.
- Available time.
- Interests or mood.
- Budget.
- Transportation preference.
- Optional next calendar commitment.

Output:

A small ranked selection of feasible things to do.

Examples:

- Restaurants.
- Coffee shops.
- Workshops.
- Meetups.
- Community events.
- Concerts.
- Museums.
- Local experiences.
- Outdoor activities.
- Unusual nearby discoveries.

Design provider interfaces for Luma, Partiful, Eventbrite, Meetup, places and local event sources.

Use legitimate APIs or permitted data access only. Do not assume access to private or undocumented endpoints.

When live providers are unavailable, use explicit sample data.

Recommendations should consider travel time, duration, operating hours, budget and the next commitment.

Provide Save, Navigate, View Details and Book actions where supported.

## 8. Digital Wardrobe — Major Feature

Build a functional digital wardrobe as part of the consumer app.

This must not be just a static mockup.

### Seed Wardrobe

Provide at least:

- 10 shirts/tops.
- 10 pants/bottoms.
- 4 pairs of shoes.
- 10 accessories.

Total: at least 34 clothing items.

Use coherent demo assets with consistent visual presentation.

Each item should include:

- Unique ID.
- Name.
- Category.
- Color.
- Image.
- Style.
- Season.
- Warmth.
- Suitable occasions.
- Optional material.
- Optional packing size or weight.
- Ownership status.

Seed realistic combinations, not random incompatible garments.

### Wardrobe Management

Users can:

- Browse their wardrobe.
- Add clothing items.
- Upload clothing photos.
- Edit item details.
- Remove items.
- Filter by category, color and occasion.
- Mark favorites.
- Reuse wardrobe items across multiple trips.

Persist wardrobe items separately from trip-specific packing lists.

If AI garment recognition is available, use it to suggest attributes from an uploaded photo, with user confirmation.

Otherwise provide manual tagging.

### Outfit Generator

Generate outfits using:

- Destination.
- Weather.
- Day's itinerary.
- Activity type.
- User preferences.
- Available clothing.
- Previously liked outfits.
- Comfort and walking requirements.

Each outfit should contain compatible clothing items.

Display the outfit on a consistent 2D model/avatar using layered clothing images or prepared lookbook compositions.

Do not claim photorealistic virtual try-on unless a real try-on system is implemented.

If asset layering is technically impractical, implement a consistent full-outfit lookbook view and preserve the model-rendering interface for later upgrades.

### Tinder-Style Outfit Swiping

This is a required interaction.

Display one outfit at a time.

- Swipe right: Like outfit.
- Swipe left: Dislike outfit.
- Tap heart: Like.
- Tap X: Dislike.
- Undo last swipe.
- View outfit details.
- Save favorite combinations.

Support touch gestures and desktop mouse dragging.

Provide accessible button alternatives and keyboard interaction.

Animate the card naturally.

Save preferences and avoid repeatedly recommending rejected combinations.

Use likes and dislikes to improve future outfit ranking.

### Outfit Selection Summary

When the user finishes swiping, show:

- Liked outfits.
- Which days/activities they suit.
- Shared clothing items.
- Clothing items still needed.
- Suggested substitutions.
- Number of unique items to pack.

Optimize packing by reusing clothing across multiple outfits.

Do not add duplicate shirts or shoes to the packing list simply because they appear in multiple outfits.

### Packing Dashboard

Convert selected outfits into a persistent packing checklist.

Group by:

- Tops.
- Bottoms.
- Shoes.
- Accessories.
- Other essentials.

Each item must show:

- Item name.
- Photo.
- Packed/unpacked state.
- Number of outfits using it.
- Relevant days.

Users can check off items as packed.

The packing dashboard should remain accessible during the trip.

### During-Trip Wardrobe

Users should be able to open a trip and see:

- What they packed.
- Photos of packed items.
- Saved outfits.
- Today's recommended outfit.
- Tomorrow's outfit options.
- Which clothes are already assigned to an activity.

The objective is to avoid unpacking or searching through luggage to remember what they brought.

Allow the user to mark clothing as worn, dirty, unavailable or ready to wear.

Avoid recommending unavailable clothing without warning.

## 9. Google Calendar Integration

Implement a calendar integration boundary.

If Google OAuth credentials are available, support user-authorized read-only Google Calendar access.

Otherwise create a clearly labeled demo-calendar mode.

Calendar data may inform:

- Daily itinerary.
- Upcoming activities.
- Outfit recommendations.
- Available time for Magic.
- Travel reminders.

Do not infer that every calendar event represents travel.

Allow users to choose which calendars and events Wonder may use.

Handle revoked access, expired tokens, missing permissions and disconnected calendars.

Store tokens securely on the backend. Never expose credentials in client bundles.

## 10. Daily Briefing

Create a personalized morning briefing.

Example:

"Good morning. You have a museum visit at 10 AM and dinner at 7 PM. The forecast is cool with possible rain. I'd suggest your navy trousers, cream sweater, waterproof shoes and crossbody bag."

The daily brief should include:

- Today's schedule.
- Weather when available.
- Suggested outfit.
- Travel preparation reminders.
- Important trip tasks.
- Relevant disruptions.
- Optional Magic suggestions.

Support manual viewing and configurable notifications.

Build an in-app briefing widget/card first.

If the native iOS project and signing environment are ready, also implement a WidgetKit target. Otherwise prepare a documented widget data contract and do not claim the native widget is shipped.

Do not promise automated morning delivery until scheduling and notification permissions work.

## 11. Trip Management

Support:

- Multiple trips.
- Multiple travelers.
- Partial-trip participants.
- Trip segments.
- Shared itinerary items.
- Shared expenses.
- Expense splits.
- Invitations and share links.
- Trip-specific permissions.

Keep group collaboration simple in the consumer interface.

Use deterministic code for expenses, authorization and financial calculations.

## 12. Backend and Data

Prefer the existing FastAPI backend and contracts.

Reuse existing SQLite/local adapters for development where appropriate.

Do not silently introduce an entirely new backend or duplicate agent implementations.

Provide persistent models for:

- Users.
- Trips.
- Trip participants.
- Preferences.
- Tasks.
- Agent runs.
- Itinerary items.
- Saved experiences.
- Wardrobe items.
- Outfit combinations.
- Outfit votes.
- Packing lists.
- Packing items.
- Calendar connections.
- Daily briefings.

Ensure data ownership and isolation.

Use mock/demo authentication only in clearly labeled local development mode. Do not expose shared development tokens in production clients.

## 13. Implementation Priority

Implement in this order:

**Phase 1: Consumer Application**
- Minimal homepage.
- Trip onboarding.
- Trip dashboard.
- Checklist.
- Existing agent API integration.

**Phase 2: Wardrobe**
- 34-item seed collection.
- Wardrobe gallery.
- Outfit generation.
- Model/lookbook display.
- Swipe interface.
- Preference persistence.
- Packing checklist.
- During-trip outfit viewer.

**Phase 3: Magic**
- Search interface.
- Existing backend integration.
- Ranked results.
- Saved experiences.
- Provider abstraction.

**Phase 4: Calendar and Daily Brief**
- Calendar demo mode.
- Optional real Google Calendar OAuth.
- Outfit recommendations.
- In-app daily briefing.
- Native widget preparation.

**Phase 5: Integration and Validation**
- Connect trip tasks, packing, wardrobe, Magic and briefings.
- Test multiple trips.
- Test partial-trip participants.
- Test persistence after refresh.
- Test mobile responsiveness.
- Test loading, empty and error states.
- Run backend and frontend test suites.

## 14. Definition of Done

The application must demonstrate this complete user journey:

1. Open Wonder.
2. Create a Tokyo trip.
3. Select family travelers, preferences, budget and dates.
4. Generate a personalized checklist.
5. Open an agent task and review its recommendations.
6. Open the digital wardrobe.
7. Browse at least 34 seeded clothing items.
8. Generate compatible outfits.
9. Swipe right and left through outfits.
10. Save liked outfits.
11. Generate an optimized packing list.
12. Mark items packed.
13. Reopen the trip and view saved outfit photos.
14. Open a daily briefing using itinerary or demo-calendar data.
15. Use Magic to find an activity.
16. Save the activity.
17. Refresh and verify saved state persists.

The complete journey must work locally without paid third-party credentials, using clearly labeled fixture data where necessary.

## 15. Execution Instructions

Do not stop after producing a plan.

Inspect the repository, summarize the implementation approach briefly, then begin building.

Use existing code and avoid unnecessary rewrites.

Create focused commits on a feature branch.

Run tests and fix failures.

Implement as much of the complete journey as possible within the available execution budget.

If the environment prevents a real external integration, implement the interface, demo adapter, error handling and documentation instead of faking success.

Prioritize a working, visually polished, connected application over large amounts of disconnected code.

At completion, report:

- What was actually implemented.
- What works end to end.
- What uses demo data.
- What requires credentials.
- What remains incomplete.
- Exact commands to run locally.
- Test results.
- Screenshots or preview evidence where possible.

**Do not describe a planned feature as implemented.**

The result should feel like one beautifully simple product, not five separate engineering projects.

Build Wonder.