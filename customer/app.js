// Wonder customer app (traveler view): trip card + chat with the human advisor.
// Talks to the same control API as the advisor dashboard, through the server's /api proxy.

const QUICK_REPLIES = [
  "I'm at border control in Barcelona and the officer is asking for proof of travel insurance. I don't have any!",
  "What time can we check in at the hotel?",
];
const THROUGH_TEXT = "I showed the certificate and I'm through! We're in Spain. Thank you so much!";

const state = { intake: null, messages: [], policies: {}, poll: null, sending: false, entered: false };
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const dateLabel = (iso) => { const [, m, d] = iso.split("-").map(Number); return `${MONTHS[m - 1]} ${d}`; };
const clock = (iso) => new Intl.DateTimeFormat("en-US", { hour: "2-digit", minute: "2-digit", hour12: false }).format(new Date(iso));
const civilDay = (iso) => { const [y, m, d] = iso.slice(0, 10).split("-").map(Number); return Date.UTC(y, m - 1, d) / 86400000; };
const todayDay = () => { const t = new Date(); return Date.UTC(t.getFullYear(), t.getMonth(), t.getDate()) / 86400000; };
function money(m) {
  const fmt = new Intl.NumberFormat("en-US", { style: "currency", currency: m.currency });
  return fmt.format(m.amount_minor / 10 ** fmt.resolvedOptions().maximumFractionDigits);
}

async function api(path, body) {
  const init = body === undefined ? {} : {
    method: "POST",
    headers: { "content-type": "application/json", "idempotency-key": crypto.randomUUID() },
    body: JSON.stringify(body),
  };
  const res = await fetch("/api" + path, init);
  const json = await res.json().catch(() => null);
  if (!res.ok) throw new Error(json?.error?.message || `Request failed (${res.status})`);
  return json.data;
}

// ---------- render ----------
function renderTrip() {
  const i = state.intake;
  const city = i.destination.split(",")[0];
  const now = todayDay(), start = civilDay(i.start_date), end = civilDay(i.end_date);
  const phase = now < start ? `${start - now} days to go` : now <= end ? `Day ${now - start + 1} of ${end - start + 1}` : "Trip complete";
  const kids = i.traveler_configuration.child_count;
  $("greeting").textContent = `Hi, ${i.client_name.split(" ")[0]}`;
  $("trip-card").innerHTML = `
    <p class="micro">Your trip · ${esc(dateLabel(i.start_date))} – ${esc(dateLabel(i.end_date))}</p>
    <h1><em>${esc(city)}</em></h1>
    <p>${esc(i.accommodation_area || i.destination)}${kids ? ` · with your ${kids === 1 ? "child" : "children"}` : ""}</p>
    <span class="chip">${state.entered ? "✓ Entered Spain" : esc(phase)}</span>`;
  const advisor = i.advisor_name || "your Wonder advisor";
  $("advisor-card").innerHTML = `<div class="avatar">${esc(advisor.split(/\s+/).map((p) => p[0]).join("").slice(0, 2).toUpperCase())}</div>
    <div><b>${esc(advisor)}</b><small>Your travel advisor · usually replies in minutes</small></div>`;
}

function policyCard(policy) {
  return `<div class="policy-card">
    <p class="micro">Travel insurance</p>
    <h3>${esc(policy.insurer)}</h3>
    <p>Policy ${esc(policy.policy_number)} · ${esc(dateLabel(policy.coverage_start))} – ${esc(dateLabel(policy.coverage_end))}</p>
    <p>${esc(money(policy.medical_cover))} medical${policy.repatriation ? " incl. repatriation" : ""}${policy.schengen_compliant ? " · Schengen-compliant" : ""}</p>
    <p class="sim">Simulated demo policy</p>
    <button class="btn primary" type="button" data-show="${esc(policy.id)}">Show to officer</button>
  </div>`;
}

function renderThread() {
  const thread = $("thread");
  const atBottom = thread.scrollHeight - window.innerHeight - window.scrollY < 120;
  if (!state.messages.length) {
    thread.innerHTML = `<p class="empty">Message ${esc(state.intake.advisor_name || "your advisor")} any time: a real person who can send our AI agents to help.</p>`;
  } else {
    let lastDay = null;
    thread.innerHTML = state.messages.map((m) => {
      const mine = m.sender === "traveler";
      const day = m.created_at.slice(0, 10);
      const divider = day !== lastDay ? `<span class="day">${esc(dateLabel(day))}</span>` : "";
      lastDay = day;
      const policy = m.attachment && state.policies[m.attachment.policy_id];
      return `${divider}<div class="bubble ${mine ? "me" : "them"}">${esc(m.text)}</div>
        ${policy ? policyCard(policy) : ""}
        <span class="meta ${mine ? "me" : "them"}">${mine ? "You" : esc(state.intake.advisor_name || "Advisor")} · ${esc(clock(m.created_at))}</span>`;
    }).join("");
  }
  const asked = state.messages.some((m) => m.sender === "traveler");
  $("quick").innerHTML = asked ? "" : QUICK_REPLIES.map((q, n) => `<button type="button" data-quick="${n}">${esc(q)}</button>`).join("");
  if (atBottom) window.scrollTo({ top: document.body.scrollHeight });
}

