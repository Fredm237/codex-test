"use client";

import { Verdict, type VerdictData } from "@/components/editorial/Verdict";
import { DecisionPanel, type DecisionData, type DecisionSignal } from "@/components/filon/DecisionPanel";
import { useLocale } from "@/lib/i18n";
import {
  comparablePriceHistory,
  comparableHistoryTrackedDays,
  currentStockState,
  hasCurrentOfferEvidence,
  isFreshObservation,
  isPurchasableOffer,
  money,
  observationAgeHours,
  positiveFinitePrice,
  type ComparableHistoryPoint,
} from "./product-copy";
import { normalizeSupportedCurrency } from "@/lib/currency";
import { useEvidenceNow } from "./use-evidence-now";

type Hist = { price: number | null; currency?: string | null; at: string | null; in_stock?: boolean | null };
type Offer = {
  id: number;
  name: string;
  brand: string | null;
  offer_kind?: string | null;
  ean: string | null;
  price: number | null;
  currency: string | null;
  in_stock: boolean | null;
  observed_at: string | null;
  evidence_current: boolean | null;
  link: string | null;
  merchant: { name: string; slug: string; domain: string | null; region: string | null };
  history: Hist[];
  verdict: VerdictData | null;
  decision: DecisionData | null;
  product: { ean: string } | null;
};

const COPY = {
  fr: {
    back: "← Retour au catalogue", stock: "En stock", unavailable: "Indisponible", at: "chez",
    offer: "Voir l’offre chez le marchand", grouped: "Autres offres indexées pour ce produit",
    compare: "Comparer les offres de ce produit →", history: "Historique de prix",
    low: "Plus bas", high: "Plus haut", current: "Actuel", accumulating: "L’historique se constitue jour après jour. Revenez bientôt.",
    note: "Prix indicatif, susceptible d’évoluer chez le marchand. FILON peut percevoir une commission via ce lien. Confirmez le prix, les frais et le total chez le marchand.",
    observedRate: "Tarif observé", contextStatus: "À confirmer pour votre contexte", currentUnknown: "Prix ou disponibilité à vérifier", contextNote: "Ce tarif ne constitue pas un prix total de réservation. Confirmez les dates, les voyageurs, les frais et les conditions chez le marchand.",
  },
  nl: {
    back: "← Terug naar de catalogus", stock: "Op voorraad", unavailable: "Niet beschikbaar", at: "bij",
    offer: "Bekijk de aanbieding bij de winkel", grouped: "Andere geïndexeerde aanbiedingen voor dit product",
    compare: "Vergelijk de aanbiedingen voor dit product →", history: "Prijsgeschiedenis",
    low: "Laagste", high: "Hoogste", current: "Huidig", accumulating: "De prijsgeschiedenis groeit dag na dag. Kom binnenkort terug.",
    note: "Prijs is indicatief en kan wijzigen bij de winkel. Via deze link kan FILON een commissie ontvangen. Bevestig prijs, kosten en eindtotaal bij de winkel.",
    observedRate: "Waargenomen tarief", contextStatus: "Te bevestigen voor jouw context", currentUnknown: "Prijs of beschikbaarheid controleren", contextNote: "Dit tarief is geen totale boekingsprijs. Bevestig data, reizigers, kosten en voorwaarden bij de winkel.",
  },
  en: {
    back: "← Back to catalogue", stock: "In stock", unavailable: "Unavailable", at: "at",
    offer: "See offer at merchant", grouped: "Other indexed offers for this product",
    compare: "Compare this product's offers →", history: "Price history",
    low: "Lowest", high: "Highest", current: "Current", accumulating: "Price history is building day by day. Check back soon.",
    note: "Price is indicative and may change at the merchant. FILON may earn a commission through this link. Confirm the price, fees and final total with the merchant.",
    observedRate: "Observed rate", contextStatus: "Confirm for your context", currentUnknown: "Check price or availability", contextNote: "This rate is not a total booking price. Confirm dates, travellers, fees and terms with the merchant.",
  },
} as const;

