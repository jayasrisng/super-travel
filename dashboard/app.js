// Wonder Agency Console: live view of the five agents for each client intake.
// Reads the control API through the dashboard server's /api proxy (the token stays server-side).

const AGENTS = [
  { key: "plan_book", num: "01", title: "Plan & Book", tagline: "From idea to a bookable trip" },
  { key: "pack_shop", num: "02", title: "Pack & Shop", tagline: "Never forget the important thing" },
  { key: "explore_magic", num: "03", title: "Explore & Experience", tagline: "Make the most of every day" },
  { key: "travel_essentials", num: "04", title: "Travel Essentials", tagline: "Arrive prepared, travel confidently" },
  { key: "manage_recover", num: "05", title: "Manage & Recover", tagline: "Handle what doesn't go to plan" },
];
const AGENT = Object.fromEntries(AGENTS.map((a) => [a.key, a]));
const ACTIVE = ["queued", "running"];
const TOPICS = { payments_currency: "Money", connectivity: "Connectivity", health: "Health", insurance: "Insurance", safety: "Safety", customs_etiquette: "Customs", language: "Language", emergency: "Emergency" };
const MAGIC_CENTERS = { barcelona: { latitude: 41.3851, longitude: 2.1734 } };

const store = {
  get(key, fallback) { try { const v = localStorage.getItem(key); return v === null ? fallback : JSON.parse(v); } catch { return fallback; } },
  set(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* storage unavailable */ } },
};

const state = {
  agentsInfo: [], intakes: [], intake: null, trip: null, runs: [],
  agent: store.get("wonder.agent", "plan_book"), decisions: store.get("wonder.decisions", {}),
  poll: null, error: null,
};

// ---------- helpers ----------
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const ms = (iso) => new Date(iso).getTime();
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const civil = (iso) => { const [y, m, d] = iso.split("-").map(Number); return { y, m, d }; };
const dateLabel = (iso) => { const { m, d } = civil(iso); return `${MONTHS[m - 1]} ${d}`; };
const rangeLabel = (a, b) => `${dateLabel(a)} – ${dateLabel(b)}, ${civil(b).y}`;
const timeIn = (iso, tz) => new Intl.DateTimeFormat("en-US", { timeZone: tz, month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", hour12: false }).format(new Date(iso));
const localTime = (iso) => new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", hour12: false }).format(new Date(iso));
function money(m) {
  if (!m) return "";
  const fmt = new Intl.NumberFormat("en-US", { style: "currency", currency: m.currency });
  const digits = fmt.resolvedOptions().maximumFractionDigits;
  return fmt.format(m.amount_minor / 10 ** digits);
}
const city = (destination) => (destination || "").split(",")[0].trim();
const firstName = (name) => (name || "").split(/\s+/)[0];
const daysBetween = (a, b) => Math.round((Date.UTC(...civilArgs(b)) - Date.UTC(...civilArgs(a))) / 86400000);
const civilArgs = (iso) => { const { y, m, d } = civil(iso); return [y, m - 1, d]; };
const todayIso = () => { const t = new Date(); return `${t.getFullYear()}-${String(t.getMonth() + 1).padStart(2, "0")}-${String(t.getDate()).padStart(2, "0")}`; };
const plural = (n, word) => `${n} ${word}${n === 1 ? "" : "s"}`;

function partyLabel(intake) {
  const t = intake.traveler_configuration;
  const parts = [plural(t.adult_count, "adult")];
  if (t.child_count) parts.push(plural(t.child_count, "child").replace("childs", "children") + (intake.child_ages.length ? ` (age ${intake.child_ages.join(", ")})` : ""));
  if (t.infant_count) parts.push(plural(t.infant_count, "infant"));
  return parts.join(", ");
}

// ---------- API ----------
async function api(path, { method = "GET", body, headers = {} } = {}) {
  const init = { method, headers: { ...headers } };
  if (body !== undefined) {
    init.headers["content-type"] = "application/json";
    init.headers["idempotency-key"] = crypto.randomUUID();
    init.body = JSON.stringify(body);
  }
  let res;
  try {
    res = await fetch("/api" + path, init);
  } catch {
    throw new Error("Dashboard server isn't reachable.");
  }
  const json = res.status === 204 ? null : await res.json().catch(() => null);
  if (!res.ok) {
    const e = json?.error;
    const detail = e?.details?.length ? ` (${e.details.map((d) => d.field).join(", ")})` : "";
    throw new Error((e?.message || `Request failed (${res.status})`) + detail);
  }
  return json;
}

function showBanner(message) {
  const el = $("banner");
  el.hidden = !message;
  el.innerHTML = message ? esc(message) : "";
}

let toastTimer;
function toast(message) {
  const el = $("toast");
  el.textContent = message;
  el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.hidden = true; }, 3200);
}

