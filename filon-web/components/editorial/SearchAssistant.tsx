"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useLocale } from "@/lib/i18n";

const SL = {
  fr: {
    steps: ["Compréhension du besoin", "Analyse des marchands", "Analyse des prix", "Analyse de l'historique", "Analyse du cashback", "Analyse des avis", "Recherche d'alternatives", "Calcul du Score FILON"],
    eyebrow: "Assistant d'achat",
    h1Idle: "Que voulez-vous acheter, ou décider ?", h1Again: "Un autre achat à décider ?",
    placeholder: "Décrivez un besoin, ou un produit…", ask: "Demander",
    priceFor: "Prix pour",
    chips: ["Un PC portable pour étudiant, 800€", "Un bon smartphone à 500€", "Un casque à réduction de bruit", "Une machine pour le montage vidéo"],
    why: "Pourquoi", alt: "Alternative", see: "Voir l'offre", good: "Bon moment", wait: "Attendre",
    real: "Prix réels · Google Shopping", est: "Prix estimés, à titre indicatif",
    analysed: "offres analysées", forNeed: "pour", recos: "Voici mes", recoTail: "recommandation", classed: "classée", nounPl: "s", adjPl: "s",
    disc: "FILON est gratuit. Vous ne payez jamais, et vos données ne sont pas revendues.",
    at: "chez", cashback: "cashback", coupon: "coupon",
    hist: { baisse: "En baisse", hausse: "En hausse", stable: "Stable" } as Record<Hist, string>,
  },
  nl: {
    steps: ["Begrip van de behoefte", "Analyse van de winkels", "Prijsanalyse", "Analyse van de geschiedenis", "Analyse van de cashback", "Analyse van de reviews", "Alternatieven zoeken", "Berekening van de FILON-Score"],
    eyebrow: "Koopassistent",
    h1Idle: "Wat wil je kopen, of beslissen ?", h1Again: "Nog een aankoop om te beslissen ?",
    placeholder: "Beschrijf een behoefte, of een product…", ask: "Vragen",
    priceFor: "Prijs voor",
    chips: ["Een studentenlaptop, 800€", "Een goede smartphone voor 500€", "Een koptelefoon met ruisonderdrukking", "Een machine voor videomontage"],
    why: "Waarom", alt: "Alternatief", see: "Bekijk de aanbieding", good: "Goed moment", wait: "Wachten",
    real: "Echte prijzen · Google Shopping", est: "Geschatte prijzen, ter indicatie",
    analysed: "aanbiedingen geanalyseerd", forNeed: "voor", recos: "Dit zijn mijn", recoTail: "aanbeveling", classed: "gerangschikt", nounPl: "en", adjPl: "",
    disc: "FILON is gratis. Je betaalt nooit, en je gegevens worden niet doorverkocht.",
    at: "bij", cashback: "cashback", coupon: "code",
    hist: { baisse: "Dalend", hausse: "Stijgend", stable: "Stabiel" } as Record<Hist, string>,
  },
  en: {
    steps: ["Understanding the need", "Analysing merchants", "Analysing prices", "Analysing price history", "Analysing cashback", "Analysing reviews", "Searching for alternatives", "Computing the FILON Score"],
    eyebrow: "Shopping assistant",
    h1Idle: "What do you want to buy, or decide ?", h1Again: "Another purchase to decide ?",
    placeholder: "Describe a need, or a product…", ask: "Ask",
    priceFor: "Price for",
    chips: ["A student laptop, €800", "A good smartphone at €500", "Noise-cancelling headphones", "A machine for video editing"],
    why: "Why", alt: "Alternative", see: "See the offer", good: "Good time", wait: "Wait",
    real: "Real prices · Google Shopping", est: "Estimated prices, for guidance",
    analysed: "offers analysed", forNeed: "for", recos: "Here are my", recoTail: "recommendation", classed: "ranked", nounPl: "s", adjPl: "",
    disc: "FILON is free. You never pay, and your data is not resold.",
    at: "at", cashback: "cashback", coupon: "coupon",
    hist: { baisse: "Falling", hausse: "Rising", stable: "Stable" } as Record<Hist, string>,
  },
};

