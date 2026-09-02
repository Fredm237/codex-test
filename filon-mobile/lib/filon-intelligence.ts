import { FILON_OFFER_MAX_AGE_HOURS, isFilonOfferActionable, normalizeFilonObservedAt, type FilonOffer } from "./filon-api";
import { buildFashionRelations, critiqueFashionComposition, type FashionCritique, type FashionRelation } from "./filon-fashion-graph";
import type { OutfitOccasionCode, OutfitPublicMessage, OutfitSeasonCode, OutfitStyleCode } from "./filon-outfit-i18n";
import { createV3PipelineTrace, updateV3PipelineStage, type V3PipelineStage, type V3PipelineTrace } from "./filon-v3-contracts";
import { isSafePartnerOfferUrl } from "./partner-offer";

export type IntelligenceMeasurementStatus = "not_calibrated";
export type OutfitRole = "base" | "structure" | "footwear" | "accessory";
export type OutfitIntent = {
  request: string;
  occasion: OutfitOccasionCode | null;
  season: OutfitSeasonCode | null;
  budget: number | null;
  declaredStyle: OutfitStyleCode | null;
};

export type OutfitPiece = {
  role: OutfitRole;
  offer: FilonOffer;
  confidence: IntelligenceMeasurementStatus;
  provenance: "catalogue_partner" | "filon_inference";
  explanation: OutfitPublicMessage;
};

export type OutfitSolution = {
  pieces: OutfitPiece[];
  total: number;
  currency: string;
  styleScore: null;
  confidenceScore: null;
  confidence: IntelligenceMeasurementStatus;
  measurementStatus: IntelligenceMeasurementStatus;
  scoreExplanation: OutfitPublicMessage;
  constraints: OutfitPublicMessage[];
  relations: FashionRelation[];
  critique: FashionCritique;
};

export type OutfitRecommendation =
  | { status: "solution"; solution: OutfitSolution; trace: RecommendationTrace }
  | { status: "abstain"; reason: OutfitPublicMessage; trace: RecommendationTrace };

export type RecommendationTrace = {
  intent: OutfitIntent;
  considered: number;
  eligible: number;
  /** Offres au lien sûr mais non actionnables ou incompatibles avec le budget EUR. */
  excludedNonEligible: number;
  excludedUnsafe: number;
  pipeline?: V3PipelineTrace;
};

function readFlag(value: string | undefined, fallback: boolean) {
  if (value === undefined || value === "") return fallback;
  return value.toLowerCase() === "true";
}

/**
 * Les trois flags isolent entièrement l’extension. Ils restent fermés tant
 * qu’une configuration de build ne les active pas explicitement tous les trois.
 */
export function resolveIntelligenceFeatures(environment: Record<string, string | undefined> = {}) {
  return {
    intelligence: readFlag(environment.EXPO_PUBLIC_FILON_INTELLIGENCE_ENABLED, false),
    outfitStudio: readFlag(environment.EXPO_PUBLIC_OUTFIT_STUDIO_ENABLED, false),
    fashionExpert: readFlag(environment.EXPO_PUBLIC_FASHION_EXPERT_ENABLED, false),
  };
}

export const intelligenceFeatures = resolveIntelligenceFeatures({
  EXPO_PUBLIC_FILON_INTELLIGENCE_ENABLED: typeof process === "undefined" ? undefined : process.env.EXPO_PUBLIC_FILON_INTELLIGENCE_ENABLED,
  EXPO_PUBLIC_OUTFIT_STUDIO_ENABLED: typeof process === "undefined" ? undefined : process.env.EXPO_PUBLIC_OUTFIT_STUDIO_ENABLED,
  EXPO_PUBLIC_FASHION_EXPERT_ENABLED: typeof process === "undefined" ? undefined : process.env.EXPO_PUBLIC_FASHION_EXPERT_ENABLED,
});

export function isOutfitStudioEnabled() {
  return intelligenceFeatures.intelligence && intelligenceFeatures.outfitStudio && intelligenceFeatures.fashionExpert;
}

export function getOutfitSolutionEvidenceExpiry(solution: OutfitSolution) {
  const observations = solution.pieces.map((piece) => normalizeFilonObservedAt(piece.offer.observedAt));
  if (observations.length === 0 || observations.some((observedAt) => observedAt === null)) return null;
  return Math.min(...(observations as string[]).map((observedAt) => Date.parse(observedAt) + FILON_OFFER_MAX_AGE_HOURS * 60 * 60 * 1000));
}

export function isOutfitSolutionCurrent(solution: OutfitSolution, now: number | Date = Date.now()) {
  const currency = solution.currency;
  const observedTotal = solution.pieces.reduce((total, piece) => total + piece.offer.price, 0);
  return solution.pieces.length > 0
    && solution.pieces.every((piece) => piece.offer.currency === currency && isFilonOfferActionable(piece.offer, now) && isSafePartnerOfferUrl(piece.offer.link))
    && Number.isFinite(solution.total)
    && Math.abs(observedTotal - solution.total) <= 0.005;
}

