"use client";

import { useRef, useState } from "react";

/* ──────────────────────────────────────────────────────────────────────────
   FILON assistant — a decision surface, not a chat.
   The analysis is consumed as a stream of events (mockAnalyze below). A real
   backend only has to yield the same events over SSE for this UI to light up
   identically — nothing else changes.
   ────────────────────────────────────────────────────────────────────────── */

const euro = (n: number) => `${n.toLocaleString("fr-FR")} €`;
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));
const hash = (s: string) => {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  return h;
};

const STEPS = [
  "Compréhension du besoin",
  "Analyse des marchands",
  "Analyse des prix",
  "Analyse de l'historique",
  "Analyse du cashback",
  "Analyse des avis",
  "Recherche d'alternatives",
  "Calcul du Score FILON",
];

type Hist = "baisse" | "hausse" | "stable";
type Card = {
  rank: string; medal: string; name: string; emoji: string;
  price: number; merchant: string; delivery: string; warranty: string;
  cashback: number; coupon: string | null; hist: Hist; histNote: string;
  score: number; why: string; alt: string | null; buy: boolean;
};
type Result = { usage: string; offers: number; cards: Card[] };

const CATALOGS: Record<string, { usage: string; emoji: string; cards: Card[] }> = {
  laptop: {
    usage: "ordinateur portable", emoji: "💻",
    cards: [
      { rank: "Meilleur rapport qualité/prix", medal: "🥇", name: "Lenovo IdeaPad Slim 5", emoji: "💻", price: 749, merchant: "Fnac", delivery: "48 h", warranty: "24 mois", cashback: 5, coupon: "−30 €", hist: "baisse", histNote: "au plus bas sur 90 j", score: 94, why: "Le meilleur équilibre performances, autonomie et prix.", alt: "Acer Aspire 15", buy: true },
      { rank: "Meilleur budget", medal: "🥈", name: "HP Pavilion 14", emoji: "💻", price: 499, merchant: "Cdiscount", delivery: "3-4 j", warranty: "24 mois", cashback: 3, coupon: null, hist: "stable", histNote: "proche de la moyenne", score: 87, why: "L'essentiel pour étudier, au prix le plus bas.", alt: "Asus Vivobook 15", buy: true },
      { rank: "Meilleure autonomie", medal: "🥉", name: "MacBook Air (puce M)", emoji: "💻", price: 1049, merchant: "Amazon", delivery: "24 h", warranty: "24 mois", cashback: 4, coupon: null, hist: "baisse", histNote: "−80 € vs moyenne", score: 90, why: "Jusqu'à 18 h d'autonomie, silencieux et léger.", alt: null, buy: true },
      { rank: "Meilleure performance", medal: "⭐", name: "Asus TUF Gaming A15", emoji: "💻", price: 1099, merchant: "Amazon", delivery: "24 h", warranty: "24 mois", cashback: 3, coupon: null, hist: "stable", histNote: "prix habituel", score: 86, why: "GPU RTX pour le jeu et la création exigeante.", alt: "MSI Katana", buy: false },
      { rank: "Meilleur reconditionné", medal: "♻️", name: "Lenovo Legion · reconditionné A+", emoji: "💻", price: 899, merchant: "vendeur certifié", delivery: "3 j", warranty: "24 mois", cashback: 3, coupon: null, hist: "baisse", histNote: "−32 % vs neuf", score: 89, why: "Une machine puissante, garantie, bien moins chère.", alt: "Dell G15 recond.", buy: true },
    ],
  },
  phone: {
    usage: "smartphone", emoji: "📱",
    cards: [
      { rank: "Meilleur rapport qualité/prix", medal: "🥇", name: "Google Pixel (série a)", emoji: "📱", price: 459, merchant: "Amazon", delivery: "24 h", warranty: "24 mois", cashback: 4, coupon: "−20 €", hist: "baisse", histNote: "au plus bas sur 90 j", score: 93, why: "La meilleure photo à ce prix, 7 ans de mises à jour.", alt: "Samsung A55", buy: true },
      { rank: "Meilleur budget", medal: "🥈", name: "Samsung Galaxy A (5G)", emoji: "📱", price: 299, merchant: "Boulanger", delivery: "48 h", warranty: "24 mois", cashback: 3, coupon: null, hist: "stable", histNote: "proche de la moyenne", score: 85, why: "Grand écran, grosse batterie, très polyvalent.", alt: null, buy: true },
      { rank: "Meilleure autonomie", medal: "🥉", name: "Motorola Edge", emoji: "📱", price: 379, merchant: "Fnac", delivery: "48 h", warranty: "24 mois", cashback: 4, coupon: null, hist: "baisse", histNote: "−30 € vs moyenne", score: 88, why: "Deux jours d'autonomie sans forcer.", alt: null, buy: true },
      { rank: "Meilleure performance", medal: "⭐", name: "iPhone (modèle récent)", emoji: "📱", price: 869, merchant: "Amazon", delivery: "24 h", warranty: "24 mois", cashback: 2, coupon: null, hist: "hausse", histNote: "mieux vaut attendre", score: 84, why: "La puissance et l'écosystème iOS, si le budget suit.", alt: "iPhone recond.", buy: false },
      { rank: "Meilleur reconditionné", medal: "♻️", name: "iPhone · reconditionné A+", emoji: "📱", price: 449, merchant: "vendeur certifié", delivery: "3 j", warranty: "24 mois", cashback: 3, coupon: null, hist: "baisse", histNote: "−30 % vs neuf", score: 89, why: "Un iPhone récent garanti, à prix Android.", alt: null, buy: true },
    ],
  },
  audio: {
    usage: "casque / écouteurs", emoji: "🎧",
    cards: [
      { rank: "Meilleur rapport qualité/prix", medal: "🥇", name: "Sony WH (réduction de bruit)", emoji: "🎧", price: 279, merchant: "Fnac", delivery: "48 h", warranty: "24 mois", cashback: 5, coupon: "−15 €", hist: "baisse", histNote: "au plus bas sur 90 j", score: 92, why: "La référence anti-bruit, 30 h d'autonomie.", alt: "Bose QC", buy: true },
      { rank: "Meilleur budget", medal: "🥈", name: "Écouteurs sans fil", emoji: "🎧", price: 79, merchant: "Amazon", delivery: "24 h", warranty: "24 mois", cashback: 3, coupon: null, hist: "stable", histNote: "prix habituel", score: 84, why: "Un très bon son sans se ruiner.", alt: null, buy: true },
      { rank: "Meilleure autonomie", medal: "🥉", name: "Casque longue autonomie", emoji: "🎧", price: 189, merchant: "Boulanger", delivery: "48 h", warranty: "24 mois", cashback: 4, coupon: null, hist: "baisse", histNote: "−20 € vs moyenne", score: 87, why: "Jusqu'à 60 h d'écoute par charge.", alt: null, buy: true },
      { rank: "Meilleure performance", medal: "⭐", name: "Casque audiophile", emoji: "🎧", price: 349, merchant: "Fnac", delivery: "3 j", warranty: "24 mois", cashback: 3, coupon: null, hist: "stable", histNote: "prix habituel", score: 85, why: "Le son le plus détaillé de la sélection.", alt: null, buy: false },
      { rank: "Meilleur reconditionné", medal: "♻️", name: "Sony WH · reconditionné A+", emoji: "🎧", price: 189, merchant: "vendeur certifié", delivery: "3 j", warranty: "24 mois", cashback: 3, coupon: null, hist: "baisse", histNote: "−35 % vs neuf", score: 88, why: "Le même casque premium, garanti, moins cher.", alt: null, buy: true },
    ],
  },
};

