import type { IntelligenceConfidence, OutfitIntent, OutfitPiece, OutfitRole } from "./filon-intelligence";
import type { IntelligenceRelationType } from "./filon-intelligence-contract";

export type FashionRelationType = Extract<IntelligenceRelationType, "COMPLEMENTS" | "RECOMMENDED_WITH" | "SUITABLE_FOR" | "SUITABLE_IN_SEASON">;
export type FashionRelation = {
  type: FashionRelationType;
  fromOfferId: number;
  toOfferId: number | null;
  confidence: IntelligenceConfidence;
  provenance: "catalogue_partner" | "filon_inference";
  reason: "ROLE_COMPLEMENT" | "DECLARED_OCCASION" | "DECLARED_SEASON";
  score: number;
  justification: string;
  updatedAt: string;
};

export type FashionCritiqueFinding = {
  code: "MISSING_STRUCTURE" | "MISSING_ACCESSORY" | "CONTEXT_UNSPECIFIED" | "SEASON_UNSPECIFIED" | "LOW_RELATION_COVERAGE";
  severity: "info" | "advisory";
};

export type FashionCritique = {
  verdict: "approved" | "refine";
  findings: FashionCritiqueFinding[];
  scorePenalty: number;
};

/**
 * Représentation parallèle des relations de style. Les offres partenaires
 * restent intactes : chaque relation est explicitement qualifiée d’inférence.
 */
export function buildFashionRelations(pieces: OutfitPiece[], intent: OutfitIntent): FashionRelation[] {
  const relations: FashionRelation[] = [];
  const updatedAt = new Date().toISOString();
  for (let index = 0; index < pieces.length - 1; index += 1) {
    relations.push({
      type: index === 0 ? "COMPLEMENTS" : "RECOMMENDED_WITH",
      fromOfferId: pieces[index].offer.id,
      toOfferId: pieces[index + 1].offer.id,
      confidence: "medium",
      provenance: "filon_inference",
      reason: "ROLE_COMPLEMENT",
      score: 0.72,
      justification: "Les rôles de tenue sont complémentaires dans cette composition.",
      updatedAt,
    });
  }
  if (intent.occasion && pieces[0]) {
    relations.push({ type: "SUITABLE_FOR", fromOfferId: pieces[0].offer.id, toOfferId: null, confidence: "medium", provenance: "filon_inference", reason: "DECLARED_OCCASION", score: 0.6, justification: "Contexte déclaré par l’utilisateur ; adéquation à confirmer par les attributs catalogue.", updatedAt });
  }
  if (intent.season && pieces[0]) {
    relations.push({ type: "SUITABLE_IN_SEASON", fromOfferId: pieces[0].offer.id, toOfferId: null, confidence: "medium", provenance: "filon_inference", reason: "DECLARED_SEASON", score: 0.6, justification: "Saison déclarée par l’utilisateur ; adéquation à confirmer par les attributs catalogue.", updatedAt });
  }
  return relations;
}

/**
 * Le critique ne transforme jamais une hypothèse en fait marchand. Il pointe
 * les lacunes restantes afin de rendre le score et l’explication calibrables.
 */
export function critiqueFashionComposition(pieces: OutfitPiece[], intent: OutfitIntent, relations: FashionRelation[], ownedRole?: OutfitRole): FashionCritique {
  const roles = new Set(pieces.map((piece) => piece.role));
  if (ownedRole) roles.add(ownedRole);
  const findings: FashionCritiqueFinding[] = [];
  if (!roles.has("structure") && (intent.occasion?.toLocaleLowerCase().includes("mariage") || intent.occasion?.toLocaleLowerCase().includes("travail"))) {
    findings.push({ code: "MISSING_STRUCTURE", severity: "advisory" });
  }
  if (!roles.has("accessory")) findings.push({ code: "MISSING_ACCESSORY", severity: "info" });
  if (!intent.occasion) findings.push({ code: "CONTEXT_UNSPECIFIED", severity: "info" });
  if (!intent.season) findings.push({ code: "SEASON_UNSPECIFIED", severity: "info" });
  if (relations.filter((relation) => relation.toOfferId !== null).length < Math.max(1, pieces.length - 1)) {
    findings.push({ code: "LOW_RELATION_COVERAGE", severity: "advisory" });
  }
  const scorePenalty = findings.reduce((total, finding) => total + (finding.severity === "advisory" ? 8 : 3), 0);
  return { verdict: findings.some((finding) => finding.severity === "advisory") ? "refine" : "approved", findings, scorePenalty };
}
