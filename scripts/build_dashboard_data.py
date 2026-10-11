"""Build dashboard/data/demo.json from the demo fixtures plus REAL deterministic code.

Computed by our code (not authored): EU261 assessment, baggage rights, settle-up, FX rate,
eSIM plan search, emergency numbers. Agent narratives come from fixtures/demo_agent_outputs.json.

    uv run python scripts/build_dashboard_data.py
"""

import json
from datetime import datetime, timezone

from super_travel.agents.essentials import tools as essentials_tools
from super_travel.agents.recovery.tools import RecoveryTools
from super_travel.core.tools.fx import fetch_rate
from super_travel.core.trip_context import REPO_ROOT, load_trip

FALLBACK_EUR_USD = 1.12


def main() -> None:
    trip = load_trip()
    authored = json.loads((REPO_ROOT / "fixtures" / "demo_agent_outputs.json").read_text())
    events = json.loads((REPO_ROOT / "fixtures" / "demo_events.json").read_text())["events"]

    try:
        rate, as_of = fetch_rate("EUR", "USD")
        fx = {"rate": rate, "as_of": as_of, "source": "ECB via frankfurter.dev", "live": True}
    except Exception:
        rate = FALLBACK_EUR_USD
        fx = {"rate": rate, "as_of": None, "source": "fallback constant", "live": False}
    convert = lambda amount, frm, to: amount * (rate if (frm, to) == ("EUR", "USD") else 1.0)  # noqa: E731

    tools = RecoveryTools(trip, convert_fn=convert)
    delay = events[0]["data"]
    compensation = json.loads(tools.check_compensation("s2", "delay", arrival_delay_minutes=delay["arrival_delay_minutes"],
                                                       extraordinary_circumstances=delay["extraordinary_circumstances"]))
    baggage = json.loads(tools.get_baggage_rights("delayed"))
    settle_before = json.loads(tools.reconcile_expenses())
    receipt = events[2]["data"]
    tools.record_expense("Farmàcia Gràcia (delayed bag essentials)", receipt["amount"], receipt["currency"], receipt["traveler_id"],
                         "2026-11-17", "delayed_baggage", incident_id="i1", claimable=True)
    settle_after = json.loads(tools.reconcile_expenses())
    spent_usd = round(sum(convert(e["amount"], e["currency"], "USD") for e in trip.expenses), 2)

    days = (trip.destinations[-1].depart - trip.destinations[0].arrive).days + 1
    esim = json.loads(essentials_tools.find_esim_plans([d.country for d in trip.destinations], days))
    countries = {d.country: json.loads(essentials_tools.get_country_info(d.country)) for d in trip.destinations}

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "notice": "Demo scenario. Agent narratives are sample outputs; figures marked computed come from Wonder's rules code. Flight status, eSIM plans and shop links are mock data.",
        **{k: authored[k] for k in ("agency", "onboarding", "agents", "stages")},
        "trip": json.loads(trip.model_dump_json()),
        "events": events,
        "computed": {
            "fx_eur_usd": fx,
            "compensation": {"s2_delay": compensation},
            "baggage": {"delayed": baggage},
            "settle_up": {"before_receipt": settle_before, "after_receipt": settle_after},
            "budget": {"total_usd": trip.budget["total"], "spent_usd": spent_usd},
            "esim": esim,
            "countries": countries,
        },
    }
    path = REPO_ROOT / "dashboard" / "data" / "demo.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {path.relative_to(REPO_ROOT)} (EUR->USD {rate}, live={fx['live']})")
    print("EU261:", compensation["assessments"][0]["total"], "EUR · settle-up:", settle_after["transfers"])


if __name__ == "__main__":
    main()