// ---------- derived ----------
const runsFor = (key) => state.runs.filter((r) => r.agent === key).sort((a, b) => ms(b.created_at) - ms(a.created_at));
const latest = (key) => runsFor(key)[0];
const skipped = (key) => state.intake?.runs.find((r) => r.agent === key && !r.run_id);

function reviewItems() {
  const items = [];
  for (const { key } of AGENTS) {
    const run = runsFor(key).find((r) => r.status === "succeeded");
    if (!run) continue;
    const p = run.proposal;
    if (key === "manage_recover") {
      for (const a of p.actions) items.push({ id: `${run.id}:${a.item_id}`, agent: key, at: run.created_at, title: a.summary, meta: `To ${a.recipient}${a.amount ? " · " + money(a.amount) : ""}`, draft: a.draft, high: a.high_stakes, approve: a.kind === "send_claim" ? "Approve claim" : "Approve" });
    } else if (key === "plan_book") {
      items.push({ id: `${run.id}:plan`, agent: key, at: run.created_at, title: "Review the itinerary proposal", meta: `${plural(p.itinerary_items.length, "item")} · ${plural(p.checklist_tasks.length, "task")}`, high: false, approve: "Accept plan" });
    } else if (key === "pack_shop") {
      const n = p.packing_lists.reduce((s, l) => s + l.items.length, 0);
      items.push({ id: `${run.id}:pack`, agent: key, at: run.created_at, title: "Review the packing list", meta: plural(n, "item"), high: false, approve: "Accept list" });
    } else if (key === "travel_essentials" && p.sections.length) {
      items.push({ id: `${run.id}:brief`, agent: key, at: run.created_at, title: "Send the pre-departure briefing to the client", meta: `${plural(p.sections.length, "section")} · ${plural(p.checklist_tasks.length, "task")}`, high: false, approve: "Approve & send" });
    }
  }
  return items.sort((a, b) => ms(b.at) - ms(a.at));
}

function agentStatus(key) {
  const run = latest(key);
  if (!run) return skipped(key) ? { cls: "waiting", text: "Not available" } : { cls: "waiting", text: "Not started" };
  if (run.status === "queued") return { cls: "working", text: "Queued" };
  if (run.status === "running") return { cls: "working", text: "Working" };
  if (run.status === "failed") return { cls: "failed", text: "Failed" };
  if (run.status !== "succeeded") return { cls: "waiting", text: run.status };
  const open = reviewItems().some((i) => i.agent === key && !state.decisions[i.id]);
  return open ? { cls: "attention", text: "Needs review" } : { cls: "done", text: "Up to date" };
}

// ---------- render: chrome ----------
function renderStrip() {
  const mode = state.agentsInfo[0]?.mode;
  $("mode-strip").textContent = mode
    ? `Wonder Agency Console · agents in ${mode === "fixture" ? "fixture mode (synthetic outputs)" : "model mode (unverified drafts)"} · rules and rates computed live`
    : "Wonder Agency Console";
}

function renderPicker() {
  document.querySelector(".client-picker").hidden = !state.intakes.length;
  $("client-select").innerHTML = state.intakes.map((i) =>
    `<option value="${esc(i.id)}" ${i.id === state.intake?.id ? "selected" : ""}>${esc(i.client_name)} · ${esc(city(i.destination))} · ${esc(dateLabel(i.start_date))} · intake ${esc(localTime(i.created_at))}</option>`).join("");
}

