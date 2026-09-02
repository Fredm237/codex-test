import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const api = require(join(root, "product-observation.js"));
const observedAt = "2026-09-02T08:00:00Z";
const product = JSON.stringify({
  "@context": "https://schema.org",
  "@type": "Product",
  name: "Sony WH-1000XM6 Black",
  brand: { "@type": "Brand", name: "Sony" },
  sku: "XM6-BLK",
  mpn: "WH1000XM6B.CE7",
  gtin13: "4006381333931",
  model: "WH-1000XM6",
  color: "Black",
  offers: {
    "@type": "Offer",
    price: "449.00",
    priceCurrency: "eur",
    availability: "https://schema.org/InStock",
  },
});

const exact = api.buildObservation({
  url: "https://merchant.example/products/xm6?utm_source=private#reviews",
  jsonLdTexts: [product],
  title: "fallback",
  looksLikeProduct: true,
}, observedAt);
assert.equal(exact.page.url, "https://merchant.example/products/xm6");
assert.equal(exact.page.merchant, "merchant.example");
assert.equal(exact.page.gtin, "4006381333931");
assert.deepEqual(exact.page.price, { amount: "449.00", currency: "EUR" });
assert.equal(exact.page.availability, "in_stock");
assert.equal(exact.capture_mode, "explicit_user_action");
assert.ok(!JSON.stringify(exact).includes("utm_source"));

const noCurrency = api.buildObservation({
  url: "https://merchant.example/p/1",
  jsonLdTexts: [JSON.stringify({ "@type": "Product", name: "Produit test", offers: { "@type": "Offer", price: "99.99" } })],
  looksLikeProduct: true,
}, observedAt);
assert.equal(noCurrency.page.price, null, "un montant sans devise doit rester inconnu");

const aggregate = api.buildObservation({
  url: "https://merchant.example/p/2",
  jsonLdTexts: [JSON.stringify({ "@type": "Product", name: "Produit multiple", offers: { "@type": "AggregateOffer", lowPrice: "10", highPrice: "20", priceCurrency: "EUR" } })],
  looksLikeProduct: true,
}, observedAt);
assert.equal(aggregate.page.price, null, "une fourchette ne doit pas devenir un prix exact");
assert.equal(aggregate.page.availability, "unknown");

assert.equal(api.normalizeGtin("4006381333931"), "4006381333931");
assert.equal(api.normalizeGtin("4006381333932"), null);
assert.equal(api.canonicalUrl("http://merchant.example/p"), null);
assert.equal(api.canonicalUrl("https://user:pass@merchant.example/p"), null);
assert.equal(api.buildObservation({ url: "https://merchant.example/category", title: "Rayon", looksLikeProduct: false, jsonLdTexts: [] }, observedAt), null);

console.log("✓ extension Phase 12 : observation bornée, exacte et respectueuse de la vie privée");
