import type { FilonOffer } from "./filon-api";
import { buildFashionRelations, critiqueFashionComposition } from "./filon-fashion-graph";
import { isOutfitSolutionCurrent, summarizeOutfitOfferEligibility, type OutfitIntent, type OutfitPiece, type OutfitRole, type OutfitSolution, type RecommendationTrace } from "./filon-intelligence";
import type { OutfitPublicMessage } from "./filon-outfit-i18n";

export type OwnedPiece = { label: string; role: OutfitRole };
export type OutfitStrategyId = "safe" | "signature" | "statement";
export type OutfitStrategy = { id: OutfitStrategyId; label: string; description: OutfitPublicMessage; solution: OutfitSolution };
export type CompleteRecommendation =
  | { status: "solution"; ownedPiece: OwnedPiece; strategies: OutfitStrategy[]; trace: RecommendationTrace }
  | { status: "abstain"; ownedPiece: OwnedPiece; reason: OutfitPublicMessage; trace: RecommendationTrace };

export function filterCurrentOutfitStrategies(strategies: OutfitStrategy[], now: number | Date = Date.now()) {
  return strategies.filter((strategy) => isOutfitSolutionCurrent(strategy.solution, now));
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

function asPiece(offer: FilonOffer): OutfitPiece {
  const role = roleFromCatalogue(offer) ?? "accessory";
  return { role, offer, confidence: role === "accessory" && !roleFromCatalogue(offer) ? "low" : "medium", provenance: "filon_inference", explanation: { code: "piece.role_inferred" } };
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

function emptyTrace(intent: OutfitIntent, offers: FilonOffer[], now: number | Date): RecommendationTrace {
  const eligibility = summarizeOutfitOfferEligibility(offers, intent.budget, now);
  return {
    intent,
    considered: offers.length,
    eligible: eligibility.eligibleOffers.length,
    excludedNonEligible: eligibility.excludedNonEligible,
    excludedUnsafe: eligibility.excludedUnsafe,
  };
}

function buildViableCompositions(intent: OutfitIntent, ownedPiece: OwnedPiece, eligible: FilonOffer[]) {
  const requiredRoles: OutfitRole[] = [];
  if (ownedPiece.role !== "base") requiredRoles.push("base");
  if (ownedPiece.role !== "footwear") requiredRoles.push("footwear");
  let combinations: FilonOffer[][] = [[]];
  for (const role of requiredRoles) {
    const choices = eligible.filter((offer) => roleFromCatalogue(offer) === role);
    if (choices.length === 0) return [];
    combinations = combinations.flatMap((chosen) => choices.filter((offer) => !chosen.some((piece) => piece.id === offer.id)).map((offer) => [...chosen, offer]));
  }
  return combinations.reduce<FilonOffer[][]>((viable, required) => {
    const requiredTotal = required.reduce((sum, offer) => sum + offer.price, 0);
    if (intent.budget !== null && requiredTotal > intent.budget) return viable;
    if (ownedPiece.role === "structure") {
      viable.push(required);
      return viable;
    }
    const remaining = intent.budget === null ? null : intent.budget - requiredTotal;
    const structure = eligible.find((offer) => roleFromCatalogue(offer) === "structure" && !required.some((piece) => piece.id === offer.id) && (remaining === null || offer.price <= remaining));
    viable.push(structure ? [...required, structure] : required);
    return viable;
  }, []);
}

function buildStrategy(intent: OutfitIntent, ownedPiece: OwnedPiece, eligible: FilonOffer[], pickOffset: number, id: OutfitStrategyId): OutfitStrategy | null {
  const chosen = buildViableCompositions(intent, ownedPiece, eligible)[pickOffset];
  if (!chosen || chosen.length === 0) return null;
  const total = chosen.reduce((sum, offer) => sum + offer.price, 0);
  const pieces = chosen.map(asPiece);
  const relations = buildFashionRelations(pieces, intent);
  const critique = critiqueFashionComposition(pieces, intent, relations, ownedPiece.role);
  const currency = eligible[0].currency;
  const solution: OutfitSolution = {
    pieces,
    total,
    currency,
    styleScore: null,
    confidenceScore: null,
    confidence: "not_calibrated",
    measurementStatus: "not_calibrated",
    scoreExplanation: { code: "score.not_measured" },
    constraints: [{ code: "constraint.owned_piece", label: ownedPiece.label }, { code: "constraint.catalogue_current_offers" }, { code: "constraint.single_currency", currency }, intent.budget === null ? { code: "constraint.budget_unspecified" } : { code: "constraint.budget_respected", amount: intent.budget, currency: "EUR" }],
    relations,
    critique,
  };
  const label = id === "safe" ? "Safe" : id === "signature" ? "Signature" : "Statement";
  const description: OutfitPublicMessage = { code: id === "safe" ? "strategy.safe" : id === "signature" ? "strategy.signature" : "strategy.statement" };
  return { id, label, description, solution };
}

/** Compose autour d’une pièce possédée, qui reste une déclaration utilisateur et n’est jamais transformée en offre marchande. */
export function buildCompleteRecommendation(intent: OutfitIntent, ownedPiece: OwnedPiece, offers: FilonOffer[], now: number | Date = Date.now()): CompleteRecommendation {
  const trace = emptyTrace(intent, offers, now);
  const eligible = summarizeOutfitOfferEligibility(offers, intent.budget, now).eligibleOffers;
  let comparable: FilonOffer[] | null = null;
  let safe: OutfitStrategy | null = null;
  for (const currencyGroup of groupByCurrency(eligible)) {
    const candidate = buildStrategy(intent, ownedPiece, currencyGroup, 0, "safe");
    if (candidate) {
      comparable = currencyGroup;
      safe = candidate;
      break;
    }
  }
  if (!safe || !comparable) return { status: "abstain", ownedPiece, reason: { code: "complete.insufficient_current_pieces" }, trace };
  const signature = buildStrategy(intent, ownedPiece, comparable, 1, "signature");
  const boldDirection = intent.declaredStyle === "bold";
  const statement = boldDirection ? buildStrategy(intent, ownedPiece, comparable, 2, "statement") : null;
  return { status: "solution", ownedPiece, strategies: [safe, signature, statement].filter((strategy): strategy is OutfitStrategy => strategy !== null), trace };
}