function renderHero() {
  const i = state.intake;
  const today = todayIso();
  const toGo = daysBetween(today, i.start_date);
  const phase = toGo > 0 ? `${plural(toGo, "day")} to departure` : daysBetween(today, i.end_date) >= 0 ? `Day ${1 - toGo} of ${daysBetween(i.start_date, i.end_date) + 1}` : "Trip complete";
  const done = AGENTS.filter((a) => latest(a.key)?.status === "succeeded").length;
  const working = state.runs.filter((r) => ACTIVE.includes(r.status)).length;
  const pending = reviewItems().filter((x) => !state.decisions[x.id]);
  $("hero").innerHTML = `
    <div>
      <div class="eyebrow"><p class="micro">Client · ${esc(i.purpose)}</p><span class="rule"></span><p class="micro">${esc(rangeLabel(i.start_date, i.end_date))}</p></div>
      <h1>${esc(firstName(i.client_name))}’s <span class="amp">${esc(city(i.destination))}</span></h1>
      <p class="lede">${esc(i.client_name)} · ${esc(partyLabel(i))}${i.accommodation_area ? ` · ${esc(i.accommodation_area)}` : ""}. <strong>${esc(phase)}.</strong></p>
      <div class="travelers"><span class="avatar soft">${esc(i.client_name.split(/\s+/).map((p) => p[0]).join("").slice(0, 2))}</span><span>Intake ${esc(localTime(i.created_at))}${i.advisor_name ? ` by ${esc(i.advisor_name)}` : ""}</span></div>
    </div>
    <div class="stats">
      <div class="glass stat"><p class="micro">Agents done</p><div class="val">${done}<small>of 5</small></div>
        <div class="bar"><span style="width:${done * 20}%"></span></div></div>
      <div class="glass stat"><p class="micro">Needs review</p><div class="val">${pending.length}<small>${pending.length === 1 ? "item" : "items"}</small></div>
        <div class="sub">${pending.filter((x) => x.high).length} high-stakes</div></div>
      <div class="glass stat"><p class="micro">In progress</p><div class="val">${working}<small>${working === 1 ? "run" : "runs"}</small></div>
        <div class="sub">${working ? "Updating live" : "All runs settled"}</div></div>
      <div class="glass stat"><p class="micro">Departure</p><div class="val">${esc(dateLabel(i.start_date))}</div>
        <div class="sub">${esc(phase)}</div></div>
    </div>`;
}

function renderOnboarding() {
  const i = state.intake;
  const rows = [
    ["Client", i.client_name], ["Purpose", i.purpose], ["Destination", i.destination],
    ["Dates", rangeLabel(i.start_date, i.end_date)], ["Travelers", partyLabel(i)],
    ["Stay", i.accommodation_area], ["Interests", i.interests.join(", ")], ["Needs", i.needs.join(", ")],
  ].filter(([, v]) => v);
  $("onboarding").innerHTML = `
    <div class="card-head">
      <div><p class="micro">${i.channel === "phone_call" ? "Intake call" : "Web intake"} · ${esc(localTime(i.created_at))}</p><h3>Onboarded${i.advisor_name ? ` by ${esc(i.advisor_name)}` : ""}</h3></div>
      <span class="tag ok"><span class="dot"></span>Sent to agents</span>
    </div>
    <dl class="kv">${rows.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join("")}</dl>
    <div class="note"><p class="micro">What the agents received</p>
      <ul><li>Destination, dates, party size and interests only. The client's name and needs stay with the agency.</li>
      ${i.runs.filter((r) => !r.run_id).map((r) => `<li>${esc(AGENT[r.agent].title)} skipped: ${esc(r.skipped_reason)}</li>`).join("")}</ul></div>`;
}

function renderQueue() {
  const items = reviewItems();
  const pending = items.filter((x) => !state.decisions[x.id]);
  const handled = items.filter((x) => state.decisions[x.id]);
  const card = (x) => {
    const decided = state.decisions[x.id];
    return `<li class="q-item">
      <div class="q-top"><span class="q-agent">${esc(AGENT[x.agent].num)} ${esc(AGENT[x.agent].title)}</span>
        ${x.high ? `<span class="tag warn">Human review required</span>` : ""}
        <span class="q-meta" style="margin-left:auto">${esc(localTime(x.at))}</span></div>
      <div class="q-title">${esc(x.title)}</div>
      <div class="q-meta">${esc(x.meta)}</div>
      ${x.draft ? `<details class="q-draft"><summary>${esc(x.draft.length > 110 ? x.draft.slice(0, 110).trimEnd() + "…" : x.draft)}</summary>${x.draft.length > 110 ? `<p>${esc(x.draft)}</p>` : ""}</details>` : ""}
      <div class="q-actions">${decided
        ? `<span class="q-done">${decided === "approved" ? "✓ Approved" : "Dismissed"} · recorded in this browser, nothing sent</span><button class="btn" type="button" data-undo="${esc(x.id)}">Undo</button>`
        : `<button class="btn primary" type="button" data-approve="${esc(x.id)}">${esc(x.approve)}</button>
           <button class="btn" type="button" data-agent-jump="${esc(x.agent)}">View</button>
           <button class="btn" type="button" data-dismiss="${esc(x.id)}">Dismiss</button>`}</div>
    </li>`;
  };
  const working = state.runs.some((r) => ACTIVE.includes(r.status));
  $("queue").innerHTML = `
    <div class="card-head">
      <div><p class="micro">Human in the loop</p><h3>Needs your review</h3></div>
      <span class="tag ${pending.length ? "warn" : "ok"}"><span class="dot"></span>${pending.length} open</span>
    </div>
    ${pending.length ? `<ul class="queue">${pending.map(card).join("")}</ul>` : `<p class="empty">${working ? "Agents are still working. Proposals will appear here." : "Nothing waiting. Anything that needs a person will show up here."}</p>`}
    ${handled.length ? `<p class="micro" style="margin:20px 0 10px">Handled</p><ul class="queue">${handled.map(card).join("")}</ul>` : ""}`;
}

