// Wonder Agency Console: renders the five agents' work for one trip from data/demo.json.

const AGENT_ORDER = ["planning", "packing", "explore", "essentials", "recovery"];
const PLACE_BY_OFFSET = { "-07:00": "San Francisco", "-08:00": "San Francisco", "+00:00": "Lisbon", "+01:00": "Barcelona" };
const EVENT_LABELS = {
  flight_status_update: (e) => `Flight feed: ${e.data.status} ${e.data.arrival_delay_minutes} min`,
  baggage_delayed: (e) => `Airport: bag missing, PIR ${e.data.pir_reference}`,
  receipt_uploaded: (e) => `Receipt uploaded: ${e.data.merchant}`,
  trip_ended: () => "Trip ended",
};

const store = {
  get(key, fallback) { try { const v = localStorage.getItem(key); return v === null ? fallback : JSON.parse(v); } catch { return fallback; } },
  set(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* storage unavailable */ } },
};

const state = { data: null, stage: store.get("wonder.stage", "disruption"), agent: store.get("wonder.agent", "recovery"), decisions: store.get("wonder.decisions", {}) };

// ---------- helpers ----------
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const ms = (iso) => new Date(iso).getTime();
const money = (n, cur = "USD") => new Intl.NumberFormat("en-US", { style: "currency", currency: cur, maximumFractionDigits: n % 1 ? 2 : 0 }).format(n);
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
function when(iso) {
  // Show the local wall-clock time where it happened, not the viewer's timezone.
  const [, y, mo, d, hh, mm, off] = iso.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}).*?([+-]\d{2}:\d{2}|Z)$/) || [];
  if (!y) return { date: iso, time: "", place: "" };
  return { date: `${MONTHS[+mo - 1]} ${+d}`, time: `${hh}:${mm}`, place: PLACE_BY_OFFSET[off === "Z" ? "+00:00" : off] || off };
}
const dayLabel = (isoDate) => { const [, mo, d] = isoDate.split("-"); return `${MONTHS[+mo - 1]} ${+d}`; };
const initials = (name) => name.split(/\s+/).map((p) => p[0]).join("").slice(0, 2).toUpperCase();

const stageObj = () => state.data.stages.find((s) => s.id === state.stage) || state.data.stages[0];
const stageTime = () => ms(stageObj().at);
const runsFor = (key) => (state.data.agents[key].runs || []).filter((r) => ms(r.at) <= stageTime());
function agentStatus(key) {
  const runs = runsFor(key);
  if (!runs.length) return "waiting";
  const open = runs.some((r) => (r.actions || []).some((a) => !state.decisions[a.id]));
  return open ? "attention" : "done";
}
const STATUS_TEXT = { done: "Up to date", attention: "Needs review", waiting: "Waiting" };
const agentTitle = (key) => state.data.agents[key].title;

function visibleActions() {
  const out = [];
  for (const key of AGENT_ORDER) for (const run of runsFor(key)) for (const a of run.actions || []) out.push({ ...a, agent: key, at: run.at });
  return out.sort((a, b) => ms(b.at) - ms(a.at));
}

function visibleExpenses() {
  const receiptAt = ms(state.data.events.find((e) => e.type === "receipt_uploaded").at);
  return state.data.trip.expenses.filter((e) => e.recorded_by_agent !== "recovery" || stageTime() >= receiptAt);
}

// ---------- render: chrome ----------
function renderStages() {
  $("stages").innerHTML = state.data.stages.map((s, i) => `
    <button class="stage-btn" type="button" data-stage="${esc(s.id)}" aria-pressed="${s.id === state.stage}" title="${esc(s.caption)}">
      <span class="n">0${i + 1}</span>${esc(s.label)}
    </button>`).join("");
}

function renderAdvisor() {
  const a = state.data.agency.advisor;
  $("advisor").innerHTML = `<div class="who">${esc(a.name)}<small>${esc(a.role)}</small></div><div class="avatar">${esc(a.initials)}</div>`;
}