function Sparkline({ hist }: { hist: ComparableHistoryPoint[] }) {
  const values = hist.map((entry) => entry.price).filter((price): price is number => price != null);
  if (values.length < 2) return null;
  const width = 600; const height = 120; const padding = 8;
  const min = Math.min(...values); const max = Math.max(...values); const span = max - min || 1;
  const step = (width - padding * 2) / (values.length - 1);
  const path = values.map((price, index) => `${index === 0 ? "M" : "L"} ${padding + index * step} ${height - padding - ((price - min) / span) * (height - padding * 2)}`).join(" ");
  return <svg viewBox={`0 0 ${width} ${height}`} width="100%" height="120" preserveAspectRatio="none" aria-hidden="true" style={{ display: "block" }}><path d={path} fill="none" stroke="var(--accent)" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" /></svg>;
}

export function OfferBackLink() {
  const { locale } = useLocale();
  return <a href="/catalogue" style={{ fontSize: 13.5, color: "var(--ink-3)" }}>{COPY[locale].back}</a>;
}

export function OfferProductDetails({ offer }: { offer: Offer }) {
  const { locale } = useLocale();
  const C = COPY[locale];
  const evidenceNow = useEvidenceNow([offer.observed_at]);
  const isContextualOffer = Boolean(offer.offer_kind && !["physical_product", "tech_accessory"].includes(offer.offer_kind));
  const canBuy = isPurchasableOffer(offer, evidenceNow);
  const stockState = currentStockState(offer, evidenceNow);
  const hasCurrentPriceEvidence = hasCurrentOfferEvidence(offer, evidenceNow);
  const history = comparablePriceHistory(offer.history, offer.currency, evidenceNow);
  const hasHistory = !isContextualOffer && history.length >= 2;
  const historyTrackedDays = comparableHistoryTrackedDays(history);
  const historyMetricsMatch = Boolean(offer.verdict)
    && offer.verdict!.samples === history.length
    && offer.verdict!.tracked_days === historyTrackedDays;
  const historyPrices = history.map((entry) => entry.price);
  const historyMin = hasHistory ? Math.min(...historyPrices) : null;
  const historyMax = hasHistory ? Math.max(...historyPrices) : null;
  const hasComparableMoment = hasHistory && hasCurrentPriceEvidence && historyMetricsMatch;
  const verdict = offer.verdict?.basis === "price_history" && hasComparableMoment
    ? offer.verdict
    : offer.verdict?.basis === "insufficient"
      && historyMetricsMatch
      ? offer.verdict
      : null;
  const ageHours = offer.evidence_current === true
    ? observationAgeHours(offer.observed_at, evidenceNow)
    : null;
  const freshnessSignal: DecisionSignal | null = ageHours === null
    ? null
    : {
        key: "freshness",
        status: isFreshObservation(offer.observed_at, evidenceNow) ? "positive" : "warning",
        age_hours: ageHours,
        reason: isFreshObservation(offer.observed_at, evidenceNow) ? "fresh" : "stale",
      };
  const availabilitySignal: DecisionSignal | null = stockState === null
    ? null
    : {
        key: "availability",
        status: stockState ? "positive" : "warning",
        in_stock: stockState,
      };
  const decision = (() => {
    if (!offer.decision) return null;
    const removedComparison = offer.decision.signals.some((signal) =>
      ["comparison", "comparison_strength"].includes(signal.key),
    );
    const signals = offer.decision.signals.filter((signal) => {
      if (["comparison", "comparison_strength", "availability", "freshness"].includes(signal.key)) return false;
      if (signal.key !== "price_moment") return true;
      return offer.verdict?.basis === "price_history"
        && hasComparableMoment
        && signal.samples === history.length
        && signal.tracked_days === historyTrackedDays
        && signal.level === offer.verdict.level;
    });
    if (freshnessSignal) signals.push(freshnessSignal);
    if (availabilitySignal) signals.push(availabilitySignal);
    const missing = new Set(offer.decision.missing);
    if (removedComparison) missing.add("comparison_scope");
    if (!hasHistory) {
      missing.add("price_history");
      missing.add("history_currency");
    }
    if (!positiveFinitePrice(offer.price)) missing.add("item_price");
    if (normalizeSupportedCurrency(offer.currency) === null) missing.add("currency");
    if (stockState === null) missing.add("availability");
    if (offer.evidence_current !== true || !isFreshObservation(offer.observed_at, evidenceNow)) missing.add("data_freshness");
    return {
      ...offer.decision,
      evidence_summary: undefined,
      recommendation_scope: offer.decision.recommendation_scope === "meilleur_prix_observe"
        ? "a_verifier" as const
        : offer.decision.recommendation_scope,
      signals,
      missing: [...missing],
      facts: {
        ...offer.decision.facts,
        currency: normalizeSupportedCurrency(offer.currency),
        merchants_compared: 0,
        offers_compared: 0,
        item_price: positiveFinitePrice(offer.price) ? offer.price : null,
        last_observed_at: ageHours === null ? null : offer.observed_at,
      },
    };
  })();
  const hasGroupedProduct = offer.product
    && typeof offer.product.ean === "string"
    && offer.product.ean.length > 0;

  return (
    <div className="p19-offer-dossier">
      {offer.brand && <span className="p19-offer-brand" style={{ fontSize: 12.5, letterSpacing: "0.05em", textTransform: "uppercase", color: "var(--ink-3)" }}>{offer.brand}</span>}
      <h1 className="p19-offer-title" style={{ fontFamily: "var(--serif)", fontSize: "clamp(24px, 4vw, 34px)", lineHeight: 1.15, margin: "6px 0 14px" }}>{offer.name}</h1>
      <div className="p19-offer-headline" style={{ display: "flex", alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
        {isContextualOffer && <span style={{ fontSize: 12.5, fontWeight: 700, letterSpacing: "0.04em", textTransform: "uppercase", color: "var(--ink-3)" }}>{C.observedRate}</span>}
        <b className="p19-offer-price" style={{ fontSize: 30, color: "var(--ink)" }}>{money(
          hasCurrentPriceEvidence ? offer.price : null,
          hasCurrentPriceEvidence ? offer.currency : null,
          locale,
        )}</b>
        <span className="p19-offer-status" data-purchasable={canBuy || undefined} style={{ fontSize: 13, fontWeight: 600, color: canBuy ? "var(--accent)" : "var(--ink-3)" }}>{isContextualOffer ? C.contextStatus : canBuy ? C.stock : stockState === false ? C.unavailable : C.currentUnknown}</span>
      </div>
      <p className="p19-offer-merchant" style={{ fontSize: 14, color: "var(--ink-2)", marginTop: 6 }}>{C.at} <b>{offer.merchant.name}</b></p>
      {offer.link && canBuy && <a className="ed-btn wave" href={offer.link} target="_blank" rel="noopener noreferrer sponsored" style={{ marginTop: 18, textDecoration: "none" }}>{C.offer}</a>}
      {verdict && <Verdict v={verdict} />}
      <DecisionPanel decision={decision} />
      {hasGroupedProduct && offer.product && <a className="pd-compare" href={`/produits/${offer.product.ean}/`}><b>{C.grouped}</b><span>{C.compare}</span></a>}
      {!isContextualOffer && <div className="p19-offer-history" style={{ marginTop: 30, background: "var(--card)", border: "1px solid var(--line-2)", borderRadius: 16, padding: 18 }}>
        <span style={{ fontSize: 12.5, letterSpacing: "0.04em", textTransform: "uppercase", color: "var(--ink-3)" }}>{C.history}</span>
        {hasHistory ? <><div style={{ marginTop: 12 }}><Sparkline hist={history} /></div><div style={{ display: "flex", gap: 22, marginTop: 12, fontSize: 13 }}><span><span style={{ color: "var(--ink-3)" }}>{C.low} </span><b>{money(historyMin, offer.currency, locale)}</b></span><span><span style={{ color: "var(--ink-3)" }}>{C.high} </span><b>{money(historyMax, offer.currency, locale)}</b></span>{hasCurrentPriceEvidence && <span><span style={{ color: "var(--ink-3)" }}>{C.current} </span><b>{money(offer.price, offer.currency, locale)}</b></span>}</div></> : <p style={{ fontSize: 13.5, color: "var(--ink-3)", marginTop: 10 }}>{C.accumulating}</p>}
      </div>}
      <p className="p19-offer-note" style={{ fontSize: 12, color: "var(--ink-3)", marginTop: 16, lineHeight: 1.5 }}>{isContextualOffer ? C.contextNote : C.note}</p>
    </div>
  );
}
