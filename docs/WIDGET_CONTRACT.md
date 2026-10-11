# Briefing widget handoff — native target not shipped

There is no native iOS project/signing target in this repository. The shipped widget is the web morning-note view. WidgetKit, background scheduling and notifications have not been implemented.

The current shared wire contract is `Briefing` in checked OpenAPI, generated from `super_travel/consumer/models.py`. Read `GET /v1/consumer/trips/{trip_id}/briefing?day=YYYY-MM-DD` through the authenticated API. It contains `trip_id`, civil `day`, `note`, selected `schedule`, optional ready packed `outfit`, `weather` with `weather_mode=fixture`, `reminders`, `disruptions`, `delivery=in_app_only` and `version`. Profile notification preference is consent intent only.

Native implementation gate:

1. Generate Swift models from the same spec; do not copy a separate schema. Implement verified account authentication before real beta data.
2. Host app fetches an authorized brief and creates a minimal cached widget projection. Add `generated_at`, trip timezone and freshness expiry to the shared contract before relying on cached data; current payload lacks those cache fields.
3. Use a private App Group container and Keychain for credentials. Widget reads only the minimum redacted projection and deep-links into the authenticated app. Do not include passport, ledger, child identity, precise location or access tokens in widget text.
4. Timeline uses trip-local civil day and explicit stale/offline indication, including DST tests. No claim of guaranteed morning delivery from WidgetKit refresh scheduling.
5. Wipe cached projections on logout, membership removal or revocation. Distinguish disabled/expired calendar access from an empty day; show fixture labels if using synthetic calendar/weather.
6. Verify device, signing, deep link, permission/denial, lock-screen privacy, ready/worn packing and account isolation before marking native parity complete.

This contract prepares the integration boundary. It is not a released native widget or a push-notification service.
