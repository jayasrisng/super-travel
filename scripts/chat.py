"""Chat with super-travel about the demo trip, through the orchestrator.

    uv run python scripts/chat.py                 # interactive
    uv run python scripts/chat.py --event ev1     # play one demo event (or --event all)
"""

import json
import sys
from datetime import datetime

from super_travel.core.trip_context import REPO_ROOT, demo_today, load_trip
from super_travel.orchestrator import Session, TurnResult


def show(result: TurnResult) -> None:
    print(f"\n{result.reply}\n")
    for d in result.delegations:
        print(f"  · {d.agent}: {d.status}{' - ' + d.error if d.error else ''}")
    for a in result.pending_actions:
        print(f"  [confirm {a['id']}] {a['summary']}")
    for h in result.open_handoffs:
        print(f"  [open handoff] {h.to_agent}: {h.task}")
    print()


def main() -> None:
    session = Session(load_trip())
    if len(sys.argv) > 2 and sys.argv[1] == "--event":
        events = json.loads((REPO_ROOT / "fixtures" / "demo_events.json").read_text())["events"]
        for event in events:
            if sys.argv[2] in ("all", event["id"]):
                print(f"===== {event['id']}: {event['type']} =====")
                show(session.event(event, today=datetime.fromisoformat(event["at"]).date()))
        return
    print(f"Trip: {session.trip.name}. Ctrl-D to quit.")
    while True:
        try:
            message = input("you> ").strip()
        except EOFError:
            break
        if message:
            show(session.send(message, today=demo_today()))


if __name__ == "__main__":
    main()
