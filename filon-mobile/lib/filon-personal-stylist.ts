import { isFilonOfferActionable, type FilonOffer } from "./filon-api";
import type { OutfitRole } from "./filon-intelligence";
import type { OutfitOccasionCode } from "./filon-outfit-i18n";
import { isSafePartnerOfferUrl } from "./partner-offer";
import type { StyleDirectionId } from "./style-dna";
import { sanitizeWardrobe, type WardrobeItem } from "./filon-wardrobe";

export type StylistWeather = {
  location: string;
  observedAt: string;
  validFor: string;
  temperatureC: number;
  precipitation: "none" | "rain" | "snow" | "unknown";
  source: "trusted_provider" | "user_declared";
};

export type PersonalStylistBrief = {
  occasion: OutfitOccasionCode | null;
  occasionAt: string | null;
  location: string | null;
  style: StyleDirectionId | null;
  budget: number | null;
  requestedSize: string | null;
};

export type StylistCatalogueCandidate = {
  offer: FilonOffer;
  role: OutfitRole;
  roleEvidence: "product_ontology";
  size: string | null;
  sizeEvidence: "merchant_variant" | null;
};

export type StylistPiece =
  | { source: "wardrobe"; role: OutfitRole; wardrobeItemId: string; label: string; marginalCost: 0; provenance: "user_declared" }
  | { source: "catalogue"; role: OutfitRole; offerId: number; label: string; marginalCost: number; currency: string; size: string; provenance: "verified_offer" };

export type StylistLook = {
  pieces: StylistPiece[];
  shoppingTotal: number;
  currency: "EUR" | null;
  compatibilityScore: null;
  measurementStatus: "not_calibrated";
};

export type PersonalStylistDecision =
  | { status: "solution"; looks: StylistLook[]; usedOwnedFirst: true; unknowns: string[] }
  | { status: "abstain"; reason: string; unknowns: string[] };

const WEATHER_EVIDENCE_MAX_AGE_MS = 6 * 60 * 60 * 1000;
const WEATHER_TARGET_TOLERANCE_MS = 6 * 60 * 60 * 1000;
const ROLE_ORDER: OutfitRole[] = ["base", "structure", "footwear"];

function canonical(value: string | null) {
  return (value ?? "").trim().toLocaleLowerCase().replace(/\s+/g, " ");
}

function validTimestamp(value: string | null) {
  if (!value) return null;
  const timestamp = Date.parse(value);
  return Number.isFinite(timestamp) ? timestamp : null;
}

function weatherIsApplicable(brief: PersonalStylistBrief, weather: StylistWeather | null, now: number) {
  if (!weather || !canonical(brief.location) || !brief.occasionAt) return false;
  const observedAt = validTimestamp(weather.observedAt);
  const validFor = validTimestamp(weather.validFor);
  const occasionAt = validTimestamp(brief.occasionAt);
  return observedAt !== null
    && validFor !== null
    && occasionAt !== null
    && observedAt <= now
    && now - observedAt <= WEATHER_EVIDENCE_MAX_AGE_MS
    && Math.abs(validFor - occasionAt) <= WEATHER_TARGET_TOLERANCE_MS
    && canonical(weather.location) === canonical(brief.location)
    && (weather.source === "trusted_provider" || weather.source === "user_declared")
    && (weather.precipitation === "none" || weather.precipitation === "rain" || weather.precipitation === "snow" || weather.precipitation === "unknown")
    && Number.isFinite(weather.temperatureC)
    && weather.temperatureC >= -60
    && weather.temperatureC <= 60;
}

function requiredRoles(occasion: OutfitOccasionCode): OutfitRole[] {
  return occasion === "work" || occasion === "wedding"
    ? ["base", "structure", "footwear"]
    : ["base", "footwear"];
}

function catalogueEligible(candidate: StylistCatalogueCandidate, requestedSize: string, now: number) {
  return candidate.roleEvidence === "product_ontology"
    && candidate.sizeEvidence === "merchant_variant"
    && canonical(candidate.size) === canonical(requestedSize)
    && candidate.offer.currency === "EUR"
    && isFilonOfferActionable(candidate.offer, now)
    && isSafePartnerOfferUrl(candidate.offer.link);
}

