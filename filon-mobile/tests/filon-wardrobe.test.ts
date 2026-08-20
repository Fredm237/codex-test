import { describe, expect, it } from "vitest";

import { mergeWardrobeItems, sanitizeWardrobe, type WardrobeItem } from "../lib/filon-wardrobe";

const first: WardrobeItem = { id: "1", label: "Blazer bleu marine", role: "structure", createdAt: "2026-01-01T00:00:00.000Z", updatedAt: "2026-01-01T00:00:00.000Z" };

describe("Dressing FILON", () => {
  it("actualise une pièce identique au lieu de la dupliquer", () => {
    const result = mergeWardrobeItems([first], { ...first, id: "2", label: " blazer bleu marine ", updatedAt: "2026-08-16T00:00:00.000Z" });
    expect(result).toHaveLength(1);
    expect(result[0].updatedAt).toBe("2026-08-16T00:00:00.000Z");
  });

  it("élimine les entrées locales invalides avant affichage", () => {
    expect(sanitizeWardrobe([first, { id: "x", label: "", role: "invalid" }])).toEqual([first]);
  });
});