// Calendar-day arithmetic on the local dates as written (no timezone conversion).
const dayNumber = (iso) => Math.round(Date.UTC(...iso.slice(0, 10).split("-").map((v, i) => (i === 1 ? v - 1 : +v))) / 86400000);

function tripPhase() {
  const segs = state.data.trip.segments;
  const now = dayNumber(stageObj().at), start = dayNumber(segs[0].depart), end = dayNumber(segs[segs.length - 1].arrive);
  if (now < start) return `${start - now} days to departure`;
  if (now <= end) return `Day ${now - start + 1} of ${end - start + 1}, on the road`;
  return "Trip complete";
}

function renderHero() {
  const { trip, computed } = state.data;
  const rate = computed.fx_eur_usd.rate;
  const spent = visibleExpenses().reduce((s, e) => s + e.amount * (e.currency === "EUR" ? rate : 1), 0);
  const total = computed.budget.total_usd;
  const actions = visibleActions();
  const pending = actions.filter((a) => !state.decisions[a.id]);
  const worked = AGENT_ORDER.filter((k) => runsFor(k).length).length;
  const next = trip.segments.find((s) => ms(s.depart) > stageTime());
  const travelerNames = trip.travelers.map((t) => t.name.split(" ")[0]).join(" & ");

  $("hero").innerHTML = `
    <div>
      <div class="eyebrow"><p class="micro">Trip · ${esc(state.data.onboarding.trip_type)}</p><span class="rule"></span><p class="micro">Nov 12 – 21, 2026 · ${trip.travelers.length} travelers</p></div>
      <h1>Lisbon <span class="amp">&amp;</span><br>Barcelona</h1>
      <p class="lede">${esc(travelerNames)}'s week of food markets, architecture and slow mornings. <strong>${esc(tripPhase())}.</strong></p>
      <div class="travelers">
        <div class="stack">${trip.travelers.map((t) => `<span class="avatar soft" title="${esc(t.name)}">${esc(initials(t.name))}</span>`).join("")}</div>
        <span>${esc(stageObj().caption)}</span>
      </div>
    </div>
    <div class="stats">
      <div class="glass stat"><p class="micro">Budget used</p><div class="val">${esc(money(Math.round(spent)))}<small>of ${esc(money(total))}</small></div>
        <div class="bar"><span style="width:${Math.min(100, (spent / total) * 100).toFixed(1)}%"></span></div></div>
      <div class="glass stat"><p class="micro">Needs review</p><div class="val">${pending.length}<small>${pending.length === 1 ? "item" : "items"}</small></div>
        <div class="sub">${pending.filter((a) => a.high_stakes).length} high-stakes</div></div>
      <div class="glass stat"><p class="micro">Agents engaged</p><div class="val">${worked}<small>of 5</small></div>
        <div class="sub">${AGENT_ORDER.filter((k) => agentStatus(k) === "attention").length} flagged for you</div></div>
      <div class="glass stat"><p class="micro">Next leg</p>${next
        ? `<div class="val">${esc(next.number)}</div><div class="sub">${esc(next.from.iata)} → ${esc(next.to.iata)} · ${esc(when(next.depart).date)}</div>`
        : `<div class="val">Home</div><div class="sub">All flights complete</div>`}</div>
    </div>`;
}

function renderOnboarding() {
  const o = state.data.onboarding;
  const w = when(o.at);
  $("onboarding").innerHTML = `
    <div class="card-head">
      <div><p class="micro">Intake call · ${esc(w.date)}, ${esc(w.time)}</p><h3>Onboarded by ${esc(o.advisor)}</h3></div>
      <span class="tag ok"><span class="dot"></span>Complete</span>
    </div>
    <p style="margin:0 0 18px;color:var(--ink-2)">${esc(o.summary)}</p>
    <dl class="kv">${o.captured.map((c) => `<dt>${esc(c.label)}</dt><dd>${esc(c.value)}</dd>`).join("")}</dl>
    <div class="note"><p class="micro">Advisor notes</p><ul>${o.advisor_notes.map((n) => `<li>${esc(n)}</li>`).join("")}</ul></div>`;
}

