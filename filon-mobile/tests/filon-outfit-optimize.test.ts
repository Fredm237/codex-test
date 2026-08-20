import { describe, expect, it } from "vitest";

import { optimizeSavedOutfit } from "../lib/filon-outfit-optimize";

const offer = (id: number, name: string, price: number, inStock = true) => ({ id, name, brand: null, category: "Mode", price, currency: "EUR", inStock, imageUrl: null, merchantName: "Partenaire", merchantSlug: "partner", link: `https://example.com/${id}` });
const outfit = { id: "outfit-1", title: "Tenue bureau", mode: "create" as const, total: 180, confidenceScore: 80, createdAt: "2026-08-16T00:00:00.000Z", pieces: [{ offerId: 1, name: "Chemise", price: 80, currency: "EUR", merchantName: "Ancien partenaire", link: "https://example.com/1", imageUrl: null, role: "base" as const }, { offerId: 2, name: "Mocassins", price: 100, currency: "EUR", merchantName: "Ancien partenaire", link: "https://example.com/2", imageUrl: null, role: "footwear" as const }] };

describe("Optimize de tenue FILON", () => {
  it("propose uniquement une offre actuelle, disponible et moins chère du même rôle", () => {
    const result = optimizeSavedOutfit(outfit, [offer(10, "Chemise coton", 50), offer(11, "Mocassins cuir", 120), offer(12, "Chemise indisponible", 20, false)]);
    expect(result.status).toBe("solution");
    if (result.status === "solution") expect(result).toMatchObject({ savings: 30, optimizedTotal: 150, replacements: [{ previous: { offerId: 1 }, next: { id: 10 } }] });
  });

  it("s’abstient lorsqu’aucune amélioration vérifiable n’existe", () => {
    expect(optimizeSavedOutfit(outfit, [offer(10, "Chemise premium", 100)])).toMatchObject({ status: "abstain" });
  });
});
