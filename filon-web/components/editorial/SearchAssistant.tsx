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
    why: "Pourquoi", alt: "Alternative", see: "Voir l'offre", catalogue: "Voir dans le catalogue", good: "Bon moment", wait: "Attendre",
    real: "Prix réels · Catalogue FILON", est: "Prix estimés, à titre indicatif",
    analysed: "offres analysées", forNeed: "pour", recos: "Voici mes", recoTail: "recommandation", classed: "classée", nounPl: "s", adjPl: "s",
    failedTitle: "Je ne peux pas répondre pour le moment.",
    failedBody: "L'analyse s'appuie sur les offres de nos marchands partenaires, et ce service est momentanément injoignable. Plutôt que de vous proposer des produits inventés, je préfère ne rien vous proposer. Réessayez dans un instant.",
    sourceTitle: "Aucune offre vérifiée n’est disponible pour cette recherche.",
    sourceBody: "FILON s’appuie uniquement sur les offres de son catalogue partenaire. Cette recherche ne renvoie pas encore de prix vérifiables ; explorez le catalogue ou reformulez votre demande.",
    retry: "Réessayer",
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
    why: "Waarom", alt: "Alternatief", see: "Bekijk de aanbieding", catalogue: "Bekijk in de catalogus", good: "Goed moment", wait: "Wachten",
    real: "Echte prijzen · FILON Catalogus", est: "Geschatte prijzen, ter indicatie",
    analysed: "aanbiedingen geanalyseerd", forNeed: "voor", recos: "Dit zijn mijn", recoTail: "aanbeveling", classed: "gerangschikt", nounPl: "en", adjPl: "",
    failedTitle: "Ik kan nu niet antwoorden.",
    failedBody: "De analyse steunt op de aanbiedingen van onze partnerwinkels, en die dienst is tijdelijk onbereikbaar. Liever niets voorstellen dan verzonnen producten. Probeer het zo meteen opnieuw.",
    sourceTitle: "Geen geverifieerde aanbieding voor deze zoekopdracht.",
    sourceBody: "FILON gebruikt uitsluitend aanbiedingen uit zijn partnercatalogus. Deze zoekopdracht levert nog geen verifieerbare prijzen op; verken de catalogus of verfijn je vraag.",
    retry: "Opnieuw proberen",
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
    why: "Why", alt: "Alternative", see: "See the offer", catalogue: "View in catalogue", good: "Good time", wait: "Wait",
    real: "Real prices · FILON Catalogue", est: "Estimated prices, for guidance",
    analysed: "offers analysed", forNeed: "for", recos: "Here are my", recoTail: "recommendation", classed: "ranked", nounPl: "s", adjPl: "",
    failedTitle: "I can't answer right now.",
    failedBody: "The analysis draws on offers from our partner merchants, and that service is temporarily unreachable. Rather than show you invented products, I would rather show you nothing. Try again in a moment.",
    sourceTitle: "No verified offer is available for this search.",
    sourceBody: "FILON relies only on offers from its partner catalogue. This search does not yet return verifiable prices; explore the catalogue or refine your request.",
    retry: "Try again",
    disc: "FILON is free. You never pay, and your data is not resold.",
    at: "at", cashback: "cashback", coupon: "coupon",
    hist: { baisse: "Falling", hausse: "Rising", stable: "Stable" } as Record<Hist, string>,
  },
};

/* ──────────────────────────────────────────────────────────────────────────
   FILON assistant — a decision surface, not a chat.
   The analysis is consumed as a stream of events, produced by the backend over
   SSE. There is no second source: when the stream fails, the assistant says so.
   ────────────────────────────────────────────────────────────────────────── */

const money = (n: number, cur = "€") => `${n.toLocaleString("fr-FR")} ${cur}`;

