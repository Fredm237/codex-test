import { describe, expect, it } from "vitest";

import { mergePlannedOccasions, sanitizePlannedOccasions, type PlannedOccasion } from "../lib/filon-occasion-planner";

const planned: PlannedOccasion = { id: "1", title: "Dîner", date: "2026-08-20", outfitId: "outfit-1", createdAt: "2026-08-16T00:00:00.000Z" };

describe("Planificateur d’occasions FILON", () => {
  it("remplace un doublon d’occasion et de tenue au même jour", () => {
    const result = mergePlannedOccasions([planned], { ...planned, id: "2" });
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe("2");
  });

  it("écarte les occasions locales invalides", () => {
    expect(sanitizePlannedOccasions([planned, { id: "bad", title: "", date: "tomorrow", outfitId: 1 }])).toEqual([planned]);
  });

  it("préserve un identifiant de rappel lorsqu’il est enregistré localement", () => {
    expect(sanitizePlannedOccasions([{ ...planned, reminderId: "notification-1" }])[0].reminderId).toBe("notification-1");
  });
});
