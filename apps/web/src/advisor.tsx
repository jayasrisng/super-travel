import { useEffect, useRef, useState, type FormEvent } from "react";
import { api, type Schema } from "./api";
import { Heading, Loading, Note } from "./components";

type Link = Schema["AdvisorLink"];
type Message = Schema["Message"];
type Policy = Schema["InsurancePolicy"];

const BORDER_HELP =
  "I'm at border control in Barcelona and the officer is asking for proof of travel insurance. I don't have any!";
const THROUGH =
  "I showed the certificate and I'm through! We're in Spain. Thank you so much!";

const money = (m: { amount_minor: number; currency: string }) => {
  const fmt = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: m.currency,
  });
  return fmt.format(
    m.amount_minor / 10 ** (fmt.resolvedOptions().maximumFractionDigits ?? 2),
  );
};
const day = (iso: string) =>
  new Date(iso + "T12:00:00").toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
const clock = (iso: string) =>
  new Date(iso).toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });

export function Advisor() {
  const [link, setLink] = useState<Link | null>();
  const [error, setError] = useState("");
  useEffect(() => {
    api<Link>("/consumer/advisor")
      .then(setLink)
      .catch(() => setLink(null));
  }, []);
  if (link === undefined) return <Loading />;
  if (link === null)
    return <Connect onLinked={setLink} error={error} setError={setError} />;
  return <Conversation link={link} />;
}

function Connect({
  onLinked,
  error,
  setError,
}: {
  onLinked: (link: Link) => void;
  error: string;
  setError: (e: string) => void;
}) {
  const [code, setCode] = useState(
    new URLSearchParams(location.search).get("code") || "",
  );
  const [busy, setBusy] = useState(false);
  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      onLinked(
        await api<Link>("/consumer/advisor-link", "POST", {
          client_code: code.trim(),
        }),
      );
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <Heading
        eyebrow="a real person, on your side"
        title="Your travel advisor"
        note="Connect with the code your advisor gave you after your onboarding call."
      />
      <form className="notebook-form advisor-connect" onSubmit={submit}>
        <label>
          Client code
          <input
            value={code}
            onChange={(e) => setCode(e.target.value.toUpperCase())}
            placeholder="e.g. K7Q2XB"
            autoComplete="off"
            maxLength={12}
            required
          />
        </label>
        <button
          className="ink-button"
          disabled={busy || code.trim().length < 4}
        >
          {busy ? "Connecting…" : "Connect"}
        </button>
        {error ? <Note kind="error">{error}</Note> : null}
      </form>
    </>
  );
}

