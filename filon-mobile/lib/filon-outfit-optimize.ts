import { FILON_OFFER_MAX_AGE_HOURS, isFilonOfferActionable, normalizeFilonCurrency, normalizeFilonObservedAt, type FilonOffer } from "./filon-api";
import type { OutfitRole } from "./filon-intelligence";
import type { OutfitPublicMessage } from "./filon-outfit-i18n";
import type { SavedOutfit, SavedOutfitPiece } from "./filon-outfit-journal";
import { isSafePartnerOfferUrl } from "./partner-offer";

export type OutfitOptimizationReplacement = { previous: SavedOutfitPiece; next: FilonOffer; saving: number };
export type OutfitOptimization =
  | { status: "solution"; sourceOutfitId: string; checkedOffers: number; replacements: OutfitOptimizationReplacement[]; originalTotal: number; optimizedTotal: number; savings: number; currency: string; constraints: OutfitPublicMessage[] }
  | { status: "abstain"; sourceOutfitId: string; checkedOffers: number; reason: OutfitPublicMessage };

export function getOutfitOptimizationEvidenceExpiry(optimization: OutfitOptimization) {
  if (optimization.status !== "solution" || optimization.replacements.length === 0) return null;
  const observations = optimization.replacements.map((replacement) => normalizeFilonObservedAt(replacement.next.observedAt));
  if (observations.some((observedAt) => observedAt === null)) return null;
  return Math.min(...(observations as string[]).map((observedAt) => Date.parse(observedAt) + FILON_OFFER_MAX_AGE_HOURS * 60 * 60 * 1000));
}

export function isOutfitOptimizationCurrent(optimization: OutfitOptimization, now: number | Date = Date.now()) {
  return optimization.status === "solution"
    && optimization.replacements.length > 0
    && optimization.replacements.every((replacement) => replacement.next.currency === optimization.currency && isFilonOfferActionable(replacement.next, now) && isSafePartnerOfferUrl(replacement.next.link));
}

function normalized(value: string | null | undefined) {
  return (value ?? "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase();
}

function roleFromOffer(offer: FilonOffer): OutfitRole | null {
  const text = normalized(`${offer.name} ${offer.category ?? ""}`);
  if (/\b(chaussures?|shoes?|sneakers?|baskets?|boots?|bottines?|escarpins?|mocassins?|sandals?|sandales?)\b/.test(text)) return "footwear";
  if (/\b(blazers?|vestes?|jackets?|manteaux?|coats?|surchemises?|vestons?|gilets?)\b/.test(text)) return "structure";
  if (/\b(sacs?|bags?|ceintures?|belts?|echarpes?|scarves|bijoux|jewellery|chapeaux|hats?|montres?|watches)\b/.test(text)) return "accessory";
  if (/\b(robes?|dresses?|chemises?|shirts?|pantalons?|trousers?|jeans?|jupes?|skirts?|tops?|pulls?|sweaters?|t-shirts?|tshirts?|combinaisons?)\b/.test(text)) return "base";
  return null;
}

/** Compare uniquement des instantanés locaux avec des offres catalogue à relevé récent ; aucune disponibilité passée n’est supposée. */
export function optimizeSavedOutfit(outfit: SavedOutfit, offers: FilonOffer[], now: number | Date = Date.now()): OutfitOptimization {
  const currency = normalizeFilonCurrency(outfit.currency);
  const observedTotal = outfit.pieces.reduce((total, piece) => total + (typeof piece.price === "number" && Number.isFinite(piece.price) ? piece.price : Number.NaN), 0);
  const uniquePieceIds = new Set(outfit.pieces.map((piece) => piece.offerId));
  if (currency === null || typeof outfit.total !== "number" || !Number.isFinite(outfit.total) || outfit.total <= 0 || outfit.pieces.length === 0 || uniquePieceIds.size !== outfit.pieces.length || outfit.pieces.some((piece) => !Number.isInteger(piece.offerId) || piece.offerId <= 0 || typeof piece.price !== "number" || !Number.isFinite(piece.price) || piece.price <= 0 || normalizeFilonCurrency(piece.currency) !== currency) || !Number.isFinite(observedTotal) || Math.abs(observedTotal - outfit.total) > 0.005) {
    return { status: "abstain", sourceOutfitId: outfit.id, checkedOffers: offers.length, reason: { code: "optimization.invalid_snapshot" } };
  }
  const eligible = offers.filter((offer) => offer.currency === currency && isFilonOfferActionable(offer, now) && isSafePartnerOfferUrl(offer.link));
  const replacements: OutfitOptimizationReplacement[] = [];
  const usedOfferIds = new Set<number>();
  for (const previous of outfit.pieces) {
    const next = eligible.filter((offer) => !usedOfferIds.has(offer.id) && roleFromOffer(offer) === previous.role && offer.price < previous.price).sort((left, right) => left.price - right.price)[0];
    if (next) {
      usedOfferIds.add(next.id);
      replacements.push({ previous, next, saving: previous.price - next.price });
    }
  }
  if (replacements.length === 0) return { status: "abstain", sourceOutfitId: outfit.id, checkedOffers: offers.length, reason: { code: "optimization.no_documented_alternative" } };
  const savings = replacements.reduce((total, replacement) => total + replacement.saving, 0);
  return {
    status: "solution",
    sourceOutfitId: outfit.id,
    checkedOffers: offers.length,
    replacements,
    originalTotal: outfit.total,
    optimizedTotal: Math.max(0, outfit.total - savings),
    savings,
    currency,
    constraints: [{ code: "constraint.optimization_current_offers" }, { code: "constraint.saved_price_historical" }, { code: "constraint.unknown_costs_excluded" }],
  };
}
