import type { OutfitRecommendation } from "./filon-intelligence";
import type { OutfitPublicMessageCode } from "./filon-outfit-i18n";

export type FashionErrorCode = "WRONG_CATEGORY" | "WRONG_COLOR" | "WRONG_STYLE" | "WRONG_CONTEXT" | "WRONG_PROPORTION" | "WRONG_SEASON" | "WRONG_PRICE" | "WRONG_COMPATIBILITY" | "LOW_CONFIDENCE" | "HALLUCINATION" | "POOR_PERSONALIZATION";

export type FashionBenchmarkCase = {
  id: string;
  label: string;
  expectedStatus: "solution" | "abstain";
  minStyleScore?: number;
  minConfidenceScore?: number;
  requiredConstraint?: OutfitPublicMessageCode;
};

export type FashionBenchmarkResult = { caseId: string; passed: boolean; reasons: string[] };

/** Évalue une recommandation avec des critères déclarés, sans jeu d’exemples ni verdict marchand inventé. */
export function evaluateFashionBenchmark(benchmark: FashionBenchmarkCase, recommendation: OutfitRecommendation): FashionBenchmarkResult {
  const reasons: string[] = [];
  if (recommendation.status !== benchmark.expectedStatus) reasons.push(`Statut attendu : ${benchmark.expectedStatus}.`);
  if (recommendation.status === "solution") {
    if (benchmark.minStyleScore !== undefined) reasons.push("Style Score non mesuré : aucun seuil ne peut être validé.");
    if (benchmark.minConfidenceScore !== undefined) reasons.push("Confidence Score non mesuré : aucun seuil ne peut être validé.");
    if (benchmark.requiredConstraint && !recommendation.solution.constraints.some((constraint) => constraint.code === benchmark.requiredConstraint)) reasons.push("Contrainte de référence absente.");
  }
  return { caseId: benchmark.id, passed: reasons.length === 0, reasons };
}

export function normalizeFashionErrorCode(value: unknown): FashionErrorCode | null {
  const codes: FashionErrorCode[] = ["WRONG_CATEGORY", "WRONG_COLOR", "WRONG_STYLE", "WRONG_CONTEXT", "WRONG_PROPORTION", "WRONG_SEASON", "WRONG_PRICE", "WRONG_COMPATIBILITY", "LOW_CONFIDENCE", "HALLUCINATION", "POOR_PERSONALIZATION"];
  return typeof value === "string" && codes.includes(value as FashionErrorCode) ? value as FashionErrorCode : null;
}
