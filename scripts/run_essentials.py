"""Run the Travel Essentials agent against the demo trip.

    uv run python scripts/run_essentials.py
    uv run python scripts/run_essentials.py "Do we need cash in Lisbon?"
"""

import json
import sys

from super_travel.agents.essentials.agent import EssentialsAgent
from super_travel.core.trip_context import demo_today, load_trip

DEFAULT_TASK = "What do we need to know about money, phones, health and safety before we go? Give us the full briefing."


def main() -> None:
    task = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TASK
    trip = load_trip()
    result = EssentialsAgent().run(task, trip, today=demo_today())

    print(result.reply)
    print("\n--- handoffs ---")
    for h in result.handoffs:
        print(f"-> {h.to_agent}: {h.task}")
    print("\n--- checklist added ---")
    for t in result.data["checklist_added"]:
        print(f"[{t['due']}] {t['title']}")
    print("\n--- structured data ---")
    print(json.dumps({k: v for k, v in result.data.items() if k != "reply"}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