function ownedPiece(item: WardrobeItem): StylistPiece {
  return {
    source: "wardrobe",
    role: item.role,
    wardrobeItemId: item.id,
    label: item.label,
    marginalCost: 0,
    provenance: "user_declared",
  };
}

function cataloguePiece(candidate: StylistCatalogueCandidate): StylistPiece {
  return {
    source: "catalogue",
    role: candidate.role,
    offerId: candidate.offer.id,
    label: candidate.offer.name,
    marginalCost: candidate.offer.price,
    currency: "EUR",
    size: candidate.size!,
    provenance: "verified_offer",
  };
}

function combinations(groups: StylistPiece[][], limit = 3): StylistPiece[][] {
  let result: StylistPiece[][] = [[]];
  for (const group of groups) {
    result = result.flatMap((current) => group.map((piece) => [...current, piece])).slice(0, limit);
  }
  return result;
}

/**
 * Produit au plus trois propositions. Les pièces possédées excluent les achats
 * du même rôle ; aucune compatibilité stylistique ou météo n'est inventée.
 */
export function buildPersonalStylistDecision(
  brief: PersonalStylistBrief,
  wardrobeInput: unknown,
  weather: StylistWeather | null,
  candidates: StylistCatalogueCandidate[],
  now: number | Date = Date.now(),
): PersonalStylistDecision {
  const reference = now instanceof Date ? now.getTime() : now;
  if (!brief.occasion) return { status: "abstain", reason: "occasion_unspecified", unknowns: ["occasion"] };
  if (!brief.style) return { status: "abstain", reason: "style_unspecified", unknowns: ["style"] };
  if (!weatherIsApplicable(brief, weather, reference)) return { status: "abstain", reason: "weather_unverified", unknowns: ["weather"] };
  if (weather!.precipitation !== "none" || weather!.temperatureC < 10 || weather!.temperatureC > 30) {
    return { status: "abstain", reason: "weather_garment_capability_unknown", unknowns: ["garment_weather_capability"] };
  }

  const wardrobe = sanitizeWardrobe(wardrobeInput);
  const roles = requiredRoles(brief.occasion);
  const ownedByRole = new Map<OutfitRole, WardrobeItem[]>();
  for (const role of ROLE_ORDER) ownedByRole.set(role, wardrobe.filter((item) => item.role === role));
  const missingRoles = roles.filter((role) => (ownedByRole.get(role) ?? []).length === 0);

  if (missingRoles.length > 0 && (brief.budget === null || !Number.isFinite(brief.budget) || brief.budget <= 0)) {
    return { status: "abstain", reason: "shopping_budget_unspecified", unknowns: ["budget"] };
  }
  if (missingRoles.length > 0 && !canonical(brief.requestedSize)) {
    return { status: "abstain", reason: "size_unspecified", unknowns: ["size"] };
  }

  const eligible = brief.requestedSize
    ? candidates.filter((candidate) => catalogueEligible(candidate, brief.requestedSize!, reference))
    : [];
  const groups: StylistPiece[][] = [];
  for (const role of roles) {
    const owned = (ownedByRole.get(role) ?? []).map(ownedPiece);
    if (owned.length > 0) {
      groups.push(owned.slice(0, 3));
      continue;
    }
    const additions = eligible.filter((candidate) => candidate.role === role).map(cataloguePiece);
    if (additions.length === 0) return { status: "abstain", reason: "required_role_unavailable", unknowns: [role] };
    groups.push(additions.slice(0, 3));
  }

  const looks = combinations(groups).map((pieces) => {
    const shoppingTotal = Math.round(pieces.reduce((total, piece) => total + piece.marginalCost, 0) * 100) / 100;
    return { pieces, shoppingTotal, currency: shoppingTotal > 0 ? "EUR" as const : null, compatibilityScore: null, measurementStatus: "not_calibrated" as const };
  }).filter((look) => brief.budget === null || look.shoppingTotal <= brief.budget);
  if (looks.length === 0) return { status: "abstain", reason: "budget_exceeded", unknowns: [] };

  return {
    status: "solution",
    looks,
    usedOwnedFirst: true,
    unknowns: ["style_compatibility_not_calibrated", "occasion_compatibility_not_calibrated"],
  };
}