// ---------- render: agents ----------
function renderAgentList() {
  $("agent-list").innerHTML = AGENTS.map((a) => {
    const st = agentStatus(a.key);
    return `<li><button class="agent-item" type="button" role="tab" data-agent="${a.key}" aria-selected="${a.key === state.agent}">
      <span class="num">${a.num}</span>
      <span><span class="name">${esc(a.title)}</span><span class="line">${esc(a.tagline)}</span></span>
      <span class="status ${st.cls}"><span class="dot"></span>${esc(st.text)}</span>
    </button></li>`;
  }).join("");
}

const subHead = (label, extra = "") => `<p class="sub-h">${esc(label)}${extra}</p>`;
const modeTag = (p) => p.data_mode === "fixture" ? `<span class="tag mock">Fixture data</span>` : `<span class="tag warn">Model-generated, unverified</span>`;
const prioTag = (p) => `<span class="tag ${p === "must" ? "bad" : p === "should" ? "warn" : "mock"}">${esc(p)}</span>`;

function tasksBlock(tasks) {
  if (!tasks?.length) return "";
  return subHead("Checklist tasks") + `<ul class="itin">${tasks.map((t) => `<li><span class="d">${t.due_date ? esc(dateLabel(t.due_date)) : "—"}</span><span>${esc(t.title)}</span>${prioTag(t.priority)}</li>`).join("")}</ul>`;
}

function footerBlock(p) {
  const parts = [];
  if (p.assumptions?.length) parts.push(`<details class="fine"><summary>Assumptions (${p.assumptions.length})</summary><ul class="list">${p.assumptions.map((a) => `<li>${esc(a)}</li>`).join("")}</ul></details>`);
  if (p.sources?.length) parts.push(`<details class="fine"><summary>Sources (${p.sources.length})</summary><ul class="list">${p.sources.map((s) => `<li>${esc(s.provider)} · ${esc(s.data_mode)} · <a href="${esc(s.source_url)}" target="_blank" rel="noopener noreferrer">link</a></li>`).join("")}</ul></details>`);
  return parts.join("");
}