/** Pays couverts par les offres et prix suivis dans le catalogue FILON. */
const COUNTRIES: Array<{ code: string; label: string }> = [
  { code: "be", label: "Belgique (FR)" },
  { code: "be-nl", label: "België (NL)" },
  { code: "fr", label: "France" },
  { code: "ch", label: "Suisse" },
  { code: "lu", label: "Luxembourg" },
  { code: "nl", label: "Pays-Bas" },
];

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

/* Il n'y a plus de catalogue de démonstration ici, et c'est délibéré.

   Ce fichier contenait cinq recommandations écrites à la main par catégorie —
   Fnac, Cdiscount, Boulanger, Darty, Amazon — avec des taux de cashback, des
   historiques de prix et des Scores FILON inventés. Elles s'affichaient dès
   que l'API échouait, sans rien qui les distingue d'une vraie analyse.

   FILON n'est partenaire d'aucun de ces marchands. Recommander leurs produits
   avec des chiffres fabriqués, c'est exactement ce qu'un comparateur ne peut
   pas se permettre : le visiteur n'a aucun moyen de savoir qu'il lit une
   maquette. Un assistant qui n'a pas de réponse doit le dire. */

function detectBudget(q: string): number | null {
  const m = q.replace(/\s/g, "").match(/(\d{2,5})(?:€|eur)/i) || q.match(/(?:moins de|budget|à|max|environ|autour)\D{0,6}(\d{2,5})/i);
  return m ? parseInt(m[1], 10) : null;
}

type Ev =
  | { type: "step"; i: number }
  | { type: "step-done"; i: number }
  | { type: "results"; data: Result };

const isGoogleShoppingUrl = (value?: string | null) =>
  Boolean(value && /(^|\.)google\.[^/]+\/search/i.test(value) && /(?:[?&]tbm=shop|[?&]ibp=oshop)/i.test(value));

// Une demande conversationnelle (« un casque sous 300 € ») ne doit pas être
// envoyée telle quelle au moteur catalogue. Ce dernier cherche des noms de
// produit ; cette extraction courte préserve l’intention sans promettre de
// compréhension artificielle.
function catalogueSearchTerm(input: string) {
  const normalized = input
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
  const concepts: Array<[RegExp, string]> = [
    [/casque|headphone|koptelefoon|noise.?cancell?/, "casque"],
    [/ecouteur|earbud|oortje/, "ecouteurs"],
    [/smartphone|telephone|telefoon|iphone|android/, "smartphone"],
    [/ordinateur|laptop|portable|pc\b|computer/, "ordinateur"],
    [/montre|watch|horloge/, "montre"],
    [/television|televiseur|tv\b/, "television"],
    [/aspirateur|vacuum|stofzuiger/, "aspirateur"],
    [/sneaker|basket|chaussure|shoe/, "chaussures"],
  ];
  const match = concepts.find(([pattern]) => pattern.test(normalized));
  if (match) return match[1];

  const terms = normalized
    .replace(/\b(?:un|une|des|le|la|les|de|du|pour|avec|sous|moins|budget|euro|euros|eur|a|au|en|the|a|an|and|with|under|voor|met|onder)\b/g, " ")
    .replace(/\b\d+[\d\s,.]*\b/g, " ")
    .split(/[^a-z0-9]+/)
    .filter((term) => term.length > 2)
    .slice(0, 3);
  return terms.join(" ") || input.trim();
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
  // Une offre sans deep link ne doit jamais faire sortir l’utilisateur vers
  // Google Shopping : on le laisse explorer le même produit dans FILON.
  const hasMerchantLink = Boolean(c.link) && !isGoogleShoppingUrl(c.link);
  const offerUrl = hasMerchantLink
    ? (c.link as string)
    : `/catalogue/?q=${encodeURIComponent(q || c.name)}`;
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
          <a
            className="ed-btn wave"
            href={offerUrl}
            target={hasMerchantLink ? "_blank" : undefined}
            rel={hasMerchantLink ? "noopener noreferrer" : undefined}
          >
            {hasMerchantLink ? S.see : S.catalogue}
          </a>
        </div>
      </div>
    </motion.article>
  );
}

