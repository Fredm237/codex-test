import { describe, expect, it } from "vitest";

import type { FilonOffer } from "../lib/filon-api";
import {
  routedOfferFactsMatch,
  selectVerifiedAlertOffer,
  selectVerifiedDetailOffer,
} from "../lib/filon-offer-evidence";

const NOW = new Date("2026-08-29T12:00:00.000Z");
const detailed: FilonOffer = {
  id: 7,
  name: "Produit",
  brand: null,
  category: null,
  price: 99,
  currency: "EUR",
  inStock: true,
  observedAt: "2026-08-29T10:00:00.000Z",
  evidenceCurrent: true,
  imageUrl: null,
  merchantName: "Marchand",
  merchantSlug: "marchand",
  link: "https://merchant.example.com/item",
};
const routed = {
  id: "7",
  name: "Produit",
  price: "99",
  currency: "EUR",
  merchant: "Marchand",
  link: "https://merchant.example.com/item",
  stock: "1",
  observedAt: "2026-08-29T10:00:00Z",
  evidenceCurrent: "1",
};

describe("offer action evidence", () => {
  it("never grants authority to route facts when the catalogue detail is absent", () => {
    expect(selectVerifiedDetailOffer(routed, null, NOW)).toBeNull();
    expect(selectVerifiedAlertOffer(routed, null, NOW)).toBeNull();
  });

  it("accepts the current safe detail only after every supplied fact matches", () => {
    expect(routedOfferFactsMatch(routed, detailed)).toBe(true);
    expect(selectVerifiedDetailOffer(routed, detailed, NOW)).toBe(detailed);
    expect(selectVerifiedAlertOffer(routed, detailed, NOW)).toBe(detailed);
  });

  it("closes forged deep links and every critical contradiction", () => {
    for (const facts of [
      { ...routed, id: "8" },
      { ...routed, name: "Imposteur" },
      { ...routed, price: "98" },
      { ...routed, currency: "USD" },
      { ...routed, merchant: "Autre" },
      { ...routed, link: "https://attacker.example.net/item" },
      { ...routed, stock: "0" },
      { ...routed, observedAt: "2026-08-29T11:00:00Z" },
      { ...routed, evidenceCurrent: "0" },
    ]) {
      expect(selectVerifiedDetailOffer(facts, detailed, NOW)).toBeNull();
    }
    expect(routedOfferFactsMatch({ ...routed, stock: "0" }, { ...detailed, inStock: null })).toBe(false);
  });

  it("accepts an id-only product route but never an incomplete alert route", () => {
    expect(selectVerifiedDetailOffer({ id: "7" }, detailed, NOW)).toBe(detailed);
    expect(selectVerifiedAlertOffer({ id: "7" }, detailed, NOW)).toBeNull();
    expect(selectVerifiedAlertOffer({ ...routed, observedAt: "" }, detailed, NOW)).toBeNull();
    expect(selectVerifiedAlertOffer({ ...routed, evidenceCurrent: undefined }, detailed, NOW)).toBeNull();
  });

  it("rejects stale, legacy and unsafe catalogue details even when route facts claim freshness", () => {
    expect(selectVerifiedDetailOffer(routed, { ...detailed, evidenceCurrent: false }, NOW)).toBeNull();
    expect(selectVerifiedDetailOffer(routed, { ...detailed, observedAt: "2026-08-26T11:59:59.999Z" }, NOW)).toBeNull();
    expect(selectVerifiedDetailOffer({ ...routed, link: "https://127.0.0.1/item" }, { ...detailed, link: "https://127.0.0.1/item" }, NOW)).toBeNull();
  });
});
