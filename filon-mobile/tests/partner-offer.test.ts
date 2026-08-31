import { describe, expect, it } from "vitest";

import type { FilonOffer } from "../lib/filon-api";
import { comparePartnerOffers, isSafePartnerOfferUrl } from "../lib/partner-offer";

const NOW = new Date("2026-08-29T12:00:00.000Z");
const offer = (id: number, price: number): FilonOffer => ({ id, name: "Test", brand: null, category: null, price, currency: "EUR", inStock: true, observedAt: "2026-08-29T10:00:00.000Z", evidenceCurrent: true, imageUrl: null, merchantName: `Merchant ${id}`, merchantSlug: null, link: `https://merchant${id}.example.com/item` });

describe("partner comparison and handoff", () => {
  it("ranks only finite observed offer prices and calculates transparent deltas", () => {
    const result = comparePartnerOffers([offer(1, 199), offer(2, 189), offer(3, Number.NaN)], NOW);
    expect(result.map((item) => item.offer.id)).toEqual([2, 1]);
    expect(result[0].isLowestObserved).toBe(true);
    expect(result[1].differenceFromLowest).toBe(10);
  });
  it("excludes offers without current actionable evidence", () => {
    const valid = offer(1, 199);
    expect(comparePartnerOffers([
      valid,
      { ...offer(2, 180), inStock: null },
      { ...offer(3, 170), observedAt: "2026-08-26T11:59:59.999Z" },
      { ...offer(4, 160), observedAt: "2026-08-29T12:00:00.001Z" },
      { ...offer(5, 150), link: "http://merchant.example/item" },
      { ...offer(6, 140), evidenceCurrent: false },
    ], NOW).map((item) => item.offer.id)).toEqual([1]);
  });
  it("refuses to compare mixed or unknown currencies", () => {
    expect(comparePartnerOffers([offer(1, 199), { ...offer(2, 189), currency: "USD" }], NOW)).toEqual([]);
    expect(comparePartnerOffers([offer(1, 199), { ...offer(2, 189), currency: "ZZZ" }], NOW)).toEqual([]);
    expect(comparePartnerOffers([offer(1, 199), { ...offer(2, 189), currency: "USD", evidenceCurrent: false }], NOW).map((item) => item.offer.id)).toEqual([1]);
  });
  it("opens only non-local HTTPS partner URLs", () => {
    expect(isSafePartnerOfferUrl("https://partner.example.com/item")).toBe(true);
    expect(isSafePartnerOfferUrl("http://partner.example.com/item")).toBe(false);
    expect(isSafePartnerOfferUrl("https://intranet/item")).toBe(false);
    expect(isSafePartnerOfferUrl("https://router/item")).toBe(false);
    expect(isSafePartnerOfferUrl("https://partner.local/item")).toBe(false);
    expect(isSafePartnerOfferUrl("https://partner.internal/item")).toBe(false);
    expect(isSafePartnerOfferUrl("https://partner.test/item")).toBe(false);
    expect(isSafePartnerOfferUrl("https://partner.example/item")).toBe(false);
    expect(isSafePartnerOfferUrl("https://partner.onion/item")).toBe(false);
    expect(isSafePartnerOfferUrl("https://localhost/item")).toBe(false);
    expect(isSafePartnerOfferUrl("https://localhost./item")).toBe(false);
    expect(isSafePartnerOfferUrl("https://foo.localhost./item")).toBe(false);
    expect(isSafePartnerOfferUrl("https://127.0.0.1/item")).toBe(false);
    expect(isSafePartnerOfferUrl("https://192.168.1.10/item")).toBe(false);
    expect(isSafePartnerOfferUrl("https://100.64.0.1/item")).toBe(false);
    expect(isSafePartnerOfferUrl("https://198.18.0.1/item")).toBe(false);
    expect(isSafePartnerOfferUrl("https://8.8.8.8/item")).toBe(false);
    expect(isSafePartnerOfferUrl("https://[::1]/item")).toBe(false);
    expect(isSafePartnerOfferUrl("https://[fec0::1]/item")).toBe(false);
    expect(isSafePartnerOfferUrl("https://[2001:4860:4860::8888]/item")).toBe(false);
    expect(isSafePartnerOfferUrl("https://[::ffff:127.0.0.1]/item")).toBe(false);
    expect(isSafePartnerOfferUrl("https://user:secret@partner.example.com/item")).toBe(false);
  });
});
