import { describe, expect, it } from "vitest";

import { mergeSavedOutfits, sanitizeSavedOutfits, type SavedOutfit } from "../lib/filon-outfit-journal";

const saved = (id: string, ids: number[]): SavedOutfit => ({ id, title: "Tenue travail", mode: "create", total: ids.length * 50, currency: "EUR", confidenceScore: null, measurementStatus: "not_calibrated", pieces: ids.map((offerId) => ({ offerId, name: `Pièce ${offerId}`, price: 50, currency: "EUR", merchantName: "Partenaire", link: `https://example.com/${offerId}`, imageUrl: null, role: "base" })), createdAt: "2026-08-16T00:00:00.000Z" });

describe("Journal de tenues FILON", () => {
  it("remplace une tenue avec les mêmes offres au lieu de la dupliquer", () => {
    const result = mergeSavedOutfits([saved("old", [2, 1])], saved("new", [1, 2]));
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe("new");
  });

  it("rejette les journaux locaux qui ne respectent pas le contrat", () => {
    expect(sanitizeSavedOutfits([saved("ok", [1]), { id: "broken" }])).toHaveLength(1);
  });

  it("conserve une ancienne sauvegarde en dégradant devise et score inconnus", () => {
    const { currency: _currency, measurementStatus: _measurementStatus, confidenceScore: _confidenceScore, ...legacyBase } = saved("legacy", [1]);
    const legacy = { ...legacyBase, confidenceScore: 91 };
    expect(sanitizeSavedOutfits([legacy])[0]).toMatchObject({ currency: null, confidenceScore: null, measurementStatus: "not_calibrated" });
  });

  it("rejette les pièces malformées, les doublons, les devises mixtes et les totaux incohérents", () => {
    const valid = saved("valid", [1, 2]);
    const stringPrice = { ...valid, id: "string-price", pieces: [{ ...valid.pieces[0], price: "50" }, valid.pieces[1]] };
    const duplicate = { ...valid, id: "duplicate", pieces: [valid.pieces[0], { ...valid.pieces[1], offerId: valid.pieces[0].offerId }] };
    const mixedCurrency = { ...valid, id: "mixed", pieces: [valid.pieces[0], { ...valid.pieces[1], currency: "USD" }] };
    const badTotal = { ...valid, id: "total", total: 999 };
    const unsafeLink = { ...valid, id: "link", pieces: [{ ...valid.pieces[0], link: "http://example.com/1" }, valid.pieces[1]] };
    expect(sanitizeSavedOutfits([stringPrice, duplicate, mixedCurrency, badTotal, unsafeLink])).toEqual([]);
  });
});