/* ──────────────────────────────────────────────────────────────────────────
   FILON assistant — a decision surface, not a chat.
   The analysis is consumed as a stream of events (mockAnalyze below). A real
   backend only has to yield the same events over SSE for this UI to light up
   identically — nothing else changes.
   ────────────────────────────────────────────────────────────────────────── */

const euro = (n: number) => `${n.toLocaleString("fr-FR")} €`;
const money = (n: number, cur = "€") => `${n.toLocaleString("fr-FR")} ${cur}`;

/** Pays supportés pour les prix (SerpApi côté backend). */
const COUNTRIES: Array<{ code: string; label: string }> = [
  { code: "be", label: "Belgique (FR)" },
  { code: "be-nl", label: "België (NL)" },
  { code: "fr", label: "France" },
  { code: "ch", label: "Suisse" },
  { code: "lu", label: "Luxembourg" },
  { code: "nl", label: "Pays-Bas" },
];
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

/* Icônes ligne, nettes et sobres (currentColor) — remplacent les émojis. */
const IconBase = ({ children }: { children: React.ReactNode }) => (
  <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{children}</svg>
);
const IcTruck = () => <IconBase><path d="M3 6h11v9H3zM14 9h4l3 3v3h-7" /><circle cx="7" cy="18" r="1.6" /><circle cx="17.5" cy="18" r="1.6" /></IconBase>;
const IcShield = () => <IconBase><path d="M12 3l7 3v5c0 4.2-2.9 7.6-7 9-4.1-1.4-7-4.8-7-9V6z" /><path d="M9.2 12l2 2 3.6-4" /></IconBase>;
const IcCashback = () => <IconBase><path d="M15.5 8.5a4 4 0 100 7" /><circle cx="10" cy="12" r="6" /><path d="M18 6l3-3M21 3h-2.5M21 3v2.5" /></IconBase>;
const IcCoupon = () => <IconBase><path d="M3 8a2 2 0 012-2h14a2 2 0 012 2v2a2 2 0 000 4v2a2 2 0 01-2 2H5a2 2 0 01-2-2v-2a2 2 0 000-4z" /><path d="M13 7v10" strokeDasharray="2 2" /></IconBase>;
const IcTrendDown = () => <IconBase><path d="M4 7l7 7 3-3 6 6" /><path d="M20 17v-4h-4" /></IconBase>;
const IcTrendUp = () => <IconBase><path d="M4 17l7-7 3 3 6-6" /><path d="M20 7v4h-4" /></IconBase>;
const IcTrendFlat = () => <IconBase><path d="M4 12h16" /><path d="M17 9l3 3-3 3" /></IconBase>;
const IcCheck = () => <IconBase><path d="M5 12.5l4.2 4.2L19 7" /></IconBase>;
const IcClock = () => <IconBase><circle cx="12" cy="12" r="8.5" /><path d="M12 7.5V12l3 2" /></IconBase>;
const IcBox = () => (
  <svg viewBox="0 0 24 24" width="46" height="46" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z" /><path d="M4 7.5l8 4.5 8-4.5M12 12v9" opacity="0.6" />
  </svg>
);
const HIST_ICON = { baisse: IcTrendDown, hausse: IcTrendUp, stable: IcTrendFlat } as const;

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
  image?: string | null; link?: string | null;
  price: number; merchant: string; delivery: string; warranty: string;
  cashback: number; coupon: string | null; hist: Hist | null; histNote: string;
  score: number; why: string; alt: string | null; buy: boolean;
};
type Result = { usage: string; offers: number; cards: Card[]; real?: boolean; currency?: string; country?: string };

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
const API = (process.env.NEXT_PUBLIC_FILON_API || "https://web-production-c6842.up.railway.app").replace(/\/$/, "");

