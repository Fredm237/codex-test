import { describe, expect, it } from "vitest";

import { buildFashionRelations, critiqueFashionComposition } from "../lib/filon-fashion-graph";

const offer = (id: number) => ({ id, name: `Pièce ${id}`, brand: null, category: "Mode", price: 50, currency: "EUR", inStock: true as const, imageUrl: null, merchantName: "Partenaire", merchantSlug: "partner", link: `https://example.com/${id}` });
const piece = (id: number, role: "base" | "structure" | "footwear" | "accessory") => ({ role, offer: offer(id), confidence: "medium" as const, provenance: "filon_inference" as const, explanation: { code: "piece.role_inferred" as const } });

describe("Fashion graph et critique", () => {
  it("établit des relations explicables sans altérer les offres", () => {
    const pieces = [piece(1, "base"), piece(2, "footwear"), piece(3, "structure")];
    const relations = buildFashionRelations(pieces, { request: "mariage", occasion: "wedding", season: "summer", budget: 200, declaredStyle: null });
    expect(relations).toHaveLength(4);
    expect(relations[0]).toMatchObject({ type: "COMPLEMENTS", fromOfferId: 1, toOfferId: 2, provenance: "filon_inference" });
  });

  it("signale une tenue contextuelle qui manque de structure au lieu de la présenter comme parfaite", () => {
    const pieces = [piece(1, "base"), piece(2, "footwear")];
    const relations = buildFashionRelations(pieces, { request: "mariage", occasion: "wedding", season: "summer", budget: 200, declaredStyle: null });
    const critique = critiqueFashionComposition(pieces, { request: "mariage", occasion: "wedding", season: "summer", budget: 200, declaredStyle: null }, relations);
    expect(critique.verdict).toBe("refine");
    expect(critique.findings.map((finding) => finding.code)).toContain("MISSING_STRUCTURE");
  });
});