const RENDER = {
  plan_book(p) {
    const tz = state.trip?.timezone || "UTC";
    return (p.itinerary_items.length ? subHead("Itinerary") + `<ul class="itin">${p.itinerary_items.map((x) => `<li><span class="d">${esc(timeIn(x.starts_at, x.timezone || tz).split(",")[0])}</span><span>${esc(x.title)}<br><span class="k">${esc(timeIn(x.starts_at, x.timezone).split(", ")[1] || "")} – ${esc(timeIn(x.ends_at, x.timezone).split(", ")[1] || "")} · ${esc(x.kind)}</span></span><span class="tag">${esc(x.kind)}</span></li>`).join("")}</ul>` : "")
      + (p.budget_estimates.length ? subHead("Budget estimates") + `<div class="grid-2">${p.budget_estimates.map((m) => `<div class="computed"><div class="money">${esc(money(m))}</div></div>`).join("")}</div>` : "")
      + tasksBlock(p.checklist_tasks);
  },
  pack_shop(p) {
    return subHead("Packing lists") + `<div class="grid-2">${p.packing_lists.map((l) => `<div class="mini"><div class="t">${esc(l.title)}</div><ul class="list">${l.items.map((x) => `<li>${esc(x.title)} × ${x.quantity}${x.purchase_status === "missing" ? ` <span class="tag warn">to buy</span>` : ""}</li>`).join("")}</ul></div>`).join("")}</div>` + tasksBlock(p.checklist_tasks);
  },
  explore_magic(p, run) {
    const rec = (r) => `<div class="mini rec">
      <div class="t">${esc(r.title)}<span class="tag ${r.feasibility === "feasible" ? "ok" : "warn"}">${esc(r.feasibility)}</span></div>
      <div class="s">${esc(r.category)} · ${r.duration_minutes} min · ${r.outbound_minutes ?? "?"} min there${r.cost ? ` · ${esc(money(r.cost))} (${esc(r.cost_status)})` : ""}</div>
      <div class="s">${esc(r.reason)} · valid until ${esc(timeIn(r.valid_until, "Europe/Madrid").split(", ")[1] || "")}</div>
      <button class="btn" type="button" data-save="${esc(run.id)}|${esc(r.id)}">Save for client</button></div>`;
    return (p.warnings.length ? `<div class="note warn-note">${p.warnings.map(esc).join("<br>")}</div>` : "")
      + subHead("Ideas that fit", ` <span class="tag">${esc(p.coverage.area)}</span>`)
      + (p.recommendations.length ? `<div class="grid-2">${p.recommendations.map(rec).join("")}</div>` : `<p class="empty">No options fit this window.</p>`)
      + (p.uncertain_recommendations.length ? subHead("Needs verification") + `<div class="grid-2">${p.uncertain_recommendations.map(rec).join("")}</div>` : "");
  },
  travel_essentials(p) {
    const fx = p.exchange_rate;
    return `<div class="grid-2">${p.sections.map((s) => `<div class="mini"><p class="micro" style="margin-bottom:8px">${esc(TOPICS[s.topic] || s.topic)}</p>${s.items.map((x) => `<div class="brief"><b>${esc(x.title)}</b> ${prioTag(x.priority)}<div class="s">${esc(x.detail)}</div></div>`).join("")}</div>`).join("")}</div>`
      + subHead("Computed for this trip", ` <span class="tag">Wonder code</span>`)
      + `<div class="grid-2">
        ${fx ? `<div class="computed"><p class="micro">Exchange rate</p><div class="money">1 ${esc(fx.from_currency)} = ${fx.rate.toFixed(2)} ${esc(fx.to_currency)}</div><div class="s">ECB reference · ${esc(fx.as_of)}</div></div>` : ""}
        ${p.emergency_contacts.length ? `<div class="computed"><p class="micro">Emergency</p><div class="money">${esc(p.emergency_contacts[0].phone)}</div><div class="s">${p.emergency_contacts.slice(1).map((c) => `${esc(c.label)} ${esc(c.phone)}`).join(" · ")}</div></div>` : ""}
        ${p.connectivity_options.map((o) => `<div class="computed"><p class="micro">eSIM <span class="tag mock">Mock plan</span></p><div class="money">${esc(money(o.price))}</div><div class="s">${esc(o.provider)} · ${esc(o.data)} · ${o.days} days</div></div>`).join("")}
      </div>` + tasksBlock(p.checklist_tasks);
  },
  manage_recover(p) {
    let html = "";
    for (const r of p.rights) {
      html += subHead("Passenger rights", ` <span class="tag">Computed by rules code</span>`) + `<div class="computed">
        <div style="display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;align-items:flex-end">
          <div><p class="micro">${esc(r.regulation)}</p><div class="money">${r.total ? esc(money(r.total)) : "No compensation"}</div>${r.per_passenger ? `<div class="s">${esc(money(r.per_passenger))} × ${r.passengers} passengers</div>` : ""}</div>
          <div class="s" style="max-width:34ch">${r.right_to_care.length ? `Care: ${esc(r.right_to_care.join(", "))}. ` : ""}${r.right_to_refund ? "Refund right applies." : ""}</div>
        </div>
        <ul class="reasons">${r.reasoning.map((x) => `<li>${esc(x)}</li>`).join("")}${r.caveats.map((x) => `<li class="dim">${esc(x)}</li>`).join("")}</ul></div>`;
    }
    if (p.baggage) {
      html += subHead("Baggage rights", ` <span class="tag">${esc(p.baggage.regulation)}</span>`) + `<div class="grid-2">
        <div class="mini"><div class="t">Claim window</div><div class="s">${esc(p.baggage.claim_window)}</div></div>
        <div class="mini"><div class="t">Liability cap</div><div class="s">${esc(p.baggage.liability_cap)}</div></div></div>`;
    }
    if (p.actions.length) html += `<div class="handoffs">${p.actions.map((a) => `<span class="handoff">◷ In review: ${esc(a.summary)}</span>`).join("")}</div>`;
    return html + tasksBlock(p.checklist_tasks);
  },
};

