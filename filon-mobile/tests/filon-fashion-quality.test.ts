import { describe, expect, it } from "vitest";

import { evaluateFashionBenchmark, normalizeFashionErrorCode } from "../lib/filon-fashion-quality";
import { mergeFashionCorrection, sanitizeFashionCorrections } from "../lib/filon-fashion-corrections";
import type { OutfitRecommendation } from "../lib/filon-intelligence";

const solution: OutfitRecommendation = { status: "solution", trace: { intent: { request: "mariage", occasion: "wedding", season: "summer", budget: 200, declaredStyle: null }, considered: 4, eligible: 4, excludedNonEligible: 0, excludedUnsafe: 0 }, solution: { pieces: [], total: 100, currency: "EUR", styleScore: null, confidenceScore: null, confidence: "not_calibrated", measurementStatus: "not_calibrated", scoreExplanation: { code: "score.not_measured" }, constraints: [{ code: "constraint.budget_respected", amount: 200, currency: "EUR" }], relations: [], critique: { verdict: "approved", findings: [], scorePenalty: 0 } } };

describe("Qualité Fashion FILON", () => {
  it("évalue un benchmark explicite sans inventer de cas catalogue", () => {
    expect(evaluateFashionBenchmark({ id: "case-1", label: "Budget", expectedStatus: "solution", requiredConstraint: "constraint.budget_respected" }, solution)).toMatchObject({ passed: true, reasons: [] });
  });

  it("refuse de valider un seuil lorsque les scores ne sont pas calibrés", () => {
    expect(evaluateFashionBenchmark({ id: "case-score", label: "Score", expectedStatus: "solution", minStyleScore: 80, minConfidenceScore: 70 }, solution)).toMatchObject({ passed: false });
  });

  it("borne les codes d’erreurs et déduplique les corrections locales", () => {
    expect(normalizeFashionErrorCode("HALLUCINATION")).toBe("HALLUCINATION");
    expect(normalizeFashionErrorCode("UNKNOWN_CODE")).toBeNull();
    const candidate = { id: "1", recommendationKey: "outfit", code: "WRONG_STYLE" as const, note: "Trop formel", createdAt: "2026-08-16T00:00:00.000Z" };
    expect(sanitizeFashionCorrections([candidate, { code: "INVALID" }])).toEqual([candidate]);
    expect(mergeFashionCorrection([candidate], { ...candidate, id: "2" })).toHaveLength(1);
  });
});
