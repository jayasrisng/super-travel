import { useEffect, useState, type FormEvent } from "react";
import { api, agents, type Schema } from "./api";
import {
  AgentSelect,
  Check,
  Empty,
  Heading,
  Loading,
  Note,
  Result,
  statusLabels,
} from "./components";
import type { Navigate } from "./App";

export function minorAmount(text: string, currency: string) {
  const digits = currency === "JPY" ? 0 : 2;
  const expression = digits ? /^\d+(?:\.\d{1,2})?$/ : /^\d+$/;
  if (!expression.test(text))
    throw new Error(
      `Enter a positive ${currency} amount${digits ? " with at most 2 decimal places" : ""}.`,
    );
  const [whole, fraction = ""] = text.split(".");
  const value = Number(whole + fraction.padEnd(digits, "0"));
  if (!Number.isSafeInteger(value)) throw new Error("Amount is too large");
  return value;
}
function dateIn(days: number) {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}
export function TripForm({
  nav,
  profile,
  existing,
}: {
  nav: Navigate;
  profile?: Schema["Profile"];
  existing?: Schema["Trip"];
}) {
  const [step, setStep] = useState(0),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const [trip, setTrip] = useState<Schema["TripCreate"]>(() =>
    existing
      ? (({ id, owner_user_id, context_version, version, ...rest }) => rest)(
          existing,
        )
      : {
          title: "",
          destination: "Tokyo",
          start_date: dateIn(30),
          end_date: dateIn(36),
          date_certainty: "confirmed",
          timezone: "Asia/Tokyo",
          currency: "JPY",
          traveler_configuration: {
            adult_count: 2,
            child_count: 1,
            infant_count: 0,
          },
          dietary: profile?.dietary || "",
          accessibility: profile?.accessibility || "",
          travel_style: profile?.travel_style || "unhurried",
          interests: profile?.interests || ["culture", "food"],
          activities: [],
          child_ages: [],
          existing_bookings: "",
          status: "planned",
        },
  );
  const [budget, setBudget] = useState(
    existing?.budget
      ? String(
          existing.budget.amount_minor /
            (existing.currency === "JPY" ? 1 : 100),
        )
      : "",
  );
  const [ages, setAges] = useState(existing?.child_ages?.join(", ") || "");
  const [context, setContext] = useState("family");
  const change = <K extends keyof Schema["TripCreate"]>(
    key: K,
    value: Schema["TripCreate"][K],
  ) => setTrip((t) => ({ ...t, [key]: value }));
  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    if (step < 2) {
      setStep((s) => s + 1);
      return;
    }
    setBusy(true);
    try {
      const payload = {
        ...trip,
        title: trip.title || `${trip.destination || "Somewhere"} notes`,
        budget: budget
          ? {
              amount_minor: minorAmount(budget, trip.currency || "JPY"),
              currency: trip.currency || "JPY",
            }
          : null,
        child_ages: ages ? ages.split(",").map((a) => Number(a.trim())) : [],
      };
      const saved = await api<Schema["Trip"]>(
        existing ? "/consumer/trips/" + existing.id : "/consumer/trips",
        existing ? "PUT" : "POST",
        payload,
        existing?.version,
      );
      nav("/trip?trip=" + saved.id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <Heading
        eyebrow={
          existing ? "rewrite the details" : "chapter one · a new adventure"
        }
        title={existing ? "Make it your trip." : "Let’s make a little plan."}
        note="Only the essentials now. The rest can find its way onto the page."
      />
      <div className="stepper" aria-label="Onboarding progress">
        {["The possibility", "Your people", "Your kind of trip"].map(
          (title, i) => (
            <span key={i} className={step === i ? "active" : ""}>
              {i + 1}. {title}
            </span>
          ),
        )}
      </div>
      <form className="notebook-form" onSubmit={submit}>
        {error ? <Note kind="error">{error}</Note> : null}
        {step === 0 ? (
          <>
            <label>
              Where are we going?
              <input
                required
                value={trip.destination}
                onChange={(e) => change("destination", e.target.value)}
                placeholder="Tokyo, perhaps?"
              />
            </label>
            <button
              type="button"
              className="text-button"
              onClick={() => change("destination", "Undecided")}
            >
              I’m still deciding
            </button>
            <label>
              Dates
              <select
                value={trip.date_certainty}
                onChange={(e) => {
                  change(
                    "date_certainty",
                    e.target.value as Schema["TripCreate"]["date_certainty"],
                  );
                  if (e.target.value === "flexible") {
                    change("start_date", null);
                    change("end_date", null);
                  }
                }}
              >
                <option value="confirmed">Confirmed</option>
                <option value="tentative">Tentative</option>
                <option value="flexible">Flexible · decide later</option>
              </select>
            </label>
            <div className="form-pair">
              <label>
                Leaving
                <input
                  type="date"
                  required={trip.date_certainty === "confirmed"}
                  value={trip.start_date || ""}
                  onChange={(e) => change("start_date", e.target.value || null)}
                />
              </label>
              <label>
                Returning
                <input
                  type="date"
                  min={trip.start_date || undefined}
                  required={trip.date_certainty === "confirmed"}
                  value={trip.end_date || ""}
                  onChange={(e) => change("end_date", e.target.value || null)}
                />
              </label>
            </div>
            <label>
              A name for these pages
              <input
                value={trip.title}
                onChange={(e) => change("title", e.target.value)}
                placeholder="A week of Tokyo wonders"
              />
            </label>
            <div className="form-pair">
              <label>
                Local timezone
                <select
                  value={trip.timezone}
                  onChange={(e) => change("timezone", e.target.value)}
                >
                  {[
                    "Asia/Tokyo",
                    "Europe/Madrid",
                    "Europe/Lisbon",
                    "Europe/Paris",
                    "America/New_York",
                    "America/Los_Angeles",
                    "UTC",
                  ].map((z) => (
                    <option key={z}>{z}</option>
                  ))}
                </select>
              </label>
              <label>
                Trip currency
                <select
                  value={trip.currency}
                  onChange={(e) =>
                    change(
                      "currency",
                      e.target.value as Schema["TripCreate"]["currency"],
                    )
                  }
                >
                  {["JPY", "EUR", "USD"].map((c) => (
                    <option key={c}>{c}</option>
                  ))}
                </select>
              </label>
            </div>
          </>
        ) : step === 1 ? (
          <>
            <p className="hand">Who’s in this chapter?</p>
            <div className="chips">
              {[
                "solo",
                "couple",
                "friends",
                "family",
                "business",
                "multigenerational",
              ].map((c) => (
                <button
                  type="button"
                  aria-pressed={context === c}
                  key={c}
                  onClick={() => {
                    setContext(c);
                    if (c === "solo")
                      change("traveler_configuration", {
                        adult_count: 1,
                        child_count: 0,
                        infant_count: 0,
                      });
                  }}
                >
                  {c}
                </button>
              ))}
            </div>
            <p className="annotation">
              These are starting points, not boxes you have to fit.
            </p>
            <div className="form-trio">
              {(["adult_count", "child_count", "infant_count"] as const).map(
                (key, i) => (
                  <label key={key}>
                    {["Adults", "Children", "Infants"][i]}
                    <input
                      type="number"
                      min={i === 0 ? 1 : 0}
                      max={i === 2 ? 10 : 30}
                      value={trip.traveler_configuration?.[key] || 0}
                      onChange={(e) =>
                        change("traveler_configuration", {
                          adult_count: 1,
                          child_count: 0,
                          infant_count: 0,
                          ...trip.traveler_configuration,
                          [key]: Number(e.target.value),
                        })
                      }
                    />
                  </label>
                ),
              )}
            </div>
            {(trip.traveler_configuration?.child_count || 0) > 0 ? (
              <label>
                Relevant child ages · optional
                <input
                  value={ages}
                  placeholder="6, 10 — no names needed"
                  onChange={(e) => setAges(e.target.value)}
                />
              </label>
            ) : null}
            <label>
              Dietary preferences · optional
              <input
                value={trip.dietary}
                onChange={(e) => change("dietary", e.target.value)}
                placeholder="Vegetarian, perhaps"
              />
            </label>
            <label>
              Accessibility or special requirements · optional
              <textarea
                value={trip.accessibility}
                onChange={(e) => change("accessibility", e.target.value)}
                placeholder="Easy walks, step-free access, time to rest… No medical records needed."
              />
            </label>
          </>
        ) : (
          <>
            <p className="hand">Leave a little room for what you love.</p>
            <label>
              Travel style
              <select
                value={trip.travel_style}
                onChange={(e) => change("travel_style", e.target.value)}
              >
                {[
                  "unhurried",
                  "adventurous",
                  "comfort first",
                  "budget mindful",
                  "a little of everything",
                ].map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
            </label>
            <label>
              Interests
              <input
                value={trip.interests?.join(", ")}
                onChange={(e) =>
                  change(
                    "interests",
                    e.target.value
                      .split(",")
                      .map((s) => s.trim())
                      .filter(Boolean),
                  )
                }
                placeholder="Culture, coffee, nature"
              />
            </label>
            <label>
              Activities you enjoy · optional
              <input
                value={trip.activities?.join(", ")}
                onChange={(e) =>
                  change(
                    "activities",
                    e.target.value
                      .split(",")
                      .map((s) => s.trim())
                      .filter(Boolean),
                  )
                }
              />
            </label>
            <label>
              Approximate budget ({trip.currency}) · optional
              <input
                inputMode="decimal"
                value={budget}
                onChange={(e) => setBudget(e.target.value)}
                placeholder="An estimate is fine"
              />
            </label>
            <label>
              Existing bookings · optional
              <textarea
                value={trip.existing_bookings}
                onChange={(e) => change("existing_bookings", e.target.value)}
                placeholder="Hotel booked, flights still undecided. Don’t paste passports or payment details."
              />
            </label>
            <Note>
              Your checklist is a draft. You can edit every line. Wonder won’t
              book or buy anything without you.
            </Note>
          </>
        )}
        <div className="actions">
          {step > 0 ? (
            <button
              type="button"
              className="text-button"
              onClick={() => setStep((s) => s - 1)}
            >
              ← Back a page
            </button>
          ) : null}
          <button className="ink-button" disabled={busy}>
            {busy
              ? "Saving…"
              : step < 2
                ? "Next page →"
                : existing
                  ? "Save trip details"
                  : "Create my notebook →"}
          </button>
        </div>
      </form>
    </>
  );
}
export function TripPage({ id, nav }: { id: string; nav: Navigate }) {
  const [book, setBook] = useState<Schema["TripNotebook"]>(),
    [error, setError] = useState(""),
    [open, setOpen] = useState<string>(),
    [adding, setAdding] = useState(false),
    [editing, setEditing] = useState(false);
  async function refresh() {
    setBook(await api("/consumer/trips/" + id));
  }
  useEffect(() => {
    setBook(undefined);
    void refresh().catch((e) => setError(e.message));
  }, [id]);
  const active = book?.tasks.some((t) =>
    ["queued", "agent_working"].includes(t.status),
  );
  useEffect(() => {
    if (!active) return;
    const timer = setInterval(
      () => void refresh().catch((e) => setError(e.message)),
      1000,
    );
    return () => clearInterval(timer);
  }, [active, id]);
  async function decide(
    task: Schema["Task"],
    action: Schema["TaskDecision"]["action"],
  ) {
    try {
      await api(
        `/consumer/trips/${id}/tasks/${task.id}/decision`,
        "POST",
        { action },
        task.version,
      );
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    }
  }
  if (!book) return error ? <Note kind="error">{error}</Note> : <Loading />;
  if (editing) return <TripForm existing={book.trip} nav={nav} />;
  const done = book.tasks.filter((t) => t.status === "completed").length;
  return (
    <>
      <Heading
        eyebrow={`your notebook · ${book.trip.destination}`}
        title={book.trip.title}
        note={`${book.trip.start_date || "Flexible dates"} ${book.trip.end_date ? "— " + book.trip.end_date : ""} · ${book.participants.length} travelers`}
      >
        <button className="text-button" onClick={() => setEditing(true)}>
          ✎ Trip details
        </button>
      </Heading>
      <div className="trip-tools">
        <button onClick={() => nav("/wardrobe?trip=" + id)}>
          Wardrobe & outfits ↗
        </button>
        <button onClick={() => nav("/packing?trip=" + id)}>
          Packing list ↗
        </button>
        <button onClick={() => nav("/briefing?trip=" + id)}>
          Morning note ↗
        </button>
        <button onClick={() => nav("/group?trip=" + id)}>
          People & plans ↗
        </button>
      </div>
      {error ? <Note kind="error">{error}</Note> : null}
      <div className="section-heading">
        <h2>A little list for a good trip</h2>
        <span className="annotation">
          {done} of {book.tasks.length} done · one thing at a time
        </span>
      </div>
      <div className="checklist">
        {book.tasks.map((task) => (
          <div
            key={task.id}
            className={`task ${task.status === "completed" ? "done" : ""}`}
          >
            <div className="task-line">
              <Check
                checked={task.status === "completed"}
                label={`${task.status === "completed" ? "Reopen" : "Complete"} ${task.title}`}
                onChange={() =>
                  void decide(
                    task,
                    task.status === "completed" ? "reopen" : "complete",
                  )
                }
              />
              <button
                className="task-title"
                aria-expanded={open === task.id}
                onClick={() => {
                  setAdding(false);
                  setOpen(open === task.id ? undefined : task.id);
                }}
              >
                <span>{task.title}</span>
                <small>
                  {task.created_by === "wonder"
                    ? "✎ Wonder’s suggestion"
                    : "✎ Your note"}
                </small>
              </button>
              <span
                className={`annotation status-${task.status}`}
                role={
                  ["queued", "agent_working"].includes(task.status)
                    ? "status"
                    : undefined
                }
              >
                {statusLabels[task.status]}
              </span>
              <button
                className="expand-button"
                aria-label={`Open ${task.title}`}
                onClick={() => setOpen(open === task.id ? undefined : task.id)}
              >
                {open === task.id ? "−" : "+"}
              </button>
            </div>
            {open === task.id ? (
              <TaskEditor
                key={task.id}
                task={task}
                trip={book.trip}
                refresh={refresh}
                decide={decide}
                close={() => setOpen(undefined)}
                nav={nav}
              />
            ) : null}
          </div>
        ))}
      </div>
      <button
        className="add-line"
        onClick={() => {
          setAdding(!adding);
          setOpen(undefined);
        }}
      >
        + Write another note
      </button>
      {adding ? (
        <TaskEditor
          trip={book.trip}
          refresh={refresh}
          close={() => setAdding(false)}
          nav={nav}
          decide={decide}
        />
      ) : null}
      <div className="end-note hand">
        you don’t have to plan every moment.<span aria-hidden>↗</span>
      </div>
    </>
  );
}
function TaskEditor({
  task,
  trip,
  refresh,
  close,
  decide,
  nav,
}: {
  task?: Schema["Task"];
  trip: Schema["Trip"];
  refresh: () => Promise<void>;
  close: () => void;
  decide: (
    task: Schema["Task"],
    action: Schema["TaskDecision"]["action"],
  ) => Promise<void>;
  nav: Navigate;
}) {
  const [draft, setDraft] = useState<Schema["TaskCreate"]>({
    title: task?.title || "",
    description: task?.description || "",
    agent_instructions: task?.agent_instructions || "",
    assigned_agent: task?.assigned_agent || "plan_book",
    priority: task?.priority || "should",
    requires_approval: task?.requires_approval ?? true,
    due_date: task?.due_date || null,
  });
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const route = `/consumer/trips/${trip.id}/tasks`;
  async function save(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api(
        task ? route + "/" + task.id : route,
        task ? "PATCH" : "POST",
        draft,
        task?.version,
      );
      await refresh();
      if (!task) close();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function run() {
    if (!task) return;
    setBusy(true);
    setError("");
    try {
      await api(
        route + "/" + task.id + "/run",
        "POST",
        task.assigned_agent === "explore_magic"
          ? {
              magic: {
                location: trip.destination.toLowerCase().includes("tokyo")
                  ? { latitude: 35.6762, longitude: 139.6503 }
                  : { latitude: 41.385, longitude: 2.174 },
                city: trip.destination,
                timezone: trip.timezone,
                available_minutes: 120,
                interests: trip.interests,
              },
            }
          : {},
        task.version,
      );
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function remove() {
    if (!task) return;
    try {
      await api(route + "/" + task.id, "DELETE", undefined, task.version);
      await refresh();
      close();
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function cancel() {
    if (!task?.agent_run_id) return;
    try {
      const run = await api<Schema["AgentRun"]>(
        "/agent-runs/" + task.agent_run_id,
      );
      await api("/agent-runs/" + run.id + "/cancel", "POST", {}, run.version);
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    }
  }
  const dirty =
    !!task &&
    (draft.title !== task.title ||
      draft.description !== task.description ||
      draft.agent_instructions !== task.agent_instructions ||
      draft.assigned_agent !== task.assigned_agent);
  return (
    <section className="task-sheet">
      {error ? <Note kind="error">{error}</Note> : null}
      <form className="notebook-form compact" onSubmit={save}>
        <label>
          Task title
          <input
            required
            value={draft.title}
            onChange={(e) => setDraft((d) => ({ ...d, title: e.target.value }))}
            placeholder="Find a vegetarian birthday dinner for my mom in Tokyo"
          />
        </label>
        <label>
          What this task means
          <textarea
            value={draft.description}
            onChange={(e) =>
              setDraft((d) => ({ ...d, description: e.target.value }))
            }
          />
        </label>
        <label>
          What Wonder should do
          <textarea
            value={draft.agent_instructions}
            onChange={(e) =>
              setDraft((d) => ({ ...d, agent_instructions: e.target.value }))
            }
            placeholder="Research three suitable options. Present them for review; don’t book."
          />
        </label>
        <div className="form-pair">
          <AgentSelect
            value={draft.assigned_agent}
            onChange={(assigned_agent) =>
              setDraft((d) => ({ ...d, assigned_agent }))
            }
          />
          <label>
            Priority
            <select
              value={draft.priority}
              onChange={(e) =>
                setDraft((d) => ({
                  ...d,
                  priority: e.target.value as Schema["TaskCreate"]["priority"],
                }))
              }
            >
              <option value="must">Important</option>
              <option value="should">Useful</option>
              <option value="could">Nice to have</option>
            </select>
          </label>
        </div>
        <label>
          Due date · optional
          <input
            type="date"
            value={draft.due_date || ""}
            onChange={(e) =>
              setDraft((d) => ({ ...d, due_date: e.target.value || null }))
            }
          />
        </label>
        <div className="actions">
          <button className="outline-button" disabled={busy}>
            Save {task ? "changes" : "note"}
          </button>
          {task ? (
            <button
              type="button"
              className="ink-button"
              onClick={() => void run()}
              disabled={
                busy ||
                dirty ||
                ["queued", "agent_working"].includes(task.status)
              }
            >
              {task.agent_run_id ? "Rerun Wonder" : "Ask Wonder →"}
            </button>
          ) : null}
        </div>
        {dirty ? (
          <p className="annotation">
            Save your instructions before asking Wonder.
          </p>
        ) : null}
      </form>
      {task ? (
        <>
          <p className="annotation">
            {agents[task.assigned_agent]} · {statusLabels[task.status]}
          </p>
          {["queued", "agent_working"].includes(task.status) ? (
            <button onClick={() => void cancel()}>Cancel this run</button>
          ) : null}
          <Result value={task.result} />
          {task.status === "ready_for_review" ? (
            <>
              <Note>
                Accepting a draft saves proposed itinerary notes. It doesn’t
                book, buy or send anything. Complete the task yourself when it’s
                actually done.
              </Note>
              <div className="actions">
                <button
                  className="outline-button"
                  onClick={() => void decide(task, "approve")}
                >
                  Accept draft
                </button>
                <button onClick={() => void decide(task, "reject")}>
                  Reject proposal
                </button>
              </div>
            </>
          ) : null}
          <div className="actions">
            <button
              onClick={() =>
                void decide(
                  task,
                  task.status === "completed" ? "reopen" : "complete",
                )
              }
            >
              {task.status === "completed"
                ? "Reopen task"
                : "Mark complete myself"}
            </button>
            <button onClick={() => nav("/wardrobe?trip=" + trip.id)}>
              Open wardrobe ↗
            </button>
            <button className="danger" onClick={() => void remove()}>
              Delete note
            </button>
          </div>
          <details>
            <summary>
              Execution history · {(task.history || []).length} entries
            </summary>
            {(task.history || []).map((entry, i) => (
              <p className="annotation" key={i}>
                {String(entry.status || entry.action)} ·{" "}
                {String(entry.message || entry.at)}
              </p>
            ))}
          </details>
        </>
      ) : null}
    </section>
  );
}
