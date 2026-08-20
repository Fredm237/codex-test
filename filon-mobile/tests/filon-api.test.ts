import { describe, expect, it } from "vitest";

import { buildFilonOfferSearchParams, getFirstImageUrl, normalizeFilonCatalogueNavigation, normalizeFilonCataloguePulse, normalizeFilonCatalogueRelief, normalizeOffer, normalizeOfferDetail, normalizeProduct } from "../lib/filon-api";

describe("FILON catalogue normalization", () => {
  it("preserves new taxonomy aliases and their child branches", () => {
    const navigation = normalizeFilonCatalogueNavigation({ roots: [{ name: "Nouveau", slug: "nouveau", count: 4, children: [{ name: "Rayon", slug: "rayon", count: 4, children: [{ name: "Sous-rayon", slug: "sous-rayon", count: 4 }] }] }] });
    expect(navigation.departments[0]?.categories[0]?.name).toBe("Rayon");
    expect(navigation.departments[0]?.categories[0]?.subcategories[0]).toEqual({ name: "Sous-rayon", slug: "sous-rayon", count: 4 });
  });

  it("keeps the first valid image from multi-image merchant feeds", () => {
    expect(getFirstImageUrl("https://images.filon.be/one.jpg,https://images.filon.be/two.jpg")).toBe("https://images.filon.be/one.jpg");
  });

  it("maps the public catalogue contract to a mobile offer", () => {
    const offer = normalizeOffer({ id: 7, name: "Casque test", price: 99.9, image: "https://images.filon.be/casque.jpg", link: "https://www.awin1.com/example", merchant: { name: "Partenaire test", slug: "partner" }, in_stock: true });
    expect(offer).toMatchObject({ id: 7, merchantName: "Partenaire test", imageUrl: "https://images.filon.be/casque.jpg", inStock: true, currency: "EUR" });
  });

  it("preserves an unknown merchant availability instead of claiming the offer is in stock", () => {
    const offer = normalizeOffer({ id: 8, name: "Disponibilité inconnue", price: 19, link: "https://example.com", in_stock: null });
    expect(offer.inStock).toBeNull();
  });

  it("keeps the grouped product identity on every verified EAN offer", () => {
    const product = normalizeProduct({ ean: "4717622052664", name: "Winter Activa SV-3", brand: "NANKANG", category: "tyres", image: "https://example.com/product.jpg", price_min: 44.56, price_max: 50.01, currency: "EUR", offers_count: 2, merchants_count: 2, offers: [{ id: 1, price: 44.56, currency: "EUR", in_stock: true, link: "https://example.com/a", merchant: { name: "Pneus BE" } }] });
    expect(product.offers[0]).toMatchObject({ name: "Winter Activa SV-3", brand: "NANKANG", merchantName: "Pneus BE" });
  });

  it("keeps price history limited to observed numeric readings", () => {
    const detail = normalizeOfferDetail({ id: 7, name: "Produit", price: 99, link: "https://example.com", history: [{ price: 99, at: "2026-08-13T00:00:00" }, { price: null }, {}], price_min: 99, price_max: 99 });
    expect(detail.history).toEqual([{ price: 99, at: "2026-08-13T00:00:00" }]);
  });

  it("uses server-side category criteria and cursor offset rather than fetching the whole catalogue", () => {
    const params = buildFilonOfferSearchParams({ department: "high-tech", category: "Informatique", subcategory: "Ordinateurs portables", merchant: "acer-be", brand: "Acer", priceMin: 500, priceMax: 900, sort: "price_asc", limit: 24, offset: 48 });
    expect(params.toString()).toContain("department=high-tech");
    expect(params.toString()).toContain("category=Informatique");
    expect(params.toString()).toContain("subcategory=Ordinateurs+portables");
    expect(params.toString()).toContain("merchant=acer-be");
    expect(params.toString()).toContain("brand=Acer");
    expect(params.toString()).toContain("price_min=500");
    expect(params.toString()).toContain("price_max=900");
    expect(params.toString()).toContain("sort=price_asc");
    expect(params.get("offset")).toBe("48");
  });

  it("maps the factual source status and keeps the upstream synchronization state", () => {
    expect(normalizeFilonCataloguePulse({ live: true, last_reading: "2026-08-16T10:00:00Z", readings_24h: 12, sync: { status: "syncing", age_hours: 2 } })).toMatchObject({ live: true, readings24h: 12, syncStatus: "syncing", ageHours: 2 });
  });

  it("keeps only observed relief records with evidence of a lower current price", () => {
    const relief = normalizeFilonCatalogueRelief({ live: true, columns: [{ id: 1, name: "Casque", merchant: "Partenaire", price: 79, high: 99, low: 69, drop_pct: -20.2, tracked_days: 12, samples: 7 }, { id: 2, name: "Sans preuve", merchant: "Partenaire", price: 99, high: 99, low: 99, drop_pct: 0, tracked_days: 1, samples: 1 }] });
    expect(relief.items).toEqual([expect.objectContaining({ id: 1, dropPercentage: 20.2, confidence: null })]);
  });
});
