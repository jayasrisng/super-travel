import { useEffect, useState } from "react";
import { api, type Schema } from "./api";
import { Heading, Loading, Note } from "./components";
import { minorAmount } from "./trip";
export function GroupPage({ id }: { id: string }) {
  const [book, setBook] = useState<Schema["TripNotebook"]>(),
    [error, setError] = useState(""),
    [share, setShare] = useState<Schema["ShareCreated"]>();
  const [label, setLabel] = useState(""),
    [arrive, setArrive] = useState(""),
    [depart, setDepart] = useState(""),
    [title, setTitle] = useState(""),
    [amount, setAmount] = useState("");
  async function refresh() {
    setBook(await api("/consumer/trips/" + id));
  }
  useEffect(() => {
    void refresh().catch((e) => setError(e.message));
  }, [id]);
  async function action(operation: () => Promise<unknown>) {
    try {
      await operation();
      await refresh();
      setError("");
    } catch (e) {
      setError((e as Error).message);
    }
  }
  if (!book) return <Loading />;
  return (
    <>
      <Heading
        eyebrow="shared moments, simple plans"
        title="Who’s coming along?"
        note="Partial-trip dates and exact shared expenses. No money is moved."
      />
      {error ? <Note kind="error">{error}</Note> : null}
      <section className="ruled-section">
        <h2>People</h2>
        {book.participants.map((p) => (
          <p className="result-row" key={p.id}>
            <strong>{p.label}</strong>
            <span>
              {p.arrive || "Whole trip"} {p.depart ? "— " + p.depart : ""}
            </span>
          </p>
        ))}
        <form
          className="notebook-form"
          onSubmit={(e) => {
            e.preventDefault();
            void action(() =>
              api("/consumer/trips/" + id + "/participants", "POST", {
                label,
                arrive: arrive || null,
                depart: depart || null,
              }),
            );
            setLabel("");
          }}
        >
          <label>
            Participant label
            <input
              required
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="A friend joining for the weekend"
            />
          </label>
          <div className="form-pair">
            <label>
              Joining
              <input
                type="date"
                value={arrive}
                onChange={(e) => setArrive(e.target.value)}
              />
            </label>
            <label>
              Leaving
              <input
                type="date"
                value={depart}
                onChange={(e) => setDepart(e.target.value)}
              />
            </label>
          </div>
          <button className="outline-button">Add traveler</button>
        </form>
      </section>
      <section className="ruled-section">
        <h2>Shared expenses</h2>
        {book.expenses.map((expense) => (
          <p className="result-row" key={expense.id}>
            {expense.title}
            <span>
              {expense.money.amount_minor /
                (expense.money.currency === "JPY" ? 1 : 100)}{" "}
              {expense.money.currency} · {expense.split_between.length} shares
            </span>
          </p>
        ))}
        <form
          className="notebook-form"
          onSubmit={(e) => {
            e.preventDefault();
            void action(() =>
              api("/consumer/trips/" + id + "/expenses", "POST", {
                title,
                money: {
                  amount_minor: minorAmount(amount, book.trip.currency),
                  currency: book.trip.currency,
                },
                paid_by: book.participants[0].id,
                split_between: book.participants.map((p) => p.id),
              }),
            );
            setTitle("");
            setAmount("");
          }}
        >
          <label>
            Expense
            <input
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Museum tickets"
            />
          </label>
          <label>
            Amount ({book.trip.currency})
            <input
              required
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              inputMode="decimal"
            />
          </label>
          <p className="annotation">
            First traveler pays; split equally among listed travelers with exact
            minor-unit rounding.
          </p>
          <button className="outline-button">Record expense</button>
        </form>
      </section>
      <TravelPlans book={book} action={action} />
      <section>
        <h2>A page to share</h2>
        <Note>
          A read-only, one-day itinerary link. Private tasks, budget, wardrobe
          and people aren’t shared.
        </Note>
        {share ? (
          <div className="share-link">
            <input
              aria-label="Read-only share link"
              readOnly
              value={location.origin + "/share/" + share.token}
            />
            <button
              onClick={() =>
                void navigator.clipboard.writeText(
                  location.origin + "/share/" + share.token,
                )
              }
            >
              Copy link
            </button>
            <button
              onClick={() =>
                void action(async () => {
                  await api(
                    `/consumer/trips/${id}/shares/${share.id}`,
                    "DELETE",
                    undefined,
                    share.version,
                  );
                  setShare(undefined);
                })
              }
            >
              Revoke link
            </button>
          </div>
        ) : (
          <button
            className="outline-button"
            onClick={() =>
              void action(async () =>
                setShare(
                  await api("/consumer/trips/" + id + "/shares", "POST", {}),
                ),
              )
            }
          >
            Create read-only invitation
          </button>
        )}
      </section>
    </>
  );
}

