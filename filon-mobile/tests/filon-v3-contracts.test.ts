import { describe, expect, it } from "vitest";

import { createV3PipelineTrace, snapshotCoreOffer, updateV3PipelineStage } from "../lib/filon-v3-contracts";

const offer = { id: 1, name: "Veste", brand: null, category: "Mode", price: 90, currency: "EUR", inStock: null, imageUrl: null, merchantName: "Partenaire", merchantSlug: null, link: "https://example.com/1" };

describe("Fondation de contrats V3", () => {
  it("préserve une disponibilité Core inconnue au lieu de la supposer", () => {
    expect(snapshotCoreOffer(offer)).toMatchObject({ offerId: 1, price: { value: null, status: "unknown" }, availability: { value: null, status: "unknown", source: "unavailable" } });
  });

  it("ne qualifie prix et stock de vérifiés qu'avec un snapshot courant explicite", () => {
    const current = { ...offer, inStock: true as const, observedAt: "2026-08-29T10:00:00.000Z", evidenceCurrent: true };
    expect(snapshotCoreOffer(current, current.observedAt, new Date("2026-08-29T12:00:00.000Z"))).toMatchObject({ price: { value: 90, status: "verified" }, availability: { value: true, status: "verified" } });
  });

  it("produit une trace complète et immuable par étape", () => {
    const pending = createV3PipelineTrace("trace-1");
    const completed = updateV3PipelineStage(pending, "INTENT", "completed", "Brief reçu");
    expect(pending.stages[0].status).toBe("skipped");
    expect(completed.stages).toHaveLength(11);
    expect(completed.stages[0]).toMatchObject({ stage: "INTENT", status: "completed" });
  });
});
