import { describe, expect, it } from "vitest";

import { buildOutfitRecommendation, getOutfitSolutionEvidenceExpiry, isOutfitSolutionCurrent, resolveIntelligenceFeatures } from "../lib/filon-intelligence";
import { buildCompleteRecommendation, filterCurrentOutfitStrategies } from "../lib/filon-complete";
import { resolveOutfitPublicMessage } from "../lib/filon-outfit-i18n";

const NOW = new Date("2026-08-29T12:00:00.000Z");
const FRESH = "2026-08-28T12:00:00.000Z";
const offer = (id: number, name: string, price: number, inStock: boolean | null = true, overrides: Partial<{ currency: string; observedAt: string | null; link: string; evidenceCurrent: boolean }> = {}) => ({ id, name, brand: null, category: "Mode", price, currency: overrides.currency ?? "EUR", inStock, observedAt: overrides.observedAt === undefined ? FRESH : overrides.observedAt, evidenceCurrent: overrides.evidenceCurrent ?? true, imageUrl: null, merchantName: "Partenaire", merchantSlug: "partner", link: overrides.link ?? `https://example.com/${id}` });

describe("FILON Intelligence Layer", () => {
  it("compose une solution uniquement avec des offres disponibles, sûres et sous budget", () => {
    const result = buildOutfitRecommendation({ request: "mariage", occasion: "wedding", season: "summer", budget: 220, declaredStyle: "classic" }, [offer(1, "Robe midi", 100), offer(2, "Escarpins cuir", 70), offer(3, "Blazer fluide", 45), offer(4, "Sac soirée", 30, false)], NOW);
    expect(result.status).toBe("solution");
    if (result.status === "solution") {
      expect(result.solution.total).toBeLessThanOrEqual(220);
      expect(result.solution.pieces.every((piece) => piece.offer.inStock === true)).toBe(true);
      expect(result.solution).toMatchObject({ currency: "EUR", styleScore: null, confidenceScore: null, confidence: "not_calibrated", measurementStatus: "not_calibrated" });
      expect(result.solution.scoreExplanation).toEqual({ code: "score.not_measured" });
      expect(resolveOutfitPublicMessage(result.solution.scoreExplanation, "fr")).toContain("Non mesuré");
      expect(result.trace.pipeline?.stages.find((stage) => stage.stage === "RESPONSE")).toMatchObject({ status: "completed" });
      expect(result.trace.pipeline?.stages.find((stage) => stage.stage === "CONFIDENCE")).toMatchObject({ status: "skipped" });
    }
  });

  it("s’abstient lorsque le catalogue ne permet pas une tenue identifiable", () => {
    const result = buildOutfitRecommendation({ request: "mariage", occasion: null, season: null, budget: 80, declaredStyle: null }, [offer(1, "Sac soirée", 45), offer(2, "Escarpins cuir", 60)], NOW);
    expect(result.status).toBe("abstain");
    if (result.status === "abstain") expect(result.reason).toEqual({ code: "recommendation.no_comparable_currency" });
    expect(result.trace.pipeline?.stages.find((stage) => stage.stage === "RESPONSE")).toMatchObject({ status: "abstained" });
  });

  it("n’inclut jamais une offre sans disponibilité confirmée", () => {
    const result = buildOutfitRecommendation({ request: "mariage", occasion: null, season: null, budget: 220, declaredStyle: null }, [offer(1, "Robe midi", 100, false), offer(2, "Escarpins cuir", 70), offer(3, "Robe alternative", 110)], NOW);
    expect(result.status).toBe("solution");
    if (result.status === "solution") expect(result.solution.pieces.map((piece) => piece.offer.id)).not.toContain(1);
  });

  it("complète une pièce possédée sans la faire passer pour une offre partenaire", () => {
    const result = buildCompleteRecommendation({ request: "compléter", occasion: "work", season: "spring", budget: 180, declaredStyle: null }, { label: "Mon blazer bleu marine", role: "structure" }, [offer(1, "Chemise blanche", 55), offer(2, "Mocassins cuir", 80), offer(3, "Pantalon droit", 45), offer(4, "Chemise oxford", 60)], NOW);
    expect(result.status).toBe("solution");
    if (result.status === "solution") {
      expect(result.strategies[0].solution.constraints[0]).toEqual({ code: "constraint.owned_piece", label: "Mon blazer bleu marine" });
      expect(resolveOutfitPublicMessage(result.strategies[0].solution.constraints[0], "nl")).toContain("Mon blazer bleu marine");
      expect(result.strategies[0].solution.pieces.map((piece) => piece.offer.name)).not.toContain("Mon blazer bleu marine");
      expect(result.strategies[0].solution).toMatchObject({ currency: "EUR", styleScore: null, confidenceScore: null, measurementStatus: "not_calibrated" });
    }
  });

  it("n’ajoute une stratégie Statement que pour une direction audacieuse déclarée et des alternatives vérifiables", () => {
    const result = buildCompleteRecommendation({ request: "compléter", occasion: "evening", season: "summer", budget: 300, declaredStyle: "bold" }, { label: "Mon blazer", role: "structure" }, [offer(1, "Chemise blanche", 55), offer(2, "Chemise noire", 65), offer(3, "Chemise imprimée", 75), offer(4, "Mocassins cuir", 80)], NOW);
    expect(result.status).toBe("solution");
    if (result.status === "solution") {
      expect(result.strategies.map((strategy) => strategy.id)).toContain("statement");
      expect(result.strategies.find((strategy) => strategy.id === "statement")?.description).toEqual({ code: "strategy.statement" });
    }
  });

  it("laisse les trois extensions désactivées par défaut", () => {
    expect(resolveIntelligenceFeatures({})).toEqual({ intelligence: false, outfitStudio: false, fashionExpert: false });
    expect(resolveIntelligenceFeatures({ EXPO_PUBLIC_FILON_INTELLIGENCE_ENABLED: "true", EXPO_PUBLIC_OUTFIT_STUDIO_ENABLED: "true", EXPO_PUBLIC_FASHION_EXPERT_ENABLED: "true" })).toEqual({ intelligence: true, outfitStudio: true, fashionExpert: true });
  });

  it.each([
    ["périmée", offer(1, "Robe midi", 100, true, { observedAt: "2026-08-20T00:00:00.000Z" })],
    ["datée dans le futur", offer(1, "Robe midi", 100, true, { observedAt: "2026-08-30T00:00:00.000Z" })],
    ["sans date", offer(1, "Robe midi", 100, true, { observedAt: null })],
    ["sans devise reconnue", offer(1, "Robe midi", 100, true, { currency: "XYZ" })],
    ["sans prix positif", offer(1, "Robe midi", 0)],
    ["sans lien sûr", offer(1, "Robe midi", 100, true, { link: "javascript:alert(1)" })],
    ["sans preuve de snapshot courant", offer(1, "Robe midi", 100, true, { evidenceCurrent: false })],
  ])("exclut une offre %s", (_label, invalidBase) => {
    const result = buildOutfitRecommendation({ request: "tenue", occasion: null, season: null, budget: null, declaredStyle: null }, [invalidBase, offer(2, "Escarpins cuir", 70)], NOW);
    expect(result.status).toBe("abstain");
  });

  it("exclut une offre legacy sans preuve explicite de snapshot courant", () => {
    const current = offer(1, "Robe midi", 100);
    const { evidenceCurrent: _omitted, ...legacy } = current;
    const result = buildOutfitRecommendation({ request: "tenue", occasion: null, season: null, budget: null, declaredStyle: null }, [legacy, offer(2, "Escarpins cuir", 70)], NOW);
    expect(result.status).toBe("abstain");
  });

  it("classe chaque offre Outfit une seule fois dans des agrégats exhaustifs", () => {
    const offers = [
      offer(1, "Robe midi", 100),
      offer(2, "Escarpins cuir", 70),
      offer(3, "Robe périmée", 80, true, { observedAt: "2026-08-20T00:00:00.000Z" }),
      offer(4, "Robe au lien dangereux", 60, true, { link: "javascript:alert(1)" }),
    ];
    const result = buildOutfitRecommendation({ request: "tenue", occasion: null, season: null, budget: null, declaredStyle: null }, offers, NOW);
    expect(result.trace).toMatchObject({ considered: 4, eligible: 2, excludedNonEligible: 1, excludedUnsafe: 1 });
    expect(result.trace.eligible + result.trace.excludedNonEligible + result.trace.excludedUnsafe).toBe(result.trace.considered);

    const completed = buildCompleteRecommendation({ request: "compléter", occasion: null, season: null, budget: null, declaredStyle: null }, { label: "Mon blazer", role: "structure" }, offers, NOW);
    expect(completed.trace).toMatchObject({ considered: 4, eligible: 2, excludedNonEligible: 1, excludedUnsafe: 1 });
    expect(completed.trace.eligible + completed.trace.excludedNonEligible + completed.trace.excludedUnsafe).toBe(completed.trace.considered);
  });

  it("ne compte pas comme éligible une offre qui dépasse seule le budget EUR", () => {
    const result = buildOutfitRecommendation(
      { request: "tenue", occasion: null, season: null, budget: 120, declaredStyle: null },
      [offer(1, "Robe hors budget", 150), offer(2, "Escarpins cuir", 70)],
      NOW,
    );
    expect(result.trace).toMatchObject({ considered: 2, eligible: 1, excludedNonEligible: 1, excludedUnsafe: 0 });
    expect(result.trace.eligible + result.trace.excludedNonEligible + result.trace.excludedUnsafe).toBe(result.trace.considered);
  });

  it("s’abstient plutôt que d’additionner plusieurs devises", () => {
    const result = buildOutfitRecommendation({ request: "tenue", occasion: null, season: null, budget: null, declaredStyle: null }, [offer(1, "Robe midi", 100, true, { currency: "EUR" }), offer(2, "Escarpins cuir", 70, true, { currency: "USD" })], NOW);
    expect(result.status).toBe("abstain");
  });

  it("traite un budget saisi comme une contrainte EUR sans conversion implicite", () => {
    const result = buildOutfitRecommendation({ request: "tenue", occasion: null, season: null, budget: 250, declaredStyle: null }, [offer(1, "Robe midi", 100, true, { currency: "CHF" }), offer(2, "Escarpins cuir", 70, true, { currency: "CHF" })], NOW);
    expect(result.status).toBe("abstain");
  });

  it("évite un premier choix trop cher lorsqu’une autre combinaison respecte le budget", () => {
    const result = buildOutfitRecommendation({ request: "tenue", occasion: null, season: null, budget: 180, declaredStyle: null }, [offer(1, "Robe premium", 170), offer(2, "Robe simple", 80), offer(3, "Escarpins cuir", 100)], NOW);
    expect(result.status).toBe("solution");
    if (result.status === "solution") expect(result.solution.pieces.map((piece) => piece.offer.id)).toEqual([2, 3]);
  });

  it("expire une proposition exactement avec sa preuve la plus ancienne", () => {
    const result = buildOutfitRecommendation({ request: "tenue", occasion: null, season: null, budget: null, declaredStyle: null }, [offer(1, "Robe midi", 100), offer(2, "Escarpins cuir", 70)], NOW);
    expect(result.status).toBe("solution");
    if (result.status === "solution") {
      expect(getOutfitSolutionEvidenceExpiry(result.solution)).toBe(Date.parse("2026-08-31T12:00:00.000Z"));
      expect(isOutfitSolutionCurrent(result.solution, new Date("2026-08-31T12:00:00.000Z"))).toBe(true);
      expect(isOutfitSolutionCurrent(result.solution, new Date("2026-08-31T12:00:00.001Z"))).toBe(false);
    }
  });

  it("applique les mêmes preuves actuelles et la mono-devise au mode Complete", () => {
    const result = buildCompleteRecommendation(
      { request: "compléter", occasion: null, season: null, budget: null, declaredStyle: null },
      { label: "Mon blazer", role: "structure" },
      [offer(1, "Chemise blanche", 55, true, { currency: "EUR" }), offer(2, "Mocassins cuir", 80, true, { currency: "USD" }), offer(3, "Chemise périmée", 50, true, { currency: "USD", observedAt: "2026-08-20T00:00:00.000Z" })],
      NOW,
    );
    expect(result.status).toBe("abstain");
    if (result.status === "abstain") expect(result.reason).toEqual({ code: "complete.insufficient_current_pieces" });
  });

  it("cherche aussi une combinaison Complete viable sous le budget avant de s’abstenir", () => {
    const result = buildCompleteRecommendation(
      { request: "compléter", occasion: null, season: null, budget: 180, declaredStyle: null },
      { label: "Mon blazer", role: "structure" },
      [offer(1, "Chemise premium", 170), offer(2, "Chemise simple", 80), offer(3, "Mocassins cuir", 100)],
      NOW,
    );
    expect(result.status).toBe("solution");
    if (result.status === "solution") expect(result.strategies[0].solution.pieces.map((piece) => piece.offer.id)).toEqual([2, 3]);
  });

  it("retire une stratégie Complete expirée sans mal étiqueter l’alternative encore actuelle", () => {
    const result = buildCompleteRecommendation(
      { request: "compléter", occasion: null, season: null, budget: null, declaredStyle: null },
      { label: "Mon blazer", role: "structure" },
      [offer(1, "Chemise ancienne", 55, true, { observedAt: "2026-08-27T13:00:00.000Z" }), offer(2, "Chemise actuelle", 60), offer(3, "Mocassins cuir", 80)],
      NOW,
    );
    expect(result.status).toBe("solution");
    if (result.status === "solution") {
      expect(filterCurrentOutfitStrategies(result.strategies, new Date("2026-08-30T14:00:00.000Z")).map((strategy) => strategy.id)).toEqual(["signature"]);
    }
  });
});
