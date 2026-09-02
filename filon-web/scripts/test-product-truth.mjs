import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const webRoot = join(dirname(fileURLToPath(import.meta.url)), "..");

function loadTypeScript(relativePath, dependencies = {}) {
  const source = readFileSync(join(webRoot, relativePath), "utf8");
  const output = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2022,
      esModuleInterop: true,
    },
    fileName: relativePath,
  }).outputText;
  const module = { exports: {} };
  const localRequire = (specifier) => {
    if (specifier in dependencies) return dependencies[specifier];
    throw new Error(`Dépendance inattendue dans ${relativePath}: ${specifier}`);
  };
  new Function("require", "module", "exports", output)(localRequire, module, module.exports);
  return module.exports;
}

const currency = loadTypeScript("lib/currency.ts");
const truth = loadTypeScript("components/filon/product-copy.ts", {
  "@/lib/currency": currency,
});
const jsonLd = loadTypeScript("lib/json-ld.ts");
const siteModule = loadTypeScript("lib/site.ts");
const siteUrls = loadTypeScript("lib/site-url.ts", { "./site": siteModule });
const catalogue = loadTypeScript("lib/catalogue.ts", {
  "@/lib/api": { API: "https://api.example.com" },
});
const assistantCatalogueUrl = loadTypeScript("lib/catalogue-assistant-url.ts", {
  "@/lib/catalogue": catalogue,
});

assert.equal(siteUrls.siteUrl(), "https://www.filon.be/");
assert.equal(siteUrls.siteUrl("/catalogue"), "https://www.filon.be/catalogue/");
assert.equal(siteUrls.siteUrl("/recherche?q={query}"), "https://www.filon.be/recherche/?q={query}");
assert.equal(catalogue.pageNumber({ page: "2" }), 2);
for (const page of ["2.5", "1e100", "9007199254740991", "0", "-1", "NaN"]) {
  assert.equal(catalogue.pageNumber({ page }), 1, `page catalogue non sûre : ${page}`);
}
assert.equal(catalogue.href({ page: "9", brand: "Acme" }, { page: "3" }), "/catalogue/?page=3&brand=Acme");
assert.equal(
  assistantCatalogueUrl.catalogueAssistantHref("Un casque sous 300 €"),
  catalogue.href({}, { dept: "high-tech", cat: "tv-son", sub: "Casques audio" }),
  "l'Assistant et le catalogue doivent partager le même constructeur d'URL",
);
assert.equal(
  assistantCatalogueUrl.catalogueAssistantHref("Thermos robuste 100 EUR"),
  catalogue.href({}, { q: "thermos robuste" }),
  "une recherche libre doit utiliser l'encodage canonique du catalogue",
);

const hostileJsonLd = jsonLd.serializeJsonLd({
  name: "</script><script>alert(1)</script>",
  separators: "\u2028\u2029",
});
assert.doesNotMatch(hostileJsonLd, /</, "un champ de flux ne doit jamais fermer le script JSON-LD");
assert.match(hostileJsonLd, /\\u003c\/script>/);
assert.match(hostileJsonLd, /\\u2028\\u2029/);

assert.equal(currency.normalizeSupportedCurrency(" eur "), "EUR");
for (const unknown of [null, "", "unknown", "XXX", "XTS", 123]) {
  assert.equal(currency.normalizeSupportedCurrency(unknown), null);
}
assert.deepEqual(currency.normalizeSupportedMoney(42, " eur "), { amount: 42, currency: "EUR" });
assert.match(currency.formatSupportedMoney(42, "EUR", "fr"), /€/);
assert.match(currency.formatSupportedMoney(42, "GBP", "en"), /£/);
for (const [amount, code] of [
  [42, null], [42, "XXX"], [Number.NaN, "EUR"], [Number.POSITIVE_INFINITY, "EUR"],
  [0, "EUR"], [-1, "EUR"],
]) {
  assert.equal(currency.normalizeSupportedMoney(amount, code), null);
  assert.equal(currency.formatSupportedMoney(amount, code, "fr"), null);
}

assert.match(truth.money(42, "EUR", "fr"), /€/);
assert.match(truth.money(42, "GBP", "en"), /£/);
for (const [amount, code] of [[42, null], [42, "XXX"], [Number.NaN, "EUR"], [0, "EUR"], [-1, "EUR"]]) {
  assert.equal(truth.money(amount, code, "fr"), "—", "aucun fallback EUR/symbole ne doit être inventé");
}