function synthCards(q: string, budget: number | null): Card[] {
  const seed = hash(q);
  const base = budget || 200 + (seed % 700);
  const M = ["Amazon", "Fnac", "Cdiscount", "Boulanger", "Darty"];
  const defs: Array<[string, string, number, number, boolean, string, string | null, Hist, string]> = [
    ["Meilleur rapport qualité/prix", "🥇", 0.98, 93, true, "Le meilleur équilibre global pour votre besoin.", "−20 €", "baisse", "sous la moyenne"],
    ["Meilleur budget", "🥈", 0.8, 86, true, "Presque aussi bon, sensiblement moins cher.", null, "stable", "prix habituel"],
    ["Meilleure autonomie", "🥉", 1.05, 88, false, "L'endurance en plus, si c'est votre priorité.", null, "stable", "proche moyenne"],
    ["Meilleure performance", "⭐", 1.18, 85, false, "Le plus puissant de la sélection.", null, "hausse", "mieux vaut attendre"],
    ["Meilleur reconditionné", "♻️", 0.72, 87, true, "L'équivalent reconditionné, garanti, au meilleur prix.", null, "baisse", "−28 % vs neuf"],
  ];
  const del = ["24 h", "48 h", "2-3 j", "3-4 j"];
  return defs.map(([rank, medal, mult, score, buy, why, coupon, hist, histNote], i) => ({
    rank, medal, name: `Option ${i + 1}`, emoji: "🛍️",
    price: Math.round(base * mult), merchant: rank.includes("recond") ? "vendeur certifié" : M[(seed >> i) % 5],
    delivery: del[i % 4], warranty: "24 mois", cashback: 3 + ((seed >> i) % 5), coupon, hist, histNote,
    score, why, alt: null, buy,
  }));
}

