import { describe, expect, it } from "vitest";

import { emptyLocalPriceAlertState, markPriceAlertsPending, markPriceAlertsReconciled, removeLocalPriceAlertFromList, serializeAlertForSync, upsertLocalPriceAlert } from "../lib/alerts";
import { applyFavoriteToggle } from "../lib/favorites";

const favorite = { id: 11, name: "Produit", price: 99, currency: "EUR", imageUrl: null, merchantName: "Partenaire", link: "https://example.com", inStock: true, category: null };
const alert = { offerId: 11, name: "Produit", threshold: 85, currency: "EUR", createdAt: "2026-08-13T00:00:00.000Z" };

describe("FILON local tracking transitions", () => {
  it("adds then removes a favorite deterministically", () => {
    expect(applyFavoriteToggle([], favorite)).toEqual([favorite]);
    expect(applyFavoriteToggle([favorite], favorite)).toEqual([]);
  });

  it("replaces a price threshold for the same offer", () => {
    const updated = { ...alert, threshold: 75 };
    expect(upsertLocalPriceAlert([alert], updated)).toEqual([updated]);
  });

  it("removes only the targeted local threshold", () => {
    const second = { ...alert, offerId: 12, name: "Autre" };
    expect(removeLocalPriceAlertFromList([alert, second], 11)).toEqual([second]);
  });

  it("creates a stable versioned payload for a future account sync", () => {
    expect(serializeAlertForSync(alert)).toEqual({ version: 1, kind: "price-alert", alert });
  });

  it("keeps an alert change pending until reconciliation succeeds", () => {
    const pending = markPriceAlertsPending({ ...emptyLocalPriceAlertState, items: [alert] });
    expect(pending.pendingSync).toBe(true);
    expect(markPriceAlertsReconciled(pending, "2026-08-13T01:00:00.000Z")).toMatchObject({ pendingSync: false, lastSyncedAt: "2026-08-13T01:00:00.000Z" });
  });
});