const now = Date.parse("2026-08-29T12:00:00.000Z");
assert.equal(truth.observationTimestamp("2026-08-29T12:00:00"), now, "une date SQL sans zone est UTC");
assert.equal(truth.isFreshObservation("2026-08-26T12:00:00.000Z", now), true, "72 h exactes restent dans la fenêtre");
assert.equal(truth.isFreshObservation("2026-08-26T11:59:59.999Z", now), false);
assert.equal(truth.isFreshObservation("2026-08-29T12:00:00.001Z", now), false, "une date future n'est jamais fraîche");
assert.equal(truth.observationAgeHours("2026-08-26T13:01:00.000Z", now), 70);
assert.equal(truth.observationAgeHours("2026-08-30T12:00:00.000Z", now), null);
for (const invalid of [null, "", "hier", "2026-13-40T99:00:00Z", "2026-02-30T12:00:00Z"]) {
  assert.equal(truth.isFreshObservation(invalid, now), false);
}

const validOffer = {
  id: 1,
  price: 99,
  currency: "EUR",
  in_stock: true,
  observed_at: "2026-08-29T11:00:00Z",
  evidence_current: true,
  link: "https://merchant.example.com/item",
};
assert.equal(truth.isPurchasableOffer(validOffer, now), true);
assert.equal(truth.hasCurrentOfferEvidence(validOffer, now), true);
for (const patch of [
  { price: null }, { price: 0 }, { price: Number.NaN }, { price: Number.POSITIVE_INFINITY },
  { currency: null }, { currency: "XXX" }, { in_stock: false }, { in_stock: null }, { evidence_current: false },
  { observed_at: null }, { observed_at: "2026-08-20T12:00:00Z" }, { observed_at: "2026-08-30T12:00:00Z" },
  { link: null }, { link: "http://merchant.example.com/item" }, { link: "javascript:alert(1)" }, { link: "https://intranet/item" }, { link: "https://router/item" }, { link: "https://merchant.local/item" }, { link: "https://merchant.internal/item" }, { link: "https://merchant.test/item" }, { link: "https://merchant.example/item" }, { link: "https://merchant.onion/item" }, { link: "https://localhost/item" }, { link: "https://localhost./item" }, { link: "https://foo.localhost./item" }, { link: "https://127.0.0.1/item" }, { link: "https://192.168.1.2/item" }, { link: "https://100.64.0.1/item" }, { link: "https://198.18.0.1/item" }, { link: "https://8.8.8.8/item" }, { link: "https://[::1]/item" }, { link: "https://[fec0::1]/item" }, { link: "https://[2001:4860:4860::8888]/item" }, { link: "https://[::ffff:127.0.0.1]/item" }, { link: "https://user:secret@merchant.example.com/item" },
]) {
  assert.equal(truth.isPurchasableOffer({ ...validOffer, ...patch }, now), false);
}
for (const patch of [
  { price: null }, { price: 0 }, { price: Number.NaN }, { currency: null }, { currency: "XXX" },
  { in_stock: null }, { evidence_current: false }, { observed_at: null },
  { observed_at: "2026-08-20T12:00:00Z" }, { observed_at: "2026-08-30T12:00:00Z" },
]) {
  assert.equal(truth.hasCurrentOfferEvidence({ ...validOffer, ...patch }, now), false);
}
assert.equal(
  truth.hasCurrentOfferEvidence({ ...validOffer, in_stock: false }, now),
  true,
  "un prix courant peut rester visible pour une indisponibilité explicitement attestée",
);
assert.equal(
  truth.hasCurrentOfferEvidence({ ...validOffer, link: null }, now),
  true,
  "le lien marchand ne fait pas partie de la preuve du montant",
);
assert.equal(truth.currentStockState({ in_stock: false, observed_at: "2026-08-29T11:00:00Z", evidence_current: true }, now), false);
assert.equal(truth.currentStockState({ in_stock: false, observed_at: "2026-08-20T12:00:00Z", evidence_current: true }, now), null);
assert.equal(truth.currentStockState({ in_stock: true, observed_at: "2026-08-29T11:00:00Z" }, now), null);

const mono = truth.deriveProductComparison([
  { ...validOffer, id: 3, price: 120 },
  { ...validOffer, id: 2, price: 80, currency: " eur " },
  { ...validOffer, id: 1, price: 1, currency: "GBP", observed_at: "2026-08-20T12:00:00Z" },
], now);
assert.ok(mono);
assert.equal(mono.currency, "EUR");
assert.deepEqual(mono.offers.map((offer) => offer.id), [2, 3]);
assert.equal(mono.priceMin, 80);
assert.equal(mono.priceMax, 120);

