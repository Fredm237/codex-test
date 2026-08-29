import { describe, expect, it } from "vitest";

import { isIntentOfferEvidenceCurrent, linkOfferEvidence, normalizeIntentOfferEvidence, normalizeIntentOfferEvidenceList, unlinkOfferEvidence, type IntentOfferEvidence } from "../lib/intent-offer-evidence";

const first: IntentOfferEvidence = { intentId: "intent-a", offerId: 101, name: "Premier casque", price: 179, currency: "EUR", merchantName: "Marchand A", link: "https://example.com/a", imageUrl: null, inStock: true, observedAt: "2026-08-16T10:00:00.000Z", evidenceCurrent: true, linkedAt: "2026-08-16T12:00:00.000Z" };
const replacement: IntentOfferEvidence = { ...first, offerId: 202, name: "Second casque", price: 159, merchantName: "Marchand B", link: "https://example.com/b", linkedAt: "2026-08-17T12:00:00.000Z" };

describe("intent offer evidence", () => {
  it("keeps one explicit offer evidence per intent and replaces it visibly", () => {
    expect(linkOfferEvidence([first], replacement)).toEqual([replacement]);
  });

  it("can remove only the link without modelling or deleting a price alert", () => {
    expect(unlinkOfferEvidence([first], "intent-a")).toEqual([]);
    expect(unlinkOfferEvidence([first], "another-intent")).toEqual([first]);
  });

  it("keeps persisted price and stock evidence only while its explicit snapshot is current", () => {
    expect(normalizeIntentOfferEvidence(first, new Date("2026-08-19T10:00:00.000Z"))).toMatchObject({ observedAt: first.observedAt, evidenceCurrent: true, inStock: true });
    const expired = normalizeIntentOfferEvidence(first, new Date("2026-08-19T10:00:00.001Z"));
    expect(expired).toMatchObject({ observedAt: first.observedAt, evidenceCurrent: true, inStock: null });
    expect(isIntentOfferEvidenceCurrent(first, new Date("2026-08-19T10:00:00.000Z"))).toBe(true);
    expect(isIntentOfferEvidenceCurrent(first, new Date("2026-08-19T10:00:00.001Z"))).toBe(false);
  });

  it("migrates a legacy link fail-closed and rejects malformed or unsafe persisted evidence", () => {
    const { observedAt: _observedAt, evidenceCurrent: _evidenceCurrent, ...legacy } = first;
    expect(normalizeIntentOfferEvidence(legacy, new Date("2026-08-16T12:00:00.000Z"))).toMatchObject({ observedAt: null, evidenceCurrent: false, inStock: null });
    expect(normalizeIntentOfferEvidence({ ...first, currency: "" })).toBeNull();
    expect(normalizeIntentOfferEvidence({ ...first, price: Number.NaN })).toBeNull();
    expect(normalizeIntentOfferEvidence({ ...first, link: "http://example.com/a" })).toBeNull();
    expect(normalizeIntentOfferEvidence({ ...first, linkedAt: "2026-02-30T00:00:00Z" })).toBeNull();
  });

  it("deduplicates persisted links by intent after validation", () => {
    expect(normalizeIntentOfferEvidenceList([first, replacement], new Date("2026-08-17T12:00:00.000Z"))).toEqual([expect.objectContaining({ offerId: first.offerId })]);
  });
});
