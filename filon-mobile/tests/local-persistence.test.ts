import { describe, expect, it } from "vitest";

import { emptyLocalPriceAlertState, isAlertReferenceCurrent, markPriceAlertsPending, markPriceAlertsReconciled, normalizeLocalPriceAlerts, reconcilePriceAlertsAfterSync, removeLocalPriceAlertFromList, serializeAlertForSync, upsertLocalPriceAlert } from "../lib/alerts";
import { applyFavoriteToggle, normalizeFavoriteOffers } from "../lib/favorites";

const favorite = { id: 11, name: "Produit", price: 99, currency: "EUR", imageUrl: null, merchantName: "Partenaire", link: "https://example.com", inStock: true, observedAt: "2026-08-13T00:00:00.000Z", evidenceCurrent: true, category: null };
const alert = { offerId: 11, name: "Produit", threshold: 85, currency: "EUR" as const, createdAt: "2026-08-13T00:00:00.000Z" };

describe("FILON local tracking transitions", () => {
  it("adds then removes a favorite deterministically", () => {
    expect(applyFavoriteToggle([], favorite)).toEqual([favorite]);
    expect(applyFavoriteToggle([favorite], favorite)).toEqual([]);
  });

  it("does not preserve an undated legacy stock claim", () => {
    const { observedAt: _observedAt, evidenceCurrent: _evidenceCurrent, ...legacy } = favorite;
    expect(normalizeFavoriteOffers([legacy], new Date("2026-08-13T12:00:00.000Z"))).toEqual([{ ...favorite, observedAt: null, evidenceCurrent: false, inStock: null }]);
  });

  it("keeps stock only while the saved observation is current", () => {
    expect(normalizeFavoriteOffers([favorite], new Date("2026-08-15T23:59:59.000Z"))[0]).toMatchObject({ inStock: true, observedAt: favorite.observedAt });
    expect(normalizeFavoriteOffers([favorite], new Date("2026-08-16T00:00:01.000Z"))[0]).toMatchObject({ inStock: null, observedAt: favorite.observedAt });
    expect(normalizeFavoriteOffers([{ ...favorite, observedAt: "2026-08-14T00:00:00.000Z" }], new Date("2026-08-13T00:00:00.000Z"))[0]).toMatchObject({ inStock: null });
    expect(normalizeFavoriteOffers([{ ...favorite, evidenceCurrent: false }], new Date("2026-08-13T12:00:00.000Z"))[0]).toMatchObject({ evidenceCurrent: false, inStock: null });
  });

  it("rejects malformed persisted offers instead of inventing facts", () => {
    expect(normalizeFavoriteOffers([{ ...favorite, currency: "" }, { ...favorite, id: 0 }, { ...favorite, price: Number.NaN }])).toEqual([]);
  });

  it("replaces a price threshold for the same offer", () => {
    const updated = { ...alert, threshold: 75 };
    expect(upsertLocalPriceAlert([alert], updated)).toEqual([updated]);
  });

  it("drops persisted alert rules without an explicit supported currency", () => {
    expect(normalizeLocalPriceAlerts([alert, { ...alert, offerId: 12, currency: "" }, { ...alert, offerId: 13, threshold: Number.NaN }])).toEqual([alert]);
  });

  it("requires a fresh explicit offer snapshot for every alert reference", () => {
    const reference = { price: 99, currency: "EUR", observedAt: "2026-08-13T00:00:00.000Z", evidenceCurrent: true };
    expect(isAlertReferenceCurrent(reference, new Date("2026-08-16T00:00:00.000Z"))).toBe(true);
    expect(isAlertReferenceCurrent(reference, new Date("2026-08-16T00:00:00.001Z"))).toBe(false);
    expect(isAlertReferenceCurrent({ ...reference, observedAt: null }, new Date("2026-08-13T12:00:00.000Z"))).toBe(false);
    expect(isAlertReferenceCurrent({ ...reference, evidenceCurrent: false }, new Date("2026-08-13T12:00:00.000Z"))).toBe(false);
    expect(isAlertReferenceCurrent({ ...reference, currency: "" }, new Date("2026-08-13T12:00:00.000Z"))).toBe(false);
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

  it("reconciles only the exact alert snapshot that reached the server", () => {
    const pending = markPriceAlertsPending({ ...emptyLocalPriceAlertState, items: [alert] });
    expect(reconcilePriceAlertsAfterSync(pending, [alert], "2026-08-13T01:00:00.000Z")).toMatchObject({
      items: [alert],
      pendingSync: false,
      lastSyncedAt: "2026-08-13T01:00:00.000Z",
    });
  });

  it("preserves an alert removal made while the older snapshot is in flight", () => {
    const concurrent = markPriceAlertsPending({ ...emptyLocalPriceAlertState, items: [] });
    expect(reconcilePriceAlertsAfterSync(concurrent, [alert], "2026-08-13T01:00:00.000Z")).toMatchObject({
      items: [],
      pendingSync: true,
      lastSyncedAt: null,
    });
  });

  it("preserves an updated threshold made while the older snapshot is in flight", () => {
    const updated = { ...alert, threshold: 72 };
    const concurrent = markPriceAlertsPending({ ...emptyLocalPriceAlertState, items: [updated] });
    expect(reconcilePriceAlertsAfterSync(concurrent, [alert], "2026-08-13T01:00:00.000Z")).toMatchObject({
      items: [updated],
      pendingSync: true,
      lastSyncedAt: null,
    });
  });
});
