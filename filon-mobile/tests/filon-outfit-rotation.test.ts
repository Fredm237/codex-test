import { describe, expect, it } from "vitest";

import { buildOutfitRotation } from "../lib/filon-outfit-rotation";
import type { SavedOutfit } from "../lib/filon-outfit-journal";

const outfit = (id: string, createdAt: string): SavedOutfit => ({ id, title: id, mode: "create", total: 80, confidenceScore: 70, pieces: [], createdAt });

describe("Rotation de tenues FILON", () => {
  it("propose d’abord les sauvegardes les plus anciennes sans déduire leur port réel", () => {
    const rotation = buildOutfitRotation([outfit("recent", "2026-08-15T00:00:00.000Z"), outfit("old", "2026-07-01T00:00:00.000Z")], new Date("2026-08-16T00:00:00.000Z"));
    expect(rotation[0].outfit.id).toBe("old");
    expect(rotation[0].reason).toContain("reconsidérer");
  });
});
