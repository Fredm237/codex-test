import { describe, expect, it } from "vitest";
import { buildFavoriteCollectionSyncPayload, collectionsForFavorite, createFavoriteCollection, deleteFavoriteCollection, emptyFavoriteCollectionState, markFavoriteCollectionsPending, markFavoriteCollectionsReconciled, mergeRemoteFavoriteCollections, reconcileFavoriteCollectionsAfterSync, renameFavoriteCollection, toggleFavoriteCollectionMembership } from "../lib/favorite-collections";

describe("private favorite collections", () => {
  it("creates normalized collections and toggles membership locally", () => { const state = createFavoriteCollection(emptyFavoriteCollectionState, "  Comparer   ", "c1", "2026-01-01"); const next = toggleFavoriteCollectionMembership(state, 12, "c1"); expect(collectionsForFavorite(next, 12).map((item) => item.name)).toEqual(["Comparer"]); expect(toggleFavoriteCollectionMembership(next, 12, "c1").memberships["12"]).toEqual([]); });
  it("merges remote collections without removing private local memberships", () => { const local = toggleFavoriteCollectionMembership(createFavoriteCollection(emptyFavoriteCollectionState, "Local", "local", "2026-01-01"), 10, "local"); const merged = mergeRemoteFavoriteCollections(local, [{ clientId: "remote", name: "Remote", createdAt: "2026-01-02", updatedAt: "2026-01-02", deletedAt: null, offerIds: [12] }]); expect(collectionsForFavorite(merged, 10).map((item) => item.name)).toEqual(["Local"]); expect(collectionsForFavorite(merged, 12).map((item) => item.name)).toEqual(["Remote"]); });
  it("keeps a deletion tombstone so an active remote copy cannot return", () => { const local = deleteFavoriteCollection(createFavoriteCollection(emptyFavoriteCollectionState, "Trip", "trip", "2026-01-01"), "trip", "2026-01-03"); const merged = mergeRemoteFavoriteCollections(local, [{ clientId: "trip", name: "Trip", createdAt: "2026-01-01", updatedAt: "2026-01-02", deletedAt: null, offerIds: [4] }]); expect(merged.collections).toHaveLength(0); expect(merged.tombstones.trip.deletedAt).toBe("2026-01-03"); });
  it("keeps the newest collection name during a rename conflict", () => { const local = renameFavoriteCollection(createFavoriteCollection(emptyFavoriteCollectionState, "Old", "c1", "2026-01-01"), "c1", "Local name", "2026-01-03"); const merged = mergeRemoteFavoriteCollections(local, [{ clientId: "c1", name: "Remote name", createdAt: "2026-01-01", updatedAt: "2026-01-02", deletedAt: null, offerIds: [] }]); expect(merged.collections[0]?.name).toBe("Local name"); });
  it("keeps a local change pending until the remote reconciliation succeeds", () => { const pending = markFavoriteCollectionsPending(createFavoriteCollection(emptyFavoriteCollectionState, "Trip", "trip", "2026-01-01")); expect(pending.pendingSync).toBe(true); expect(markFavoriteCollectionsReconciled(pending, "2026-01-02")).toMatchObject({ pendingSync: false, lastSyncedAt: "2026-01-02" }); });

  it("marks only the exact collection snapshot sent to the server as reconciled", () => {
    const sent = markFavoriteCollectionsPending(toggleFavoriteCollectionMembership(createFavoriteCollection(emptyFavoriteCollectionState, "Trip", "trip", "2026-01-01T00:00:00.000Z"), 12, "trip"));
    const payload = buildFavoriteCollectionSyncPayload(sent);
    const reconciled = reconcileFavoriteCollectionsAfterSync(sent, payload, payload, "2026-01-02T00:00:00.000Z");
    expect(reconciled).toMatchObject({ pendingSync: false, lastSyncedAt: "2026-01-02T00:00:00.000Z" });
    expect(collectionsForFavorite(reconciled, 12).map((item) => item.name)).toEqual(["Trip"]);
  });

  it("preserves a rename made while an older collection snapshot is in flight", () => {
    const sent = markFavoriteCollectionsPending(createFavoriteCollection(emptyFavoriteCollectionState, "Before", "trip", "2026-01-01T00:00:00.000Z"));
    const payload = buildFavoriteCollectionSyncPayload(sent);
    const concurrent = markFavoriteCollectionsPending(renameFavoriteCollection(sent, "trip", "After", "2026-01-03T00:00:00.000Z"));
    const remoteDeletion = [{ ...payload[0], deletedAt: "2026-01-02T00:00:00.000Z", updatedAt: "2026-01-02T00:00:00.000Z" }];
    const reconciled = reconcileFavoriteCollectionsAfterSync(concurrent, remoteDeletion, payload, "2026-01-04T00:00:00.000Z");
    expect(reconciled.collections[0]?.name).toBe("After");
    expect(reconciled.tombstones).toEqual({});
    expect(reconciled.pendingSync).toBe(true);
  });

  it("does not resurrect a collection deleted while its active snapshot is in flight", () => {
    const sent = markFavoriteCollectionsPending(createFavoriteCollection(emptyFavoriteCollectionState, "Trip", "trip", "2026-01-01T00:00:00.000Z"));
    const payload = buildFavoriteCollectionSyncPayload(sent);
    const concurrent = markFavoriteCollectionsPending(deleteFavoriteCollection(sent, "trip", "2026-01-03T00:00:00.000Z"));
    const reconciled = reconcileFavoriteCollectionsAfterSync(concurrent, payload, payload, "2026-01-04T00:00:00.000Z");
    expect(reconciled.collections).toEqual([]);
    expect(reconciled.tombstones.trip?.deletedAt).toBe("2026-01-03T00:00:00.000Z");
    expect(reconciled.pendingSync).toBe(true);
  });
});
