import { describe, expect, it } from "vitest";

import type { FilonOffer } from "../lib/filon-api";
import { buildPersonalStylistDecision, type PersonalStylistBrief, type StylistCatalogueCandidate, type StylistWeather } from "../lib/filon-personal-stylist";
import { createWardrobeItem } from "../lib/filon-wardrobe";

const NOW = new Date("2026-09-02T12:00:00.000Z");
const brief: PersonalStylistBrief = { occasion: "work", occasionAt: "2026-09-02T18:00:00.000Z", location: "Bruxelles", style: "classic", budget: 160, requestedSize: "M" };
const weather: StylistWeather = { location: "Bruxelles", observedAt: "2026-09-02T10:00:00.000Z", validFor: "2026-09-02T18:00:00.000Z", temperatureC: 18, precipitation: "none", source: "trusted_provider" };
const owned = (id: string, label: string, role: "base" | "structure" | "footwear") => createWardrobeItem({ label, role }, id, "2026-09-01T00:00:00.000Z")!;
const offer = (id: number, name: string, price: number, overrides: Partial<FilonOffer> = {}): FilonOffer => ({ id, name, brand: null, category: "Mode", price, currency: "EUR", inStock: true, observedAt: "2026-09-01T12:00:00.000Z", evidenceCurrent: true, imageUrl: null, merchantName: "Partenaire", merchantSlug: "partner", link: `https://example.com/${id}`, ...overrides });
const candidate = (id: number, role: "base" | "structure" | "footwear", price: number, overrides: Partial<StylistCatalogueCandidate> = {}): StylistCatalogueCandidate => ({ offer: offer(id, `${role}-${id}`, price), role, roleEvidence: "product_ontology", size: "M", sizeEvidence: "merchant_variant", ...overrides });

describe("Personal Stylist FILON", () => {
  it("utilise uniquement le dressing lorsqu’il couvre la tenue de travail", () => {
    const result = buildPersonalStylistDecision(brief, [owned("b", "Chemise", "base"), owned("s", "Blazer", "structure"), owned("f", "Derbies", "footwear")], weather, [candidate(1, "base", 50)], NOW);
    expect(result.status).toBe("solution");
    if (result.status === "solution") {
      expect(result.looks[0].pieces.every((piece) => piece.source === "wardrobe")).toBe(true);
      expect(result.looks[0]).toMatchObject({ shoppingTotal: 0, currency: null, compatibilityScore: null, measurementStatus: "not_calibrated" });
      expect(result.usedOwnedFirst).toBe(true);
    }
  });

  it("n’achète que le rôle absent avec une taille et une offre prouvées", () => {
    const result = buildPersonalStylistDecision(brief, [owned("b", "Chemise", "base"), owned("s", "Blazer", "structure")], weather, [candidate(1, "footwear", 80)], NOW);
    expect(result.status).toBe("solution");
    if (result.status === "solution") {
      expect(result.looks[0].pieces.filter((piece) => piece.source === "catalogue")).toEqual([
        expect.objectContaining({ offerId: 1, role: "footwear", size: "M", marginalCost: 80 }),
      ]);
    }
  });

  it("privilégie toutes les variantes possédées au lieu d’ajouter une offre du même rôle", () => {
    const result = buildPersonalStylistDecision(brief, [owned("b1", "Chemise", "base"), owned("b2", "Pull", "base"), owned("s", "Blazer", "structure"), owned("f", "Derbies", "footwear")], weather, [candidate(1, "base", 50)], NOW);
    expect(result.status).toBe("solution");
    if (result.status === "solution") {
      expect(result.looks).toHaveLength(2);
      expect(result.looks.flatMap((look) => look.pieces).every((piece) => piece.source === "wardrobe")).toBe(true);
    }
  });

  it.each([
    ["occasion", { ...brief, occasion: null }, weather, "occasion_unspecified"],
    ["style", { ...brief, style: null }, weather, "style_unspecified"],
    ["météo absente", brief, null, "weather_unverified"],
    ["météo d’une autre ville", brief, { ...weather, location: "Paris" }, "weather_unverified"],
    ["pluie sans capacité vêtement", brief, { ...weather, precipitation: "rain" as const }, "weather_garment_capability_unknown"],
  ])("s’abstient lorsque la contrainte %s n’est pas prouvée", (_label, inputBrief, inputWeather, reason) => {
    expect(buildPersonalStylistDecision(inputBrief, [], inputWeather, [], NOW)).toMatchObject({ status: "abstain", reason });
  });

  it("refuse une taille non vérifiée et une offre périmée", () => {
    const wardrobe = [owned("b", "Chemise", "base"), owned("s", "Blazer", "structure")];
    const wrongSize = candidate(1, "footwear", 70, { size: "L" });
    const stale = candidate(2, "footwear", 70, { offer: offer(2, "Derbies", 70, { observedAt: "2026-08-20T00:00:00.000Z" }) });
    expect(buildPersonalStylistDecision(brief, wardrobe, weather, [wrongSize, stale], NOW)).toMatchObject({ status: "abstain", reason: "required_role_unavailable" });
  });

  it("s’abstient quand les ajouts vérifiés dépassent le budget", () => {
    const result = buildPersonalStylistDecision({ ...brief, budget: 60 }, [owned("b", "Chemise", "base"), owned("s", "Blazer", "structure")], weather, [candidate(1, "footwear", 80)], NOW);
    expect(result).toMatchObject({ status: "abstain", reason: "budget_exceeded" });
  });
});