function disruptionForm() {
  const total = state.intake ? Object.values(state.intake.traveler_configuration).reduce((a, b) => a + b, 0) : 1;
  return `<details class="report" ${state.reportOpen ? "open" : ""}><summary>Report a disruption</summary>
    <form id="disruption-form" class="form-grid">
      <label>What happened<select name="kind">
        <option value="delay">Flight delayed</option><option value="cancellation">Flight cancelled</option>
        <option value="denied_boarding">Denied boarding</option><option value="baggage_delayed">Bag delayed</option>
        <option value="baggage_lost">Bag lost</option><option value="baggage_damaged">Bag damaged</option></select></label>
      <label>Flight number<input name="number" placeholder="VY7821" pattern="[A-Za-z0-9]{2}[0-9]{1,4}"></label>
      <label>From (IATA)<input name="from" placeholder="LHR" maxlength="3"></label>
      <label>To (IATA)<input name="to" placeholder="BCN" maxlength="3"></label>
      <label>Flight date<input name="date" type="date" value="${esc(state.intake?.start_date || "")}"></label>
      <label>Arrival delay (min)<input name="delay" type="number" min="0" max="4320" value="0"></label>
      <label>Passengers<input name="passengers" type="number" min="1" max="30" value="${total}"></label>
      <label>Reference<input name="reference" placeholder="Booking or PIR ref" maxlength="40"></label>
      <label class="check"><input name="extraordinary" type="checkbox"> Weather, strike or ATC (outside the airline's control)</label>
      <div class="form-actions"><button class="btn primary" type="submit">Run Manage & Recover</button><span class="form-note" id="disruption-note"></span></div>
    </form></details>`;
}

function renderAgentDetail() {
  const a = AGENT[state.agent];
  const runs = runsFor(a.key);
  const run = runs[0];
  const st = agentStatus(a.key);
  let body;
  if (!run) {
    const skip = skipped(a.key);
    body = `<p class="waiting-note">${skip ? esc(skip.skipped_reason) : `${esc(a.title)} hasn't run for this trip yet.`}</p>`;
  } else if (ACTIVE.includes(run.status)) {
    body = `<div class="working-note"><span class="spinner" aria-hidden="true"></span>${run.status === "queued" ? "Queued" : "Working on it"}…</div>`;
  } else if (run.status === "failed") {
    body = `<div class="note warn-note"><b>${esc(run.error?.code || "failed")}</b>: ${esc(run.error?.message || "The agent could not finish.")}</div>`;
  } else if (run.status === "succeeded") {
    const p = run.proposal;
    body = `<article class="run"><div class="run-time"><b>${esc(localTime(run.created_at).split(",")[0])}</b>${esc(localTime(run.created_at).split(", ")[1] || "")}<br>v${run.version}</div>
      <div><h4>${esc(p.reply)}</h4><div class="handoffs" style="margin:0 0 6px">${modeTag(p)}</div>${RENDER[a.key](p, run)}${footerBlock(p)}</div></article>`;
  } else {
    body = `<p class="waiting-note">Run ${esc(run.status)}.</p>`;
  }
  const history = runs.length > 1 ? `<p class="micro" style="margin-top:18px">Earlier runs: ${runs.slice(1).map((r) => `${esc(localTime(r.created_at))} ${esc(r.status)}`).join(" · ")}</p>` : "";
  $("agent-detail").innerHTML = `
    <div class="detail-head">
      <div><p class="micro">Agent ${a.num}</p><h3>${esc(a.title)}</h3><p class="tagline">${esc(a.tagline)}</p></div>
      <div class="detail-actions"><span class="tag ${st.cls === "done" ? "ok" : st.cls === "attention" || st.cls === "failed" ? "warn" : ""}"><span class="dot"></span>${esc(st.text)}</span>
        ${canRerun(a.key) ? `<button class="btn" type="button" data-rerun="${a.key}" ${run && ACTIVE.includes(run.status) ? "disabled" : ""}>Run again</button>` : ""}</div>
    </div>
    ${a.key === "manage_recover" ? disruptionForm() : ""}
    ${body}${history}`;
}