function recommend(q: string, budget: number | null): Result {
  const s = q.toLowerCase();
  let key: string | null = null;
  if (/portable|laptop|ordinateur|\bpc\b|macbook/.test(s)) key = "laptop";
  else if (/t[ée]l[ée]phone|smartphone|iphone|pixel|galaxy|\btel\b/.test(s)) key = "phone";
  else if (/casque|[ée]couteur|audio|\bson\b|airpods/.test(s)) key = "audio";
  const cat = key ? CATALOGS[key] : null;
  return {
    usage: cat ? cat.usage : q.trim().toLowerCase() || "votre besoin",
    offers: 26 + (hash(q) % 26),
    cards: cat ? cat.cards : synthCards(q, budget),
  };
}

function detectBudget(q: string): number | null {
  const m = q.replace(/\s/g, "").match(/(\d{2,5})(?:€|eur)/i) || q.match(/(?:moins de|budget|à|max|environ|autour)\D{0,6}(\d{2,5})/i);
  return m ? parseInt(m[1], 10) : null;
}

type Ev =
  | { type: "step"; i: number }
  | { type: "step-done"; i: number }
  | { type: "results"; data: Result };

/* Local mock — used until the real backend is configured, and as a fallback. */
async function* mockAnalyze(q: string, reduce: boolean): AsyncGenerator<Ev> {
  const budget = detectBudget(q);
  for (let i = 0; i < STEPS.length; i++) {
    yield { type: "step", i };
    await sleep(reduce ? 0 : 240 + Math.random() * 200);
    yield { type: "step-done", i };
  }
  yield { type: "results", data: recommend(q, budget) };
}

/* Real backend: reads the same events over SSE from FILON's /advise/stream.
   Enabled by setting NEXT_PUBLIC_FILON_API (the backend base URL) at build time.
   The UI is identical — only the source of the events changes. */
const API = (process.env.NEXT_PUBLIC_FILON_API || "").replace(/\/$/, "");

async function* streamAnalyze(q: string): AsyncGenerator<Ev> {
  const budget = detectBudget(q);
  const url = `${API}/api/advise/stream?q=${encodeURIComponent(q)}${budget ? `&budget=${budget}` : ""}`;
  const res = await fetch(url, { headers: { Accept: "text/event-stream" } });
  if (!res.ok || !res.body) throw new Error(`stream ${res.status}`);
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const chunks = buf.split("\n\n");
    buf = chunks.pop() ?? "";
    for (const chunk of chunks) {
      const line = chunk.split("\n").find((l) => l.startsWith("data:"));
      if (!line) continue;
      yield JSON.parse(line.slice(5).trim()) as Ev;
    }
  }
}

const CHIPS = ["Un PC portable pour étudiant, 800€", "Un bon smartphone à 500€", "Un casque à réduction de bruit", "Une machine pour le montage vidéo"];

const HIST_LABEL: Record<Hist, string> = { baisse: "En baisse", hausse: "En hausse", stable: "Stable" };

function ScoreRing({ score }: { score: number }) {
  return (
    <div className="fa-score" style={{ ["--v" as string]: score }}>
      <div className="ring"><span>{score}</span></div>
      <span className="lab">Score FILON</span>
    </div>
  );
}

