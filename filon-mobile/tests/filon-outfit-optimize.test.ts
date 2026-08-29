import { describe, expect, it } from "vitest";

import { getOutfitOptimizationEvidenceExpiry, isOutfitOptimizationCurrent, optimizeSavedOutfit } from "../lib/filon-outfit-optimize";

const NOW = new Date("2026-08-29T12:00:00.000Z");
const offer = (id: number, name: string, price: number, inStock = true, currency = "EUR", observedAt: string | null = "2026-08-28T12:00:00.000Z", evidenceCurrent = true) => ({ id, name, brand: null, category: "Mode", price, currency, inStock, observedAt, evidenceCurrent, imageUrl: null, merchantName: "Partenaire", merchantSlug: "partner", link: `https://example.com/${id}` });
const outfit = { id: "outfit-1", title: "Tenue bureau", mode: "create" as const, total: 180, currency: "EUR", confidenceScore: null, measurementStatus: "not_calibrated" as const, createdAt: "2026-08-16T00:00:00.000Z", pieces: [{ offerId: 1, name: "Chemise", price: 80, currency: "EUR", merchantName: "Ancien partenaire", link: "https://example.com/1", imageUrl: null, role: "base" as const }, { offerId: 2, name: "Mocassins", price: 100, currency: "EUR", merchantName: "Ancien partenaire", link: "https://example.com/2", imageUrl: null, role: "footwear" as const }] };

describe("Optimize de tenue FILON", () => {
  it("propose uniquement une offre actuelle, disponible et moins chère du même rôle", () => {
    const result = optimizeSavedOutfit(outfit, [offer(10, "Chemise coton", 50), offer(11, "Mocassins cuir", 120), offer(12, "Chemise indisponible", 20, false)], NOW);
    expect(result.status).toBe("solution");
    if (result.status === "solution") {
      expect(result).toMatchObject({ savings: 30, optimizedTotal: 150, currency: "EUR", replacements: [{ previous: { offerId: 1 }, next: { id: 10 } }] });
      expect(result.constraints).toEqual([{ code: "constraint.optimization_current_offers" }, { code: "constraint.saved_price_historical" }, { code: "constraint.unknown_costs_excluded" }]);
    }
  });

  it("s’abstient lorsqu’aucune amélioration vérifiable n’existe", () => {
    expect(optimizeSavedOutfit(outfit, [offer(10, "Chemise premium", 100)], NOW)).toMatchObject({ status: "abstain", reason: { code: "optimization.no_documented_alternative" } });
  });

  it("ignore les alternatives périmées, futures ou dans une autre devise", () => {
    const candidates = [
      offer(10, "Chemise périmée", 20, true, "EUR", "2026-08-20T00:00:00.000Z"),
      offer(11, "Chemise future", 20, true, "EUR", "2026-08-30T00:00:00.000Z"),
      offer(12, "Chemise dollars", 20, true, "USD"),
    ];
    expect(optimizeSavedOutfit(outfit, candidates, NOW)).toMatchObject({ status: "abstain" });
  });

  it("ignore une alternative sans preuve explicite de snapshot courant", () => {
    expect(optimizeSavedOutfit(outfit, [offer(10, "Chemise coton", 50, true, "EUR", "2026-08-28T12:00:00.000Z", false)], NOW)).toMatchObject({ status: "abstain" });
  });

  it("dégrade une ancienne tenue sans devise de total au lieu de supposer EUR", () => {
    expect(optimizeSavedOutfit({ ...outfit, currency: null }, [offer(10, "Chemise coton", 50)], NOW)).toMatchObject({ status: "abstain", reason: { code: "optimization.invalid_snapshot" } });
  });

  it("refuse un instantané local dont le total ou les prix sont incohérents", () => {
    expect(optimizeSavedOutfit({ ...outfit, total: 999 }, [offer(10, "Chemise coton", 50)], NOW)).toMatchObject({ status: "abstain" });
    const malformed = { ...outfit, pieces: [{ ...outfit.pieces[0], price: "80" }, outfit.pieces[1]] };
    expect(optimizeSavedOutfit(malformed as unknown as typeof outfit, [offer(10, "Chemise coton", 50)], NOW)).toMatchObject({ status: "abstain" });
  });

  it("ne réutilise jamais la même offre actuelle pour deux pièces sauvegardées", () => {
    const twoBases = { ...outfit, total: 160, pieces: [outfit.pieces[0], { ...outfit.pieces[0], offerId: 3, name: "Chemise bis" }] };
    const result = optimizeSavedOutfit(twoBases, [offer(10, "Chemise coton", 50)], NOW);
    expect(result.status).toBe("solution");
    if (result.status === "solution") expect(result.replacements).toHaveLength(1);
  });

  it("expire aussi une optimisation lorsque sa preuve actuelle dépasse 72 heures", () => {
    const result = optimizeSavedOutfit(outfit, [offer(10, "Chemise coton", 50)], NOW);
    expect(result.status).toBe("solution");
    if (result.status === "solution") {
      expect(getOutfitOptimizationEvidenceExpiry(result)).toBe(Date.parse("2026-08-31T12:00:00.000Z"));
      expect(isOutfitOptimizationCurrent(result, new Date("2026-08-31T12:00:00.000Z"))).toBe(true);
      expect(isOutfitOptimizationCurrent(result, new Date("2026-08-31T12:00:00.001Z"))).toBe(false);
    }
  });
});
