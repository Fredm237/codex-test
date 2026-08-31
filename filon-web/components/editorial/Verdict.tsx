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
  basis?: "price_history" | "merchant_comparison" | "insufficient";
};

const COPY = {
  fr: { label: "Verdict FILON", notCalibrated: "confiance non calibrée", reading: "relevé", readings: "relevés", since: "sur", day: "jour", days: "jours", started: "suivi démarré récemment" },
  nl: { label: "FILON-oordeel", notCalibrated: "vertrouwen niet gekalibreerd", reading: "meting", readings: "metingen", since: "over", day: "dag", days: "dagen", started: "tracking is onlangs gestart" },
  en: { label: "FILON verdict", notCalibrated: "confidence not calibrated", reading: "reading", readings: "readings", since: "over", day: "day", days: "days", started: "tracking started recently" },
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
  match = reason.match(/^Le même produit est à (.+) chez un autre marchand, soit (.+) de moins\.$/);
  if (match) return locale === "nl" ? `Hetzelfde product kost ${match[1]} bij een andere winkel, ${match[2]} minder.` : `The same product costs ${match[1]} at another merchant, ${match[2]} less.`;
  match = reason.match(/^Parmi les observations en stock, aucun prix inférieur n'a été relevé sur (\d+) jours de suivi\.$/);
  if (match) return locale === "nl" ? `Binnen de voorraadwaarnemingen is in ${match[1]} dagen geen lagere prijs gemeten.` : `Among in-stock observations, no lower price was recorded over ${match[1]} days.`;
  match = reason.match(/^(\d+) % sous la moyenne des observations en stock sur (\d+) jours de suivi\.$/);
  if (match) return locale === "nl" ? `${match[1]}% onder het gemiddelde van de voorraadwaarnemingen over ${match[2]} dagen.` : `${match[1]}% below the average of in-stock observations over ${match[2]} days.`;
  match = reason.match(/^(\d+) % au-dessus de la moyenne des observations en stock sur (\d+) jours de suivi\.$/);
  if (match) return locale === "nl" ? `${match[1]}% boven het gemiddelde van de voorraadwaarnemingen over ${match[2]} dagen.` : `${match[1]}% above the average of in-stock observations over ${match[2]} days.`;
  match = reason.match(/^Au niveau moyen des observations en stock sur (\d+) jours de suivi\.$/);
  if (match) return locale === "nl" ? `Rond het gemiddelde van de voorraadwaarnemingen over ${match[1]} dagen.` : `Around the average of in-stock observations over ${match[1]} days.`;
  match = reason.match(/^Parmi les observations en stock, le prix est déjà descendu à (.+) sur (\d+) jours de suivi\.$/);
  if (match) return locale === "nl" ? `Binnen de voorraadwaarnemingen daalde de prijs al tot ${match[1]} over ${match[2]} dagen.` : `Among in-stock observations, the price has already fallen to ${match[1]} over ${match[2]} days.`;
  match = reason.match(/^Amplitude des observations en stock : de (.+) à (.+)\.$/);
  if (match) return locale === "nl" ? `Bereik van de voorraadwaarnemingen: van ${match[1]} tot ${match[2]}.` : `Range of in-stock observations: from ${match[1]} to ${match[2]}.`;
  return reason;
}

const HISTORICAL_HEADLINE_BY_LEVEL: Record<string, string> = {
  excellent: "Excellent moment pour acheter",
  bon: "Bon moment pour acheter",
  neutre: "Prix dans sa moyenne habituelle",
  attendre: "Mieux vaut attendre",
};

const RECOGNIZED_REASON_PATTERNS = [
  /^FILON suit ce prix depuis peu : pas encore de quoi juger son évolution\.$/,
  /^C'est le meilleur prix parmi les \d+ marchands qui vendent ce produit\.$/,
  /^Le même produit est à .+ chez un autre marchand, soit .+ de moins\.$/,
  /^Parmi les observations en stock, aucun prix inférieur n'a été relevé sur \d+ jours de suivi\.$/,
  /^\d+ % sous la moyenne des observations en stock sur \d+ jours de suivi\.$/,
  /^\d+ % au-dessus de la moyenne des observations en stock sur \d+ jours de suivi\.$/,
  /^Au niveau moyen des observations en stock sur \d+ jours de suivi\.$/,
  /^Parmi les observations en stock, le prix est déjà descendu à .+ sur \d+ jours de suivi\.$/,
  /^Amplitude des observations en stock : de .+ à .+\.$/,
];

const LEVEL_REASON_PATTERNS: Record<string, RegExp> = {
  excellent: /^Parmi les observations en stock, aucun prix inférieur/,
  bon: /^\d+ % sous la moyenne des observations en stock/,
  neutre: /^Au niveau moyen des observations en stock/,
  attendre: /^\d+ % au-dessus de la moyenne des observations en stock/,
};

function safeVerdict(v: VerdictData): VerdictData {
  const samples = Number.isInteger(v.samples) && v.samples >= 0 ? v.samples : 0;
  const trackedDays = Number.isInteger(v.tracked_days) && v.tracked_days >= 0 ? v.tracked_days : 0;
  const reasons = Array.isArray(v.reasons)
    ? v.reasons.filter((reason): reason is string =>
      typeof reason === "string" && RECOGNIZED_REASON_PATTERNS.some((pattern) => pattern.test(reason)),
    )
    : [];
  const historical = v.basis === "price_history"
    && samples >= 5
    && trackedDays >= 7
    && HISTORICAL_HEADLINE_BY_LEVEL[v.level] === v.headline
    && Boolean(LEVEL_REASON_PATTERNS[v.level]?.test(reasons[0] ?? ""));
  const comparison = v.basis === "merchant_comparison"
    && v.level === "attendre"
    && v.headline === "Moins cher ailleurs"
    && reasons.some((reason) => /^Le même produit est à .+ chez un autre marchand, soit .+ de moins\.$/.test(reason));
  const valid = v.confidence === "not_calibrated" && (
    historical
    || comparison
    || (v.basis === "insufficient" && v.level === "insuffisant")
  );
  if (valid) {
    return {
      ...v,
      samples,
      tracked_days: trackedDays,
      reasons,
    };
  }
  return {
    ...v,
    level: "insuffisant",
    headline: "Historique trop récent pour se prononcer",
    reasons: [],
    tracked_days: trackedDays,
    samples,
    confidence: "not_calibrated",
    basis: "insufficient",
  };
}

export function Verdict({ v }: { v: VerdictData | null | undefined }) {
  const { locale } = useLocale();
  if (!v) return null;
  const safe = safeVerdict(v);
  const level = safe.level;
  const C = COPY[locale];
  const confidence = C.notCalibrated;
  const trackingMeta = safe.tracked_days > 0
    ? `${safe.samples} ${safe.samples > 1 ? C.readings : C.reading} ${C.since} ${safe.tracked_days} ${safe.tracked_days > 1 ? C.days : C.day}`
    : `${safe.samples} ${safe.samples > 1 ? C.readings : C.reading} · ${C.started}`;

  return (
    <motion.section className={`vd vd-${level}`} aria-label={C.label} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}>
      <span className="vd-eyebrow">{C.label}</span>
      <div className="vd-head">
        <motion.span className="vd-dot" aria-hidden="true" initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.3, type: "spring", stiffness: 400, damping: 15 }} />
        <b className="vd-title">{HEADLINES[safe.headline]?.[locale] ?? HEADLINES["Historique trop récent pour se prononcer"][locale]}</b>
      </div>
      {safe.reasons.length > 0 && (
        <motion.ul className="vd-reasons" initial="hidden" animate="show" variants={{ hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.08, delayChildren: 0.2 } } }}>
          {safe.reasons.map((reason, index) => <motion.li key={index} variants={{ hidden: { opacity: 0, x: -8 }, show: { opacity: 1, x: 0 } }}>{localizeReason(reason, locale)}</motion.li>)}
        </motion.ul>
      )}
      {safe.samples > 0 && <p className="vd-meta">{trackingMeta} · {confidence}</p>}
    </motion.section>
  );
}
