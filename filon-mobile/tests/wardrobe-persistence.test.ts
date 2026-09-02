import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  clearWardrobe,
  eraseWardrobeWithReceipt,
  exportWardrobe,
  readWardrobe,
  saveWardrobeItem,
} from "../lib/filon-wardrobe";

const { store } = vi.hoisted(() => ({ store: new Map<string, string>() }));

vi.mock("@react-native-async-storage/async-storage", () => ({
  default: {
    getItem: vi.fn(async (key: string) => store.get(key) ?? null),
    setItem: vi.fn(async (key: string, value: string) => { store.set(key, value); }),
    removeItem: vi.fn(async (key: string) => { store.delete(key); }),
    multiRemove: vi.fn(async (keys: string[]) => { keys.forEach((key) => store.delete(key)); }),
  },
}));

beforeEach(() => store.clear());

describe("wardrobe v2 persistence", () => {
  it("migrates the legacy local record and removes the old copy", async () => {
    store.set("filon.intelligence.wardrobe.v1", JSON.stringify([{ id: "legacy", label: "Blazer", role: "structure", createdAt: "2026-01-01T00:00:00Z", updatedAt: "2026-01-01T00:00:00Z" }]));

    const items = await readWardrobe();

    expect(items[0]).toMatchObject({ schemaVersion: 2, provenance: "user_declared", storageScope: "local_device" });
    expect(store.has("filon.intelligence.wardrobe.v1")).toBe(false);
    expect(store.has("filon.intelligence.wardrobe.v2")).toBe(true);
  });

  it("serializes concurrent writes without losing either declared piece", async () => {
    const [first, second] = await Promise.all([
      saveWardrobeItem({ label: "Chemise blanche", role: "base" }),
      saveWardrobeItem({ label: "Chaussures noires", role: "footwear" }),
    ]);

    expect(first).toHaveLength(1);
    expect(second.map((item) => item.label).sort()).toEqual(["Chaussures noires", "Chemise blanche"]);
    expect(await readWardrobe()).toHaveLength(2);
  });

  it("erases both current and legacy stores", async () => {
    await saveWardrobeItem({ label: "Sac", role: "accessory" });
    store.set("filon.intelligence.wardrobe.v1", "legacy");

    expect(await clearWardrobe()).toEqual([]);
    expect(await readWardrobe()).toEqual([]);
    expect(store.size).toBe(0);
  });

  it("exports a versioned local snapshot with an explicit retention policy", async () => {
    await saveWardrobeItem({ label: "Pantalon marine", role: "base" });

    const exported = await exportWardrobe("2026-09-02T12:00:00Z");

    expect(exported).toMatchObject({
      schemaVersion: 1,
      kind: "filon_wardrobe_export",
      exportedAt: "2026-09-02T12:00:00.000Z",
      storageScope: "local_device",
      retentionPolicy: "until_user_deletion",
      itemCount: 1,
    });
    expect(exported.items[0]).toMatchObject({ label: "Pantalon marine", provenance: "user_declared" });
  });

  it("issues an erasure receipt only after both stores are verified empty", async () => {
    await saveWardrobeItem({ label: "Sac", role: "accessory" });
    store.set("filon.intelligence.wardrobe.v1", "legacy");

    const receipt = await eraseWardrobeWithReceipt("2026-09-02T12:05:00Z");

    expect(receipt).toEqual({
      schemaVersion: 1,
      kind: "filon_wardrobe_erasure_receipt",
      erasedAt: "2026-09-02T12:05:00.000Z",
      storageScope: "local_device",
      removedStores: ["filon.intelligence.wardrobe.v2", "filon.intelligence.wardrobe.v1"],
      verifiedEmpty: true,
    });
    expect(store.size).toBe(0);
  });
});
