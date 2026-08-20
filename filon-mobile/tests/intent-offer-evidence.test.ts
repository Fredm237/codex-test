import { describe, expect, it } from "vitest";

import { linkOfferEvidence, unlinkOfferEvidence, type IntentOfferEvidence } from "../lib/intent-offer-evidence";

const first: IntentOfferEvidence = { intentId: "intent-a", offerId: 101, name: "Premier casque", price: 179, currency: "EUR", merchantName: "Marchand A", link: "https://example.com/a", imageUrl: null, inStock: true, linkedAt: "2026-08-16T12:00:00.000Z" };
const replacement: IntentOfferEvidence = { ...first, offerId: 202, name: "Second casque", price: 159, merchantName: "Marchand B", link: "https://example.com/b", linkedAt: "2026-08-17T12:00:00.000Z" };

describe("intent offer evidence", () => {
  it("keeps one explicit offer evidence per intent and replaces it visibly", () => {
    expect(linkOfferEvidence([first], replacement)).toEqual([replacement]);
  });

  it("can remove only the link without modelling or deleting a price alert", () => {
    expect(unlinkOfferEvidence([first], "intent-a")).toEqual([]);
    expect(unlinkOfferEvidence([first], "another-intent")).toEqual([first]);
  });
});
