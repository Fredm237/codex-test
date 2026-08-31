import { describe, expect, it } from "vitest";

import { parseFilonAdviceSse } from "../lib/filon-assistant";

const NOW = new Date("2026-08-29T12:00:00Z");

function resultsEvent(cards: object[], extra: Record<string, unknown> = {}) {
  return `data: ${JSON.stringify({ type: "results", data: { usage: "ordinateur portable", offers: cards.length, real: true, cards, ...extra } })}\n\n`;
}

describe("parseFilonAdviceSse", () => {
  it("keeps only verified result cards with a valid merchant and price", () => {
    const result = parseFilonAdviceSse('data: {"type":"step","i":0}\n\ndata: {"type":"results","data":{"usage":"ordinateur portable","offers":2,"real":true,"cards":[{"offer_id":42,"product_ean":"1234567890123","rank":"Le plus polyvalent","name":"PC catalogue","price":699,"currency":"EUR","merchant":"Marchand","in_stock":true,"observed_at":"2026-08-29T10:00:00Z","evidence_current":true,"image":"https://merchant.example.com/product.jpg,https://merchant.example.com/second.jpg","link":"https://merchant.example.com/item","why":"Offre catalogue.","buy":true},{"name":"Carte incomplète"}]}}\n\n', NOW);
    expect(result.real).toBe(true);
    expect(result.offers).toBe(1);
    expect(result.cards).toEqual([{ offerId: 42, productEan: "1234567890123", rank: "catalogue_current", name: "PC catalogue", price: 699, currency: "EUR", merchant: "Marchand", inStock: true, observedAt: "2026-08-29T10:00:00.000Z", evidenceCurrent: true, imageUrl: "https://merchant.example.com/product.jpg", link: "https://merchant.example.com/item", why: "current_offer_evidence", buy: false }]);
  });

  it("returns an explicit empty verified state rather than synthetic cards", () => {
    const result = parseFilonAdviceSse('data: {"type":"results","data":{"usage":"besoin rare","offers":0,"real":false,"cards":[]}}\n\n', NOW);
    expect(result.real).toBe(false);
    expect(result.cards).toEqual([]);
  });

  it("fails closed on missing currency, stock, identity or observation", () => {
    const valid = { offer_id: 42, name: "PC catalogue", price: 699, currency: "EUR", merchant: "Marchand", in_stock: true, observed_at: "2026-08-29T10:00:00Z", evidence_current: true, link: "https://merchant.example.com/item" };
    const result = parseFilonAdviceSse(resultsEvent([
      valid,
      { ...valid, offer_id: null },
      { ...valid, price: 0 },
      { ...valid, currency: null },
      { ...valid, currency: "ZZZ" },
      { ...valid, merchant: " " },
      { ...valid, in_stock: null },
      { ...valid, in_stock: false },
      { ...valid, observed_at: null },
    ]), NOW);
    expect(result.cards).toHaveLength(1);
    expect(result.cards[0]?.offerId).toBe(42);
    expect(result.cards[0]?.buy).toBe(false);
  });

  it("requires an explicit current-evidence marker from the server", () => {
    const valid = { offer_id: 42, name: "PC catalogue", price: 699, currency: "EUR", merchant: "Marchand", in_stock: true, observed_at: "2026-08-29T10:00:00Z" };
    const result = parseFilonAdviceSse(resultsEvent([
      valid,
      { ...valid, offer_id: 43, evidence_current: false },
      { ...valid, offer_id: 44, evidence_current: true },
    ]), NOW);

    expect(result.cards.map((card) => card.offerId)).toEqual([44]);
    expect(result.cards[0]?.evidenceCurrent).toBe(true);
  });

  it("rejects stale and future observations, including one millisecond beyond the boundary", () => {
    const valid = { offer_id: 42, name: "PC catalogue", price: 699, currency: "EUR", merchant: "Marchand", in_stock: true, observed_at: "2026-08-26T12:00:00Z", evidence_current: true };
    const result = parseFilonAdviceSse(resultsEvent([
      valid,
      { ...valid, offer_id: 43, observed_at: "2026-08-26T11:59:59.999Z" },
      { ...valid, offer_id: 44, observed_at: "2026-08-29T12:00:00.001Z" },
    ]), NOW);
    expect(result.cards.map((card) => card.offerId)).toEqual([42]);
  });

  it("does not revive cards when the server reports an abstention", () => {
    const valid = { offer_id: 42, name: "PC catalogue", price: 699, currency: "EUR", merchant: "Marchand", in_stock: true, observed_at: "2026-08-29T10:00:00Z", evidence_current: true };
    const result = parseFilonAdviceSse(resultsEvent([valid], { real: false }), NOW);
    expect(result).toMatchObject({ real: false, offers: 0, cards: [] });
  });

  it("does not expose a literal IP as a merchant link", () => {
    const card = { offer_id: 42, name: "PC catalogue", price: 699, currency: "EUR", merchant: "Marchand", in_stock: true, observed_at: "2026-08-29T10:00:00Z", evidence_current: true, link: "https://8.8.8.8/item" };
    expect(parseFilonAdviceSse(resultsEvent([card]), NOW).cards[0]?.link).toBeNull();
  });
});
