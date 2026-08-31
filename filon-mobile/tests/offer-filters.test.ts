import { describe, expect, it } from "vitest";

import { filterOffers } from "../lib/offer-filters";

const offers = [
  { id: 1, name: "A", brand: "Marque A", category: null, price: 50, currency: "EUR", inStock: true, observedAt: "2026-08-29T10:00:00.000Z", evidenceCurrent: true, imageUrl: null, merchantName: "A", merchantSlug: "a", link: "https://example.com/a" },
  { id: 2, name: "B", brand: "Marque B", category: null, price: 125, currency: "EUR", inStock: false, observedAt: "2026-08-29T10:00:00.000Z", evidenceCurrent: true, imageUrl: null, merchantName: "B", merchantSlug: "b", link: "https://example.com/b" },
];

const NOW = new Date("2026-08-29T12:00:00.000Z");

describe("FILON mobile filters", () => {
  it("can exclude offers with unconfirmed availability", () => {
    const legacy = { ...offers[0], id: 3, evidenceCurrent: false };
    expect(filterOffers([...offers, legacy], { inStockOnly: true, merchant: null, brand: null }, NOW)).toEqual([offers[0]]);
  });
  it("keeps an explicit merchant and brand selection factual", () => expect(filterOffers(offers, { inStockOnly: false, merchant: "b", brand: "Marque B" })).toEqual([offers[1]]));
});
