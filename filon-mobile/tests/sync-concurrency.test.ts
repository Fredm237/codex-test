import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  createFavoriteCollection,
  markFavoriteCollectionsPending,
  readFavoriteCollections,
  updateFavoriteCollections,
} from "../lib/favorite-collections";
import {
  readLocalPriceAlertState,
  reconcilePriceAlertsAfterSync,
  saveLocalPriceAlert,
  updateLocalPriceAlertState,
} from "../lib/alerts";

const persisted = vi.hoisted(() => new Map<string, string>());

vi.mock("@react-native-async-storage/async-storage", () => ({
  default: {
    getItem: vi.fn(async (key: string) => persisted.get(key) ?? null),
    setItem: vi.fn(async (key: string, value: string) => { persisted.set(key, value); }),
  },
}));

const firstAlert = { offerId: 11, name: "First", threshold: 85, currency: "EUR" as const, createdAt: "2026-08-13T00:00:00.000Z" };
const secondAlert = { offerId: 12, name: "Second", threshold: 64, currency: "EUR" as const, createdAt: "2026-08-13T00:01:00.000Z" };

describe("serialized local synchronization", () => {
  beforeEach(() => { persisted.clear(); });

  it("preserves writes from two collection-hook instances", async () => {
    await Promise.all([
      updateFavoriteCollections((current) => markFavoriteCollectionsPending(createFavoriteCollection(current, "First", "first", "2026-08-13T00:00:00.000Z"))),
      updateFavoriteCollections((current) => markFavoriteCollectionsPending(createFavoriteCollection(current, "Second", "second", "2026-08-13T00:01:00.000Z"))),
    ]);

    const current = await readFavoriteCollections();
    expect(current.collections.map((collection) => collection.name)).toEqual(["First", "Second"]);
    expect(current.pendingSync).toBe(true);
  });

  it("does not erase an alert created while an older sync snapshot is reconciled", async () => {
    await saveLocalPriceAlert(firstAlert);
    const sentItems = (await readLocalPriceAlertState()).items;

    await Promise.all([
      saveLocalPriceAlert(secondAlert),
      updateLocalPriceAlertState((current) => reconcilePriceAlertsAfterSync(current, sentItems, "2026-08-13T01:00:00.000Z")),
    ]);

    const current = await readLocalPriceAlertState();
    expect(current.items.map((item) => item.offerId)).toEqual([12, 11]);
    expect(current.pendingSync).toBe(true);
    expect(current.lastSyncedAt).toBeNull();
  });

  it("refreshes both hook instances whenever their screen regains focus", () => {
    const root = join(dirname(fileURLToPath(import.meta.url)), "..", "hooks");
    for (const file of ["use-favorite-collections.ts", "use-local-alerts.ts"]) {
      const source = readFileSync(join(root, file), "utf8");
      expect(source).toContain('import { useFocusEffect } from "expo-router";');
      expect(source).toContain("useFocusEffect(useCallback(() => { void refresh(); }, [refresh]));");
    }
  });
});
