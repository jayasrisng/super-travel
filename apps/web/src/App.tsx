import { useEffect, useState } from "react";
import { api, type Schema } from "./api";
import { Heading, Note, Loading, Empty, Theme } from "./components";
import { TripForm, TripPage } from "./trip";
import { GroupPage } from "./group";
import { Wardrobe, Outfits, Packing, Briefing, Preferences } from "./wardrobe";
import { Magic } from "./magic";

export type Navigate = (path: string) => void;
export default function App() {
  const [path, setPath] = useState(location.pathname + location.search);
  const [home, setHome] = useState<Schema["Home"]>();
  const [error, setError] = useState("");
  const [ready, setReady] = useState(false);
  const nav: Navigate = (p) => {
    history.pushState({}, "", p);
    setPath(p);
    window.scrollTo({ top: 0, behavior: "instant" });
  };
  useEffect(() => {
    const onPop = () => setPath(location.pathname + location.search);
    addEventListener("popstate", onPop);
    return () => removeEventListener("popstate", onPop);
  }, []);
  async function refresh() {
    setHome(await api<Schema["Home"]>("/consumer/home"));
  }
  async function start() {
    setError("");
    try {
      await api("/demo/session", "POST", {});
      await refresh();
      setReady(true);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  useEffect(() => {
    if (!path.startsWith("/share/")) void start();
    else setReady(true);
  }, []);
  useEffect(() => {
    if (ready && !path.startsWith("/share/"))
      void refresh().catch((e) => setError(e.message));
  }, [path, ready]);
  const url = new URL(path, location.origin);
  const tripId = url.searchParams.get("trip") || undefined;
  const view = url.pathname.split("/")[1] || "home";
  return (
    <>
      <a className="skip" href="#notebook">
        Skip to notebook
      </a>
      <div className="app-shell">
        <header className="masthead">
          <button
            className="wordmark"
            onClick={() => nav("/")}
            aria-label="Wonder home"
          >
            wonder<span className="brand-star">✳</span>
          </button>
          <nav aria-label="Main navigation">
            <button
              aria-current={view === "home" ? "page" : undefined}
              onClick={() => nav("/")}
            >
              Home
            </button>
            <button
              aria-current={
                ["trip", "packing", "briefing", "group"].includes(view)
                  ? "page"
                  : undefined
              }
              onClick={() =>
                nav(
                  home?.trips.length
                    ? "/trip?trip=" + home.trips[home.trips.length - 1].id
                    : "/new",
                )
              }
            >
              My notebook
            </button>
            <button
              aria-current={view === "magic" ? "page" : undefined}
              onClick={() => nav("/magic" + (tripId ? "?trip=" + tripId : ""))}
            >
              Magic <span aria-hidden>✧</span>
            </button>
          </nav>
          <Theme />
        </header>
        <main id="notebook">
          <div className="edition">
            <span>Your personal travel notebook</span>
            <span>Local demo · sample travel data</span>
          </div>
          {error ? (
            <Note kind="error">
              {error} <button onClick={() => void start()}>Try again</button>
            </Note>
          ) : null}
          {!ready ? (
            <>
              <Loading />
              {error ? (
                <p>
                  Run the local consumer server, then try again. Setup is in
                  README.
                </p>
              ) : null}
            </>
          ) : view === "share" ? (
            <Shared token={url.pathname.split("/")[2]} />
          ) : !home ? (
            <Loading />
          ) : view === "home" ? (
            <Home home={home} nav={nav} />
          ) : view === "new" ? (
            <TripForm nav={nav} profile={home.profile} />
          ) : view === "trip" && tripId ? (
            <TripPage id={tripId} nav={nav} />
          ) : view === "wardrobe" ? (
            <Wardrobe nav={nav} tripId={tripId} />
          ) : view === "outfits" ? (
            <Outfits key={tripId || "standalone"} nav={nav} tripId={tripId} />
          ) : view === "packing" && tripId ? (
            <Packing nav={nav} tripId={tripId} />
          ) : view === "briefing" && tripId ? (
            <Briefing nav={nav} tripId={tripId} />
          ) : view === "magic" ? (
            <Magic tripId={tripId} />
          ) : view === "group" && tripId ? (
            <GroupPage id={tripId} />
          ) : view === "preferences" ? (
            <Preferences profile={home.profile} refresh={refresh} nav={nav} />
          ) : (
            <Empty title="This page needs a trip">
              <button onClick={() => nav("/")}>Back home</button>
            </Empty>
          )}
        </main>
        <footer className="site-foot">
          <p>Less searching. More experiencing.</p>
          <button onClick={() => nav("/wardrobe")}>My wardrobe ↗</button>
          <button onClick={() => nav("/preferences")}>Preferences</button>
          <span>made for the moments in between.</span>
        </footer>
      </div>
    </>
  );
}
function Home({ home, nav }: { home: Schema["Home"]; nav: Navigate }) {
  return (
    <>
      <Heading
        eyebrow="a place for your next chapter"
        title="Where shall we go?"
        note="Big adventures. Small discoveries. Everything in one little notebook."
      >
        <button className="ink-button" onClick={() => nav("/new")}>
          + New trip
        </button>
      </Heading>
      <div className="home-note">
        <p className="hand">A good trip starts with a little wonder.</p>
        <span className="doodle" aria-hidden>
          ↗<br />✳
        </span>
      </div>
      <section aria-label="Your trips" className="trip-list">
        <div className="section-heading">
          <h2>Your journeys</h2>
          <span className="annotation">
            {home.trips.length
              ? `${home.trips.length} chapters, and counting`
              : "the first page is yours"}
          </span>
        </div>
        {home.trips.length ? (
          [...home.trips].reverse().map((trip) => {
            const tasks = home.tasks.filter((t) => t.trip_id === trip.id);
            const done = tasks.filter((t) => t.status === "completed").length;
            const next = tasks.find((t) => t.status !== "completed");
            return (
              <button
                className="trip-line"
                key={trip.id}
                onClick={() => nav("/trip?trip=" + trip.id)}
              >
                <span className="trip-number">
                  {trip.destination.slice(0, 2).toUpperCase()}
                </span>
                <span>
                  <strong>{trip.title}</strong>
                  <small>
                    {trip.start_date
                      ? `${trip.start_date} — ${trip.end_date || "open-ended"}`
                      : "Dates are still a possibility"}{" "}
                    ·{" "}
                    {(trip.traveler_configuration?.adult_count ?? 1) +
                      (trip.traveler_configuration?.child_count ?? 0) +
                      (trip.traveler_configuration?.infant_count ?? 0)}{" "}
                    travelers
                  </small>
                  <span className="trip-next">
                    Next: {next?.title || "Enjoy the trip."}
                  </span>
                </span>
                <span className="trip-progress">
                  <span>
                    {done} / {tasks.length} notes done
                  </span>
                  <span className="progress-track">
                    <i
                      style={{
                        width: `${tasks.length ? (done / tasks.length) * 100 : 0}%`,
                      }}
                    />
                  </span>
                </span>
                <span className="arrow" aria-hidden>
                  ↗
                </span>
              </button>
            );
          })
        ) : (
          <Empty title="An unwritten adventure">
            <p>Create a trip, or discover something lovely close to home.</p>
            <button className="ink-button" onClick={() => nav("/new")}>
              Write your first trip
            </button>
          </Empty>
        )}
      </section>
      <button className="magic-invitation" onClick={() => nav("/magic")}>
        <span aria-hidden className="magic-symbol">
          ✧
        </span>
        <span>
          <h2>A little time. A little Magic.</h2>
          <p>A coffee, a museum, a moment you didn’t plan. Discover nearby.</p>
        </span>
        <span className="arrow" aria-hidden>
          ↗
        </span>
      </button>
      <div className="home-bottom">
        <button onClick={() => nav("/wardrobe")}>
          <h3>The fashion sketchbook</h3>
          <p>
            {home.wardrobe_count} pieces. Many possibilities. Pack a little
            lighter. ↗
          </p>
        </button>
        <span className="hand">
          collect moments,
          <br />
          not open tabs.
        </span>
      </div>
    </>
  );
}
function Shared({ token }: { token: string }) {
  const [data, setData] = useState<Schema["SharedNotebook"]>();
  const [error, setError] = useState("");
  useEffect(() => {
    void api<Schema["SharedNotebook"]>("/consumer/share/" + token)
      .then(setData)
      .catch((e) => setError(e.message));
  }, [token]);
  return error ? (
    <Note kind="error">{error}</Note>
  ) : !data ? (
    <Loading />
  ) : (
    <>
      <Heading
        eyebrow="a shared page · read only"
        title={data.title}
        note={`${data.destination} · ${data.start_date || "Flexible dates"}`}
      />
      <Note>
        Only the itinerary is shared. Personal tasks, wardrobe, preferences and
        expenses stay private.
      </Note>
      {data.itinerary.map((item) => (
        <p className="result-row" key={item.id}>
          {item.day} · {item.local_time} — {item.title}
        </p>
      ))}
    </>
  );
}