function canRerun(key) {
  return key !== "explore_magic" || Boolean(MAGIC_CENTERS[city(state.intake?.destination).toLowerCase()]);
}

// ---------- render: timeline ----------
function renderTimeline() {
  const i = state.intake;
  const items = [
    { at: i.created_at, kind: "human", who: i.advisor_name ? `Advisor · ${i.advisor_name}` : "Advisor", what: `Intake for ${i.client_name} sent to the agents.` },
    ...state.runs.map((r) => ({
      at: r.created_at, kind: r.status === "failed" ? "event" : "agent", who: `${AGENT[r.agent].num} ${AGENT[r.agent].title}`,
      what: r.status === "succeeded" ? r.proposal.reply : r.status === "failed" ? `Failed: ${r.error?.message || ""}` : `Run ${r.status}`,
    })),
  ].sort((a, b) => ms(b.at) - ms(a.at));
  $("timeline").innerHTML = items.map((x) => `<li class="t-item ${x.kind}"><div class="t-when"><b>${esc(localTime(x.at).split(",")[0])}</b>${esc(localTime(x.at).split(", ")[1] || "")}</div>
    <div class="t-what"><span class="who">${esc(x.who)}</span>${esc(x.what)}</div></li>`).join("");
}

function renderEmpty() {
  $("main").innerHTML = `<section class="empty-state glass card">
    <p class="micro">No clients yet</p><h3>Start with an intake call</h3>
    <p>When an advisor finishes the onboarding form, the trip appears here with all five agents working on it.</p>
    <a class="btn primary" href="/onboarding/#onboard">Open onboarding →</a></section>`;
}

function render() {
  renderStrip();
  if (!state.intake) return;
  renderPicker(); renderHero(); renderOnboarding(); renderQueue(); renderAgentList(); renderAgentDetail(); renderTimeline();
}

// ---------- data loading ----------
async function refreshRuns() {
  const res = await api(`/agent-runs?trip_id=${encodeURIComponent(state.intake.trip_id)}&limit=100`);
  state.runs = res.data;
}

function schedulePoll() {
  clearTimeout(state.poll);
  if (!state.runs.some((r) => ACTIVE.includes(r.status))) return;
  state.poll = setTimeout(async () => {
    try { await refreshRuns(); showBanner(""); render(); } catch (err) { showBanner(err.message); }
    schedulePoll();
  }, 1500);
}

async function selectIntake(id) {
  const intake = (await api(`/intakes/${encodeURIComponent(id)}`)).data;
  state.intake = intake;
  state.trip = (await api(`/trips/${encodeURIComponent(intake.trip_id)}`)).data;
  await refreshRuns();
  store.set("wonder.intake", id);
  const url = new URL(location.href);
  url.searchParams.set("intake", id);
  history.replaceState(null, "", url);
  render();
  schedulePoll();
}

// ---------- actions ----------
function decide(id, value) {
  if (value) state.decisions[id] = value; else delete state.decisions[id];
  store.set("wonder.decisions", state.decisions);
  render();
}

async function startRun(agent, input) {
  await api("/agent-runs", { method: "POST", body: { agent, trip_id: state.intake.trip_id, input } });
  await refreshRuns();
  state.agent = agent;
  render();
  schedulePoll();
}

function rerunInput(key) {
  if (key === "explore_magic") return { location: MAGIC_CENTERS[city(state.intake.destination).toLowerCase()], available_minutes: 120 };
  if (key === "travel_essentials") return { home_currency: state.intake.home_currency };
  return {};
}

function disruptionInput(form) {
  const f = new FormData(form);
  const kind = f.get("kind");
  const number = String(f.get("number") || "").toUpperCase().replace(/\s/g, "");
  const flight = number ? {
    carrier_code: number.slice(0, 2), number, from_iata: String(f.get("from") || "").toUpperCase(),
    to_iata: String(f.get("to") || "").toUpperCase(), ...(f.get("date") ? { scheduled_date: f.get("date") } : {}),
  } : null;
  const flightEvent = ["delay", "cancellation", "denied_boarding"].includes(kind);
  if (flightEvent && (!flight || flight.from_iata.length !== 3 || flight.to_iata.length !== 3)) throw new Error("Add the flight number and both airport codes.");
  return {
    disruption: {
      kind, passengers: Number(f.get("passengers") || 1), arrival_delay_minutes: Number(f.get("delay") || 0),
      extraordinary_circumstances: f.get("extraordinary") === "on",
      ...(flight && (flightEvent || flight.from_iata.length === 3) ? { flight } : {}),
      ...(f.get("reference") ? { reference: String(f.get("reference")) } : {}),
    },
  };
}

