import type { FilonOffer } from "@/lib/filon-api";
import { buildFashionRelations, critiqueFashionComposition, type FashionCritique, type FashionRelation } from "./filon-fashion-graph";
import { createV3PipelineTrace, updateV3PipelineStage, type V3PipelineStage, type V3PipelineTrace } from "./filon-v3-contracts";
import { isSafePartnerOfferUrl } from "./partner-offer";

export type IntelligenceConfidence = "high" | "medium" | "low";
export type OutfitRole = "base" | "structure" | "footwear" | "accessory";
export type OutfitIntent = {
  request: string;
  occasion: string | null;
  season: string | null;
  budget: number | null;
  declaredStyle: string | null;
};

export type OutfitPiece = {
  role: OutfitRole;
  offer: FilonOffer;
  confidence: IntelligenceConfidence;
  provenance: "catalogue_partner" | "filon_inference";
  explanation: string;
};

export type OutfitSolution = {
  pieces: OutfitPiece[];
  total: number;
  styleScore: number;
  confidenceScore: number;
  confidence: IntelligenceConfidence;
  scoreExplanation: string;
  constraints: string[];
  relations: FashionRelation[];
  critique: FashionCritique;
};

export type OutfitRecommendation =
  | { status: "solution"; solution: OutfitSolution; trace: RecommendationTrace }
  | { status: "abstain"; reason: string; trace: RecommendationTrace };

export type RecommendationTrace = {
  intent: OutfitIntent;
  considered: number;
  eligible: number;
  excludedUnavailable: number;
  excludedUnsafe: number;
  pipeline?: V3PipelineTrace;
};

function readFlag(name: string, fallback: boolean) {
  const value = typeof process === "undefined" ? undefined : process.env?.[name];
  if (value === undefined || value === "") return fallback;
  return value.toLowerCase() === "true";
}

/**
 * Les trois flags isolent entièrement l’extension. Les valeurs par défaut
 * activent le MVP, tandis qu’une configuration de build peut le masquer sans
 * changer le Core FILON.
 */
export const intelligenceFeatures = {
  intelligence: readFlag("EXPO_PUBLIC_FILON_INTELLIGENCE_ENABLED", true),
  outfitStudio: readFlag("EXPO_PUBLIC_OUTFIT_STUDIO_ENABLED", true),
  fashionExpert: readFlag("EXPO_PUBLIC_FASHION_EXPERT_ENABLED", true),
};