async function* streamAnalyze(q: string, country: string): AsyncGenerator<Ev> {
  const budget = detectBudget(q);
  const url = `${API}/api/advise/stream?q=${encodeURIComponent(q)}${budget ? `&budget=${budget}` : ""}${country ? `&country=${encodeURIComponent(country)}` : ""}`;
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

function ScoreRing({ score }: { score: number }) {
  return (
    <div className="fa-score" style={{ ["--v" as string]: score }}>
      <div className="ring"><span>{score}</span></div>
      <span className="lab">Score FILON</span>
    </div>
  );
}

function RecCard({ c, i, q, cur }: { c: Card; i: number; q: string; cur: string }) {
  const [imgOk, setImgOk] = useState(true);
  const S = SL[useLocale().locale];
  const offerUrl = c.link || `https://www.google.com/search?tbm=shop&q=${encodeURIComponent(q || c.name)}`;
  const showImg = c.image && imgOk;
  return (
    <motion.article 
      className={`fa-card${i === 0 ? " win" : ""}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: i * 0.1, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      whileHover={{ y: -4, boxShadow: "var(--fx-elevation-3)" }}
    >
      {i === 0
        ? <div className="fa-flag"><IcCheck /> {c.rank}</div>
        : <div className="fa-rank"><span className="num">{i + 1}</span> {c.rank}</div>}
      <div className="fa-body">
        <div className={`fa-thumb${showImg ? " has-img" : ""}`} aria-hidden="true">
          {showImg
            ? <img src={c.image as string} alt="" loading="lazy" onError={() => setImgOk(false)} />
            : <IcBox />}
        </div>
        <div className="fa-main">
          <h3>{c.name}</h3>
          <div className="fa-price"><b>{money(c.price, cur)}</b><span className="mc">{S.at} {c.merchant}</span></div>
          <div className="fa-specs">
            <span><IcTruck /> {c.delivery}</span>
            <span><IcShield /> {c.warranty}</span>
            {c.cashback ? <span className="g"><IcCashback /> {S.cashback} {c.cashback} %</span> : null}
            {c.coupon && <span className="g"><IcCoupon /> {S.coupon} {c.coupon}</span>}
            {c.hist && c.histNote ? (() => { const Ic = HIST_ICON[c.hist as Hist]; return <span className={`hist ${c.hist}`}><Ic /> {S.hist[c.hist]} · {c.histNote}</span>; })() : null}
          </div>
          <p className="fa-why"><b>{S.why}&nbsp;:</b> {c.why}</p>
          {c.alt && <p className="fa-alt">{S.alt}&nbsp;: {c.alt}</p>}
        </div>
        <div className="fa-aside">
          <ScoreRing score={c.score} />
          <span className={`fa-verdict ${c.buy ? "buy" : "wait"}`}>{c.buy ? <><IcCheck /> {S.good}</> : <><IcClock /> {S.wait}</>}</span>
          <a className="ed-btn wave" href={offerUrl} target="_blank" rel="noopener noreferrer">{S.see}</a>
        </div>
      </div>
    </motion.article>
  );
}

export function SearchAssistant() {
  const [query, setQuery] = useState("");
  const [phase, setPhase] = useState<"idle" | "thinking" | "results">("idle");
  const [active, setActive] = useState(-1);
  const [done, setDone] = useState<number[]>([]);
  const [result, setResult] = useState<Result | null>(null);
  const [asked, setAsked] = useState("");
  // Pays proposé par géolocalisation plutôt que « be » en dur : le prix, la
  // devise et les marchands disponibles en dépendent, et un visiteur français
  // n'a aucune raison de partir sur la Belgique. Le sélecteur reste maître —
  // la détection ne fait que choisir la valeur de départ.
  const [country, setCountry] = useState("be");
  const { locale, country: geoCountry } = useLocale();
  const geoApplied = useRef(false);
  useEffect(() => {
    if (geoApplied.current) return;
    const detected = (geoCountry || "").toLowerCase();
    if (!detected) return;
    // La Belgique est bilingue : le néerlandophone part sur « be-nl ».
    const code = detected === "be" && locale === "nl" ? "be-nl" : detected;
    if (COUNTRIES.some((c) => c.code === code)) {
      setCountry(code);
      geoApplied.current = true;
    }
  }, [geoCountry, locale]);
  const S = SL[locale];
  const runId = useRef(0);

  const ask = async (raw: string) => {
    const q = raw.trim();
    if (!q) return;
    setAsked(q);
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
        for await (const ev of streamAnalyze(q, country)) if (!apply(ev)) return;
        return;
      } catch {
        if (runId.current !== id) return;
        setDone([]);
        setActive(0);
      }
    }
    for await (const ev of mockAnalyze(q, reduce)) if (!apply(ev)) return;
  };

  // Question passée dans l'URL (?q=…) — le hero et les suggestions y envoient.
  // Lue depuis window plutôt qu'avec useSearchParams : ce dernier force le
  // rendu dynamique de la page, qui est statique et doit le rester.
  useEffect(() => {
    const q = new URLSearchParams(window.location.search).get("q");
    if (!q) return;
    setQuery(q);
    ask(q);
    // Au montage uniquement : relancer à chaque rendu boucherait l'analyse.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <section className={`sa ${phase !== "idle" ? "searched" : ""}`}>
      <div className="ed-wrap">
        {phase === "idle" && <span className="eyebrow">{S.eyebrow}</span>}
        <h1>{phase === "idle" ? S.h1Idle : S.h1Again}</h1>

        <form className="sa-search" onSubmit={(e) => { e.preventDefault(); ask(query || S.chips[0]); }}>
          <div className="sa-box">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <circle cx="11" cy="11" r="7" />
              <path d="m21 21-4.2-4.2" strokeLinecap="round" />
            </svg>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={S.placeholder}
              aria-label={S.placeholder}
              autoComplete="off"
            />
            <button type="submit" className="ed-btn wave">{S.ask}</button>
          </div>
          <div className="sa-country">
            <label htmlFor="sa-cc">{S.priceFor}</label>
            <select id="sa-cc" value={country} onChange={(e) => setCountry(e.target.value)}>
              {COUNTRIES.map((c) => (
                <option key={c.code} value={c.code}>{c.label}</option>
              ))}
            </select>
          </div>
          <div className="sa-chips">
            {S.chips.map((c) => (
              <button key={c} type="button" className="sa-chip" onClick={() => { setQuery(c); ask(c); }}>{c}</button>
            ))}
          </div>
        </form>

        <AnimatePresence mode="wait">
          {phase !== "idle" && (
            <motion.div 
              key="assistant-output"
              className="fa-out" 
              aria-live="polite"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              {/* streamed reasoning */}
              <motion.div 
                className={`fa-steps ${phase === "results" ? "collapsed" : ""}`}
                layout
              >
                {S.steps.map((s, i) => {
                  const st = done.includes(i) ? "done" : i === active ? "active" : "pending";
                  return (
                    <motion.div 
                      layout
                      className={`fa-step ${st}`} 
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                    >
                      <span className="tk">{st === "done" ? "✓" : ""}</span>
                      {s}
                    </motion.div>
                  );
                })}
              </motion.div>

              {phase === "results" && result && (
                <motion.div 
                  className="fa-results"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.6 }}
                >
                  <p className="fa-summary">
                    <b>{result.offers} {S.analysed}</b> {S.forNeed} {result.usage}. {S.recos} {result.cards.length} {S.recoTail}{result.cards.length > 1 ? S.nounPl : ""}, {S.classed}{result.cards.length > 1 ? S.adjPl : ""}.
                    <span className="fa-est"> {result.real ? S.real : S.est}{" · "}{COUNTRIES.find((x) => x.code === (result.country || country))?.label || "Belgique"}.</span>
                  </p>
                  <div className="fa-cards">
                    {result.cards.map((c, i) => <RecCard key={c.rank} c={c} i={i} q={asked} cur={result.currency || "€"} />)}
                  </div>
                  <p className="sa-disc">{S.disc}</p>
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </section>
  );
}