function RecCard({ c, i }: { c: Card; i: number }) {
  return (
    <article className={`fa-card${i === 0 ? " win" : ""}`} style={{ ["--d" as string]: `${i * 90}ms` }}>
      <div className="fa-rank"><span className="medal">{c.medal}</span> {c.rank}</div>
      <div className="fa-body">
        <div className="fa-thumb" aria-hidden="true">{c.emoji}</div>
        <div className="fa-main">
          <h3>{c.name}</h3>
          <div className="fa-price"><b>{euro(c.price)}</b><span className="mc">chez {c.merchant}</span></div>
          <div className="fa-specs">
            <span>🚚 {c.delivery}</span>
            <span>🛡️ {c.warranty}</span>
            <span className="g">💸 cashback {c.cashback} %</span>
            {c.coupon && <span className="g">🎟️ coupon {c.coupon}</span>}
            <span className={`hist ${c.hist}`}>📈 {HIST_LABEL[c.hist]} · {c.histNote}</span>
          </div>
          <p className="fa-why"><b>Pourquoi&nbsp;:</b> {c.why}</p>
          {c.alt && <p className="fa-alt">Alternative&nbsp;: {c.alt}</p>}
        </div>
        <div className="fa-aside">
          <ScoreRing score={c.score} />
          <span className={`fa-verdict ${c.buy ? "buy" : "wait"}`}>{c.buy ? "✓ Bon moment" : "◷ Attendre"}</span>
          <a className="ed-btn wave" href="/#installer">Voir l&apos;offre</a>
        </div>
      </div>
    </article>
  );
}

export function SearchAssistant() {
  const [query, setQuery] = useState("");
  const [phase, setPhase] = useState<"idle" | "thinking" | "results">("idle");
  const [active, setActive] = useState(-1);
  const [done, setDone] = useState<number[]>([]);
  const [result, setResult] = useState<Result | null>(null);
  const runId = useRef(0);

  const ask = async (raw: string) => {
    const q = raw.trim();
    if (!q) return;
    const id = ++runId.current;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    setPhase("thinking");
    setResult(null);
    setDone([]);
    setActive(0);

    const apply = (ev: Ev): boolean => {
      if (runId.current !== id) return false; // superseded by a newer query
      if (ev.type === "step") setActive(ev.i);
      else if (ev.type === "step-done") setDone((d) => [...d, ev.i]);
      else if (ev.type === "results") {
        setActive(-1);
        setResult(ev.data);
        setPhase("results");
      }
      return true;
    };

    // Prefer the real backend when configured; fall back to the local mock on
    // any error so the assistant always answers.
    if (API) {
      try {
        for await (const ev of streamAnalyze(q)) if (!apply(ev)) return;
        return;
      } catch {
        if (runId.current !== id) return;
        setDone([]);
        setActive(0);
      }
    }
    for await (const ev of mockAnalyze(q, reduce)) if (!apply(ev)) return;
  };

  return (
    <section className={`sa ${phase !== "idle" ? "searched" : ""}`}>
      <div className="ed-wrap">
        {phase === "idle" && <span className="eyebrow">Assistant d&apos;achat · IA</span>}
        <h1>{phase === "idle" ? "Que voulez-vous acheter, ou décider ?" : "Un autre achat à décider ?"}</h1>

        <form className="sa-search" onSubmit={(e) => { e.preventDefault(); ask(query || CHIPS[0]); }}>
          <div className="sa-box">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <circle cx="11" cy="11" r="7" />
              <path d="m21 21-4.2-4.2" strokeLinecap="round" />
            </svg>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Décrivez un besoin, ou un produit…"
              aria-label="Décrivez un besoin ou un produit"
              autoComplete="off"
            />
            <button type="submit" className="ed-btn wave">Demander</button>
          </div>
          <div className="sa-chips">
            {CHIPS.map((c) => (
              <button key={c} type="button" className="sa-chip" onClick={() => { setQuery(c); ask(c); }}>{c}</button>
            ))}
          </div>
        </form>

        {phase !== "idle" && (
          <div className="fa-out" aria-live="polite">
            {/* streamed reasoning */}
            <div className={`fa-steps ${phase === "results" ? "collapsed" : ""}`}>
              {STEPS.map((s, i) => {
                const st = done.includes(i) ? "done" : i === active ? "active" : "pending";
                return (
                  <div className={`fa-step ${st}`} key={s}>
                    <span className="tk">{st === "done" ? "✓" : ""}</span>
                    {s}
                  </div>
                );
              })}
            </div>

            {phase === "results" && result && (
              <div className="fa-results">
                <p className="fa-summary">
                  <b>{result.offers} offres analysées</b> pour {result.usage}. Voici mes 5 recommandations, classées.
                  <span className="fa-est"> Prix estimés, à titre indicatif.</span>
                </p>
                <div className="fa-cards">
                  {result.cards.map((c, i) => <RecCard key={c.rank} c={c} i={i} />)}
                </div>
                <p className="sa-disc">FILON est gratuit. Vous ne payez jamais, et vos données ne sont pas revendues.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
