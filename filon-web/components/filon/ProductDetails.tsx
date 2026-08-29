"use client";

import { Verdict, type VerdictData } from "@/components/editorial/Verdict";
import { DecisionPanel, type DecisionData, type DecisionSignal } from "@/components/filon/DecisionPanel";
import { useLocale } from "@/lib/i18n";
import {
  deriveProductComparison,
  currentStockState,
  hasCurrentOfferEvidence,
  isFreshObservation,
  isPurchasableOffer,
  money,
  observationAgeHours,
} from "./product-copy";
import { useEvidenceNow } from "./use-evidence-now";

type Offer = {
  id: number;
  price: number | null;
  currency: string | null;
  in_stock: boolean | null;
  observed_at: string | null;
  evidence_current: boolean | null;
  link: string | null;
  merchant: { name: string; slug: string; region: string | null };
};

type Product = {
  ean: string;
  name: string;
  brand: string | null;
  offers: Offer[];
  verdict: VerdictData | null;
  decision: DecisionData | null;
};

const COPY = {
  fr: {
    from: "à partir de", at: "chez", merchant: "marchand", merchants: "marchands",
    save: "Écart de prix observé", saveTail: "entre l’offre la moins chère et la plus chère comparées.",
    best: "Vérifier le prix chez", all: "Toutes les offres", bestPrice: "Prix le plus bas observé",
    stock: "En stock", unavailable: "Indisponible", availabilityUnknown: "Prix ou disponibilité à vérifier", comparisonUnknown: "Comparaison de prix à vérifier", see: "Voir", note: "Prix indicatifs, susceptibles d’évoluer chez les marchands. Les offres sont regroupées par code-barres", commission: "FILON peut percevoir une commission via ces liens. Confirmez le prix, les frais et le total chez le marchand.",
  },
  nl: {
    from: "vanaf", at: "bij", merchant: "winkel", merchants: "winkels",
    save: "Waargenomen prijsverschil", saveTail: "tussen de goedkoopste en duurste vergeleken aanbieding.",
    best: "Controleer de prijs bij", all: "Alle aanbiedingen", bestPrice: "Laagste waargenomen prijs",
    stock: "Op voorraad", unavailable: "Niet beschikbaar", availabilityUnknown: "Prijs of beschikbaarheid controleren", comparisonUnknown: "Prijsvergelijking te controleren", see: "Bekijk", note: "Prijzen zijn indicatief en kunnen veranderen bij de winkels. Aanbiedingen zijn gegroepeerd per barcode", commission: "Via deze links kan FILON een commissie ontvangen. Bevestig prijs, kosten en eindtotaal bij de winkel.",
  },
  en: {
    from: "from", at: "at", merchant: "merchant", merchants: "merchants",
    save: "Observed price spread", saveTail: "between the lowest and highest compared offer.",
    best: "Check the price at", all: "All offers", bestPrice: "Lowest observed price",
    stock: "In stock", unavailable: "Unavailable", availabilityUnknown: "Check price or availability", comparisonUnknown: "Price comparison to verify", see: "View", note: "Prices are indicative and may change at merchants. Offers are grouped by barcode", commission: "FILON may earn a commission through these links. Confirm the price, fees and final total with the merchant.",
  },
} as const;

