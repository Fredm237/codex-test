"use client";

import { motion } from "framer-motion";
import { useLocale, type Locale } from "@/lib/i18n";

export type VerdictData = {
  level: string;
  headline: string;
  reasons: string[];
  tracked_days: number;
  samples: number;
  confidence: string;
};

const COPY = {
  fr: { label: "Verdict FILON", low: "confiance faible", medium: "confiance moyenne", high: "bonne confiance", reading: "relevé", readings: "relevés", since: "sur", day: "jour", days: "jours", started: "suivi démarré récemment" },
  nl: { label: "FILON-oordeel", low: "laag vertrouwen", medium: "gemiddeld vertrouwen", high: "goed vertrouwen", reading: "meting", readings: "metingen", since: "over", day: "dag", days: "dagen", started: "tracking is onlangs gestart" },
  en: { label: "FILON verdict", low: "low confidence", medium: "medium confidence", high: "high confidence", reading: "reading", readings: "readings", since: "over", day: "day", days: "days", started: "tracking started recently" },
} as const;

const HEADLINES: Record<string, Record<Locale, string>> = {
  "Moins cher ailleurs": { fr: "Moins cher ailleurs", nl: "Elders goedkoper", en: "Cheaper elsewhere" },
  "Historique trop récent pour se prononcer": { fr: "Historique trop récent pour se prononcer", nl: "Prijsgeschiedenis te recent voor een oordeel", en: "Price history is too recent for a verdict" },
  "Excellent moment pour acheter": { fr: "Excellent moment pour acheter", nl: "Uitstekend moment om te kopen", en: "An excellent time to buy" },
  "Bon moment pour acheter": { fr: "Bon moment pour acheter", nl: "Een goed moment om te kopen", en: "A good time to buy" },
  "Mieux vaut attendre": { fr: "Mieux vaut attendre", nl: "Je kunt beter wachten", en: "Better to wait" },
  "Prix dans sa moyenne habituelle": { fr: "Prix dans sa moyenne habituelle", nl: "Prijs ligt rond het gebruikelijke gemiddelde", en: "Price is around its usual average" },
};

function localizeReason(reason: string, locale: Locale) {
  if (locale === "fr") return reason;
  const simple: Record<string, Record<Exclude<Locale, "fr">, string>> = {
    "FILON suit ce prix depuis peu : pas encore de quoi juger son évolution.": {
      nl: "FILON volgt deze prijs nog maar net: er is nog te weinig informatie om de evolutie te beoordelen.",
      en: "FILON has only recently started tracking this price: there is not enough data to judge its evolution yet.",
    },
  };
  if (simple[reason]) return simple[reason][locale];

  let match = reason.match(/^C'est le meilleur prix parmi les (\d+) marchands qui vendent ce produit\.$/);
  if (match) return locale === "nl" ? `Dit is de beste prijs van ${match[1]} winkels die dit product verkopen.` : `This is the best price among ${match[1]} merchants selling this product.`;
  match = reason.match(/^Jamais relevé moins cher depuis (\d+) jours de suivi\.$/);
  if (match) return locale === "nl" ? `Sinds ${match[1]} dagen tracking nooit goedkoper gemeten.` : `Never recorded cheaper in ${match[1]} days of tracking.`;
  match = reason.match(/^(\d+) % sous la moyenne observée depuis (\d+) jours de suivi\.$/);
  if (match) return locale === "nl" ? `${match[1]}% onder het gemiddelde dat we in ${match[2]} dagen zagen.` : `${match[1]}% below the average observed over ${match[2]} days.`;
  match = reason.match(/^(\d+) % au-dessus de la moyenne observée depuis (\d+) jours de suivi\.$/);
  if (match) return locale === "nl" ? `${match[1]}% boven het gemiddelde dat we in ${match[2]} dagen zagen.` : `${match[1]}% above the average observed over ${match[2]} days.`;
  match = reason.match(/^Au niveau habituel depuis (\d+) jours de suivi\.$/);
  if (match) return locale === "nl" ? `Op het gebruikelijke niveau van de laatste ${match[1]} dagen.` : `At its usual level over the last ${match[1]} days.`;
  return reason;
}

export function Verdict({ v }: { v: VerdictData }) {
  const { locale } = useLocale();
  if (!v) return null;
  const level = ["excellent", "bon", "neutre", "attendre", "insuffisant"].includes(v.level) ? v.level : "neutre";
  const C = COPY[locale];
  const confidence = v.confidence === "faible" ? C.low : v.confidence === "moyenne" ? C.medium : v.confidence === "bonne" ? C.high : v.confidence;
  const trackingMeta = v.tracked_days > 0
    ? `${v.samples} ${v.samples > 1 ? C.readings : C.reading} ${C.since} ${v.tracked_days} ${v.tracked_days > 1 ? C.days : C.day}`
    : `${v.samples} ${v.samples > 1 ? C.readings : C.reading} · ${C.started}`;

  return (
    <motion.section className={`vd vd-${level}`} aria-label={C.label} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}>
      <span className="vd-eyebrow">{C.label}</span>
      <div className="vd-head">
        <motion.span className="vd-dot" aria-hidden="true" initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.3, type: "spring", stiffness: 400, damping: 15 }} />
        <b className="vd-title">{HEADLINES[v.headline]?.[locale] ?? v.headline}</b>
      </div>
      {v.reasons?.length > 0 && (
        <motion.ul className="vd-reasons" initial="hidden" animate="show" variants={{ hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.08, delayChildren: 0.2 } } }}>
          {v.reasons.map((reason, index) => <motion.li key={index} variants={{ hidden: { opacity: 0, x: -8 }, show: { opacity: 1, x: 0 } }}>{localizeReason(reason, locale)}</motion.li>)}
        </motion.ul>
      )}
      {v.samples > 0 && <p className="vd-meta">{trackingMeta} · {confidence}</p>}
    </motion.section>
  );
}
