"use client";

import { useLocale } from "@/lib/i18n";

export type DecisionSignal = {
  key: string;
  status: "positive" | "warning" | "neutral" | "unknown";
  merchants_count?: number;
  offers_count?: number;
  is_best_observed?: boolean;
  in_stock?: boolean;
  age_hours?: number | null;
  level?: string;
  tracked_days?: number;
  samples?: number;
  price_semantics?: string;
};

export type DecisionData = {
  recommendation_scope: "meilleur_prix_observe" | "offre_documentee" | "a_verifier" | "non_recommandee" | "tarif_a_verifier" | "conditions_a_verifier";
  score_observed: number;
  score_possible: number;
  confidence: "elevee" | "moyenne" | "faible" | "insuffisante";
  signals: DecisionSignal[];
  missing: string[];
  facts: { currency: string | null; merchants_compared: number; offers_compared: number };
};

const COPY = {
  fr: {
    eyebrow: "Pourquoi FILON vous montre cette offre",
    scope: {
      meilleur_prix_observe: "Meilleur prix observé",
      offre_documentee: "Offre documentée par FILON",
      a_verifier: "Prix à vérifier avant d’acheter",
      non_recommandee: "Offre non recommandée pour l’instant",
      tarif_a_verifier: "Tarif de séjour à confirmer",
      conditions_a_verifier: "Conditions à confirmer avant de choisir",
    },
    confidence: { elevee: "Données solides", moyenne: "Données partielles", faible: "Peu de données", insuffisante: "Données insuffisantes" },
    check: "À vérifier chez le marchand",
    evidence: "Ce que FILON a observé",
    best: (n: number) => `Meilleur prix parmi ${n} marchand${n > 1 ? "s" : ""} comparé${n > 1 ? "s" : ""}.`,
    compared: (n: number) => `Comparé chez ${n} marchand${n > 1 ? "s" : ""}.`,
    lowest: "Prix au plus bas observé par FILON.",
    favourable: "Prix sous la moyenne observée par FILON.",
    typical: "Prix dans sa moyenne observée.",
    high: "Prix au-dessus de la moyenne observée.",
    contextualPrice: "Tarif observé : à confirmer avec le contexte de réservation ou de prestation.",
    inStock: "En stock selon le dernier flux marchand.",
    outStock: "Indisponible selon le dernier flux marchand.",
    freshness: (hours: number) => hours < 24 ? `Prix relevé il y a ${hours} h.` : `Prix relevé il y a ${Math.floor(hours / 24)} j.`,
    stale: (hours: number) => `Prix relevé il y a ${Math.floor(hours / 24)} j : à confirmer.`,
    missing: {
      shipping_cost: "Frais de livraison", delivery_destination: "Livraison vers votre adresse", return_policy: "Conditions de retour",
      availability: "Disponibilité", price_history: "Historique de prix", comparison_scope: "Comparaison avec d’autres marchands",
      data_freshness: "Fraîcheur du prix", item_price: "Prix de l’article",
      stay_dates: "Dates du séjour", travellers: "Nombre de voyageurs", booking_total: "Prix total de réservation", mandatory_fees: "Taxes et frais obligatoires", availability_for_dates: "Disponibilité pour vos dates", cancellation_policy: "Conditions d’annulation",
      service_scope: "Périmètre de la prestation", service_conditions: "Conditions de service", appointment_availability: "Disponibilité du rendez-vous",
      digital_compatibility: "Compatibilité numérique", digital_region: "Région d’activation", digital_terms: "Conditions de licence", offer_nature: "Nature de l’offre", purchase_conditions: "Conditions d’achat",
    } as Record<string, string>,
  },
  nl: {
    eyebrow: "Waarom FILON deze aanbieding toont",
    scope: {
      meilleur_prix_observe: "Laagste waargenomen prijs",
      offre_documentee: "Aanbieding gedocumenteerd door FILON",
      a_verifier: "Controleer de prijs vóór aankoop",
      non_recommandee: "Aanbieding voorlopig niet aanbevolen",
      tarif_a_verifier: "Verblijfstarief te bevestigen",
      conditions_a_verifier: "Voorwaarden controleren vóór je kiest",
    },
    confidence: { elevee: "Sterke gegevens", moyenne: "Gedeeltelijke gegevens", faible: "Weinig gegevens", insuffisante: "Onvoldoende gegevens" },
    check: "Te controleren bij de winkel",
    evidence: "Wat FILON heeft waargenomen",
    best: (n: number) => `Laagste prijs bij ${n} vergeleken winkel${n > 1 ? "s" : ""}.`,
    compared: (n: number) => `Vergeleken bij ${n} winkel${n > 1 ? "s" : ""}.`,
    lowest: "Laagste prijs waargenomen door FILON.",
    favourable: "Prijs onder het door FILON waargenomen gemiddelde.",
    typical: "Prijs rond het waargenomen gemiddelde.",
    high: "Prijs boven het waargenomen gemiddelde.",
    contextualPrice: "Waargenomen tarief: bevestig dit met de boekings- of servicecontext.",
    inStock: "Op voorraad volgens de laatste winkel-feed.",
    outStock: "Niet beschikbaar volgens de laatste winkel-feed.",
    freshness: (hours: number) => hours < 24 ? `Prijs ${hours} u geleden bijgewerkt.` : `Prijs ${Math.floor(hours / 24)} d geleden bijgewerkt.`,
    stale: (hours: number) => `Prijs ${Math.floor(hours / 24)} d geleden bijgewerkt: controleer dit.`,
    missing: {
      shipping_cost: "Verzendkosten", delivery_destination: "Levering op jouw adres", return_policy: "Retourvoorwaarden",
      availability: "Beschikbaarheid", price_history: "Prijsgeschiedenis", comparison_scope: "Vergelijking met andere winkels",
      data_freshness: "Actualiteit van de prijs", item_price: "Artikelprijs",
      stay_dates: "Verblijfsdata", travellers: "Aantal reizigers", booking_total: "Totale boekingsprijs", mandatory_fees: "Verplichte belastingen en kosten", availability_for_dates: "Beschikbaarheid voor jouw data", cancellation_policy: "Annuleringsvoorwaarden",
      service_scope: "Omvang van de dienst", service_conditions: "Servicevoorwaarden", appointment_availability: "Beschikbaarheid van de afspraak",
      digital_compatibility: "Digitale compatibiliteit", digital_region: "Activeringsregio", digital_terms: "Licentievoorwaarden", offer_nature: "Aard van de aanbieding", purchase_conditions: "Aankoopvoorwaarden",
    } as Record<string, string>,
  },
  en: {
    eyebrow: "Why FILON shows this offer",
    scope: {
      meilleur_prix_observe: "Lowest observed price",
      offre_documentee: "Offer documented by FILON",
      a_verifier: "Check the price before buying",
      non_recommandee: "Offer not recommended for now",
      tarif_a_verifier: "Stay rate to confirm",
      conditions_a_verifier: "Terms to confirm before choosing",
    },
    confidence: { elevee: "Strong data", moyenne: "Partial data", faible: "Limited data", insuffisante: "Insufficient data" },
    check: "Check with the merchant",
    evidence: "What FILON observed",
    best: (n: number) => `Lowest price among ${n} compared merchant${n > 1 ? "s" : ""}.`,
    compared: (n: number) => `Compared across ${n} merchant${n > 1 ? "s" : ""}.`,
    lowest: "Lowest price observed by FILON.",
    favourable: "Price below FILON’s observed average.",
    typical: "Price within the observed average.",
    high: "Price above FILON’s observed average.",
    contextualPrice: "Observed rate: confirm it with the booking or service context.",
    inStock: "In stock according to the latest merchant feed.",
    outStock: "Unavailable according to the latest merchant feed.",
    freshness: (hours: number) => hours < 24 ? `Price checked ${hours}h ago.` : `Price checked ${Math.floor(hours / 24)}d ago.`,
    stale: (hours: number) => `Price checked ${Math.floor(hours / 24)}d ago: please confirm.`,
    missing: {
      shipping_cost: "Delivery cost", delivery_destination: "Delivery to your address", return_policy: "Return policy",
      availability: "Availability", price_history: "Price history", comparison_scope: "Comparison with other merchants",
      data_freshness: "Price freshness", item_price: "Item price",
      stay_dates: "Stay dates", travellers: "Number of travellers", booking_total: "Total booking price", mandatory_fees: "Mandatory taxes and fees", availability_for_dates: "Availability for your dates", cancellation_policy: "Cancellation policy",
      service_scope: "Service scope", service_conditions: "Service terms", appointment_availability: "Appointment availability",
      digital_compatibility: "Digital compatibility", digital_region: "Activation region", digital_terms: "Licence terms", offer_nature: "Offer nature", purchase_conditions: "Purchase conditions",
    } as Record<string, string>,
  },
} as const;