function normalized(value: string | null | undefined) {
  return (value ?? "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase();
}

function roleFromCatalogue(offer: FilonOffer): OutfitRole | null {
  const text = normalized(`${offer.name} ${offer.category ?? ""}`);
  if (/\b(chaussures?|shoes?|sneakers?|baskets?|boots?|bottines?|escarpins?|mocassins?|sandals?|sandales?)\b/.test(text)) return "footwear";
  if (/\b(blazers?|vestes?|jackets?|manteaux?|coats?|surchemises?|vestons?|gilets?)\b/.test(text)) return "structure";
  if (/\b(sacs?|bags?|ceintures?|belts?|echarpes?|scarves|bijoux|jewellery|chapeaux|hats?|montres?|watches)\b/.test(text)) return "accessory";
  if (/\b(robes?|dresses?|chemises?|shirts?|pantalons?|trousers?|jeans?|jupes?|skirts?|tops?|pulls?|sweaters?|t-shirts?|tshirts?|combinaisons?)\b/.test(text)) return "base";
  return null;
}

function pickFirst(offers: FilonOffer[], role: OutfitRole, used: Set<number>, remainingBudget: number | null) {
  return offers.find((offer) => roleFromCatalogue(offer) === role && !used.has(offer.id) && (remainingBudget === null || offer.price <= remainingBudget));
}

function isEligibleOffer(offer: FilonOffer, budget: number | null, now: number | Date) {
  return isFilonOfferActionable(offer, now)
    && isSafePartnerOfferUrl(offer.link)
    // Le budget saisi dans l’interface est explicitement libellé en euros.
    // Une offre qui le dépasse à elle seule ne doit pas gonfler le compteur
    // « éligibles », même si la composition l’écarterait ensuite.
    && (budget === null || (offer.currency === "EUR" && offer.price <= budget));
}

export function summarizeOutfitOfferEligibility(offers: FilonOffer[], budget: number | null, now: number | Date = Date.now()) {
  const eligibleOffers: FilonOffer[] = [];
  let excludedNonEligible = 0;
  let excludedUnsafe = 0;
  for (const offer of offers) {
    // Une offre appartient à une seule catégorie. Le lien est contrôlé en
    // premier pour qu'une URL dangereuse ne soit jamais recomptée ailleurs.
    if (!isSafePartnerOfferUrl(offer.link)) {
      excludedUnsafe += 1;
    } else if (isEligibleOffer(offer, budget, now)) {
      eligibleOffers.push(offer);
    } else {
      excludedNonEligible += 1;
    }
  }
  return { eligibleOffers, excludedNonEligible, excludedUnsafe };
}

function groupByCurrency(offers: FilonOffer[]) {
  const groups = new Map<string, FilonOffer[]>();
  for (const offer of offers) {
    const group = groups.get(offer.currency) ?? [];
    group.push(offer);
    groups.set(offer.currency, group);
  }
  return [...groups.values()];
}

function findBaseFootwearPair(offers: FilonOffer[], budget: number | null): [FilonOffer, FilonOffer] | null {
  const bases = offers.filter((offer) => roleFromCatalogue(offer) === "base");
  const footwear = offers.filter((offer) => roleFromCatalogue(offer) === "footwear");
  for (const base of bases) {
    for (const shoes of footwear) {
      if (base.id !== shoes.id && (budget === null || base.price + shoes.price <= budget)) return [base, shoes];
    }
  }
  return null;
}

function selectComposableCurrencyGroup(offers: FilonOffer[], budget: number | null) {
  for (const group of groupByCurrency(offers)) {
    const pair = findBaseFootwearPair(group, budget);
    if (pair) return { offers: group, pair };
  }
  return null;
}

function setPipelineStage(trace: RecommendationTrace, stage: V3PipelineStage, status: "completed" | "skipped" | "abstained", reason: string) {
  if (trace.pipeline) trace.pipeline = updateV3PipelineStage(trace.pipeline, stage, status, reason);
}

/**
 * Compose une première solution documentée uniquement à partir des offres
 * partenariales. Cette fonction ne fabrique ni prix, ni stock, ni attribut.
 */
export function buildOutfitRecommendation(intent: OutfitIntent, offers: FilonOffer[], now: number | Date = Date.now()): OutfitRecommendation {
  const eligibility = summarizeOutfitOfferEligibility(offers, intent.budget, now);
  const eligible = eligibility.eligibleOffers;
  const trace: RecommendationTrace = {
    intent,
    considered: offers.length,
    eligible: eligible.length,
    excludedNonEligible: eligibility.excludedNonEligible,
    excludedUnsafe: eligibility.excludedUnsafe,
    pipeline: createV3PipelineTrace(`fashion-${Date.now()}-${offers.length}`),
  };
  setPipelineStage(trace, "INTENT", "completed", "Brief déclaré par l’utilisateur.");
  setPipelineStage(trace, "CONSTRAINTS", "completed", "Budget, style, saison et occasion conservés séparément.");
  setPipelineStage(trace, "RETRIEVAL", "completed", `${offers.length} offre(s) reçues du Core.`);
  setPipelineStage(trace, "FILTERING", eligible.length > 0 ? "completed" : "abstained", `${eligible.length} offre(s) disponibles avec lien sûr.`);

  if (eligible.length === 0) {
    const reason: OutfitPublicMessage = { code: "recommendation.no_eligible_offers" };
    setPipelineStage(trace, "RESPONSE", "abstained", reason.code);
    return { status: "abstain", reason, trace };
  }

  const comparable = selectComposableCurrencyGroup(eligible, intent.budget);
  if (!comparable) {
    const reason: OutfitPublicMessage = { code: "recommendation.no_comparable_currency" };
    setPipelineStage(trace, "UNDERSTANDING", "abstained", "Les offres actuelles ne permettent pas une composition mono-devise identifiable.");
    setPipelineStage(trace, "COMPOSITION", "abstained", reason.code);
    setPipelineStage(trace, "RESPONSE", "abstained", reason.code);
    return { status: "abstain", reason, trace };
  }

  const currency = comparable.offers[0].currency;
  const used = new Set<number>();
  const [base, footwear] = comparable.pair;
  used.add(base.id);
  used.add(footwear.id);

  const selected = [base, footwear];
  const afterFootwear = intent.budget === null ? null : intent.budget - selected.reduce((sum, offer) => sum + offer.price, 0);
  const structure = pickFirst(comparable.offers, "structure", used, afterFootwear);
  if (structure) {
    selected.push(structure);
    used.add(structure.id);
  }
  const afterStructure = intent.budget === null ? null : intent.budget - selected.reduce((sum, offer) => sum + offer.price, 0);
  const accessory = pickFirst(comparable.offers, "accessory", used, afterStructure);
  if (accessory) selected.push(accessory);

  const pieces: OutfitPiece[] = selected.map((offer) => {
    const role = roleFromCatalogue(offer);
    return {
      role: role ?? "accessory",
      offer,
      confidence: "not_calibrated",
      provenance: role ? "filon_inference" : "catalogue_partner",
      explanation: { code: role ? "piece.role_inferred" : "piece.role_unconfirmed" },
    };
  });
  const total = pieces.reduce((sum, piece) => sum + piece.offer.price, 0);
  if (intent.budget !== null && total > intent.budget) {
    const reason: OutfitPublicMessage = { code: "recommendation.budget_exceeded" };
    setPipelineStage(trace, "COMPOSITION", "abstained", reason.code);
    setPipelineStage(trace, "RESPONSE", "abstained", reason.code);
    return { status: "abstain", reason, trace };
  }

  const relations = buildFashionRelations(pieces, intent);
  const critique = critiqueFashionComposition(pieces, intent, relations);
  const constraints = [
    { code: "constraint.catalogue_current_offers" },
    { code: "constraint.single_currency", currency },
    intent.budget === null ? { code: "constraint.budget_unspecified" } : { code: "constraint.budget_respected", amount: intent.budget, currency: "EUR" },
    intent.occasion ? { code: "constraint.context_declared", occasion: intent.occasion } : { code: "constraint.context_unspecified" },
    intent.season ? { code: "constraint.season_declared", season: intent.season } : { code: "constraint.season_unspecified" },
  ] satisfies OutfitPublicMessage[];
  setPipelineStage(trace, "UNDERSTANDING", "completed", "Rôles inférés uniquement depuis le nom et la catégorie fournis par le Core.");
  setPipelineStage(trace, "COMPOSITION", "completed", `${pieces.length} pièce(s) composées sous contraintes.`);
  setPipelineStage(trace, "CRITIC", "completed", `${critique.findings.length} constat(s) explicitement listés.`);
  setPipelineStage(trace, "RANKING", "skipped", "Aucun Style Score n’est publié sans méthode calibrée et validée.");
  setPipelineStage(trace, "OPTIMIZATION", "skipped", "L’optimisation intervient uniquement sur une tenue sauvegardée.");
  setPipelineStage(trace, "CONFIDENCE", "skipped", "La confiance quantitative reste non calibrée.");
  setPipelineStage(trace, "RESPONSE", "completed", "Solution présentée à partir des données retenues, avec contraintes et limites.");
  return {
    status: "solution",
    solution: {
      pieces,
      total,
      currency,
      styleScore: null,
      confidenceScore: null,
      confidence: "not_calibrated",
      measurementStatus: "not_calibrated",
      scoreExplanation: { code: "score.not_measured" },
      constraints,
      relations,
      critique,
    },
    trace,
  };
}
