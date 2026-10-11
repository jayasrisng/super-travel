import { useEffect, useState, type ReactNode } from "react";
import { agents, type Schema } from "./api";

export function Note({
  children,
  kind = "quiet",
}: {
  children: ReactNode;
  kind?: "quiet" | "error" | "sample";
}) {
  return (
    <div
      className={`note ${kind}`}
      role={kind === "error" ? "alert" : undefined}
    >
      {children}
    </div>
  );
}
export function Loading() {
  return (
    <p className="annotation" role="status">
      Turning the page…
    </p>
  );
}
export function Empty({
  title,
  children,
}: {
  title: string;
  children?: ReactNode;
}) {
  return (
    <div className="empty">
      <span className="sketch-star" aria-hidden>
        ✳
      </span>
      <h2>{title}</h2>
      <div>{children}</div>
    </div>
  );
}
export function Heading({
  eyebrow,
  title,
  note,
  children,
}: {
  eyebrow: string;
  title: string;
  note?: string;
  children?: ReactNode;
}) {
  return (
    <header className="page-heading">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        {note ? <p className="subtitle">{note}</p> : null}
      </div>
      {children}
    </header>
  );
}
export function Check({
  checked,
  label,
  onChange,
}: {
  checked: boolean;
  label: string;
  onChange: () => void;
}) {
  return (
    <button
      className={`pencil-check ${checked ? "checked" : ""}`}
      type="button"
      role="checkbox"
      aria-checked={checked}
      aria-label={label}
      onClick={onChange}
    >
      {checked ? <span aria-hidden>✓</span> : null}
    </button>
  );
}
export function Theme() {
  const [theme, setTheme] = useState(
    () => document.documentElement.dataset.theme || "light",
  );
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem("wonder.theme", theme);
    } catch {}
  }, [theme]);
  return (
    <button
      className="theme"
      aria-label={`Switch to ${theme === "light" ? "dark" : "light"} theme`}
      onClick={() => setTheme((t) => (t === "light" ? "dark" : "light"))}
    >
      {theme === "light" ? "☾" : "☀"}
      <span>{theme === "light" ? "Chalkboard" : "Paper"}</span>
    </button>
  );
}
export function Result({ value }: { value: Schema["Task"]["result"] }) {
  if (!value) return null;
  return (
    <section className="agent-result">
      <Note kind="sample">
        {value.data_mode === "fixture"
          ? "Sample proposal · no live prices or availability"
          : "Model draft · verify independently"}
      </Note>
      <p>{value.reply}</p>
      {value.assumptions.map((a, i) => (
        <p className="annotation" key={i}>
          {a}
        </p>
      ))}
      {"itinerary_items" in value ? (
        <>
          {value.itinerary_items.map((item) => (
            <div className="result-row" key={item.item_id}>
              <strong>{item.title}</strong>
              <span>
                {new Date(item.starts_at).toLocaleString(undefined, {
                  timeZone: item.timezone,
                })}
              </span>
            </div>
          ))}
          {value.checklist_tasks.map((item) => (
            <p key={item.item_id}>↳ {item.title}</p>
          ))}
        </>
      ) : null}
      {"packing_lists" in value
        ? value.packing_lists.map((list) => (
            <div key={list.item_id}>
              <h3>{list.title}</h3>
              {list.items.map((item) => (
                <p key={item.item_id}>
                  {item.quantity} × {item.title}
                </p>
              ))}
            </div>
          ))
        : null}
      {"recommendations" in value
        ? value.recommendations.map((item) => (
            <div className="result-row" key={item.id}>
              <strong>{item.title}</strong>
              <span>
                {item.duration_minutes} minutes · {item.feasibility}
              </span>
            </div>
          ))
        : null}
      {value.sources.length ? (
        <div>
          <h3>Sources consulted</h3>
          {value.sources.map((s, i) => (
            <a key={i} href={s.source_url} target="_blank" rel="noreferrer">
              {s.provider} ↗
            </a>
          ))}
        </div>
      ) : (
        <p className="annotation">
          No verified sources were consulted for this sample.
        </p>
      )}
    </section>
  );
}
export const statusLabels: Record<Schema["Task"]["status"], string> = {
  not_started: "Ready to start",
  queued: "Queued",
  agent_working: "Wonder is researching",
  needs_more_information: "Needs your input",
  ready_for_review: "Ready for review",
  waiting_for_approval: "Waiting for approval",
  completed: "Done",
  failed: "Couldn’t finish",
  cancelled: "Cancelled",
};
export function AgentSelect({
  value,
  onChange,
}: {
  value: Schema["Task"]["assigned_agent"];
  onChange: (value: Schema["Task"]["assigned_agent"]) => void;
}) {
  return (
    <label>
      Who should help?
      <select
        value={value}
        onChange={(e) =>
          onChange(e.target.value as Schema["Task"]["assigned_agent"])
        }
      >
        {Object.entries(agents).map(([key, label]) => (
          <option key={key} value={key}>
            {label}
          </option>
        ))}
      </select>
    </label>
  );
}
export function OutfitLook({
  outfit,
  items,
  small = false,
}: {
  outfit: Schema["Outfit"];
  items: Schema["WardrobeItem"][];
  small?: boolean;
}) {
  const selected = outfit.item_ids.map((id) => items.find((i) => i.id === id));
  return (
    <div
      className={`lookbook ${small ? "small" : ""}`}
      aria-label={`Illustrated outfit: ${outfit.title}`}
    >
      <span className="look-caption">look no. {outfit.id.slice(0, 4)}</span>
      <svg
        className="complete-look"
        viewBox="0 0 340 480"
        role="img"
        aria-label={`Complete outfit: ${selected
          .filter(Boolean)
          .map((item) => item!.name)
          .join(", ")}`}
      >
        <ellipse
          cx="158"
          cy="456"
          rx="91"
          ry="7"
          fill="currentColor"
          opacity=".06"
        />
        {(["bottoms", "tops", "shoes", "accessories"] as const).map(
          (category) => {
            const item = selected.find((piece) => piece?.category === category);
            if (!item) return null;
            const placement = {
              tops: {
                x: 73,
                y: 34,
                width: 170,
                height: 205,
                crop: "58 38 164 192",
              },
              bottoms: {
                x: 99,
                y: 225,
                width: 118,
                height: 199,
                crop: "82 40 118 198",
              },
              shoes: {
                x: 76,
                y: 410,
                width: 160,
                height: 66,
                crop: "50 115 180 88",
              },
              accessories: {
                x: 243,
                y: 115,
                width: 87,
                height: 130,
                crop: "30 35 220 205",
              },
            }[category];
            return (
              <svg
                key={item.id}
                x={placement.x}
                y={placement.y}
                width={placement.width}
                height={placement.height}
                viewBox={
                  item.image_mode === "illustration"
                    ? placement.crop
                    : "0 0 280 280"
                }
              >
                <image
                  href={item.image}
                  width="280"
                  height="280"
                  preserveAspectRatio="xMidYMid meet"
                />
              </svg>
            );
          },
        )}
      </svg>
      {selected.some((item) => !item) ? (
        <p>Item removed — choose a substitution.</p>
      ) : null}
      <span className="look-foot">
        a little less to pack, a little more to wear.
      </span>
    </div>
  );
}
