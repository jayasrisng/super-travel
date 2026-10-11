import { useEffect, useRef, useState, type FormEvent } from "react";
import { api, type Schema } from "./api";
import { Check, Empty, Heading, Loading, Note, OutfitLook } from "./components";
import type { Navigate } from "./App";

function clothingPayload(
  item: Schema["WardrobeItem"],
): Schema["WardrobeCreate"] {
  const { id, version, image_mode, ...payload } = item;
  return payload;
}
export function Wardrobe({ nav, tripId }: { nav: Navigate; tripId?: string }) {
  const [items, setItems] = useState<Schema["WardrobeItem"][]>([]),
    [loaded, setLoaded] = useState(false),
    [category, setCategory] = useState("all"),
    [color, setColor] = useState("all"),
    [occasion, setOccasion] = useState("all"),
    [error, setError] = useState(""),
    [edit, setEdit] = useState<Schema["WardrobeItem"]>(),
    [adding, setAdding] = useState(false);
  async function refresh() {
    setItems(await api("/consumer/wardrobe"));
    setLoaded(true);
  }
  useEffect(() => {
    void refresh().catch((e) => setError(e.message));
  }, []);
  async function favorite(item: Schema["WardrobeItem"]) {
    try {
      await api(
        "/consumer/wardrobe/" + item.id,
        "PUT",
        { ...clothingPayload(item), favorite: !item.favorite },
        item.version,
      );
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    }
  }
  const visible = items.filter(
    (item) =>
      (category === "all" || item.category === category) &&
      (color === "all" || item.color === color) &&
      (occasion === "all" || (item.occasions || []).includes(occasion)),
  );
  return (
    <>
      <Heading
        eyebrow="your fashion sketchbook"
        title="A few good pieces."
        note="A considered wardrobe. Comfortable combinations. A lighter suitcase."
      >
        <button
          className="ink-button"
          onClick={() => {
            setAdding(true);
            setEdit(undefined);
          }}
        >
          + Add a piece
        </button>
      </Heading>
      <div className="wardrobe-intro">
        <span className="hand">wear what feels like you.</span>
        <button
          className="outline-button"
          onClick={() => nav("/outfits" + (tripId ? "?trip=" + tripId : ""))}
        >
          Find my outfits ↗
        </button>
      </div>
      <Note kind="sample">
        Your first {items.length || 34} pieces are original illustrations. Add
        photos and tag your own clothes. No AI recognition or virtual try-on is
        claimed.
      </Note>
      {error ? <Note kind="error">{error}</Note> : null}
      {adding || edit ? (
        <ClothingForm
          item={edit}
          close={() => {
            setEdit(undefined);
            setAdding(false);
          }}
          refresh={refresh}
        />
      ) : null}
      <div className="filters">
        <div className="chips" aria-label="Clothing category">
          {["all", "tops", "bottoms", "shoes", "accessories", "essentials"].map(
            (c) => (
              <button
                key={c}
                aria-pressed={category === c}
                onClick={() => setCategory(c)}
              >
                {c === "all" ? `All pieces (${items.length})` : c}
              </button>
            ),
          )}
        </div>
        <label>
          Color
          <select value={color} onChange={(e) => setColor(e.target.value)}>
            <option value="all">Every color</option>
            {Array.from(new Set(items.map((item) => item.color)))
              .sort()
              .map((c) => (
                <option key={c}>{c}</option>
              ))}
          </select>
        </label>
        <label>
          Occasion
          <select
            value={occasion}
            onChange={(e) => setOccasion(e.target.value)}
          >
            <option value="all">Every occasion</option>
            {["walking", "casual", "dinner", "business", "outdoors"].map(
              (c) => (
                <option key={c}>{c}</option>
              ),
            )}
          </select>
        </label>
      </div>
      {!loaded ? (
        <Loading />
      ) : visible.length ? (
        <>
          <h2 className="sr-only">Wardrobe pieces</h2>
          <div className="wardrobe-grid">
            {visible.map((item) => (
              <article className="garment" key={item.id}>
                <button
                  className={`favorite ${item.favorite ? "selected" : ""}`}
                  aria-label={`${item.favorite ? "Unfavorite" : "Favorite"} ${item.name}`}
                  onClick={() => void favorite(item)}
                >
                  {item.favorite ? "♥" : "♡"}
                </button>
                <button
                  className="garment-open"
                  onClick={() => {
                    setEdit(item);
                    setAdding(false);
                    window.scrollTo({ top: 0, behavior: "smooth" });
                  }}
                >
                  <div className="garment-art">
                    <img loading="lazy" src={item.image} alt={item.name} />
                  </div>
                  <h3>{item.name}</h3>
                  <p>
                    {item.category} · {item.color}
                  </p>
                  <small>
                    {item.availability !== "ready"
                      ? `${item.availability} · `
                      : ""}
                    {item.ownership_status === "needed"
                      ? "Still needed"
                      : item.style}
                  </small>
                </button>
              </article>
            ))}
          </div>
        </>
      ) : (
        <Empty title="A little space in the wardrobe">
          Try a different filter, or add something you love.
        </Empty>
      )}
    </>
  );
}
function ClothingForm({
  item,
  close,
  refresh,
}: {
  item?: Schema["WardrobeItem"];
  close: () => void;
  refresh: () => Promise<void>;
}) {
  const [draft, setDraft] = useState<Schema["WardrobeCreate"]>(() =>
    item
      ? clothingPayload(item)
      : {
          name: "",
          category: "tops",
          color: "cream",
          image: "",
          favorite: false,
          ownership_status: "owned",
          style: "everyday",
          season: ["spring", "autumn"],
          warmth: 2,
          occasions: ["walking", "casual"],
          availability: "ready",
        },
  );
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [photo, setPhoto] = useState<File>();
  useEffect(() => {
    setDraft(
      item
        ? clothingPayload(item)
        : {
            name: "",
            category: "tops",
            color: "cream",
            image: "",
            favorite: false,
            ownership_status: "owned",
            style: "everyday",
            warmth: 2,
            occasions: ["walking", "casual"],
            availability: "ready",
          },
    );
    setPhoto(undefined);
  }, [item?.id]);
  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      let saved = await api<Schema["WardrobeItem"]>(
        "/consumer/wardrobe" + (item ? "/" + item.id : ""),
        item ? "PUT" : "POST",
        draft,
        item?.version,
      );
      if (photo) {
        if (photo.size > 2_000_000)
          throw new Error("Use a photo smaller than 2 MB.");
        const content = await new Promise<string>((resolve, reject) => {
          const r = new FileReader();
          r.onload = () => resolve(String(r.result).split(",")[1]);
          r.onerror = reject;
          r.readAsDataURL(photo);
        });
        saved = await api(
          "/consumer/wardrobe/" + saved.id + "/photo",
          "POST",
          { content_base64: content, mime: photo.type },
          saved.version,
        );
      }
      await refresh();
      close();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function remove() {
    if (!item) return;
    try {
      await api(
        "/consumer/wardrobe/" + item.id,
        "DELETE",
        undefined,
        item.version,
      );
      await refresh();
      close();
    } catch (e) {
      setError((e as Error).message);
    }
  }
  return (
    <section className="task-sheet">
      <h2>{item ? "A note about this piece" : "Add something you love"}</h2>
      {error ? <Note kind="error">{error}</Note> : null}
      <form className="notebook-form compact" onSubmit={submit}>
        <label>
          Item name
          <input
            required
            value={draft.name}
            onChange={(e) => setDraft((d) => ({ ...d, name: e.target.value }))}
          />
        </label>
        <div className="form-pair">
          <label>
            Category
            <select
              value={draft.category}
              onChange={(e) =>
                setDraft((d) => ({
                  ...d,
                  category: e.target
                    .value as Schema["WardrobeCreate"]["category"],
                }))
              }
            >
              {["tops", "bottoms", "shoes", "accessories", "essentials"].map(
                (c) => (
                  <option key={c}>{c}</option>
                ),
              )}
            </select>
          </label>
          <label>
            Color
            <input
              value={draft.color}
              onChange={(e) =>
                setDraft((d) => ({ ...d, color: e.target.value }))
              }
            />
          </label>
        </div>
        <div className="form-pair">
          <label>
            Style
            <input
              value={draft.style}
              onChange={(e) =>
                setDraft((d) => ({ ...d, style: e.target.value }))
              }
            />
          </label>
          <label>
            Warmth
            <select
              value={draft.warmth}
              onChange={(e) =>
                setDraft((d) => ({ ...d, warmth: Number(e.target.value) }))
              }
            >
              {[0, 1, 2, 3, 4, 5].map((n) => (
                <option key={n} value={n}>
                  {n} · {n < 2 ? "light" : n < 4 ? "layered" : "warm"}
                </option>
              ))}
            </select>
          </label>
        </div>
        <label>
          Suitable occasions
          <input
            value={draft.occasions?.join(", ")}
            onChange={(e) =>
              setDraft((d) => ({
                ...d,
                occasions: e.target.value
                  .split(",")
                  .map((s) => s.trim())
                  .filter(Boolean),
              }))
            }
          />
        </label>
        <div className="form-pair">
          <label>
            Ownership
            <select
              value={draft.ownership_status}
              onChange={(e) =>
                setDraft((d) => ({
                  ...d,
                  ownership_status: e.target
                    .value as Schema["WardrobeCreate"]["ownership_status"],
                }))
              }
            >
              <option value="owned">I own it</option>
              <option value="needed">Still needed</option>
            </select>
          </label>
          <label>
            Ready to wear?
            <select
              value={draft.availability}
              onChange={(e) =>
                setDraft((d) => ({
                  ...d,
                  availability: e.target
                    .value as Schema["WardrobeCreate"]["availability"],
                }))
              }
            >
              {["ready", "worn", "dirty", "unavailable"].map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </label>
        </div>
        <label>
          Clothing photo · optional
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={(e) => setPhoto(e.target.files?.[0])}
          />
          <small>
            JPEG, PNG or WebP under 2 MB. Manual tagging; metadata is removed.
          </small>
        </label>
        <div className="actions">
          <button className="ink-button" disabled={busy}>
            {busy ? "Saving…" : "Save piece"}
          </button>
          <button type="button" onClick={close}>
            Close
          </button>
          {item ? (
            <button
              type="button"
              className="danger"
              onClick={() => void remove()}
            >
              Remove piece
            </button>
          ) : null}
        </div>
      </form>
    </section>
  );
}
export function Outfits({ nav, tripId }: { nav: Navigate; tripId?: string }) {
  const [items, setItems] = useState<Schema["WardrobeItem"][]>([]),
    [outfits, setOutfits] = useState<Schema["Outfit"][]>([]),
    [votes, setVotes] = useState<Schema["OutfitVote"][]>([]),
    [index, setIndex] = useState(0),
    [last, setLast] = useState<{ index: number; id: string }>(),
    [occasion, setOccasion] =
      useState<Schema["OutfitRequest"]["occasion"]>("walking"),
    [temperature, setTemperature] = useState(18),
    [profile, setProfile] = useState<Schema["Profile"]>(),
    [trips, setTrips] = useState<Schema["Trip"][]>([]),
    [fashion, setFashion] = useState<Schema["FashionPreferences"]>({
      occasion: "walking",
      temperature_c: 18,
      preferred_style: "",
      preferred_colors: [],
      owned_only: false,
    }),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [message, setMessage] = useState(""),
    [drag, setDrag] = useState(0);
  const pointer = useRef<number | null>(null);
  useEffect(() => {
    void Promise.all([
      api<Schema["WardrobeItem"][]>("/consumer/wardrobe"),
      api<Schema["OutfitVote"][]>("/consumer/outfits/votes"),
      api<Schema["Home"]>("/consumer/home"),
    ])
      .then(([i, v, home]) => {
        setItems(i);
        setVotes(v);
        setProfile(home.profile);
        setTrips(home.trips);
        if (home.profile.fashion) setFashion(home.profile.fashion);
        setOccasion(home.profile.fashion?.occasion || "walking");
        setTemperature(home.profile.fashion?.temperature_c ?? 18);
      })
      .catch((e) => setError(e.message));
  }, []);
  async function saveFashion() {
    if (!profile)
      throw new Error("Fashion settings are still loading. Refresh to retry.");
    if (!Number.isInteger(temperature) || temperature < -30 || temperature > 50)
      throw new Error("Enter a whole-number temperature between −30 and 50°C.");
    const { id, label, version, ...preferences } = profile;
    const saved = await api<Schema["Profile"]>(
      "/consumer/preferences",
      "PUT",
      {
        ...preferences,
        fashion: { ...fashion, occasion, temperature_c: temperature },
      },
      version,
    );
    setProfile(saved);
    return saved;
  }
  async function saveSettings() {
    setBusy(true);
    setError("");
    try {
      await saveFashion();
      setMessage(
        "Fashion settings saved. Generate outfits to use your changes.",
      );
    } catch (e) {
      setError((e as Error).message);
      const home = await api<Schema["Home"]>("/consumer/home").catch(
        () => undefined,
      );
      if (home) setProfile(home.profile);
    } finally {
      setBusy(false);
    }
  }
  async function finish() {
    if (!tripId || busy) return;
    setBusy(true);
    setError("");
    try {
      await api("/consumer/trips/" + tripId + "/packing", "POST", {});
      nav("/packing?trip=" + tripId);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function generate() {
    setBusy(true);
    try {
      await saveFashion();
      const freshVotes = await api<Schema["OutfitVote"][]>(
        "/consumer/outfits/votes",
      );
      setVotes(freshVotes);
      const generated = await api<Schema["Outfit"][]>(
        "/consumer/outfits/generate",
        "POST",
        {
          trip_id: tripId || null,
          occasion,
          temperature_c: temperature,
          weather_mode: "manual",
        },
      );
      const voted = new Set(freshVotes.map((v) => v.outfit_id));
      setOutfits(generated.filter((o) => !voted.has(o.id)));
      setIndex(0);
      setLast(undefined);
      setMessage("");
      setError("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function vote(decision: Schema["VoteRequest"]["decision"]) {
    const outfit = outfits[index];
    if (!outfit || busy) return;
    setBusy(true);
    try {
      const saved = await api<Schema["OutfitVote"]>(
        "/consumer/outfits/" + outfit.id + "/vote",
        "POST",
        { decision },
      );
      setVotes((v) => [
        ...v.filter((item) => item.outfit_id !== saved.outfit_id),
        saved,
      ]);
      setLast({ index, id: outfit.id });
      setIndex((i) => i + 1);
      setMessage(
        decision === "like"
          ? "Liked & saved to your notebook."
          : "Passed. We’ll leave this combination out next time.",
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
      setDrag(0);
    }
  }
  async function undo() {
    if (!last || busy) return;
    setBusy(true);
    try {
      await api("/consumer/outfits/" + last.id + "/vote", "DELETE");
      setVotes((v) => v.filter((item) => item.outfit_id !== last.id));
      setIndex(last.index);
      setLast(undefined);
      setMessage("Back a page. Your last vote was undone.");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const liked = votes.filter(
    (v) => v.decision === "like" && v.trip_id === (tripId || null),
  ).length;
  const outfit = outfits[index];
  return (
    <>
      <Heading
        eyebrow="make room for a little style"
        title="What feels like you?"
        note="A capsule of comfortable combinations. A swipe, and a lighter suitcase."
      />
      <div className="outfit-layout">
        <aside className="outfit-notes">
          <p className="hand">
            A little edit.
            <br />A lot of possibilities.
          </p>
          {!tripId ? (
            <label>
              Packing for
              <select
                value=""
                disabled={busy}
                onChange={(e) => {
                  if (e.target.value) nav("/outfits?trip=" + e.target.value);
                }}
              >
                <option value="">Just browsing</option>
                {trips.map((trip) => (
                  <option key={trip.id} value={trip.id}>
                    {trip.title}
                  </option>
                ))}
              </select>
            </label>
          ) : null}
          <details className="fashion-panel" open={!outfits.length}>
            <summary>
              Fashion settings · {occasion} · {temperature}°C
            </summary>
            <fieldset className="fashion-settings" disabled={busy || !profile}>
              <legend className="sr-only">Fashion settings</legend>
              <label>
                What’s the occasion?
                <select
                  value={occasion}
                  onChange={(e) =>
                    setOccasion(
                      e.target.value as Schema["OutfitRequest"]["occasion"],
                    )
                  }
                >
                  {["walking", "dinner", "business", "outdoors"].map((s) => (
                    <option key={s}>{s}</option>
                  ))}
                </select>
              </label>
              <label>
                Expected temperature (°C)
                <input
                  type="number"
                  min="-30"
                  max="50"
                  value={temperature}
                  onChange={(e) => setTemperature(Number(e.target.value))}
                />
              </label>
              <label>
                Preferred style
                <select
                  value={fashion.preferred_style || ""}
                  onChange={(e) =>
                    setFashion((f) => ({
                      ...f,
                      preferred_style: e.target.value,
                    }))
                  }
                >
                  <option value="">Any style</option>
                  {Array.from(new Set(items.map((item) => item.style)))
                    .sort()
                    .map((style) => (
                      <option key={style}>{style}</option>
                    ))}
                </select>
              </label>
              <div className="fashion-colors">
                <p id="fashion-colors-label">Preferred colors</p>
                <div className="chips" aria-labelledby="fashion-colors-label">
                  {Array.from(new Set(items.map((item) => item.color)))
                    .sort()
                    .map((color) => (
                      <button
                        type="button"
                        key={color}
                        aria-pressed={
                          fashion.preferred_colors?.includes(color) || false
                        }
                        onClick={() =>
                          setFashion((f) => ({
                            ...f,
                            preferred_colors: f.preferred_colors?.includes(
                              color,
                            )
                              ? f.preferred_colors.filter((c) => c !== color)
                              : [...(f.preferred_colors || []), color].slice(
                                  0,
                                  10,
                                ),
                          }))
                        }
                      >
                        {color}
                      </button>
                    ))}
                </div>
              </div>
              <label className="fashion-owned">
                <input
                  type="checkbox"
                  checked={fashion.owned_only || false}
                  onChange={(e) =>
                    setFashion((f) => ({ ...f, owned_only: e.target.checked }))
                  }
                />
                Only clothes I own
              </label>
              <button
                className="outline-button"
                onClick={() => void saveSettings()}
              >
                Save fashion settings
              </button>
            </fieldset>
          </details>
          <p className="annotation">
            Style and colors guide ranking. Your temperature is an estimate, not
            a live forecast. Only ready clothing is considered.
          </p>
          <button
            className="ink-button"
            disabled={busy || !profile}
            onClick={() => void generate()}
          >
            Generate outfits
          </button>
          <div className="liked-counter">
            <strong>{liked}</strong>
            <span>looks you love</span>
          </div>
        </aside>
        <section className="swipe-section">
          {error ? <Note kind="error">{error}</Note> : null}
          {outfit ? (
            <>
              <div
                className="swipe-card"
                tabIndex={0}
                role="group"
                aria-label="Outfit swipe card"
                style={{
                  transform: `translateX(${drag}px) rotate(${drag / 30}deg)`,
                }}
                onKeyDown={(e) => {
                  if (e.key === "ArrowRight") {
                    e.preventDefault();
                    void vote("like");
                  }
                  if (e.key === "ArrowLeft") {
                    e.preventDefault();
                    void vote("dislike");
                  }
                  if (e.key.toLowerCase() === "u") void undo();
                }}
                onPointerDown={(e) => {
                  if (!busy) {
                    pointer.current = e.clientX;
                    e.currentTarget.setPointerCapture(e.pointerId);
                  }
                }}
                onPointerMove={(e) => {
                  if (pointer.current !== null)
                    setDrag(e.clientX - pointer.current);
                }}
                onPointerCancel={() => {
                  pointer.current = null;
                  setDrag(0);
                }}
                onPointerUp={() => {
                  pointer.current = null;
                  if (drag > 90) void vote("like");
                  else if (drag < -90) void vote("dislike");
                  else setDrag(0);
                }}
              >
                <OutfitLook outfit={outfit} items={items} />
                <div className="outfit-caption">
                  <h2>{outfit.title}</h2>
                  <p>
                    {outfit.occasion} · {index + 1} of {outfits.length}
                  </p>
                </div>
                {Math.abs(drag) > 40 ? (
                  <span className={`swipe-stamp ${drag > 0 ? "like" : "pass"}`}>
                    {drag > 0 ? "LOVE" : "PASS"}
                  </span>
                ) : null}
              </div>
              <div className="swipe-actions">
                <button
                  className="pass"
                  aria-label="Dislike outfit"
                  disabled={busy}
                  onClick={() => void vote("dislike")}
                >
                  ×
                </button>
                <button
                  className="undo"
                  aria-label="Undo last swipe"
                  disabled={!last || busy}
                  onClick={() => void undo()}
                >
                  ↶
                </button>
                <button
                  className="like"
                  aria-label="Like outfit"
                  disabled={busy}
                  onClick={() => void vote("like")}
                >
                  ♡
                </button>
              </div>
              <details>
                <summary>View outfit details</summary>
                <p>{outfit.explanation}</p>
                <ul>
                  {outfit.item_ids.map((id) => (
                    <li key={id}>
                      {items.find((item) => item.id === id)?.name ||
                        "Removed piece"}
                    </li>
                  ))}
                </ul>
                <p>
                  Suitable days:{" "}
                  {outfit.suitable_days.join(", ") || "An everyday possibility"}
                </p>
              </details>
            </>
          ) : (
            <Empty
              title={
                outfits.length
                  ? "That’s a lovely little edit."
                  : "Your next favorite look awaits."
              }
            >
              {outfits.length
                ? "Review the looks you liked, or generate more possibilities."
                : "Choose an occasion and generate your outfits."}
              {last ? (
                <button onClick={() => void undo()}>Undo last swipe</button>
              ) : null}
            </Empty>
          )}
          {tripId ? (
            <button
              className="ink-button"
              disabled={busy || liked === 0}
              onClick={() => void finish()}
            >
              Done · What to pack →
            </button>
          ) : (
            <Note>
              Likes are saved without a trip. Select a trip under “Packing for”
              before generating looks for its packing list.
            </Note>
          )}
          <p className="annotation swipe-help">
            Swipe or drag · ← pass · → like · U undo
          </p>
          <p className="vote-message" role="status">
            {message}
          </p>
          <p className="annotation">
            Illustrated lookbook compositions, not photorealistic try-on.
          </p>
        </section>
      </div>
    </>
  );
}
export function Packing({ nav, tripId }: { nav: Navigate; tripId: string }) {
  const [book, setBook] = useState<Schema["TripNotebook"]>(),
    [items, setItems] = useState<Schema["WardrobeItem"][]>([]),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [day, setDay] = useState("");
  const [extra, setExtra] = useState("");
  async function addExtra() {
    if (!extra) return;
    try {
      await api(`/consumer/trips/${tripId}/packing/items`, "POST", {
        wardrobe_item_id: extra,
      });
      await refresh();
      setExtra("");
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function refresh() {
    const [b, i] = await Promise.all([
      api<Schema["TripNotebook"]>("/consumer/trips/" + tripId),
      api<Schema["WardrobeItem"][]>("/consumer/wardrobe"),
    ]);
    setBook(b);
    setItems(i);
    setDay(
      (d) => d || b.trip.start_date || new Date().toISOString().slice(0, 10),
    );
  }
  useEffect(() => {
    void refresh().catch((e) => setError(e.message));
  }, [tripId]);
  async function build() {
    setBusy(true);
    try {
      await api("/consumer/trips/" + tripId + "/packing", "POST", {});
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function patch(
    item: Schema["super_travel__consumer__models__PackingItem"],
    payload: Schema["PackingPatch"],
  ) {
    try {
      await api(
        `/consumer/trips/${tripId}/packing/${item.id}`,
        "PATCH",
        payload,
        item.version,
      );
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    }
  }
  if (!book) return <Loading />;
  const packing = book.packing;
  const packed = packing.items.filter((i) => i.packed).length;
  const byDay = packing.liked_outfits.filter((o) =>
    o.suitable_days.includes(day),
  );
  return (
    <>
      <Heading
        eyebrow={`${book.trip.destination} · pack a little lighter`}
        title="Just what you need."
        note={`${packing.liked_outfits.length} liked looks · ${packing.unique_items} unique pieces · ${packed} packed`}
      >
        <button
          className="ink-button"
          disabled={busy}
          onClick={() => void build()}
        >
          {busy ? "Making your list…" : "Build from liked outfits"}
        </button>
      </Heading>
      {error ? <Note kind="error">{error}</Note> : null}
      <div className="trip-tools">
        <button onClick={() => nav("/outfits?trip=" + tripId)}>
          Find more outfits ↗
        </button>
        <button onClick={() => nav("/trip?trip=" + tripId)}>
          Back to trip ↗
        </button>
      </div>
      <Note>
        Shared clothes appear once. A piece can serve several outfits. Packing
        is your checkbox, never inferred from a purchase.
      </Note>
      {packing.needed_items.length ? (
        <Note kind="sample">
          Still needed: {packing.needed_items.join(", ")}.{" "}
          {packing.substitutions.join(" ")}
        </Note>
      ) : null}
      {packing.items.length ? (
        <div className="packing-list">
          {["tops", "bottoms", "shoes", "accessories", "essentials"].map(
            (category) => {
              const entries = packing.items.filter(
                (item) => item.category === category,
              );
              return entries.length ? (
                <section key={category}>
                  <h2>{category}</h2>
                  {entries.map((item) => (
                    <div
                      className={`packing-line ${item.packed ? "done" : ""}`}
                      key={item.id}
                    >
                      <Check
                        checked={item.packed}
                        label={`${item.packed ? "Unpack" : "Pack"} ${item.name}`}
                        onChange={() =>
                          void patch(item, { packed: !item.packed })
                        }
                      />
                      <img src={item.image} alt={item.name} />
                      <span>
                        <strong>{item.name}</strong>
                        <small>
                          {item.outfit_ids.length} outfits ·{" "}
                          {item.relevant_days.map((d) => d.slice(5)).join(", ")}
                        </small>
                      </span>
                      <label className="availability">
                        <span className="sr-only">
                          Wear state for {item.name}
                        </span>
                        <select
                          value={item.availability}
                          onChange={(e) =>
                            void patch(item, {
                              availability: e.target
                                .value as Schema["super_travel__consumer__models__PackingItem"]["availability"],
                            })
                          }
                        >
                          {["ready", "worn", "dirty", "unavailable"].map(
                            (s) => (
                              <option key={s}>{s}</option>
                            ),
                          )}
                        </select>
                      </label>
                    </div>
                  ))}
                </section>
              ) : null;
            },
          )}
        </div>
      ) : (
        <Empty title="A suitcase with room to spare.">
          Like some outfits, then build your packing list.
        </Empty>
      )}
      <details className="extra-packing">
        <summary>Add another piece or essential</summary>
        <p className="annotation">
          Anything else from your wardrobe, with no duplicate entries.
        </p>
        <label>
          Extra piece
          <select value={extra} onChange={(e) => setExtra(e.target.value)}>
            <option value="">Choose a piece</option>
            {items.map((item) => (
              <option value={item.id} key={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </label>
        <div className="actions">
          <button
            className="outline-button"
            disabled={!extra}
            onClick={() => void addExtra()}
          >
            Add to packing
          </button>
          <button onClick={() => nav("/wardrobe?trip=" + tripId)}>
            Add a new essential to wardrobe ↗
          </button>
        </div>
      </details>
      <section className="saved-looks">
        <div className="section-heading">
          <h2>Your outfits, on the road</h2>
          <label>
            Day
            <input
              type="date"
              value={day}
              min={book.trip.start_date || undefined}
              max={book.trip.end_date || undefined}
              onChange={(e) => setDay(e.target.value)}
            />
          </label>
        </div>
        <p className="annotation">
          Keep your saved photos handy. Unpacked, worn, dirty or unavailable
          pieces carry a warning.
        </p>
        <div className="saved-look-grid">
          {byDay.map((outfit) => {
            const problems = outfit.item_ids
              .map((id) =>
                packing.items.find((item) => item.wardrobe_item_id === id),
              )
              .filter(
                (item) =>
                  !item || !item.packed || item.availability !== "ready",
              );
            return (
              <article key={outfit.id}>
                <OutfitLook outfit={outfit} items={items} small />
                <h3>{outfit.title}</h3>
                <p>
                  {outfit.occasion} · assigned to {outfit.suitable_days.length}{" "}
                  days
                </p>
                {problems.length ? (
                  <Note kind="sample">
                    {problems.length} pieces need packing or a ready-to-wear
                    substitute.
                  </Note>
                ) : (
                  <p className="annotation">✓ Packed and ready for this day</p>
                )}
              </article>
            );
          })}
        </div>
        <button
          onClick={() => {
            const d = new Date(day + "T12:00:00Z");
            d.setUTCDate(d.getUTCDate() + 1);
            setDay(d.toISOString().slice(0, 10));
          }}
        >
          Tomorrow’s options →
        </button>
      </section>
    </>
  );
}
export function Briefing({ nav, tripId }: { nav: Navigate; tripId: string }) {
  const [brief, setBrief] = useState<Schema["Briefing"]>(),
    [events, setEvents] = useState<Schema["CalendarEvent"][]>([]),
    [connection, setConnection] = useState<Schema["CalendarConnection"]>(),
    [items, setItems] = useState<Schema["WardrobeItem"][]>([]),
    [error, setError] = useState(""),
    [selected, setSelected] = useState<string[]>(["museum", "dinner"]);
  async function refresh() {
    const [b, e, c, i] = await Promise.all([
      api<Schema["Briefing"]>("/consumer/trips/" + tripId + "/briefing"),
      api<Schema["CalendarEvent"][]>("/consumer/trips/" + tripId + "/calendar"),
      api<Schema["CalendarConnection"][]>("/consumer/calendar"),
      api<Schema["WardrobeItem"][]>("/consumer/wardrobe"),
    ]);
    setBrief(b);
    setEvents(e);
    setConnection(c[0]);
    setItems(i);
    if (c[0]) setSelected(c[0].selected_event_ids || []);
  }
  useEffect(() => {
    void refresh().catch((e) => setError(e.message));
  }, [tripId]);
  async function connect(enabled: boolean) {
    try {
      await api(
        "/consumer/calendar",
        "PUT",
        { enabled, selected_event_ids: selected },
        connection?.version,
      );
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    }
  }
  return (
    <>
      <Heading
        eyebrow="a morning note, just for you"
        title="Good morning, wanderer."
        note="A calm glance at the day ahead."
      />
      {error ? <Note kind="error">{error}</Note> : null}
      {!brief ? (
        <Loading />
      ) : (
        <>
          <section className="briefing-note">
            <p className="eyebrow">{brief.day} · your trip’s local day</p>
            <p className="hand morning-note">{brief.note}</p>
            <p>{brief.weather}</p>
            <div className="briefing-schedule">
              {brief.schedule.map((event) => (
                <p key={event.id}>
                  <strong>{event.local_time}</strong>
                  {event.title}
                  <span className="annotation">
                    {event.data_mode === "fixture" ? "sample calendar" : ""}
                  </span>
                </p>
              ))}
            </div>
            {brief.outfit ? (
              <OutfitLook outfit={brief.outfit} items={items} small />
            ) : null}
            <h3>A few little reminders</h3>
            {brief.reminders.map((title, i) => (
              <p key={i}>↳ {title}</p>
            ))}
            <p className="annotation">
              In-app viewing only. No automated delivery or native widget is
              running.
            </p>
            <button onClick={() => nav("/magic?trip=" + tripId)}>
              A little space for Magic ↗
            </button>
          </section>
          <details className="calendar-settings" open={!connection?.enabled}>
            <summary>Choose what your calendar shares</summary>
            <Note kind="sample">
              Google Calendar demo · synthetic events, no OAuth or live access.
              Personal appointments are included only if you explicitly select
              them.
            </Note>
            {events.map((event) => (
              <label className="checkbox-label" key={event.id}>
                <input
                  type="checkbox"
                  checked={selected.includes(event.id)}
                  onChange={(e) =>
                    setSelected((values) =>
                      e.target.checked
                        ? [...values, event.id]
                        : values.filter((v) => v !== event.id),
                    )
                  }
                />
                {event.title} · {event.local_time}
              </label>
            ))}
            <div className="actions">
              <button
                className="outline-button"
                onClick={() => void connect(true)}
              >
                {connection?.enabled
                  ? "Save calendar selection"
                  : "Use sample calendar"}
              </button>
              {connection?.enabled ? (
                <button onClick={() => void connect(false)}>
                  Disconnect calendar
                </button>
              ) : null}
            </div>
          </details>
        </>
      )}
    </>
  );
}
export function Preferences({
  profile,
  refresh,
  nav,
}: {
  profile: Schema["Profile"];
  refresh: () => Promise<void>;
  nav: Navigate;
}) {
  const [dietary, setDietary] = useState(profile.dietary),
    [accessibility, setAccessibility] = useState(profile.accessibility),
    [notification, setNotification] = useState(profile.notification_preference),
    [message, setMessage] = useState("");
  async function save(e: FormEvent) {
    e.preventDefault();
    try {
      await api(
        "/consumer/preferences",
        "PUT",
        {
          dietary,
          accessibility,
          travel_style: profile.travel_style,
          interests: profile.interests,
          notification_preference: notification,
          fashion: profile.fashion,
        },
        profile.version,
      );
      await refresh();
      setMessage("Saved. New trips can reuse these notes.");
    } catch (e) {
      setMessage((e as Error).message);
    }
  }
  return (
    <>
      <Heading
        eyebrow="your notebook, your way"
        title="The little details."
        note="Global preferences stay separate from each trip’s notes."
      />
      <button className="outline-button" onClick={() => nav("/outfits")}>
        Fashion settings & outfits →
      </button>
      <form className="notebook-form" onSubmit={save}>
        <label>
          Dietary preferences
          <input value={dietary} onChange={(e) => setDietary(e.target.value)} />
        </label>
        <label>
          Accessibility preferences
          <textarea
            value={accessibility}
            onChange={(e) => setAccessibility(e.target.value)}
          />
        </label>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={notification}
            onChange={(e) => setNotification(e.target.checked)}
          />
          I’d like morning reminders when delivery becomes available.
        </label>
        <Note>
          Preference only. Scheduling and notification delivery are not enabled.
        </Note>
        <button className="ink-button">Save preferences</button>
        <p role="status">{message}</p>
      </form>
    </>
  );
}