function showCertificate(policy) {
  const el = $("certificate");
  el.innerHTML = state.entered
    ? `<div class="welcome"><div class="stamp">ENTRY<br>✓<br>ESPAÑA</div><h2>Welcome to Spain</h2><p>Enjoy Barcelona. Your advisor has been told you're through.</p></div>
       <div class="cert-actions"><button class="btn dark" type="button" data-close>Back to my trip</button></div>`
    : `<article class="cert">
        <span class="ribbon">SIMULATED</span>
        <p class="kicker">Certificate of travel insurance</p>
        <h2 id="cert-title">${esc(policy.insurer)}</h2>
        <dl>
          <div><dt>Policy number</dt><dd class="big">${esc(policy.policy_number)}</dd></div>
          <div><dt>Insured</dt><dd>${policy.insured.map(esc).join("<br>")}</dd></div>
          <div><dt>Period of cover</dt><dd>${esc(dateLabel(policy.coverage_start))} – ${esc(dateLabel(policy.coverage_end))}, ${esc(policy.coverage_end.slice(0, 4))}</dd></div>
          <div><dt>Territory</dt><dd>Schengen Area</dd></div>
          <div><dt>Medical expenses</dt><dd>${esc(money(policy.medical_cover))}${policy.repatriation ? ", including repatriation" : ""}</dd></div>
          <div><dt>Deductible</dt><dd>${esc(money(policy.deductible))}</dd></div>
        </dl>
        ${policy.schengen_compliant ? `<div class="ok">✓ Meets Schengen travel-insurance requirements</div>` : ""}
        <p class="disclaimer">Demo only: issued by Wonder's simulated voice-agent flow. Not a real insurance policy.</p>
      </article>
      <div class="cert-actions">
        <button class="btn dark" type="button" data-through>I'm through ✓</button>
        <button class="btn light" type="button" data-close>Close</button>
      </div>`;
  el.hidden = false;
  el.querySelector("button")?.focus();
}

// ---------- data ----------
async function refresh() {
  const messages = await api(`/trips/${state.intake.trip_id}/messages`);
  for (const m of messages) {
    const id = m.attachment?.policy_id;
    if (id && !state.policies[id]) state.policies[id] = await api(`/trips/${state.intake.trip_id}/insurance-policies/${id}`);
  }
  state.entered = messages.some((m) => m.sender === "traveler" && m.text === THROUGH_TEXT);
  const changed = messages.length !== state.messages.length;
  state.messages = messages;
  if (changed) { renderThread(); renderTrip(); }
}

function startPolling() {
  clearInterval(state.poll);
  state.poll = setInterval(() => refresh().catch(() => {}), 2000);
}

async function send(text) {
  if (!text.trim() || state.sending) return;
  state.sending = true;
  $("composer").querySelector("button").disabled = true;
  try {
    await api(`/trips/${state.intake.trip_id}/messages`, { sender: "traveler", text: text.trim() });
    $("message").value = "";
    await refresh();
    window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
  } catch (err) {
    alert(`Couldn't send: ${err.message}`);
  } finally {
    state.sending = false;
    $("composer").querySelector("button").disabled = false;
  }
}

// ---------- events ----------
$("composer").addEventListener("submit", (e) => { e.preventDefault(); send($("message").value); });
$("message").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send($("message").value); } });
document.addEventListener("click", async (e) => {
  const el = e.target.closest("[data-quick],[data-show],[data-close],[data-through]");
  if (!el) return;
  if (el.dataset.quick !== undefined) send(QUICK_REPLIES[Number(el.dataset.quick)]);
  else if (el.dataset.show) showCertificate(state.policies[el.dataset.show]);
  else if (el.dataset.close !== undefined) $("certificate").hidden = true;
  else if (el.dataset.through !== undefined) {
    el.disabled = true;
    await send(THROUGH_TEXT);
    state.entered = true;
    showCertificate(null);
  }
});
document.addEventListener("keydown", (e) => { if (e.key === "Escape") $("certificate").hidden = true; });

async function main() {
  try {
    const intakes = await api("/intakes?limit=100");
    const wanted = new URL(location.href).searchParams.get("intake");
    state.intake = intakes.find((i) => i.id === wanted) || intakes[0];
    if (!state.intake) { $("thread").innerHTML = `<p class="empty">No trip yet. Your advisor will set it up after your call.</p>`; return; }
    renderTrip();
    renderThread();
    await refresh();
    renderThread();
    startPolling();
  } catch (err) {
    $("thread").innerHTML = `<p class="empty">Can't reach Wonder right now (${esc(err.message)}).</p>`;
  }
}

main();
