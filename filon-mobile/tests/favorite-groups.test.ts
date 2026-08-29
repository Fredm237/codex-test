import { describe, expect, it } from "vitest";

import { groupFavoriteRows } from "../lib/favorite-groups";

describe("favorite grouping", () => {
  const base = { price: 10, currency: "EUR", imageUrl: null, merchantName: "M", link: "https://m.example.com", inStock: true, observedAt: "2026-08-13T00:00:00.000Z", evidenceCurrent: true };
  it("groups category paths and keeps an explicit uncategorized heading", () => {
    const rows = groupFavoriteRows([{ ...base, id: 1, name: "A", category: "Informatique > Portable" }, { ...base, id: 2, name: "B", category: null }], "Autres");
    expect(rows.filter((row) => row.type === "heading").map((row) => row.category)).toEqual(["Autres", "Informatique"]);
    expect(rows.filter((row) => row.type === "offer")).toHaveLength(2);
  });
});
