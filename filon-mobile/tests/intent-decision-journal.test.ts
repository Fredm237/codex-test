import { describe, expect, it } from "vitest";

import { appendIntentDecisionEvent, forPurchaseIntent, makeIntentDecisionEvent, type IntentDecisionEvent } from "../lib/intent-decision-journal-rules";

describe("intent decision journal", () => {
  it("keeps a bounded, newest-first private sequence", () => {
    const events = Array.from({ length: 4 }, (_, index) => makeIntentDecisionEvent("intent-a", "catalogue-explored", `Recherche ${index}`, `2026-08-1${index}T10:00:00.000Z`));
    const result = events.reduce((current, event) => appendIntentDecisionEvent(current, event, 3), [] as IntentDecisionEvent[]);
    expect(result).toHaveLength(3);
    expect(result[0].label).toBe("Recherche 3");
  });

  it("never blends one intent’s decisions with another intent’s history", () => {
    const a = makeIntentDecisionEvent("intent-a", "offer-linked", "Offre A", "2026-08-16T10:00:00.000Z");
    const b = makeIntentDecisionEvent("intent-b", "alert-created", "Offre B", "2026-08-16T11:00:00.000Z");
    expect(forPurchaseIntent([b, a], "intent-a")).toEqual([a]);
  });
});