function Conversation({ link }: { link: Link }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [policies, setPolicies] = useState<Record<string, Policy>>({});
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [showing, setShowing] = useState<Policy | null>(null);
  const [entered, setEntered] = useState(false);
  const bottom = useRef<HTMLDivElement>(null);
  const advisor = link.advisor_name || "your advisor";

  const fetched = useRef(new Set<string>());

  async function refresh() {
    const list = await api<Message[]>("/consumer/advisor/messages");
    const missing = list
      .map((m) => m.attachment?.policy_id)
      .filter((id): id is string => !!id && !fetched.current.has(id));
    if (missing.length) {
      missing.forEach((id) => fetched.current.add(id));
      const loaded = await Promise.all(
        missing.map((id) => api<Policy>("/consumer/advisor/policies/" + id)),
      );
      setPolicies((p) => ({
        ...p,
        ...Object.fromEntries(loaded.map((x) => [x.id, x])),
      }));
    }
    setMessages((prev) => (prev.length === list.length ? prev : list));
    setEntered(list.some((m) => m.sender === "traveler" && m.text === THROUGH));
  }

  useEffect(() => {
    void refresh().catch((e) => setError(e.message));
    const timer = setInterval(() => void refresh().catch(() => {}), 2000);
    return () => clearInterval(timer);
  }, []);
  useEffect(() => {
    // Block body on purpose: newer browsers return a Promise from
    // scrollIntoView, and React treats any returned value as a cleanup.
    bottom.current?.scrollIntoView({ block: "end" });
  }, [messages.length]);

  async function send(text: string) {
    if (!text.trim() || sending) return;
    setSending(true);
    setError("");
    try {
      await api("/consumer/advisor/messages", "POST", { text: text.trim() });
      setDraft("");
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSending(false);
    }
  }

  return (
    <>
      <Heading
        eyebrow={`${link.destination} · ${day(link.start_date)} – ${day(link.end_date)}`}
        title={`Messages with ${advisor}`}
        note="A real person who can send Wonder's AI agents to help, any time."
      >
        <span className="advisor-status">
          {entered ? "✓ Entered Spain" : "● Online"}
        </span>
      </Heading>
      {error ? <Note kind="error">{error}</Note> : null}
      <section
        className="advisor-thread"
        aria-live="polite"
        aria-label={`Conversation with ${advisor}`}
      >
        {messages.length === 0 ? (
          <p className="annotation">
            Nothing here yet. Write to {advisor} whenever you need a hand.
          </p>
        ) : (
          messages.map((m) => {
            const mine = m.sender === "traveler";
            const policy = m.attachment
              ? policies[m.attachment.policy_id]
              : undefined;
            return (
              <div
                className={`advisor-msg ${mine ? "mine" : "theirs"}`}
                key={m.id}
              >
                <p className="advisor-bubble">{m.text}</p>
                {policy ? (
                  <div className="policy-slip">
                    <p className="eyebrow">Travel insurance</p>
                    <h3>{policy.insurer}</h3>
                    <p>
                      Policy {policy.policy_number} ·{" "}
                      {day(policy.coverage_start)} – {day(policy.coverage_end)}
                    </p>
                    <p>
                      {money(policy.medical_cover)} medical
                      {policy.repatriation ? " incl. repatriation" : ""}
                      {policy.schengen_compliant ? " · Schengen-compliant" : ""}
                    </p>
                    <p className="sim-note">Simulated demo policy</p>
                    <button
                      className="ink-button"
                      onClick={() => setShowing(policy)}
                    >
                      Show to officer
                    </button>
                  </div>
                ) : null}
                <small>
                  {mine ? "You" : advisor} · {clock(m.created_at)}
                </small>
              </div>
            );
          })
        )}
        <div ref={bottom} />
      </section>
      {!messages.some((m) => m.sender === "traveler") ? (
        <div className="chips advisor-quick">
          <button onClick={() => void send(BORDER_HELP)}>{BORDER_HELP}</button>
        </div>
      ) : null}
      <form
        className="advisor-compose"
        onSubmit={(e) => {
          e.preventDefault();
          void send(draft);
        }}
      >
        <label className="visually-hidden" htmlFor="advisor-draft">
          Message {advisor}
        </label>
        <input
          id="advisor-draft"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={`Message ${advisor}…`}
          maxLength={2000}
        />
        <button className="ink-button" disabled={sending || !draft.trim()}>
          Send
        </button>
      </form>
      {showing ? (
        <Certificate
          policy={showing}
          entered={entered}
          close={() => setShowing(null)}
          through={async () => {
            await send(THROUGH);
            setEntered(true);
          }}
        />
      ) : null}
    </>
  );
}

function Certificate({
  policy,
  entered,
  close,
  through,
}: {
  policy: Policy;
  entered: boolean;
  close: () => void;
  through: () => Promise<void>;
}) {
  const closeRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    closeRef.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && close();
    addEventListener("keydown", onKey);
    return () => removeEventListener("keydown", onKey);
  }, []);
  return (
    <div
      className="certificate-screen"
      role="dialog"
      aria-modal="true"
      aria-labelledby="certificate-title"
    >
      {entered ? (
        <div className="welcome-stamp">
          <div className="stamp" aria-hidden>
            ENTRY
            <br />✓<br />
            ESPAÑA
          </div>
          <h2 id="certificate-title">Welcome to Spain</h2>
          <p>Enjoy Barcelona. Your advisor knows you're through.</p>
          <button ref={closeRef} className="ink-button" onClick={close}>
            Back to my notebook
          </button>
        </div>
      ) : (
        <>
          <article className="certificate">
            <span className="ribbon">SIMULATED</span>
            <p className="eyebrow">Certificate of travel insurance</p>
            <h2 id="certificate-title">{policy.insurer}</h2>
            <dl>
              <dt>Policy number</dt>
              <dd className="big">{policy.policy_number}</dd>
              <dt>Insured</dt>
              <dd>
                {policy.insured.map((name) => (
                  <span key={name}>
                    {name}
                    <br />
                  </span>
                ))}
              </dd>
              <dt>Period of cover</dt>
              <dd>
                {day(policy.coverage_start)} – {day(policy.coverage_end)},{" "}
                {policy.coverage_end.slice(0, 4)}
              </dd>
              <dt>Territory</dt>
              <dd>Schengen Area</dd>
              <dt>Medical expenses</dt>
              <dd>
                {money(policy.medical_cover)}
                {policy.repatriation ? ", including repatriation" : ""}
              </dd>
            </dl>
            {policy.schengen_compliant ? (
              <p className="cert-ok">
                ✓ Meets Schengen travel-insurance requirements
              </p>
            ) : null}
            <p className="sim-note">
              Demo only: issued by Wonder's voice-agent flow. Not a real
              insurance policy.
            </p>
          </article>
          <div className="certificate-actions">
            <button className="ink-button" onClick={() => void through()}>
              I'm through ✓
            </button>
            <button ref={closeRef} onClick={close}>
              Close
            </button>
          </div>
        </>
      )}
    </div>
  );
}