export function isOutfitStudioEnabled() {
  return intelligenceFeatures.intelligence && intelligenceFeatures.outfitStudio && intelligenceFeatures.fashionExpert;
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

function scoreForComposition(pieces: OutfitPiece[], budget: number | null) {
  const roles = new Set(pieces.map((piece) => piece.role)).size;
  const total = pieces.reduce((sum, piece) => sum + piece.offer.price, 0);
  const allVerifiedAvailable = pieces.every((piece) => piece.offer.inStock === true);
  const withinBudget = budget === null || total <= budget;
  const coverage = pieces.length >= 3 ? 36 : 24;
  const roleCoverage = Math.min(20, roles * 7);
  const availability = allVerifiedAvailable ? 24 : 0;
  const budgetFit = withinBudget ? 15 : 0;
  const verifiedLinks = pieces.every((piece) => isSafePartnerOfferUrl(piece.offer.link)) ? 5 : 0;
  return Math.min(100, coverage + roleCoverage + availability + budgetFit + verifiedLinks);
}

function confidenceForComposition(pieces: OutfitPiece[], declaredStyle: string | null) {
  const catalogueEvidence = pieces.every((piece) => piece.offer.inStock === true && isSafePartnerOfferUrl(piece.offer.link));
  const inferredRoles = pieces.filter((piece) => piece.provenance === "filon_inference").length;
  const score = Math.max(0, Math.min(100, (catalogueEvidence ? 72 : 42) + Math.min(18, pieces.length * 5) - inferredRoles * 5 + (declaredStyle ? 4 : 0)));
  return { score, level: score >= 80 ? "high" as const : score >= 60 ? "medium" as const : "low" as const };
}

function pickFirst(offers: FilonOffer[], role: OutfitRole, used: Set<number>, remainingBudget: number | null) {
  return offers.find((offer) => roleFromCatalogue(offer) === role && !used.has(offer.id) && (remainingBudget === null || offer.price <= remainingBudget));
}

function setPipelineStage(trace: RecommendationTrace, stage: V3PipelineStage, status: "completed" | "skipped" | "abstained", reason: string) {
  if (trace.pipeline) trace.pipeline = updateV3PipelineStage(trace.pipeline, stage, status, reason);
}

/**
 * Compose une première solution vérifiable uniquement à partir des offres
 * partenariales. Cette fonction ne fabrique ni prix, ni stock, ni attribut.
 */
export function buildOutfitRecommendation(intent: OutfitIntent, offers: FilonOffer[]): OutfitRecommendation {
  const unsafe = offers.filter((offer) => !isSafePartnerOfferUrl(offer.link));
  const unavailable = offers.filter((offer) => offer.inStock !== true);
  const eligible = offers.filter((offer) => offer.inStock === true && isSafePartnerOfferUrl(offer.link));
  const trace: RecommendationTrace = {
    intent,
    considered: offers.length,
    eligible: eligible.length,
    excludedUnavailable: unavailable.length,
    excludedUnsafe: unsafe.length,
    pipeline: createV3PipelineTrace(`fashion-${Date.now()}-${offers.length}`),
  };
  setPipelineStage(trace, "INTENT", "completed", "Brief déclaré par l’utilisateur.");
  setPipelineStage(trace, "CONSTRAINTS", "completed", "Budget, style, saison et occasion conservés séparément.");
  setPipelineStage(trace, "RETRIEVAL", "completed", `${offers.length} offre(s) reçues du Core.`);
  setPipelineStage(trace, "FILTERING", eligible.length > 0 ? "completed" : "abstained", `${eligible.length} offre(s) disponibles avec lien sûr.`);

  if (eligible.length === 0) {
    const reason = "Aucune offre partenaire disponible et vérifiable ne permet de composer une proposition responsable.";
    setPipelineStage(trace, "RESPONSE", "abstained", reason);
    return { status: "abstain", reason, trace };
  }

  const used = new Set<number>();
  const base = pickFirst(eligible, "base", used, intent.budget);
  if (base) used.add(base.id);
  const afterBase = intent.budget === null || !base ? intent.budget : intent.budget - base.price;
  const footwear = pickFirst(eligible, "footwear", used, afterBase);
  if (footwear) used.add(footwear.id);

  if (!base || !footwear) {
    const reason = "FILON a trouvé des offres, mais pas assez de pièces clairement identifiables et disponibles pour former une tenue fiable. Essayez une demande plus précise ou assouplissez votre budget.";
    setPipelineStage(trace, "UNDERSTANDING", "abstained", "Les rôles base et chaussures ne sont pas tous identifiables avec les informations Core disponibles.");
    setPipelineStage(trace, "COMPOSITION", "abstained", reason);
    setPipelineStage(trace, "RESPONSE", "abstained", reason);
    return { status: "abstain", reason, trace };
  }

  const selected = [base, footwear];
  const afterFootwear = intent.budget === null ? null : intent.budget - selected.reduce((sum, offer) => sum + offer.price, 0);
  const structure = pickFirst(eligible, "structure", used, afterFootwear);
  if (structure) {
    selected.push(structure);
    used.add(structure.id);
  }
  const afterStructure = intent.budget === null ? null : intent.budget - selected.reduce((sum, offer) => sum + offer.price, 0);
  const accessory = pickFirst(eligible, "accessory", used, afterStructure);
  if (accessory) selected.push(accessory);

  const pieces: OutfitPiece[] = selected.map((offer) => {
    const role = roleFromCatalogue(offer);
    return {
      role: role ?? "accessory",
      offer,
      confidence: role ? "medium" : "low",
      provenance: role ? "filon_inference" : "catalogue_partner",
      explanation: role
        ? "Rôle interprété à partir du nom et de la catégorie fournis par le catalogue partenaire."
        : "Offre partenaire disponible ; son rôle dans la tenue reste à confirmer.",
    };
  });
  const total = pieces.reduce((sum, piece) => sum + piece.offer.price, 0);
  if (intent.budget !== null && total > intent.budget) {
    const reason = "Les pièces disponibles dépassent votre budget total. FILON préfère ne pas présenter une solution qui ne respecte pas votre contrainte.";
    setPipelineStage(trace, "COMPOSITION", "abstained", reason);
    setPipelineStage(trace, "RESPONSE", "abstained", reason);
    return { status: "abstain", reason, trace };
  }

  const relations = buildFashionRelations(pieces, intent);
  const critique = critiqueFashionComposition(pieces, intent, relations);
  const styleScore = Math.max(0, scoreForComposition(pieces, intent.budget) - critique.scorePenalty);
  const baseConfidence = confidenceForComposition(pieces, intent.declaredStyle);
  const confidenceScore = Math.max(0, baseConfidence.score - critique.scorePenalty);
  const confidence = { score: confidenceScore, level: confidenceScore >= 80 ? "high" as const : confidenceScore >= 60 ? "medium" as const : "low" as const };
  const constraints = [
    "Offres partenaires disponibles uniquement",
    intent.budget === null ? "Budget non précisé" : `Budget total respecté : ${intent.budget.toFixed(2)} €`,
    intent.occasion ? `Contexte déclaré : ${intent.occasion}` : "Contexte à préciser",
    intent.season ? `Saison déclarée : ${intent.season}` : "Saison à préciser",
  ];
  setPipelineStage(trace, "UNDERSTANDING", "completed", "Rôles inférés uniquement depuis le nom et la catégorie fournis par le Core.");
  setPipelineStage(trace, "COMPOSITION", "completed", `${pieces.length} pièce(s) composées sous contraintes.`);
  setPipelineStage(trace, "CRITIC", "completed", `${critique.findings.length} constat(s) explicitement listés.`);
  setPipelineStage(trace, "RANKING", "completed", "Style Score calculé sans signal commercial caché.");
  setPipelineStage(trace, "OPTIMIZATION", "skipped", "L’optimisation intervient uniquement sur une tenue sauvegardée.");
  setPipelineStage(trace, "CONFIDENCE", "completed", "Confidence Score séparé du Style Score.");
  setPipelineStage(trace, "RESPONSE", "completed", "Solution vérifiable présentée avec contraintes et limites.");
  return {
    status: "solution",
    solution: {
      pieces,
      total,
      styleScore,
      confidenceScore: confidence.score,
      confidence: confidence.level,
      scoreExplanation: "Score reproductible fondé sur la couverture de la tenue, la diversité des rôles, la disponibilité confirmée, le respect du budget, la validité des liens partenaires et la critique finale — jamais sur la commission.",
      constraints,
      relations,
      critique,
    },
    trace,
  };
}
