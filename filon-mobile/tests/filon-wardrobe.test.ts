import { describe, expect, it } from "vitest";

import { createWardrobeItem, mergeWardrobeItems, normalizeWardrobeItem, sanitizeWardrobe, wardrobeCoverage } from "../lib/filon-wardrobe";

const first = createWardrobeItem({ label: "Blazer bleu marine", role: "structure" }, "1", "2026-01-01T00:00:00.000Z")!;

describe("Dressing FILON", () => {
  it("actualise une pièce identique au lieu de la dupliquer", () => {
    const result = mergeWardrobeItems([first], { ...first, id: "2", label: "blazer bleu marine", updatedAt: "2026-08-16T00:00:00.000Z" });
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe("1");
    expect(result[0].createdAt).toBe(first.createdAt);
    expect(result[0].updatedAt).toBe("2026-08-16T00:00:00.000Z");
  });

  it("migre une entrée legacy vers une déclaration locale explicitement tracée", () => {
    const legacy = { id: "legacy", label: "Pantalon noir", role: "base", createdAt: "2026-01-01T00:00:00Z", updatedAt: "2026-01-02T00:00:00Z" };
    expect(normalizeWardrobeItem(legacy)).toMatchObject({
      schemaVersion: 2,
      provenance: "user_declared",
      storageScope: "local_device",
      attributes: { color: null, size: null, material: null },
    });
  });

  it("élimine les entrées invalides, dupliquées ou chronologiquement contradictoires", () => {
    expect(sanitizeWardrobe([
      first,
      { ...first, id: "duplicate-label" },
      { id: "x", label: "", role: "invalid" },
      { ...first, id: "future-order", createdAt: "2026-02-01T00:00:00Z", updatedAt: "2026-01-01T00:00:00Z" },
    ])).toEqual([first]);
  });

  it("borne les attributs déclarés et ne calcule aucun score de dressing", () => {
    const item = createWardrobeItem({ label: "  Chemise   blanche  ", role: "base", attributes: { color: " blanc ", size: "M" } }, "2", "2026-01-01T00:00:00Z")!;
    expect(item).toMatchObject({ label: "Chemise blanche", attributes: { color: "blanc", size: "M", material: null } });
    expect(wardrobeCoverage([first, item])).toEqual({
      itemCount: 2,
      representedRoles: ["base", "structure"],
      missingRoles: ["footwear", "accessory"],
      score: null,
      measurementStatus: "not_calibrated",
    });
  });
});
