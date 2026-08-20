import { describe, expect, it } from "vitest";

import { getDiscoverDirections, resolveStyleDna } from "../lib/style-dna";

describe("Style DNA", () => {
  const now = new Date("2026-08-16T12:00:00.000Z");

  it("priorise une préférence déclarée sans l’interpréter comme une preuve comportementale", () => {
    expect(resolveStyleDna("classic", [], now)).toEqual({ primary: "classic", confidence: "high", evidenceCount: 1, source: "declared" });
  });

  it("refuse de sur-apprendre à partir d’un signal isolé", () => {
    expect(resolveStyleDna(null, [{ direction: "minimal", value: "affirmed", at: now.toISOString() }], now).primary).toBeNull();
  });

  it("adopte une direction après des signaux convergents et récents", () => {
    const dna = resolveStyleDna(null, [{ direction: "bold", value: "affirmed", at: now.toISOString() }, { direction: "bold", value: "affirmed", at: "2026-08-10T12:00:00.000Z" }], now);
    expect(dna.primary).toBe("bold");
    expect(getDiscoverDirections(dna)[0].id).toBe("bold");
  });
});