function renderQueue() {
  const actions = visibleActions();
  const pending = actions.filter((a) => !state.decisions[a.id]);
  const handled = actions.filter((a) => state.decisions[a.id]);
  const item = (a) => {
    const decided = state.decisions[a.id];
    return `<li class="q-item">
      <div class="q-top"><span class="q-agent">${esc(state.data.agents[a.agent].number)} ${esc(agentTitle(a.agent))}</span>
        ${a.high_stakes ? `<span class="tag warn">Human review required</span>` : ""}
        <span class="q-meta" style="margin-left:auto">${esc(when(a.at).date)}, ${esc(when(a.at).time)}</span></div>
      <div class="q-title">${esc(a.summary)}</div>
      <div class="q-meta">To ${esc(a.recipient)}${a.amount ? ` · ${esc(money(a.amount, a.currency))}` : ""}</div>
      ${a.draft ? `<details class="q-draft"><summary>${esc(a.draft.length > 110 ? a.draft.slice(0, 110).trimEnd() + "…" : a.draft)}</summary>${a.draft.length > 110 ? `<p>${esc(a.draft)}</p>` : ""}</details>` : ""}
      <div class="q-actions">${decided
        ? `<span class="q-done">${decided === "approved" ? "✓ Approved" : "Dismissed"} by ${esc(state.data.agency.advisor.name.split(" ")[0])} · demo, nothing sent</span>
           <button class="btn" type="button" data-undo="${esc(a.id)}">Undo</button>`
        : `<button class="btn primary" type="button" data-approve="${esc(a.id)}">Approve${a.kind === "send_claim" || a.kind === "notify_traveler" ? " &amp; send" : ""}</button>
           <button class="btn" type="button" data-agent-jump="${esc(a.agent)}">View context</button>
           <button class="btn" type="button" data-dismiss="${esc(a.id)}">Dismiss</button>`}</div>
    </li>`;
  };
  $("queue").innerHTML = `
    <div class="card-head">
      <div><p class="micro">Human in the loop</p><h3>Needs your review</h3></div>
      <span class="tag ${pending.length ? "warn" : "ok"}"><span class="dot"></span>${pending.length} open</span>
    </div>
    ${pending.length ? `<ul class="queue">${pending.map(item).join("")}</ul>` : `<p class="empty">Nothing waiting. The agents will add anything that needs a person here.</p>`}
    ${handled.length ? `<p class="micro" style="margin:20px 0 10px">Handled</p><ul class="queue">${handled.map(item).join("")}</ul>` : ""}`;
}

// ---------- render: agents ----------
function renderAgentList() {
  $("agent-list").innerHTML = AGENT_ORDER.map((key) => {
    const a = state.data.agents[key];
    const st = agentStatus(key);
    return `<li><button class="agent-item" type="button" role="tab" data-agent="${key}" aria-selected="${key === state.agent}">
      <span class="num">${esc(a.number)}</span>
      <span><span class="name">${esc(a.title)}</span><span class="line">${esc(a.tagline)}</span></span>
      <span class="status ${st}"><span class="dot"></span>${STATUS_TEXT[st]}</span>
    </button></li>`;
  }).join("");
}

const handoffChips = (run) => run.handoffs?.length
  ? `<div class="handoffs">${run.handoffs.map((h) => `<span class="handoff">→ ${esc(agentTitle(h.to))}: ${esc(h.task)}</span>`).join("")}</div>` : "";

const actionChips = (run) => run.actions?.length
  ? `<div class="handoffs">${run.actions.map((a) => {
      const d = state.decisions[a.id];
      return `<span class="handoff">${d === "approved" ? "✓ Approved" : d === "dismissed" ? "Dismissed" : "◷ In review"}: ${esc(a.summary)}</span>`;
    }).join("")}</div>` : "";

