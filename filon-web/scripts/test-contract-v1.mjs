import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const contracts = join(projectRoot, "..", "contracts", "v1");
const json = (relative) => JSON.parse(readFileSync(join(contracts, relative), "utf8"));

const manifest = json("manifest.json");
assert.equal(manifest.contract_version, "1.0.0");
assert.equal(manifest.compatibility.unknown, "null_is_not_zero_false_or_true");

const unknown = json(manifest.examples.catalog_offer_unknown);
assert.equal(unknown.in_stock, null, "le snapshot doit porter un stock inconnu");

const productDetails = readFileSync(join(projectRoot, "components/filon/ProductDetails.tsx"), "utf8");
const offerDetails = readFileSync(join(projectRoot, "components/filon/OfferProductDetails.tsx"), "utf8");
const productTruth = readFileSync(join(projectRoot, "components/filon/product-copy.ts"), "utf8");
for (const source of [productDetails, offerDetails]) {
  assert.match(source, /isPurchasableOffer/);
  assert.match(source, /currentStockState/);
  assert.match(source, /availabilityUnknown|currentUnknown/);
}
assert.match(productTruth, /offer\.in_stock === true/);
assert.match(productTruth, /isFreshObservation\(offer\.observed_at/);
assert.match(productTruth, /offer\.evidence_current === true/);

console.log("✓ contrats v1 web : unknown conservé jusqu'au rendu et achat fail-closed");
