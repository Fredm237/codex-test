import { describe, expect, it } from "vitest";

import type { FilonOffer } from "../lib/filon-api";
import { comparePartnerOffers, isSafePartnerOfferUrl } from "../lib/partner-offer";

const offer = (id: number, price: number): FilonOffer => ({ id, name: "Test", brand: null, category: null, price, currency: "EUR", inStock: true, imageUrl: null, merchantName: `Merchant ${id}`, merchantSlug: null, link: `https://merchant${id}.example/item` });

describe("partner comparison and handoff", () => {
  it("ranks only finite observed offer prices and calculates transparent deltas", () => {
    const result = comparePartnerOffers([offer(1, 199), offer(2, 189), offer(3, Number.NaN)]);
    expect(result.map((item) => item.offer.id)).toEqual([2, 1]);
    expect(result[0].isLowestObserved).toBe(true);
    expect(result[1].differenceFromLowest).toBe(10);
  });
  it("opens only non-local HTTPS partner URLs", () => {
    expect(isSafePartnerOfferUrl("https://partner.example/item")).toBe(true);
    expect(isSafePartnerOfferUrl("http://partner.example/item")).toBe(false);
    expect(isSafePartnerOfferUrl("https://localhost/item")).toBe(false);
  });
});