const statusTag = (s) => `<span class="tag ${s === "done" ? "ok" : s === "attention" ? "warn" : ""}"><span class="dot"></span>${STATUS_TEXT[s]}</span>`;
const subHead = (label, extra = "") => `<p class="sub-h">${esc(label)}${extra}</p>`;
const listOf = (items) => `<ul class="list">${items.map((i) => `<li>${esc(i)}</li>`).join("")}</ul>`;

function itineraryList(items) {
  return `<ul class="itin">${items.map((i) => `<li><span class="d">${esc(i.date)}</span><span>${esc(i.title)}<br><span class="k">${esc(i.sub)}</span></span>${i.tag || ""}</li>`).join("")}</ul>`;
}

const EXTRAS = {
  planning(run) {
    const t = state.data.trip;
    const items = [
      ...t.segments.map((s) => ({ at: s.depart, date: when(s.depart).date, title: `${s.number} ${s.from.city} → ${s.to.city}`, sub: `${s.carrier} · ${when(s.depart).time} – ${when(s.arrive).time} · PNR ${s.pnr}`, tag: `<span class="tag">Flight</span>` })),
      ...t.stays.map((h) => ({ at: h.check_in, date: when(h.check_in).date, title: h.name, sub: `${h.cancellation_policy} · ${h.confirmation}`, tag: `<span class="tag">Stay</span>` })),
    ].sort((a, b) => ms(a.at) - ms(b.at));
    const docTag = { blocker: "bad", pending: "warn", ok: "ok" };
    return `${subHead("Documents")}<div class="grid-2">${run.documents.map((d) => `<div class="mini"><div class="t">${esc(d.item)}<span class="tag ${docTag[d.status]}">${esc(d.status)}</span></div><div class="s">${esc(d.traveler)} · ${esc(d.detail)}</div></div>`).join("")}</div>
      ${subHead("Itinerary")}${itineraryList(items)}`;
  },
  packing(run) {
    return `${subHead(run.weather_note ? "Lists" : "Kit", run.weather_note ? ` <span class="tag mock">${esc(run.weather_note)}</span>` : "")}
      <div class="grid-2">${run.lists.map((l) => `<div class="mini"><div class="t">${esc(l.group)}</div>${listOf(l.items)}</div>`).join("")}</div>`;
  },
  explore(run) {
    let html = "";
    if (run.reservations_ref) {
      html += subHead("Reservations") + itineraryList(state.data.trip.reservations.map((r) => ({
        date: when(r.start).date, title: r.name, sub: `${when(r.start).time} · ${r.confirmation}`, tag: `<span class="tag ok">${esc(r.status)}</span>`,
      })));
    }
    if (run.magic) {
      html += subHead("Magic: ideas for the gap", ` <span class="tag mock">Sample</span>`) +
        `<div class="grid-2">${run.magic.map((m) => `<div class="mini"><div class="t">${esc(m.title)}<span class="serif">${m.minutes} min</span></div><div class="s">${esc(m.why)}</div></div>`).join("")}</div>`;
    }
    return html;
  },
  essentials(run) {
    const c = state.data.computed;
    const fx = c.fx_eur_usd;
    const plan = c.esim.plans[0];
    const countries = Object.values(c.countries);
    return `<div class="grid-2">${run.sections.map((s) => `<div class="mini"><div class="t">${esc(s.topic)}</div>${listOf(s.items)}</div>`).join("")}</div>
      ${subHead("Computed for this trip", ` <span class="tag">Wonder code</span>`)}
      <div class="grid-2">
        <div class="computed"><p class="micro">Exchange rate</p><div class="money">€1 = ${esc(money(fx.rate))}</div><div class="s" style="font-size:12.5px;color:var(--muted)">${esc(fx.source)}${fx.as_of ? ` · ${esc(fx.as_of)}` : ""}</div></div>
        <div class="computed"><p class="micro">Connectivity <span class="tag mock">Mock plans</span></p><div class="money">${esc(money(plan.price_usd))}</div><div class="s" style="font-size:12.5px;color:var(--muted)">${esc(plan.provider)} · ${esc(plan.data_gb)} GB · ${plan.days} days · PT + ES</div></div>
        ${countries.map((k) => `<div class="computed"><p class="micro">Emergency · ${esc(k.name)}</p><div class="money">${esc(k.emergency.general || Object.values(k.emergency)[0])}</div><div class="s" style="font-size:12.5px;color:var(--muted)">Plugs ${esc(k.plug_types.join("/"))} · ${k.voltage}V · ${esc(k.tap_water)}</div></div>`).join("")}
      </div>`;
  },
  recovery(run) {
    const c = state.data.computed;
    let html = "";
    if (run.compensation_ref) {
      const a = c.compensation[run.compensation_ref].assessments[0];
      html += subHead("Passenger rights", ` <span class="tag">Computed by rules code</span>`) + `<div class="computed">
        <div style="display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;align-items:flex-end">
          <div><p class="micro">${esc(a.regulation)} compensation</p><div class="money">${esc(money(a.total, a.currency))}</div><div style="font-size:12.5px;color:var(--muted)">${esc(money(a.amount_per_passenger, a.currency))} × ${a.passengers} passengers</div></div>
          <div style="font-size:12.5px;color:var(--ink-2);max-width:32ch">Also owed: ${esc(a.right_to_care.join(", ") || "nothing extra")}</div>
        </div>
        <ul class="reasons">${a.reasoning.map((r) => `<li>${esc(r)}</li>`).join("")}</ul></div>`;
    }
    if (run.baggage_ref) {
      const b = c.baggage[run.baggage_ref];
      html += subHead("Baggage rights", ` <span class="tag">${esc(b.regulation)}</span>`) + `<div class="grid-2">
        <div class="mini"><div class="t">Claim window</div><div class="s">${esc(b.claim_window)}</div></div>
        <div class="mini"><div class="t">Liability cap</div><div class="s">${esc(b.liability_cap)}</div></div></div>`;
    }
    if (run.settle_ref) {
      const s = c.settle_up.after_receipt;
      html += subHead("Settle-up", ` <span class="tag">Computed by split code</span>`) + `<div class="grid-2">
        ${s.transfers.map((t) => `<div class="computed"><p class="micro">${esc(t.from)} pays ${esc(t.to)}</p><div class="money">${esc(money(t.amount, s.currency))}</div><div style="font-size:12.5px;color:var(--muted)">${s.expense_count} expenses · ${esc(s.note)}</div></div>`).join("")}
        <div class="mini"><div class="t">Balances</div>${Object.entries(s.balances).map(([n, v]) => `<div class="s" style="display:flex;justify-content:space-between"><span>${esc(n)}</span><span>${v >= 0 ? "+" : "−"}${esc(money(Math.abs(v), s.currency))}</span></div>`).join("")}</div></div>`;
    }
    if (run.tasks) html += subHead("Follow-ups added") + listOf(run.tasks);
    return html;
  },
};

