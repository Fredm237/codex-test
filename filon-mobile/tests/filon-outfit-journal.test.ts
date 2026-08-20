import { describe, expect, it } from "vitest";

import { mergeSavedOutfits, sanitizeSavedOutfits, type SavedOutfit } from "../lib/filon-outfit-journal";

const saved = (id: string, ids: number[]): SavedOutfit => ({ id, title: "Tenue travail", mode: "create", total: 120, confidenceScore: 80, pieces: ids.map((offerId) => ({ offerId, name: `Pièce ${offerId}`, price: 50, currency: "EUR", merchantName: "Partenaire", link: `https://example.com/${offerId}`, imageUrl: null, role: "base" })), createdAt: "2026-08-16T00:00:00.000Z" });

describe("Journal de tenues FILON", () => {
  it("remplace une tenue avec les mêmes offres au lieu de la dupliquer", () => {
    const result = mergeSavedOutfits([saved("old", [2, 1])], saved("new", [1, 2]));
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe("new");
  });

  it("rejette les journaux locaux qui ne respectent pas le contrat", () => {
    expect(sanitizeSavedOutfits([saved("ok", [1]), { id: "broken" }])).toHaveLength(1);
  });
});
