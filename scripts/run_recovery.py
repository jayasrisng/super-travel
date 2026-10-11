"""Run the Manage & Recover agent against the demo trip.

    uv run python scripts/run_recovery.py                 # play all demo events in order
    uv run python scripts/run_recovery.py ev1             # one event
    uv run python scripts/run_recovery.py "Our flight to Barcelona is delayed 4 hours. What are we owed?"
"""

import json
import sys
from datetime import datetime

from super_travel.agents.recovery.agent import RecoveryAgent
from super_travel.core.agent import AgentResult
from super_travel.core.trip_context import REPO_ROOT, demo_today, load_trip


def show(result: AgentResult) -> None:
    print(result.reply)
    for a in result.pending_actions:
        print(f"\n[confirm] {a.kind}: {a.summary}")
        if a.payload.get("draft"):
            print("  " + a.payload["draft"].replace("\n", "\n  "))
    for h in result.handoffs:
        print(f"-> {h.to_agent}: {h.task}")
    for t in result.data["checklist_added"]:
        print(f"[task {t['due']}] {t['title']}")


def main() -> None:
    agent, trip = RecoveryAgent(), load_trip()
    events = json.loads((REPO_ROOT / "fixtures" / "demo_events.json").read_text())["events"]
    arg = sys.argv[1] if len(sys.argv) > 1 else None

    if arg and not arg.startswith("ev"):
        show(agent.run(arg, trip, today=demo_today()))
        return
    for event in events:
        if arg and event["id"] != arg:
            continue
        print(f"\n===== {event['id']}: {event['type']} =====")
        show(agent.handle_event(event, trip, today=datetime.fromisoformat(event["at"]).date()))
    print(f"\nIncidents: {json.dumps(trip.incidents, indent=2, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