function renderAgentDetail() {
  const key = state.agent;
  const a = state.data.agents[key];
  const runs = runsFor(key).slice().reverse();
  const st = agentStatus(key);
  $("agent-detail").innerHTML = `
    <div class="detail-head">
      <div><p class="micro">Agent ${esc(a.number)}</p><h3>${esc(a.title)}</h3><p class="tagline">${esc(a.tagline)}</p></div>
      ${statusTag(st)}
    </div>
    ${runs.length ? runs.map((run) => {
      const w = when(run.at);
      return `<article class="run">
        <div class="run-time"><b>${esc(w.date)}</b>${esc(w.time)}<br>${esc(w.place)}</div>
        <div>
          <h4>${esc(run.headline)} ${run.status === "attention" ? `<span class="tag warn">Flagged</span>` : ""}</h4>
          <p>${esc(run.summary)}</p>
          ${EXTRAS[key](run)}
          ${actionChips(run)}${handoffChips(run)}
        </div>
      </article>`;
    }).join("") : `<p class="waiting-note">Nothing yet at this point in the trip. ${esc(a.title)} will pick up work when it's needed.</p>`}`;
}

// ---------- render: timeline ----------
function renderTimeline() {
  const d = state.data;
  const items = [
    { at: d.onboarding.at, kind: "human", who: `Advisor · ${d.onboarding.advisor}`, what: `Intake call completed (${d.onboarding.channel}). Trip handed to the agents.` },
    ...d.events.map((e) => ({ at: e.at, kind: "event", who: "App event", what: EVENT_LABELS[e.type]?.(e) || e.type })),
    ...AGENT_ORDER.flatMap((k) => d.agents[k].runs.map((r) => ({ at: r.at, kind: "agent", who: `${d.agents[k].number} ${d.agents[k].title}`, what: r.headline }))),
  ].filter((i) => ms(i.at) <= stageTime()).sort((a, b) => ms(b.at) - ms(a.at));
  $("timeline").innerHTML = items.map((i) => {
    const w = when(i.at);
    return `<li class="t-item ${i.kind}"><div class="t-when"><b>${esc(w.date)}</b>${esc(w.time)} · ${esc(w.place)}</div>
      <div class="t-what"><span class="who">${esc(i.who)}</span>${esc(i.what)}</div></li>`;
  }).join("");
}