const mixed = [
  { ...validOffer, id: 5, price: 10, currency: "GBP" },
  { ...validOffer, id: 2, price: 100, currency: "EUR" },
];
assert.equal(truth.deriveProductComparison(mixed, now), null, "aucun agrégat multidevise");
assert.deepEqual(
  truth.orderOffersForDisplay(mixed).map((offer) => offer.id),
  [2, 5],
  "une liste multidevise est ordonnée par identité, jamais par montant",
);
assert.deepEqual(
  truth.orderOffersForDisplay([
    { ...validOffer, id: 8, price: 120 },
    { ...validOffer, id: 7, price: 80 },
  ]).map((offer) => offer.id),
  [7, 8],
);

const history = truth.comparablePriceHistory([
  { price: 120, at: "2026-08-20T12:00:00Z", in_stock: true },
  { price: 110, currency: "GBP", at: "2026-08-21T12:00:00Z", in_stock: true },
  { price: 100, currency: " eur ", at: "2026-08-22T12:00:00Z", in_stock: true },
  { price: 95, currency: "EUR", at: "2026-08-22T18:00:00Z", in_stock: false },
  { price: 90, currency: "EUR", at: "2026-08-23T12:00:00Z", in_stock: true },
  { price: 80, currency: "EUR", at: "2026-08-30T12:00:00Z", in_stock: true },
  { price: 0, currency: "EUR", at: "2026-08-24T12:00:00Z", in_stock: true },
], "EUR", now);
assert.deepEqual(history.map((point) => point.price), [100, 90]);
assert.equal(truth.comparableHistoryTrackedDays(history), 1);
assert.deepEqual(
  truth.comparablePriceHistory([{ price: 120, at: "2026-08-20T12:00:00Z", in_stock: true }], "EUR", now),
  [],
  "un historique legacy sans devise explicite reste inconnu",
);
assert.deepEqual(
  truth.comparablePriceHistory([{ price: 120, currency: "EUR", at: "2026-08-20T12:00:00Z" }], "EUR", now),
  [],
  "un historique sans disponibilité explicite reste inconnu",
);