function TravelPlans({
  book,
  action,
}: {
  book: Schema["TripNotebook"];
  action: (operation: () => Promise<unknown>) => Promise<void>;
}) {
  const [title, setTitle] = useState(""),
    [day, setDay] = useState(book.trip.start_date || ""),
    [time, setTime] = useState("10:00"),
    [people, setPeople] = useState<string[]>([]),
    [segment, setSegment] = useState(""),
    [destination, setDestination] = useState(book.trip.destination),
    [start, setStart] = useState(book.trip.start_date || ""),
    [end, setEnd] = useState(book.trip.end_date || "");
  return (
    <section className="ruled-section">
      <h2>Pages in the itinerary</h2>
      {book.itinerary.map((item) => (
        <p className="result-row" key={item.id}>
          {item.day} · {item.local_time}
          <strong>{item.title}</strong>
        </p>
      ))}
      <details>
        <summary>Write an itinerary note</summary>
        <form
          className="notebook-form"
          onSubmit={(e) => {
            e.preventDefault();
            void action(() =>
              api(`/consumer/trips/${book.trip.id}/itinerary`, "POST", {
                title,
                day,
                local_time: time,
                participant_ids: people,
              }),
            );
          }}
        >
          <label>
            Activity title
            <input
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </label>
          <div className="form-pair">
            <label>
              Activity day
              <input
                type="date"
                required
                min={book.trip.start_date || undefined}
                max={book.trip.end_date || undefined}
                value={day}
                onChange={(e) => setDay(e.target.value)}
              />
            </label>
            <label>
              Local time
              <input
                type="time"
                required
                value={time}
                onChange={(e) => setTime(e.target.value)}
              />
            </label>
          </div>
          <fieldset>
            <legend>Assigned travelers · optional</legend>
            {book.participants.map((person) => (
              <label className="checkbox-label" key={person.id}>
                <input
                  type="checkbox"
                  checked={people.includes(person.id)}
                  onChange={(e) =>
                    setPeople((ids) =>
                      e.target.checked
                        ? [...ids, person.id]
                        : ids.filter((id) => id !== person.id),
                    )
                  }
                />
                {person.label}
              </label>
            ))}
          </fieldset>
          <button className="outline-button">Save itinerary note</button>
        </form>
      </details>
      <h2>Trip chapters</h2>
      {book.segments.map((item) => (
        <p className="result-row" key={item.id}>
          <strong>
            {item.title} · {item.destination}
          </strong>
          <span>
            {item.start_date} — {item.end_date}
          </span>
        </p>
      ))}
      <details>
        <summary>Add a destination segment</summary>
        <form
          className="notebook-form"
          onSubmit={(e) => {
            e.preventDefault();
            void action(() =>
              api(`/consumer/trips/${book.trip.id}/segments`, "POST", {
                title: segment,
                destination,
                start_date: start,
                end_date: end,
              }),
            );
          }}
        >
          <label>
            Chapter name
            <input
              required
              value={segment}
              onChange={(e) => setSegment(e.target.value)}
            />
          </label>
          <label>
            Chapter destination
            <input
              required
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
            />
          </label>
          <div className="form-pair">
            <label>
              Chapter starts
              <input
                type="date"
                required
                value={start}
                onChange={(e) => setStart(e.target.value)}
              />
            </label>
            <label>
              Chapter ends
              <input
                type="date"
                required
                min={start || undefined}
                value={end}
                onChange={(e) => setEnd(e.target.value)}
              />
            </label>
          </div>
          <button className="outline-button">Save chapter</button>
        </form>
      </details>
    </section>
  );
}