function signalText(signal: DecisionSignal, C: (typeof COPY)[keyof typeof COPY]) {
  if (signal.key === "comparison") {
    return signal.is_best_observed ? C.best(signal.merchants_count || 1) : C.compared(signal.merchants_count || 1);
  }
  if (signal.key === "price_moment") {
    if (signal.level === "excellent") return C.lowest;
    if (signal.level === "bon") return C.favourable;
    if (signal.level === "attendre") return C.high;
    return C.typical;
  }
  if (signal.key === "availability") return signal.in_stock ? C.inStock : C.outStock;
  if (signal.key === "contextual_price") return C.contextualPrice;
  if (signal.key === "freshness" && signal.age_hours != null) {
    return signal.status === "warning" ? C.stale(signal.age_hours) : C.freshness(signal.age_hours);
  }
  if (signal.key === "comparison_strength") return C.compared(signal.merchants_count || 1);
  return null;
}

export function DecisionPanel({ decision }: { decision: DecisionData | null | undefined }) {
  const { locale } = useLocale();
  if (!decision) return null;
  const C = COPY[locale];
  const visible = decision.signals
    .filter((signal) => signal.status !== "unknown")
    .map((signal) => ({ ...signal, text: signalText(signal, C) }))
    .filter((signal): signal is DecisionSignal & { text: string } => Boolean(signal.text));
  const missing = decision.missing.map((key) => C.missing[key] || key);

  return (
    <section className="filon-decision" aria-label={C.eyebrow}>
      <div className="filon-decision-head">
        <span>{C.eyebrow}</span>
        <span className={`filon-decision-confidence confidence-${decision.confidence}`}>{C.confidence[decision.confidence]}</span>
      </div>
      <strong className={`filon-decision-title scope-${decision.recommendation_scope}`}>{C.scope[decision.recommendation_scope]}</strong>
      {visible.length > 0 && (
        <div className="filon-decision-evidence">
          <span>{C.evidence}</span>
          <ul>{visible.slice(0, 3).map((signal) => <li key={signal.key} className={signal.status}>{signal.text}</li>)}</ul>
        </div>
      )}
      {missing.length > 0 && (
        <details className="filon-decision-missing">
          <summary>{C.check} ({missing.length})</summary>
          <p>{missing.join(" · ")}</p>
        </details>
      )}
    </section>
  );
}