document.addEventListener("click", async (e) => {
  const el = e.target.closest("[data-agent],[data-approve],[data-dismiss],[data-undo],[data-agent-jump],[data-rerun],[data-save]");
  if (!el) return;
  try {
    if (el.dataset.agent) { state.agent = el.dataset.agent; store.set("wonder.agent", state.agent); renderAgentList(); renderAgentDetail(); }
    else if (el.dataset.approve) decide(el.dataset.approve, "approved");
    else if (el.dataset.dismiss) decide(el.dataset.dismiss, "dismissed");
    else if (el.dataset.undo) decide(el.dataset.undo, null);
    else if (el.dataset.agentJump) {
      state.agent = el.dataset.agentJump; renderAgentList(); renderAgentDetail();
      $("agent-detail").scrollIntoView({ behavior: "smooth", block: "start" }); $("agent-detail").focus({ preventScroll: true });
    } else if (el.dataset.rerun) {
      el.disabled = true;
      await startRun(el.dataset.rerun, rerunInput(el.dataset.rerun));
      toast(`${AGENT[el.dataset.rerun].title} started`);
    } else if (el.dataset.save) {
      const [run_id, recommendation_id] = el.dataset.save.split("|");
      el.disabled = true;
      await api("/me/saved-experiences", { method: "POST", body: { run_id, recommendation_id } });
      el.textContent = "✓ Saved";
      toast("Saved to the client's ideas");
    }
  } catch (err) {
    toast(err.message);
    if (el.dataset.save || el.dataset.rerun) el.disabled = false;
  }
});

document.addEventListener("submit", async (e) => {
  if (e.target.id !== "disruption-form") return;
  e.preventDefault();
  const note = $("disruption-note");
  try {
    const input = disruptionInput(e.target);
    note.textContent = "Starting…";
    state.reportOpen = false;
    await startRun("manage_recover", input);
    toast("Manage & Recover is assessing the disruption");
  } catch (err) {
    note.textContent = err.message;
  }
});

document.addEventListener("toggle", (e) => { if (e.target.classList?.contains("report")) state.reportOpen = e.target.open; }, true);

document.addEventListener("keydown", (e) => {
  const item = e.target.closest?.(".agent-item");
  if (!item || !["ArrowDown", "ArrowUp"].includes(e.key)) return;
  e.preventDefault();
  const keys = AGENTS.map((a) => a.key);
  const next = keys[(keys.indexOf(item.dataset.agent) + (e.key === "ArrowDown" ? 1 : -1) + keys.length) % keys.length];
  state.agent = next; renderAgentList(); renderAgentDetail();
  document.querySelector(`[data-agent="${next}"]`).focus();
});

$("client-select").addEventListener("change", (e) => selectIntake(e.target.value).catch((err) => showBanner(err.message)));

function setupTheme() {
  const root = document.documentElement;
  const saved = store.get("wonder.theme", null);
  if (saved) root.dataset.theme = saved;
  const isDark = () => root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  const label = () => { $("theme-label").textContent = isDark() ? "Morning" : "Evening"; };
  label();
  $("theme-toggle").addEventListener("click", () => { root.dataset.theme = isDark() ? "light" : "dark"; store.set("wonder.theme", root.dataset.theme); label(); });
}

async function main() {
  setupTheme();
  $("foot").innerHTML = `<span>Approvals are recorded in this browser only; nothing is sent to clients or airlines.</span><span>Data from the Wonder control API</span>`;
  if (!AGENT[state.agent]) state.agent = "plan_book";
  try {
    state.agentsInfo = (await api("/agents")).data;
    state.intakes = (await api("/intakes?limit=100")).data;
  } catch (err) {
    showBanner(`${err.message} Start the control API (see README → Agency dashboard).`);
    document.querySelector(".client-picker").hidden = true;
    renderEmpty();
    return;
  }
  renderStrip();
  if (!state.intakes.length) { renderPicker(); renderEmpty(); return; }
  const wanted = new URL(location.href).searchParams.get("intake") || store.get("wonder.intake", null);
  const id = state.intakes.some((i) => i.id === wanted) ? wanted : state.intakes[0].id;
  try { await selectIntake(id); } catch (err) { showBanner(err.message); }
}

main();
