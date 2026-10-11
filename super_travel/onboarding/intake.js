// Sends the onboarding form to the Wonder control API (via the dashboard server's /api proxy),
// which creates the trip and starts all five agents. Then opens the advisor dashboard.
(function () {
  const MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"];
  const pad = (n) => String(n).padStart(2, "0");
  const month = (word) => MONTHS.findIndex((m) => m.startsWith(String(word).toLowerCase().slice(0, 3))) + 1;
  const val = (id) => (document.getElementById("wf-" + id)?.value || "").trim();

  // "October 19–25, 2026" · "Oct 30 – Nov 2, 2026" · "2026-10-19 to 2026-10-25"
  function parseDates(text) {
    const iso = text.match(/(\d{4}-\d{2}-\d{2}).*?(\d{4}-\d{2}-\d{2})/);
    if (iso) return [iso[1], iso[2]];
    const m = text.match(/([A-Za-z]+)\s+(\d{1,2})\s*(?:–|-|to|through)\s*(?:([A-Za-z]+)\s+)?(\d{1,2}),?\s*(\d{4})/);
    if (!m || !month(m[1])) return null;
    const [, m1, d1, m2, d2, year] = m;
    const endMonth = m2 ? month(m2) : month(m1);
    const endYear = endMonth < month(m1) ? +year + 1 : +year;
    return [`${year}-${pad(month(m1))}-${pad(d1)}`, `${endYear}-${pad(endMonth)}-${pad(d2)}`];
  }

  // "1 adult, 1 child" · "2 adults and 2 kids" · "2 adults, 1 infant"
  function parseParty(text) {
    const count = (re) => { const m = text.match(re); return m ? +m[1] : 0; };
    const words = { one: 1, two: 2, three: 3, four: 4, five: 5, six: 6 };
    text = text.toLowerCase().replace(/\b(one|two|three|four|five|six)\b/g, (w) => words[w]);
    return {
      adult_count: Math.max(1, count(/(\d+)\s*adults?/)),
      child_count: count(/(\d+)\s*(?:child|children|kids?)/),
      infant_count: count(/(\d+)\s*(?:infants?|babies|baby)/),
    };
  }

  const list = (text) => text.split(/,|;|\band\b/i).map((s) => s.trim()).filter(Boolean).slice(0, 20);

  function buildIntake() {
    const errors = [];
    const dates = parseDates(val("dates"));
    if (!val("name")) errors.push("name");
    if (!val("destination")) errors.push("destination");
    if (!dates) errors.push("travel dates (e.g. “October 19–25, 2026”)");
    const party = parseParty(val("party") || "1 adult");
    const ages = (val("age").match(/\d+/g) || []).map(Number).filter((a) => a <= 17);
    return {
      errors,
      body: {
        client_name: val("name"),
        purpose: val("purpose") || "Vacation",
        destination: val("destination"),
        start_date: dates?.[0],
        end_date: dates?.[1],
        traveler_configuration: party,
        child_ages: party.child_count ? ages.slice(0, party.child_count) : [],
        accommodation_area: val("hotel") || null,
        interests: list(val("interests")),
        needs: list(val("needs")),
        channel: "phone_call",
      },
    };
  }

  async function send(button, note) {
    const { errors, body } = buildIntake();
    if (errors.length) { note.textContent = "Please fill in: " + errors.join(", ") + "."; return; }
    button.disabled = true;
    note.textContent = "Sending to the Wonder agents…";
    try {
      const res = await fetch("/api/intakes", {
        method: "POST",
        headers: { "content-type": "application/json", "idempotency-key": crypto.randomUUID() },
        body: JSON.stringify(body),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error?.message || res.statusText);
      note.textContent = "Sent. Opening the advisor dashboard…";
      location.href = "/?intake=" + encodeURIComponent(json.data.id);
    } catch (err) {
      note.textContent = "Couldn't send: " + err.message + ". Is the dashboard server and control API running?";
      button.disabled = false;
    }
  }

  const button = document.getElementById("w-send");
  const note = document.getElementById("w-send-note");
  if (button && note) button.addEventListener("click", () => send(button, note));
})();
