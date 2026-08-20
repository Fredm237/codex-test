import type { FilonOffer } from "./filon-api";
import { buildFashionRelations, critiqueFashionComposition } from "./filon-fashion-graph";
import type { IntelligenceConfidence, OutfitIntent, OutfitPiece, OutfitRole, OutfitSolution, RecommendationTrace } from "./filon-intelligence";
import { isSafePartnerOfferUrl } from "./partner-offer";

export type OwnedPiece = { label: string; role: OutfitRole };
export type OutfitStrategyId = "safe" | "signature" | "statement";
export type OutfitStrategy = { id: OutfitStrategyId; label: string; description: string; solution: OutfitSolution };
export type CompleteRecommendation =
  | { status: "solution"; ownedPiece: OwnedPiece; strategies: OutfitStrategy[]; trace: RecommendationTrace }
  | { status: "abstain"; ownedPiece: OwnedPiece; reason: string; trace: RecommendationTrace };

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
  return { role, offer, confidence: role === "accessory" && !roleFromCatalogue(offer) ? "low" : "medium", provenance: "filon_inference", explanation: "Rôle interprété à partir des données fournies par le catalogue partenaire." };
}

function emptyTrace(intent: OutfitIntent, offers: FilonOffer[]): RecommendationTrace {
  return { intent, considered: offers.length, eligible: offers.filter((offer) => offer.inStock === true && isSafePartnerOfferUrl(offer.link)).length, excludedUnavailable: offers.filter((offer) => offer.inStock !== true).length, excludedUnsafe: offers.filter((offer) => !isSafePartnerOfferUrl(offer.link)).length };
}

function buildStrategy(intent: OutfitIntent, ownedPiece: OwnedPiece, eligible: FilonOffer[], pickOffset: number, id: OutfitStrategyId): OutfitStrategy | null {
  const used = new Set<number>();
  const chosen: FilonOffer[] = [];
  const needed: OutfitRole[] = [];
  if (ownedPiece.role !== "base") needed.push("base");
  if (ownedPiece.role !== "footwear") needed.push("footwear");
  if (ownedPiece.role !== "structure") needed.push("structure");
  const primaryRole = needed[0];
  for (const role of needed) {
    const choices = eligible.filter((offer) => roleFromCatalogue(offer) === role && !used.has(offer.id));
    const candidate = choices[role === primaryRole ? pickOffset : 0];
    if (!candidate && (role === "base" || role === "footwear")) return null;
    if (candidate) { chosen.push(candidate); used.add(candidate.id); }
  }
  const total = chosen.reduce((sum, offer) => sum + offer.price, 0);
  if (intent.budget !== null && total > intent.budget) return null;
  const pieces = chosen.map(asPiece);
  const relations = buildFashionRelations(pieces, intent);
  const critique = critiqueFashionComposition(pieces, intent, relations, ownedPiece.role);
  const styleScore = Math.max(0, Math.min(100, 78 + Math.min(12, pieces.length * 4) - critique.scorePenalty));
  const confidenceScore = Math.max(0, Math.min(100, 72 + Math.min(14, pieces.length * 5) - critique.scorePenalty));
  const confidence: IntelligenceConfidence = confidenceScore >= 80 ? "high" : confidenceScore >= 60 ? "medium" : "low";
  const solution: OutfitSolution = {
    pieces,
    total,
    styleScore,
    confidenceScore,
    confidence,
    scoreExplanation: "Score reproductible fondé sur les compléments effectivement disponibles, le budget déclaré, la pièce possédée comme contrainte utilisateur et la critique finale — jamais sur la commission.",
    constraints: ["Pièce possédée déclarée par l’utilisateur : " + ownedPiece.label, "Offres partenaires disponibles uniquement", intent.budget === null ? "Budget non précisé" : `Budget d’achat respecté : ${intent.budget.toFixed(2)} €`],
    relations,
    critique,
  };
  const label = id === "safe" ? "Safe" : id === "signature" ? "Signature" : "Statement";
  const description = id === "safe" ? "La solution la plus directe autour de votre pièce." : id === "signature" ? "Une alternative construite avec une autre pièce du même rôle, lorsque le catalogue le permet." : "Une troisième variation réservée à une direction audacieuse déclarée ; son caractère reste limité aux signaux réellement disponibles.";
  return { id, label, description, solution };
}

/** Compose autour d’une pièce possédée, qui reste une déclaration utilisateur et n’est jamais transformée en offre marchande. */
export function buildCompleteRecommendation(intent: OutfitIntent, ownedPiece: OwnedPiece, offers: FilonOffer[]): CompleteRecommendation {
  const trace = emptyTrace(intent, offers);
  const eligible = offers.filter((offer) => offer.inStock === true && isSafePartnerOfferUrl(offer.link));
  const safe = buildStrategy(intent, ownedPiece, eligible, 0, "safe");
  if (!safe) return { status: "abstain", ownedPiece, reason: "FILON ne trouve pas suffisamment de pièces disponibles pour compléter votre pièce tout en respectant les contraintes déclarées.", trace };
  const signature = buildStrategy(intent, ownedPiece, eligible, 1, "signature");
  const boldDirection = normalized(intent.declaredStyle).includes("audac") || normalized(intent.declaredStyle).includes("bold") || normalized(intent.declaredStyle).includes("gedurfd");
  const statement = boldDirection ? buildStrategy(intent, ownedPiece, eligible, 2, "statement") : null;
  return { status: "solution", ownedPiece, strategies: [safe, signature, statement].filter((strategy): strategy is OutfitStrategy => strategy !== null), trace };
}
