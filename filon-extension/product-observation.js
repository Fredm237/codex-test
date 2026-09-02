/* FILON Phase 12 — extraction déterministe d'une observation produit.
 *
 * Module UMD sans dépendance : chargé par Manifest V3 et testable sous Node.
 * Il ne lit ni cookies, ni stockage, ni HTML brut. L'appelant fournit seulement
 * les signaux explicitement autorisés par le contrat.
 */
(function expose(root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.FilonProductObservation = api;
})(typeof globalThis === "object" ? globalThis : this, function createApi() {
  "use strict";

  const VERSION = "1.0.0";
  const TEXT_LIMITS = Object.freeze({ title: 300, brand: 191, sku: 191, mpn: 191, model: 191, color: 128, size: 128 });
  const AVAILABILITY = Object.freeze({
    instock: "in_stock",
    outofstock: "out_of_stock",
    preorder: "preorder",
    preorderavailability: "preorder",
    backorder: "backorder",
  });

  function text(value, max) {
    if (value === null || value === undefined) return null;
    const normalized = String(value).replace(/\s+/g, " ").trim();
    return normalized ? normalized.slice(0, max) : null;
  }

  function canonicalUrl(raw) {
    try {
      const parsed = new URL(String(raw));
      if (parsed.protocol !== "https:" || !parsed.hostname || parsed.username || parsed.password) return null;
      parsed.search = "";
      parsed.hash = "";
      const safe = `${parsed.origin}${parsed.pathname || "/"}`;
      return safe.length <= 2048 ? safe : null;
    } catch {
      return null;
    }
  }

  function normalizeGtin(value) {
    const raw = text(value, 32);
    if (!raw) return null;
    const digits = raw.replace(/[\s-]/g, "");
    if (!/^\d+$/.test(digits) || ![8, 12, 13, 14].includes(digits.length)) return null;
    const body = [...digits.slice(0, -1)].reverse();
    const sum = body.reduce((total, digit, index) => total + Number(digit) * (index % 2 === 0 ? 3 : 1), 0);
    const check = (10 - (sum % 10)) % 10;
    return Number(digits.at(-1)) === check ? digits : null;
  }

  function normalizeCurrency(value) {
    const currency = text(value, 3)?.toUpperCase() || null;
    return currency && /^[A-Z]{3}$/.test(currency) ? currency : null;
  }

  function normalizeAmount(value) {
    if (typeof value === "number") return Number.isFinite(value) && value > 0 ? String(value) : null;
    const raw = text(value, 64);
    if (!raw) return null;
    const compact = raw.replace(/\s/g, "");
    const decimal = compact.includes(",") && !compact.includes(".") ? compact.replace(",", ".") : compact;
    if (!/^\d+(?:\.\d{1,4})?$/.test(decimal)) return null;
    const amount = Number(decimal);
    return Number.isFinite(amount) && amount > 0 ? decimal : null;
  }

  function normalizeAvailability(value) {
    const raw = text(value, 128);
    if (!raw) return "unknown";
    const key = raw.split("/").at(-1).replace(/[^a-z]/gi, "").toLowerCase();
    return AVAILABILITY[key] || "unknown";
  }

  function typesOf(value) {
    const type = value && value["@type"];
    return (Array.isArray(type) ? type : [type]).filter(Boolean).map(String);
  }

  function collectProducts(value, output, depth, budget) {
    if (!value || depth > 6 || budget.count >= 128) return;
    if (Array.isArray(value)) {
      for (const item of value) collectProducts(item, output, depth + 1, budget);
      return;
    }
    if (typeof value !== "object") return;
    budget.count += 1;
    if (typesOf(value).includes("Product")) output.push(value);
    if (Array.isArray(value["@graph"])) collectProducts(value["@graph"], output, depth + 1, budget);
  }

  function parseProducts(jsonLdTexts) {
    const products = [];
    for (const source of Array.isArray(jsonLdTexts) ? jsonLdTexts.slice(0, 32) : []) {
      if (typeof source !== "string" || source.length > 1_000_000) continue;
      try {
        collectProducts(JSON.parse(source), products, 0, { count: 0 });
      } catch {
        // JSON-LD malformé : aucune supposition.
      }
    }
    return products.slice(0, 16);
  }

  function brandOf(product) {
    const value = product && product.brand;
    return text(value && typeof value === "object" ? value.name : value, TEXT_LIMITS.brand);
  }

  function gtinOf(product) {
    for (const field of ["gtin14", "gtin13", "gtin12", "gtin8", "gtin"]) {
      const normalized = normalizeGtin(product && product[field]);
      if (normalized) return { value: normalized, field };
    }
    return { value: null, field: null };
  }

  function singleOffer(product) {
    const offers = product && product.offers;
    if (Array.isArray(offers)) return offers.length === 1 && offers[0] && typeof offers[0] === "object" ? offers[0] : null;
    if (!offers || typeof offers !== "object" || typesOf(offers).includes("AggregateOffer")) return null;
    return offers;
  }

  function chooseProduct(products) {
    if (products.length === 1) return products[0];
    if (!products.length) return null;
    const byGtin = new Map();
    for (const product of products) {
      const gtin = gtinOf(product).value;
      if (gtin) byGtin.set(gtin, product);
    }
    return byGtin.size === 1 ? [...byGtin.values()][0] : null;
  }

  function buildObservation(input, observedAt) {
    const safeUrl = canonicalUrl(input && input.url);
    if (!safeUrl) return null;
    const products = parseProducts(input.jsonLdTexts);
    const product = chooseProduct(products);
    const fallbackTitle = text(input.title, TEXT_LIMITS.title);
    const title = text(product && product.name, TEXT_LIMITS.title) || (input.looksLikeProduct ? fallbackTitle : null);
    if (!title || title.length < 3) return null;
    const merchant = new URL(safeUrl).hostname.toLowerCase();
    const offer = singleOffer(product);
    const amount = normalizeAmount(offer && offer.price);
    const currency = normalizeCurrency(offer && offer.priceCurrency);
    const gtin = gtinOf(product);
    const sourceFields = [];
    if (product) {
      for (const field of ["name", "brand", "sku", "mpn", "model", "color", "size"]) {
        if (product[field] !== null && product[field] !== undefined) sourceFields.push(field);
      }
      if (gtin.field) sourceFields.push(gtin.field);
      if (offer && offer.price !== null && offer.price !== undefined) sourceFields.push("offers.price");
      if (offer && offer.priceCurrency !== null && offer.priceCurrency !== undefined) sourceFields.push("offers.priceCurrency");
      if (offer && offer.availability !== null && offer.availability !== undefined) sourceFields.push("offers.availability");
    }
    return {
      contract_version: VERSION,
      capture_mode: "explicit_user_action",
      page: {
        url: safeUrl,
        merchant,
        title,
        brand: brandOf(product),
        sku: text(product && product.sku, TEXT_LIMITS.sku),
        mpn: text(product && product.mpn, TEXT_LIMITS.mpn),
        gtin: gtin.value,
        price: amount && currency ? { amount, currency } : null,
        availability: normalizeAvailability(offer && offer.availability),
        variant: {
          model: text(product && product.model, TEXT_LIMITS.model),
          color: text(product && product.color, TEXT_LIMITS.color),
          size: text(product && product.size, TEXT_LIMITS.size),
        },
        json_ld: { present: Boolean(product), source_fields: [...new Set(sourceFields)].sort() },
      },
      observed_at: observedAt,
    };
  }

  return Object.freeze({
    VERSION,
    buildObservation,
    canonicalUrl,
    normalizeAmount,
    normalizeAvailability,
    normalizeCurrency,
    normalizeGtin,
    parseProducts,
  });
});