const guardedPaths = [
  "components/filon/ProductCard.tsx",
  "components/filon/ProductDetails.tsx",
  "components/filon/OfferProductDetails.tsx",
  "components/filon/Rails.tsx",
  "components/filon/Proof.tsx",
  "lib/proof.ts",
  "app/(site)/produits/[ean]/page.tsx",
  "app/(site)/produit/[id]/page.tsx",
];
const guardedSources = guardedPaths.map((path) => ({ path, source: readFileSync(join(webRoot, path), "utf8") }));
for (const { path, source } of guardedSources) {
  assert.doesNotMatch(source, /currency\s*(?:\|\||\?\?)\s*["']EUR["']/, `${path} ne doit pas inventer EUR`);
  assert.doesNotMatch(source, /currency\s*===\s*["']GBP["']\s*\?\s*["']£/, `${path} ne doit pas inventer un symbole par défaut`);
}
for (const path of ["components/filon/ProductCard.tsx", "components/filon/ProductDetails.tsx", "components/filon/OfferProductDetails.tsx"]) {
  const source = guardedSources.find((entry) => entry.path === path).source;
  assert.ok(source.includes("isPurchasableOffer"), `${path} doit fermer ses actions marchandes sur les quatre preuves`);
  assert.ok(source.includes("hasCurrentOfferEvidence"), `${path} doit masquer les montants sans preuve courante`);
}
const productCardSource = guardedSources.find((entry) => entry.path === "components/filon/ProductCard.tsx").source;
assert.ok(productCardSource.includes("hasCurrentOfferEvidence"), "la carte doit masquer tout montant sans preuve courante");
assert.ok(productCardSource.includes("hasCurrentPrice ? offer.price : null"), "la carte ne doit pas seulement fermer son CTA");
for (const path of ["components/filon/ProductDetails.tsx", "components/filon/OfferProductDetails.tsx"]) {
  const source = guardedSources.find((entry) => entry.path === path).source;
  assert.ok(
    source.includes("hasCurrentPriceEvidence ? offer.price : null"),
    `${path} ne doit pas imprimer un prix brut non attesté`,
  );
}
const railsSource = guardedSources.find((entry) => entry.path === "components/filon/Rails.tsx").source;
assert.ok(railsSource.includes("currentItems"), "chaque rail doit exclure les cartes dont le prix n'est pas attesté");
assert.ok(
  guardedSources.find((entry) => entry.path.endsWith("produits/[ean]/page.tsx")).source.includes("offers: comparison ?"),
  "le JSON-LD agrégé doit disparaître sans comparaison monodevise",
);
for (const path of ["components/filon/ProductCard.tsx", "components/filon/Rails.tsx"]) {
  const source = guardedSources.find((entry) => entry.path === path).source;
  assert.ok(source.includes("price_low"), `${path} doit prouver le plancher avant le badge de plus bas prix`);
}
const offerDetailsSource = guardedSources.find((entry) => entry.path === "components/filon/OfferProductDetails.tsx").source;
assert.ok(offerDetailsSource.includes("signal.samples === history.length"), "le signal historique doit couvrir exactement les points comparables");
assert.ok(offerDetailsSource.includes("observationAgeHours"), "l'âge affiché doit être recalculé depuis le relevé");
for (const path of ["app/(site)/produits/[ean]/page.tsx", "app/(site)/produit/[id]/page.tsx"]) {
  const source = guardedSources.find((entry) => entry.path === path).source;
  assert.ok(source.includes("p11-product-surface"), `${path} doit annoncer sa surface claire au header global`);
}
const filonCssSource = readFileSync(join(webRoot, "components/filon/filon.css"), "utf8");
assert.ok(
  filonCssSource.includes("body:has(.p11-product-surface) .ed-header"),
  "les fiches produit doivent maintenir un contraste explicite dans la navigation",
);
const pulseSource = readFileSync(join(webRoot, "components/filon/Pulse.tsx"), "utf8");
assert.ok(pulseSource.includes("now - metricsCheckedAt <= METRICS_MAX_AGE_MS"), "les agrégats 24 h doivent expirer sans polling réussi");
assert.ok(pulseSource.includes("now >= metricsCheckedAt"), "une preuve de contrôle future doit rester inconnue");
assert.ok(pulseSource.includes("snapshot.dropsComparable === true"), "les baisses doivent porter un contrat de comparabilité explicite");
assert.ok(pulseSource.includes("fetch(PULSE_PROXY_PATH"), "le navigateur doit interroger le proxy same-origin");
assert.doesNotMatch(pulseSource, /@\/lib\/api/, "le navigateur ne doit plus interroger Railway directement");
assert.ok(pulseSource.includes("checkedAt <= receivedAt ? checkedAt : 0"), "le cache ne doit pas rajeunir les agrégats");

const pulseProxySource = readFileSync(join(webRoot, "app/api/catalog/pulse/route.ts"), "utf8");
assert.match(pulseProxySource, /s-maxage=120, must-revalidate/, "les lectures Pulse doivent être partagées environ 120 s");
assert.match(pulseProxySource, /cache: ["']no-store["']/, "seul le proxy doit lire Railway sans cache navigateur");
assert.ok(pulseProxySource.includes("proxy_checked_at"), "le proxy doit dater sa vraie lecture Railway");
assert.match(pulseProxySource, /status: 502/, "une panne amont doit rester une erreur");
assert.match(pulseProxySource, /headers: \{ ["']Cache-Control["']: ["']no-store["'] \}/, "une panne ne doit jamais être cachée");
assert.doesNotMatch(pulseProxySource, /stale-while-revalidate/i, "une panne ne doit pas resservir un succès périmé");

const assistantSource = readFileSync(join(webRoot, "components/editorial/SearchAssistant.tsx"), "utf8");
assert.ok(
  assistantSource.includes("catalogueAssistantHref"),
  "tous les retours Assistant doivent utiliser l'URL catalogue canonique",
);
assert.doesNotMatch(
  assistantSource,
  /`\/catalogue\/\?q=\$\{encodeURIComponent/,
  "l'Assistant ne doit plus construire une URL catalogue parallèle",
);
assert.ok(assistantSource.includes("normalizeSupportedMoney"), "les cartes Assistant doivent valider montant et devise");
assert.ok(assistantSource.includes("formatSupportedMoney"), "l'Assistant doit formater sans symbole de secours");
assert.ok(assistantSource.includes("hasCurrentOfferEvidence"), "l'Assistant doit exiger une preuve prix/stock récente");
assert.ok(assistantSource.includes("isSafeExternalOfferUrl"), "l'Assistant ne doit jamais ouvrir une cible marchande non sûre");
assert.ok(assistantSource.includes("verified.in_stock === true"), "l'Assistant ne recommande pas une offre au stock inconnu");
assert.doesNotMatch(assistantSource, /cur\s*=\s*["']€["']/, "l'Assistant ne doit pas choisir EUR par défaut");
assert.doesNotMatch(assistantSource, /currency\s*(?:\|\||\?\?)/, "une carte Assistant sans devise doit disparaître");
assert.doesNotMatch(assistantSource, /result\.currency\s*(?:\|\||\?\?)/, "le résultat global ne doit pas fournir de devise de secours");

console.log("✓ vérité produit web : devise, fraîcheur, achat et historique fail-closed");
