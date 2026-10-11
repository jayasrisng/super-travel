"""Seed the agency dashboard with the demo client from the onboarding call.

Posts Sarah Mitchell's intake (the details the onboarding page's scripted call fills in) to
the running control API, with the trip starting today so the border scenario lines up:
Sarah lands in Barcelona, messages her advisor from the customer app (/app/), and the
advisor deploys the voice agent from the dashboard. Needs the API running and
WONDER_API_TOKEN in .env.

    uv run python scripts/seed_demo.py [--with-delay]
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = os.getenv("WONDER_API_URL", "http://127.0.0.1:8000").rstrip("/") + "/v1"

SARAH = {
    "client_name": "Sarah Mitchell",
    "purpose": "Family vacation",
    "destination": "Barcelona, Spain",
    "start_date": date.today().isoformat(),
    "end_date": (date.today() + timedelta(days=6)).isoformat(),
    "traveler_configuration": {"adult_count": 1, "child_count": 1},
    "child_ages": [6],
    "accommodation_area": "Near the Gothic Quarter",
    "interests": ["Aquarium", "parks", "beaches", "local food"],
    "needs": ["Kid-friendly meals", "easy walking routes", "pharmacy access", "downtime"],
    "advisor_name": "Dana Ortiz",
    "channel": "phone_call",
}

# Optional sample disruption (fictional flight details).
DELAY = {
    "kind": "delay",
    "passengers": 2,
    "arrival_delay_minutes": 220,
    "reference": "QX7K2M",
    "flight": {"carrier_code": "VY", "number": "VY7821", "from_iata": "LHR", "to_iata": "BCN",
               "scheduled_date": date.today().isoformat()},
}


def token() -> str:
    if os.getenv("WONDER_API_TOKEN"):
        return os.environ["WONDER_API_TOKEN"]
    env = ROOT / ".env"
    for line in env.read_text().splitlines() if env.exists() else []:
        if line.startswith("WONDER_API_TOKEN="):
            return line.split("=", 1)[1].strip()
    sys.exit("Set WONDER_API_TOKEN in .env (see docs/CONTROL_API.md).")


def call(method: str, path: str, body: dict | None = None) -> dict:
    headers = {"Authorization": f"Bearer {token()}"}
    data = None
    if body is not None:
        headers |= {"Content-Type": "application/json", "Idempotency-Key": str(uuid.uuid4())}
        data = json.dumps(body).encode()
    request = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        sys.exit(f"{method} {path} failed: {exc.code} {exc.read().decode()[:300]}")
    except urllib.error.URLError:
        sys.exit(f"Control API not reachable at {API}. Start it first (see README).")


def main() -> None:
    intake = call("POST", "/intakes", SARAH)["data"]
    print(f"Intake {intake['id']} -> trip {intake['trip_id']}")
    if "--with-delay" in sys.argv:
        run = call("POST", "/agent-runs", {"agent": "manage_recover", "trip_id": intake["trip_id"],
                                           "input": {"disruption": DELAY}})["data"]
        print(f"Reported sample delay -> run {run['id']}")
    for _ in range(30):
        runs = call("GET", f"/agent-runs?trip_id={intake['trip_id']}&limit=100")["data"]
        if all(r["status"] not in ("queued", "running") for r in runs):
            break
        time.sleep(0.5)
    for r in sorted(runs, key=lambda r: r["agent"]):
        print(f"  {r['agent']:<18} {r['status']}")
    print(f"Advisor dashboard: http://localhost:5180/?intake={intake['id']}")
    print(f"Sarah's app:       http://localhost:5180/app/?intake={intake['id']}")


if __name__ == "__main__":
    main()
