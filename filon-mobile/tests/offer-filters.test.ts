import { describe, expect, it } from "vitest";

import { filterOffers } from "../lib/offer-filters";

const offers = [
  { id: 1, name: "A", brand: "Marque A", category: null, price: 50, currency: "EUR", inStock: true, imageUrl: null, merchantName: "A", merchantSlug: "a", link: "https://example.com/a" },
  { id: 2, name: "B", brand: "Marque B", category: null, price: 125, currency: "EUR", inStock: false, imageUrl: null, merchantName: "B", merchantSlug: "b", link: "https://example.com/b" },
];

describe("FILON mobile filters", () => {
  it("keeps only offers within the selected price range", () => expect(filterOffers(offers, { minPrice: 40, maxPrice: 60, inStockOnly: false, merchant: null, brand: null })).toHaveLength(1));
  it("can exclude offers with unconfirmed availability", () => expect(filterOffers(offers, { minPrice: null, maxPrice: null, inStockOnly: true, merchant: null, brand: null })).toEqual([offers[0]]));
  it("keeps an explicit merchant and brand selection factual", () => expect(filterOffers(offers, { minPrice: null, maxPrice: null, inStockOnly: false, merchant: "b", brand: "Marque B" })).toEqual([offers[1]]));
});