export function SearchAssistant() {
  const [query, setQuery] = useState("");
  const [phase, setPhase] = useState<"idle" | "thinking" | "results" | "failed">("idle");
  const [active, setActive] = useState(-1);
  const [done, setDone] = useState<number[]>([]);
  const [result, setResult] = useState<Result | null>(null);
  const [asked, setAsked] = useState("");
  const [blockedExternal, setBlockedExternal] = useState(false);
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
    setPhase("thinking");
    setResult(null);
    setBlockedExternal(false);
    setDone([]);
    setActive(0);

    const apply = (ev: Ev): boolean => {
      if (runId.current !== id) return false; // superseded by a newer query
      if (ev.type === "step") setActive(ev.i);
      else if (ev.type === "step-done") setDone((d) => [...d, ev.i]);
      else if (ev.type === "results") {
        // Une recommandation ne peut pas être présentée comme FILON lorsqu’elle
        // ne contient que des liens Google Shopping. On bloque le résultat au
        // lieu de brouiller la promesse de catalogue partenaire.
        const verifiedCards = ev.data.cards.filter((card) => !isGoogleShoppingUrl(card.link));
        setActive(-1);
        // `real: false` signifie que le backend n’a pas trouvé de réponse dans
        // le catalogue FILON : ce sont des estimations et non des offres à
        // recommander. Elles restent donc hors de l’interface de décision.
        if (!ev.data.real || (ev.data.cards.length > 0 && verifiedCards.length === 0)) {
          setBlockedExternal(true);
          setPhase("failed");
          return true;
        }
        setResult({ ...ev.data, cards: verifiedCards });
        setPhase("results");
      }
      return true;
    };

    // Le backend, ou rien. Un repli qui invente des offres se présente comme une
    // vraie analyse : le visiteur n'a aucun moyen de faire la différence.
    try {
      for await (const ev of streamAnalyze(q, country)) if (!apply(ev)) return;
    } catch {
      if (runId.current !== id) return;
      setDone([]);
      setActive(-1);
      setPhase("failed");
    }
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
      {/* Scène cinématique fiable : aucun média absent, aucun visuel inventé. */}
      {phase === "idle" && (
        <>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            className="sa-bg-visual"
            src="/seq/hero/001.jpg"
            alt=""
            aria-hidden="true"
            fetchPriority="high"
          />
          <div className="sa-bg-overlay" />
        </>
      )}
      <div className="ed-wrap sa-content">
        {phase === "idle" && <span className="eyebrow sa-eyebrow-light">{S.eyebrow}</span>}
        <h1 className={phase === "idle" ? "sa-title-light" : ""}>{phase === "idle" ? S.h1Idle : S.h1Again}</h1>

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
              {/* streamed reasoning — retiré en cas d'échec : des étapes figées
                  à mi-course laissent croire que l'analyse continue. */}
              <motion.div
                className={`fa-steps ${phase === "results" ? "collapsed" : ""} ${phase === "failed" ? "hidden" : ""}`}
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

              {phase === "failed" && (
                <motion.div
                  className="sa-failed"
                  role="status"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4 }}
                >
                  <p className="sa-failed-title">{blockedExternal ? S.sourceTitle : S.failedTitle}</p>
                  <p className="sa-failed-body">{blockedExternal ? S.sourceBody : S.failedBody}</p>
                  {blockedExternal ? (
                    <a className="sa-failed-retry" href={`/catalogue/?q=${encodeURIComponent(catalogueSearchTerm(asked))}`}>
                      {S.catalogue}
                    </a>
                  ) : (
                    <button type="button" className="sa-failed-retry" onClick={() => ask(asked)}>
                      {S.retry}
                    </button>
                  )}
                </motion.div>
              )}

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
