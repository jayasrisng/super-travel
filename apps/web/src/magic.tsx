import { useEffect, useState, type FormEvent } from "react";
import { api, type Schema } from "./api";
import { Empty, Heading, Loading, Note } from "./components";

type Saved = Schema["SavedExperience"];
const cities: Record<
  string,
  { latitude: number; longitude: number; timezone: string; currency: string }
> = {
  Tokyo: {
    latitude: 35.6812,
    longitude: 139.7671,
    timezone: "Asia/Tokyo",
    currency: "JPY",
  },
  Barcelona: {
    latitude: 41.3874,
    longitude: 2.1686,
    timezone: "Europe/Madrid",
    currency: "EUR",
  },
  Lisbon: {
    latitude: 38.7223,
    longitude: -9.1393,
    timezone: "Europe/Lisbon",
    currency: "EUR",
  },
  "New York": {
    latitude: 40.7128,
    longitude: -74.006,
    timezone: "America/New_York",
    currency: "USD",
  },
};
export function Magic({ tripId }: { tripId?: string }) {
  const [city, setCity] = useState(tripId ? "Tokyo" : "Barcelona"),
    [latitude, setLatitude] = useState(tripId ? 35.6812 : 41.3874),
    [longitude, setLongitude] = useState(tripId ? 139.7671 : 2.1686),
    [minutes, setMinutes] = useState(120),
    [interests, setInterests] = useState("coffee, museums, outdoors"),
    [mode, setMode] = useState<"walk" | "transit">("walk"),
    [budget, setBudget] = useState(""),
    [commitment, setCommitment] = useState(""),
    [run, setRun] = useState<Schema["AgentRun"]>(),
    [saved, setSaved] = useState<Saved[]>([]),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [detail, setDetail] = useState<string>();
  async function refresh() {
    setSaved(await api("/me/saved-experiences"));
  }
  useEffect(() => {
    void refresh().catch((e) => setError(e.message));
    if (tripId)
      void api<Schema["TripNotebook"]>("/consumer/trips/" + tripId)
        .then((book) => {
          if (cities[book.trip.destination]) chooseCity(book.trip.destination);
        })
        .catch((e) => setError(e.message));
  }, [tripId]);
  useEffect(() => {
    if (!run || !["queued", "running"].includes(run.status)) return;
    const timer = setTimeout(() => {
      void api<Schema["AgentRun"]>("/agent-runs/" + run.id)
        .then(setRun)
        .catch((e) => setError(e.message));
    }, 800);
    return () => clearTimeout(timer);
  }, [run]);
  function chooseCity(value: string) {
    setCity(value);
    setLatitude(cities[value].latitude);
    setLongitude(cities[value].longitude);
  }
  async function search(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const config = cities[city];
      setRun(
        await api("/magic/runs", "POST", {
          trip_id: tripId || null,
          city,
          timezone: config.timezone,
          location: { latitude, longitude },
          available_minutes: minutes,
          interests: interests
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean),
          travel_mode: mode,
          budget: budget
            ? {
                amount_minor: Math.round(
                  Number(budget) * (config.currency === "JPY" ? 1 : 100),
                ),
                currency: config.currency,
              }
            : null,
          next_commitment: commitment
            ? {
                starts_at: new Date(commitment).toISOString(),
                location: { latitude, longitude },
              }
            : null,
          buffer_minutes: 15,
          allow_unknown_feasibility: false,
        }),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function save(id: string) {
    if (!run) return;
    try {
      await api("/me/saved-experiences", "POST", {
        run_id: run.id,
        recommendation_id: id,
      });
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function remove(item: Saved) {
    try {
      await api(
        "/me/saved-experiences/" + item.id,
        "DELETE",
        undefined,
        item.version,
      );
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function locate() {
    if (!navigator.geolocation) {
      setError("Location is unavailable. Enter an origin below.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLatitude(position.coords.latitude);
        setLongitude(position.coords.longitude);
      },
      () =>
        setError(
          "Location permission was not granted. Manual origin still works.",
        ),
    );
  }
  const working = !!run && ["queued", "running"].includes(run.status);
  const proposal =
    run?.proposal && "recommendations" in run.proposal ? run.proposal : null;
  return (
    <>
      <Heading
        eyebrow="for the moments in between"
        title="A little unexpected."
        note="Tell us where you are, and how much time you have. Let the day surprise you."
      />
      <div className="magic-layout">
        <form className="notebook-form magic-form" onSubmit={search}>
          <label>
            Your city
            <select value={city} onChange={(e) => chooseCity(e.target.value)}>
              {Object.keys(cities).map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </label>
          <div className="form-pair">
            <label>
              Latitude
              <input
                required
                type="number"
                step="any"
                min="-90"
                max="90"
                value={latitude}
                onChange={(e) => setLatitude(Number(e.target.value))}
              />
            </label>
            <label>
              Longitude
              <input
                required
                type="number"
                step="any"
                min="-180"
                max="180"
                value={longitude}
                onChange={(e) => setLongitude(Number(e.target.value))}
              />
            </label>
          </div>
          <button
            type="button"
            className="text-button"
            onClick={() => void locate()}
          >
            Use my current location ↗
          </button>
          <label>
            Time to wander
            <select
              value={minutes}
              onChange={(e) => setMinutes(Number(e.target.value))}
            >
              {[30, 60, 90, 120, 180, 240].map((n) => (
                <option key={n} value={n}>
                  {n} minutes
                </option>
              ))}
            </select>
          </label>
          <label>
            What are you in the mood for?
            <input
              value={interests}
              onChange={(e) => setInterests(e.target.value)}
            />
          </label>
          <div className="form-pair">
            <label>
              Getting around
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value as "walk" | "transit")}
              >
                <option value="walk">On foot</option>
                <option value="transit">Public transport</option>
              </select>
            </label>
            <label>
              Budget ({cities[city].currency})
              <input
                type="number"
                min="0"
                step={cities[city].currency === "JPY" ? "1" : ".01"}
                value={budget}
                onChange={(e) => setBudget(e.target.value)}
                placeholder="Optional"
              />
            </label>
          </div>
          <details>
            <summary>Something to get back to?</summary>
            <label>
              Next commitment (your device’s local time)
              <input
                type="datetime-local"
                value={commitment}
                onChange={(e) => setCommitment(e.target.value)}
              />
              <small>
                At this same origin. A 15-minute buffer is included.
              </small>
            </label>
          </details>
          <button disabled={busy || working} className="ink-button">
            {busy || working ? "Finding your moment…" : "Find a little Magic ✧"}
          </button>
          <Note kind="sample">
            Illustrative places, routes, hours and costs. Live event sources are
            not connected. No reservations are made.
          </Note>
        </form>
        <section className="magic-results" aria-live="polite">
          {error ? <Note kind="error">{error}</Note> : null}
          {working ? (
            <Loading />
          ) : run?.status === "failed" ? (
            <Note kind="error">
              {run.error?.message || "Discovery failed. Try again."}
            </Note>
          ) : proposal ? (
            <>
              <p className="hand">a few possibilities for your day.</p>
              {proposal.warnings.map((warning, i) => (
                <Note key={i}>{warning}</Note>
              ))}
              {proposal.recommendations.length ? (
                proposal.recommendations.map((item) => {
                  const expired = new Date(item.valid_until) < new Date();
                  const isSaved = saved.some(
                    (s) => s.recommendation_id === item.id,
                  );
                  return (
                    <article className="discovery" key={item.id}>
                      <div className="discovery-top">
                        <span className="discovery-number">0{item.rank}</span>
                        <span>
                          <p className="eyebrow">{item.category} · sample</p>
                          <h2>{item.title}</h2>
                        </span>
                      </div>
                      <p>{item.reason}</p>
                      <p className="annotation">
                        {item.outbound_minutes ?? "?"} min to arrive ·{" "}
                        {item.duration_minutes} min here ·{" "}
                        {item.slack_minutes ?? "?"} min spare
                      </p>
                      <p>
                        {item.cost
                          ? `${item.cost.currency} ${(item.cost.amount_minor / (item.cost.currency === "JPY" ? 1 : 100)).toLocaleString()} estimated`
                          : "Cost unknown"}{" "}
                        ·{" "}
                        {expired
                          ? "Expired — search again"
                          : "Feasibility uses simulated data"}
                      </p>
                      <div className="actions">
                        <button
                          className="outline-button"
                          disabled={expired || isSaved}
                          onClick={() => void save(item.id)}
                        >
                          {isSaved ? "Saved ✓" : "Save moment"}
                        </button>
                        <a
                          href={`https://www.google.com/maps/dir/?api=1&destination=${item.location.latitude},${item.location.longitude}`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Navigate ↗
                        </a>
                        <button
                          onClick={() =>
                            setDetail(detail === item.id ? undefined : item.id)
                          }
                        >
                          View details
                        </button>
                      </div>
                      {detail === item.id ? (
                        <div className="discovery-details">
                          {item.assumptions.map((s, i) => (
                            <p key={i}>{s}</p>
                          ))}
                          {item.provenance.map((source, i) => (
                            <p key={i}>
                              <a
                                href={source.source_url}
                                target="_blank"
                                rel="noreferrer"
                              >
                                {source.provider} ↗
                              </a>{" "}
                              · {source.data_mode} · {source.availability}
                            </p>
                          ))}
                          <p>
                            Valid until{" "}
                            {new Date(item.valid_until).toLocaleTimeString()}.
                            Booking is unavailable for sample places.
                          </p>
                        </div>
                      ) : null}
                    </article>
                  );
                })
              ) : (
                <Empty title="Nothing comfortably fits">
                  Try a little more time, a different origin, or a wider budget.
                </Empty>
              )}
            </>
          ) : (
            <Empty title="Leave a little room for wonder">
              A nearby moment, at home or away. Start with a city and some time.
            </Empty>
          )}
          {saved.length ? (
            <section className="saved-moments">
              <h2>Moments to remember</h2>
              {saved
                .filter((s) => !tripId || s.trip_id === tripId)
                .map((item) => (
                  <div className="result-row" key={item.id}>
                    <span>
                      {item.title}
                      <small> · saved sample</small>
                    </span>
                    <button
                      aria-label={"Remove " + item.title}
                      onClick={() => void remove(item)}
                    >
                      Remove
                    </button>
                  </div>
                ))}
            </section>
          ) : null}
        </section>
      </div>
    </>
  );
}
