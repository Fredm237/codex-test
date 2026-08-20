import { describe, expect, it } from "vitest";

import { buildOutfitRecommendation } from "../lib/filon-intelligence";
import { buildCompleteRecommendation } from "../lib/filon-complete";

const offer = (id: number, name: string, price: number, inStock = true) => ({ id, name, brand: null, category: "Mode", price, currency: "EUR", inStock, imageUrl: null, merchantName: "Partenaire", merchantSlug: "partner", link: `https://example.com/${id}` });

describe("FILON Intelligence Layer", () => {
  it("compose une solution uniquement avec des offres disponibles, sûres et sous budget", () => {
    const result = buildOutfitRecommendation({ request: "mariage", occasion: "Mariage", season: "Été", budget: 220, declaredStyle: "Classique" }, [offer(1, "Robe midi", 100), offer(2, "Escarpins cuir", 70), offer(3, "Blazer fluide", 45), offer(4, "Sac soirée", 30, false)]);
    expect(result.status).toBe("solution");
    if (result.status === "solution") {
      expect(result.solution.total).toBeLessThanOrEqual(220);
      expect(result.solution.pieces.every((piece) => piece.offer.inStock === true)).toBe(true);
      expect(result.solution.scoreExplanation).toContain("commission");
      expect(result.trace.pipeline?.stages.find((stage) => stage.stage === "RESPONSE")).toMatchObject({ status: "completed" });
      expect(result.trace.pipeline?.stages.find((stage) => stage.stage === "CONFIDENCE")).toMatchObject({ status: "completed" });
    }
  });

  it("s’abstient lorsque le catalogue ne permet pas une tenue identifiable", () => {
    const result = buildOutfitRecommendation({ request: "mariage", occasion: null, season: null, budget: 80, declaredStyle: null }, [offer(1, "Sac soirée", 45), offer(2, "Escarpins cuir", 60)]);
    expect(result.status).toBe("abstain");
    expect(result.trace.pipeline?.stages.find((stage) => stage.stage === "RESPONSE")).toMatchObject({ status: "abstained" });
  });

  it("n’inclut jamais une offre sans disponibilité confirmée", () => {
    const result = buildOutfitRecommendation({ request: "mariage", occasion: null, season: null, budget: 220, declaredStyle: null }, [offer(1, "Robe midi", 100, false), offer(2, "Escarpins cuir", 70), offer(3, "Robe alternative", 110)]);
    expect(result.status).toBe("solution");
    if (result.status === "solution") expect(result.solution.pieces.map((piece) => piece.offer.id)).not.toContain(1);
  });

  it("complète une pièce possédée sans la faire passer pour une offre partenaire", () => {
    const result = buildCompleteRecommendation({ request: "compléter", occasion: "Travail", season: "Printemps", budget: 180, declaredStyle: null }, { label: "Mon blazer bleu marine", role: "structure" }, [offer(1, "Chemise blanche", 55), offer(2, "Mocassins cuir", 80), offer(3, "Pantalon droit", 45), offer(4, "Chemise oxford", 60)]);
    expect(result.status).toBe("solution");
    if (result.status === "solution") {
      expect(result.strategies[0].solution.constraints[0]).toContain("Mon blazer bleu marine");
      expect(result.strategies[0].solution.pieces.map((piece) => piece.offer.name)).not.toContain("Mon blazer bleu marine");
    }
  });

  it("n’ajoute une stratégie Statement que pour une direction audacieuse déclarée et des alternatives vérifiables", () => {
    const result = buildCompleteRecommendation({ request: "compléter", occasion: "Soirée", season: "Été", budget: 300, declaredStyle: "Audacieux" }, { label: "Mon blazer", role: "structure" }, [offer(1, "Chemise blanche", 55), offer(2, "Chemise noire", 65), offer(3, "Chemise imprimée", 75), offer(4, "Mocassins cuir", 80)]);
    expect(result.status).toBe("solution");
    if (result.status === "solution") expect(result.strategies.map((strategy) => strategy.id)).toContain("statement");
  });
});
