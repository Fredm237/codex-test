import { describe, expect, it } from "vitest";

import { buildPurchaseIntent, describePurchaseIntent, getPurchaseIntentCatalogueParams, isPurchaseIntentValid, normalizePurchaseIntentDraft, upsertPurchaseIntent, type PurchaseIntent } from "../lib/purchase-intents";

const draft = { need: "  casque   pour le train ", maxBudget: 180.129, deadline: " avant vendredi ", preferences: "  réparable  " };

describe("purchase intents", () => {
  it("normalises explicit constraints without inventing any", () => {
    expect(normalizePurchaseIntentDraft(draft)).toEqual({ need: "casque pour le train", maxBudget: 180.13, deadline: "avant vendredi", preferences: "réparable" });
  });

  it("requires a human-readable need before persisting", () => {
    expect(isPurchaseIntentValid({ need: " ", maxBudget: null, deadline: null, preferences: null })).toBe(false);
    expect(isPurchaseIntentValid({ need: "un vélo", maxBudget: null, deadline: null, preferences: null })).toBe(true);
  });

  it("updates the same intent rather than silently creating a duplicate", () => {
    const initial = buildPurchaseIntent(draft, "2026-08-16T12:00:00.000Z");
    const changed = buildPurchaseIntent({ ...draft, maxBudget: 150 }, "2026-08-17T12:00:00.000Z", initial);
    expect(upsertPurchaseIntent([initial], changed)).toEqual([changed]);
    expect(changed.createdAt).toBe(initial.createdAt);
  });

  it("turns saved constraints into an explicit assistant prompt in every locale", () => {
    const intent: PurchaseIntent = buildPurchaseIntent(draft, "2026-08-16T12:00:00.000Z");
    expect(describePurchaseIntent(intent, "fr")).toContain("Budget maximum");
    expect(describePurchaseIntent(intent, "nl")).toContain("Maximumbudget");
    expect(describePurchaseIntent(intent, "en")).toContain("Maximum budget");
  });

  it("only carries an explicit need and budget into catalogue exploration", () => {
    const withBudget = buildPurchaseIntent(draft, "2026-08-16T12:00:00.000Z");
    const withoutBudget = buildPurchaseIntent({ ...draft, maxBudget: null }, "2026-08-16T12:00:00.000Z");
    expect(getPurchaseIntentCatalogueParams(withBudget)).toEqual({ q: "casque pour le train", max: "180.13" });
    expect(getPurchaseIntentCatalogueParams(withoutBudget)).toEqual({ q: "casque pour le train", max: "" });
  });
});
