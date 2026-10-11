# super-travel
one super app for all your travel plans

## Setup

```bash
uv sync
cp .env.example .env   # then add your ANTHROPIC_API_KEY
uv run pytest -q
```

Run the Travel Essentials agent (agent 4) on the demo trip:

```bash
uv run python scripts/run_essentials.py
uv run python scripts/run_essentials.py "Do we need cash in Lisbon?"
```

Run the Manage & Recover agent (agent 5) on the demo trip's scripted events:

```bash
uv run python scripts/run_recovery.py        # all events: delay, lost bag, receipt, trip end
uv run python scripts/run_recovery.py ev1    # just the flight delay
```

Architecture: [docs/architecture.md](docs/architecture.md)
