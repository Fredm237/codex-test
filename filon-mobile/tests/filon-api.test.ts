import { afterEach, describe, expect, it, vi } from "vitest";

import { buildFilonOfferSearchParams, formatFilonPrice, getFirstImageUrl, isFilonObservationFresh, isFilonOfferActionable, isFilonOfferPriceCurrent, normalizeFilonCatalogueNavigation, normalizeFilonCataloguePulse, normalizeFilonCatalogueRelief, normalizeOffer, normalizeOfferDetail, normalizeProduct, searchFilonOffers } from "../lib/filon-api";

afterEach(() => vi.unstubAllGlobals());

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
    const offer = normalizeOffer({ id: 7, name: "Casque test", price: 99.9, currency: "eur", observed_at: "2026-08-29T08:00:00Z", evidence_current: true, image: "https://images.filon.be/casque.jpg", link: "https://www.awin1.com/example", merchant: { name: "Partenaire test", slug: "partner" }, in_stock: true });
    expect(offer).toMatchObject({ id: 7, merchantName: "Partenaire test", imageUrl: "https://images.filon.be/casque.jpg", inStock: true, currency: "EUR", observedAt: "2026-08-29T08:00:00.000Z", evidenceCurrent: true });
  });

  it("preserves an unknown merchant availability instead of claiming the offer is in stock", () => {
    const offer = normalizeOffer({ id: 8, name: "Disponibilité inconnue", price: 19, currency: "EUR", link: "https://example.com", merchant: { name: "Partenaire" }, in_stock: null });
    expect(offer.inStock).toBeNull();
    expect(normalizeOffer({ id: 9, name: "Stock malformé", price: 19, currency: "EUR", link: "https://example.com", merchant: { name: "Partenaire" }, in_stock: "yes" as unknown as boolean }).inStock).toBeNull();
  });

  it("never invents a currency, merchant, identity or link", () => {
    const base = { id: 8, name: "Offre", price: 19, currency: "EUR", link: "https://example.com", merchant: { name: "Partenaire" } };
    expect(() => normalizeOffer({ ...base, currency: null })).toThrow();
    expect(() => normalizeOffer({ ...base, currency: "ZZZ" })).toThrow();
    expect(() => normalizeOffer({ ...base, merchant: null })).toThrow();
    expect(() => normalizeOffer({ ...base, id: 0 })).toThrow();
    expect(() => normalizeOffer({ ...base, name: " " })).toThrow();
    expect(() => normalizeOffer({ ...base, link: " " })).toThrow();
    expect(() => normalizeOffer({ ...base, price: Number.POSITIVE_INFINITY })).toThrow();
    expect(formatFilonPrice(19, "fr", null)).toBe("—");
  });

  it("requires one explicit current snapshot and an observation no older than 72 hours before action", () => {
    const now = new Date("2026-08-29T12:00:00Z");
    const offer = normalizeOffer({ id: 9, name: "Offre fraîche", price: 19, currency: "EUR", link: "https://example.com", merchant: { name: "Partenaire" }, in_stock: true, observed_at: "2026-08-26T12:00:00Z", evidence_current: true });
    expect(isFilonOfferPriceCurrent(offer, now)).toBe(true);
    expect(isFilonOfferActionable(offer, now)).toBe(true);
    expect(isFilonObservationFresh("2026-08-26T11:59:59.999Z", now)).toBe(false);
    expect(isFilonObservationFresh("2026-08-29T12:00:00.001Z", now)).toBe(false);
    expect(isFilonObservationFresh("2026-02-30T12:00:00Z", now)).toBe(false);
    expect(isFilonObservationFresh("2026-13-01T12:00:00Z", now)).toBe(false);
    expect(isFilonOfferActionable({ ...offer, inStock: null }, now)).toBe(false);
    expect(isFilonOfferActionable({ ...offer, price: 0 }, now)).toBe(false);
    expect(isFilonOfferActionable({ ...offer, evidenceCurrent: false }, now)).toBe(false);
    expect(isFilonOfferActionable({ ...offer, evidenceCurrent: undefined }, now)).toBe(false);
    expect(isFilonOfferPriceCurrent({ ...offer, observedAt: "2026-08-26T11:59:59.999Z" }, now)).toBe(false);
    const outOfStock = { ...offer, inStock: false };
    expect(isFilonOfferPriceCurrent(outOfStock, now)).toBe(true);
  });

  it("keeps the grouped product identity on every verified EAN offer", () => {
    const product = normalizeProduct({ ean: "4717622052664", name: "Winter Activa SV-3", brand: "NANKANG", category: "tyres", image: "https://example.com/product.jpg", price_min: 44.56, price_max: 50.01, currency: "EUR", offers_count: 2, merchants_count: 2, offers: [{ id: 1, price: 44.56, currency: "EUR", in_stock: true, link: "https://example.com/a", merchant: { name: "Pneus BE" } }, { id: 2, price: 50.01, currency: "EUR", in_stock: true, link: "https://example.com/b", merchant: { name: "Pneus NL" } }] });
    expect(product.offers[0]).toMatchObject({ name: "Winter Activa SV-3", brand: "NANKANG", merchantName: "Pneus BE" });
  });

  it("rejects multi-currency products and incoherent aggregate bounds", () => {
    const base = { ean: "123", name: "Produit", price_min: 10, price_max: 20, currency: "EUR", offers_count: 2, merchants_count: 2, offers: [{ id: 1, price: 10, currency: "EUR", link: "https://example.com/a", merchant: { name: "A" } }, { id: 2, price: 20, currency: "USD", link: "https://example.com/b", merchant: { name: "B" } }] };
    expect(() => normalizeProduct(base)).toThrow(/multidevises/);
    expect(() => normalizeProduct({ ...base, price_max: 19, offers: base.offers.map((offer) => ({ ...offer, currency: "EUR" })) })).toThrow(/bornes/);
  });

  it("keeps price history limited to comparable in-stock observations", () => {
    const detail = normalizeOfferDetail({ id: 7, name: "Produit", price: 99, currency: "EUR", link: "https://example.com", merchant: { name: "Partenaire" }, history: [{ price: 99, currency: "EUR", at: "2026-08-13T00:00:00", in_stock: true }, { price: 98, currency: "EUR", at: "2026-08-13T01:00:00" }, { price: 97, currency: "EUR", at: "2026-08-13T02:00:00", in_stock: null }, { price: 96, currency: "EUR", at: "2026-08-13T03:00:00", in_stock: false }, { price: 89, at: "2026-08-14T00:00:00", in_stock: true }, { price: 88, currency: "EUR", at: null, in_stock: true }, { price: 79, currency: "USD", at: "2026-08-15T00:00:00Z", in_stock: true }, { price: null, currency: "EUR", in_stock: true }, {}], price_min: 79, price_max: 99 });
    expect(detail.history).toEqual([{ price: 99, at: "2026-08-13T00:00:00.000Z" }]);
    expect(detail.priceMin).toBe(99);
    expect(detail.priceMax).toBe(99);
  });

  it("rejects future history and sorts accepted readings chronologically", () => {
    const detail = normalizeOfferDetail({
      id: 7,
      name: "Produit",
      price: 99,
      currency: "EUR",
      link: "https://example.com",
      merchant: { name: "Partenaire" },
      history: [
        { price: 95, currency: "EUR", at: "2026-08-29T11:00:00Z", in_stock: true },
        { price: 94, currency: "EUR", at: "2026-08-29T12:00:00.001Z", in_stock: true },
        { price: 97, currency: "EUR", at: "2026-08-29T09:00:00Z", in_stock: true },
        { price: 96, currency: "EUR", at: "2026-08-29T10:00:00Z", in_stock: true },
        { price: 93, currency: "EUR", at: "2026-08-29T12:00:00Z", in_stock: true },
      ],
    }, new Date("2026-08-29T12:00:00Z"));

    expect(detail.history).toEqual([
      { price: 97, at: "2026-08-29T09:00:00.000Z" },
      { price: 96, at: "2026-08-29T10:00:00.000Z" },
      { price: 95, at: "2026-08-29T11:00:00.000Z" },
      { price: 93, at: "2026-08-29T12:00:00.000Z" },
    ]);
    expect(detail.priceMin).toBe(93);
    expect(detail.priceMax).toBe(97);
  });

  it("uses factual server-side criteria and omits cross-currency price controls", () => {
    const params = buildFilonOfferSearchParams({ department: "high-tech", category: "Informatique", subcategory: "Ordinateurs portables", merchant: "acer-be", brand: "Acer", sort: "name", limit: 24, offset: 48 });
    expect(params.toString()).toContain("department=high-tech");
    expect(params.toString()).toContain("category=Informatique");
    expect(params.toString()).toContain("subcategory=Ordinateurs+portables");
    expect(params.toString()).toContain("merchant=acer-be");
    expect(params.toString()).toContain("brand=Acer");
    expect(params.toString()).not.toContain("price_min");
    expect(params.toString()).not.toContain("price_max");
    expect(params.toString()).toContain("sort=name");
    expect(params.get("offset")).toBe("48");
  });

  it("maps the factual source status and keeps the upstream synchronization state", () => {
    expect(normalizeFilonCataloguePulse({ live: true, last_reading: "2026-08-16T10:00:00Z", readings_24h: 12, drops_24h: 3, sync: { status: "syncing", age_hours: 2 } })).toMatchObject({ live: true, readings24h: 12, drops24h: 3, dropsComparable: false, syncStatus: "syncing", ageHours: 2 });
    expect(normalizeFilonCataloguePulse({ live: true, drops_24h: 3, drops_comparable: true })).toMatchObject({ drops24h: 3, dropsComparable: true });
    expect(normalizeFilonCataloguePulse({ live: true, readings_24h: -1, drops_24h: Number.NaN, sync: { age_hours: -2 } })).toMatchObject({ readings24h: null, drops24h: null, ageHours: null });
  });

  it("keeps only observed relief records with evidence of a lower current price", () => {
    const current = { id: 1, name: "Casque", merchant: "Partenaire", price: 79, currency: "EUR", history_currency: "EUR", observed_at: "2026-08-29T10:00:00Z", evidence_current: true, high: 99, low: 69, drop_pct: -20.2, tracked_days: 12, samples: 7 };
    const relief = normalizeFilonCatalogueRelief({ live: true, columns: [current, { ...current, id: 2, evidence_current: false }, { ...current, id: 3, history_currency: "USD" }, { ...current, id: 4, observed_at: "2026-08-26T11:59:59.999Z" }] }, new Date("2026-08-29T12:00:00Z"));
    expect(relief.items).toEqual([expect.objectContaining({ id: 1, observedAt: "2026-08-29T10:00:00.000Z", confidence: null })]);
    expect(relief.items[0]?.dropPercentage).toBeCloseTo((20 / 99) * 100, 8);
  });

  it("advances pagination by raw rows even when invalid offers are closed", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ total: 20, items: [{ id: 1, name: "Valide", price: 10, currency: "EUR", link: "https://example.com/a", merchant: { name: "A" } }, { id: 2, name: "Sans devise", price: 20, currency: null, link: "https://example.com/b", merchant: { name: "B" } }] }) }));
    const page = await searchFilonOffers({ limit: 2, offset: 10 });
    expect(page.items.map((offer) => offer.id)).toEqual([1]);
    expect(page.offset + page.items.length).toBe(12);
  });
});