function renderFoot() {
  const d = state.data;
  $("foot").innerHTML = `<span>${esc(d.notice)}</span><span>Data built ${esc(d.generated_at.slice(0, 16).replace("T", " "))} UTC</span>`;
}

function render() {
  renderStages(); renderHero(); renderOnboarding(); renderQueue(); renderAgentList(); renderAgentDetail(); renderTimeline();
}

// ---------- events ----------
function decide(id, value) {
  if (value) state.decisions[id] = value; else delete state.decisions[id];
  store.set("wonder.decisions", state.decisions);
  render();
}

document.addEventListener("click", (e) => {
  const el = e.target.closest("[data-stage],[data-agent],[data-approve],[data-dismiss],[data-undo],[data-agent-jump]");
  if (!el) return;
  if (el.dataset.stage) { state.stage = el.dataset.stage; store.set("wonder.stage", state.stage); render(); }
  else if (el.dataset.agent) { state.agent = el.dataset.agent; store.set("wonder.agent", state.agent); renderAgentList(); renderAgentDetail(); }
  else if (el.dataset.approve) decide(el.dataset.approve, "approved");
  else if (el.dataset.dismiss) decide(el.dataset.dismiss, "dismissed");
  else if (el.dataset.undo) decide(el.dataset.undo, null);
  else if (el.dataset.agentJump) {
    state.agent = el.dataset.agentJump; store.set("wonder.agent", state.agent); renderAgentList(); renderAgentDetail();
    $("agent-detail").scrollIntoView({ behavior: "smooth", block: "start" }); $("agent-detail").focus({ preventScroll: true });
  }
});

document.addEventListener("keydown", (e) => {
  const item = e.target.closest?.(".agent-item");
  if (!item || !["ArrowDown", "ArrowUp"].includes(e.key)) return;
  e.preventDefault();
  const i = AGENT_ORDER.indexOf(item.dataset.agent) + (e.key === "ArrowDown" ? 1 : -1);
  const next = AGENT_ORDER[(i + AGENT_ORDER.length) % AGENT_ORDER.length];
  state.agent = next; renderAgentList(); renderAgentDetail();
  document.querySelector(`[data-agent="${next}"]`).focus();
});

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
  try {
    state.data = await (await fetch("data/demo.json")).json();
  } catch (err) {
    document.querySelector("main").innerHTML = `<p class="empty" style="padding:80px 0">Couldn't load data/demo.json. Run <code>uv run python scripts/build_dashboard_data.py</code>, then serve this folder.</p>`;
    return;
  }
  if (!state.data.stages.some((s) => s.id === state.stage)) state.stage = "disruption";
  if (!AGENT_ORDER.includes(state.agent)) state.agent = "recovery";
  renderAdvisor(); renderFoot(); render();
}

main();