export function ProductDetails({ p }: { p: Product }) {
  const { locale } = useLocale();
  const C = COPY[locale];
  const evidenceNow = useEvidenceNow(p.offers.map((offer) => offer.observed_at));
  const comparison = deriveProductComparison(p.offers, evidenceNow);
  const best = comparison?.best;
  const merchantsCount = comparison
    ? new Set(comparison.offers.map((offer) => offer.merchant.slug || offer.merchant.name)).size
    : 0;
  const merchantLabel = merchantsCount === 1 ? C.merchant : C.merchants;
  const saving = comparison && comparison.priceMax > comparison.priceMin
    ? comparison.priceMax - comparison.priceMin
    : null;
  const comparedIds = new Set(comparison?.offers.map((offer) => offer.id) ?? []);
  // Les offres comparables viennent d'abord dans leur ordre de prix prouvé.
  // Le reliquat legacy suit l'identifiant stable, jamais un prix non actuel.
  const offers = [
    ...(comparison?.offers ?? []),
    ...p.offers.filter((offer) => !comparedIds.has(offer.id)).sort((left, right) => left.id - right.id),
  ];
  // La réponse produit legacy ne porte pas la devise de son historique. Un
  // verdict historique favorable reste donc masqué sur cette surface.
  const verdict = p.verdict?.basis === "insufficient"
    && p.verdict.samples === 0
    && p.verdict.tracked_days === 0
    ? p.verdict
    : null;
  const bestAgeHours = best ? observationAgeHours(best.observed_at, evidenceNow) : null;
  const derivedSignals: DecisionSignal[] = [];
  if (comparison && best && bestAgeHours !== null) {
    derivedSignals.push(
      { key: "availability", status: "positive", in_stock: true },
      {
        key: "freshness",
        status: isFreshObservation(best.observed_at, evidenceNow) ? "positive" : "warning",
        age_hours: bestAgeHours,
        reason: isFreshObservation(best.observed_at, evidenceNow) ? "fresh" : "stale",
      },
    );
    if (merchantsCount >= 2) {
      derivedSignals.push({
        key: "comparison",
        status: "positive",
        merchants_count: merchantsCount,
        offers_count: comparison.offers.length,
        is_best_observed: true,
      });
    }
  }
  const decision = (() => {
    if (!p.decision) return null;
    const signals = p.decision.signals.filter((signal) =>
      !["price_moment", "availability", "freshness", "comparison", "comparison_strength"].includes(signal.key),
    );
    signals.push(...derivedSignals);
    const missing = new Set(p.decision.missing);
    missing.add("price_history");
    missing.add("history_currency");
    if (comparison === null || merchantsCount < 2) missing.add("comparison_scope");
    if (comparison === null) {
      missing.add("availability");
      missing.add("data_freshness");
    }
    return {
      ...p.decision,
      evidence_summary: undefined,
      recommendation_scope: p.decision.recommendation_scope === "meilleur_prix_observe"
        ? "a_verifier" as const
        : p.decision.recommendation_scope,
      signals,
      missing: [...missing],
      facts: {
        ...p.decision.facts,
        currency: comparison?.currency ?? null,
        merchants_compared: merchantsCount,
        offers_compared: comparison?.offers.length ?? 0,
        item_price: comparison?.priceMin ?? null,
        last_observed_at: best?.observed_at ?? null,
      },
    };
  })();

  return (
    <div>
      {p.brand && <span className="pg-brand">{p.brand}</span>}
      <h1 className="pg-title">{p.name}</h1>

      <div className="pg-headline">
        <span>
          {comparison ? (
            <><span className="pg-from">{C.from}</span><b className="pg-price">{money(comparison.priceMin, comparison.currency, locale)}</b></>
          ) : <b className="pg-price">{C.comparisonUnknown}</b>}
        </span>
        {merchantsCount > 0 && <span className="pg-count">{C.at} {merchantsCount} {merchantLabel}</span>}
      </div>

      {verdict && <Verdict v={verdict} />}
      <DecisionPanel decision={decision} />

      {saving != null && (
        <p className="pg-saving">{C.save} <b>{money(saving, comparison?.currency, locale)}</b> {C.saveTail}</p>
      )}

      {best?.link && isPurchasableOffer(best, evidenceNow) && (
        <a className="fx-btn primary" href={best.link} target="_blank" rel="noopener noreferrer sponsored" style={{ marginTop: 18 }}>
          {C.best} {best.merchant.name}
        </a>
      )}

      <h2 className="pg-sub">{C.all}</h2>
      <ul className="pg-offers">
        {offers.map((offer) => {
          const hasCurrentPriceEvidence = hasCurrentOfferEvidence(offer, evidenceNow);
          const canBuy = isPurchasableOffer(offer, evidenceNow);
          const stockState = currentStockState(offer, evidenceNow);
          const isBest = canBuy && best?.id === offer.id;
          return (
          <li key={offer.id} className={`pg-offer${isBest ? " best" : ""}`}>
            <span className="pg-offer-merchant">
              {offer.merchant.name}
              {offer.merchant.region && <span className="pg-region">{offer.merchant.region}</span>}
              {isBest && <span className="pg-badge">{C.bestPrice}</span>}
            </span>
            <span className="pg-offer-right">
              <b>{money(
                hasCurrentPriceEvidence ? offer.price : null,
                hasCurrentPriceEvidence ? offer.currency : null,
                locale,
              )}</b>
              <span className="pg-stock">{canBuy ? C.stock : stockState === false ? C.unavailable : C.availabilityUnknown}</span>
              {offer.link && canBuy && <a className="pg-go" href={offer.link} target="_blank" rel="noopener noreferrer sponsored">{C.see}</a>}
            </span>
          </li>
          );
        })}
      </ul>

      <p className="pg-note">{C.note} (EAN&nbsp;{p.ean}). {C.commission}</p>
    </div>
  );
}
