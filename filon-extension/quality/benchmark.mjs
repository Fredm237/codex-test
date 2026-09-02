import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const repo = join(root, "..");
const api = require(join(root, "product-observation.js"));
const manifest = JSON.parse(readFileSync(join(repo, "quality", "extension-observation-manifest.json"), "utf8"));
const cases = JSON.parse(readFileSync(join(root, "quality", "extension-observation-cases.json"), "utf8"));
const observedAt = "2026-09-02T08:00:00Z";

let passed = 0;
let validGtin = 0;
let validGtinFound = 0;
let invalidAccepted = 0;
let unsupportedPriceAccepted = 0;
let unsafeUrlRetained = 0;

for (const item of cases) {
  const jsonLd = item.input.json_ld;
  const observation = api.buildObservation({
    url: item.input.url,
    title: item.input.title,
    looksLikeProduct: item.input.looksLikeProduct,
    jsonLdTexts: jsonLd === undefined ? [] : [JSON.stringify(jsonLd)],
  }, observedAt);
  const expected = item.expected;
  let ok = Boolean(observation) === expected.observation;
  if (observation) {
    ok &&= observation.page.gtin === (expected.gtin ?? null);
    ok &&= observation.page.price?.amount === (expected.price ?? undefined);
    ok &&= observation.page.price?.currency === (expected.currency ?? undefined);
    ok &&= observation.page.availability === expected.availability;
    ok &&= observation.page.url === expected.url;
    if (/[?#]/.test(observation.page.url)) unsafeUrlRetained += 1;
  }
  if (expected.gtin) {
    validGtin += 1;
    validGtinFound += Number(observation?.page?.gtin === expected.gtin);
  }
  if (item.id === "invalid_gtin_rejected") invalidAccepted += Number(Boolean(observation?.page?.gtin));
  if (["price_without_currency_unknown", "aggregate_offer_unknown"].includes(item.id)) {
    unsupportedPriceAccepted += Number(Boolean(observation?.page?.price));
  }
  passed += Number(ok);
}

const extensionSources = ["background.js", "content.js", "popup.js", "product-observation.js"]
  .map((file) => readFileSync(join(root, file), "utf8"))
  .join("\n");
const automaticTransmissionCount = (extensionSources.match(/fetch\s*\(/g) || []).length;
const metrics = {
  cases: cases.length,
  passed,
  case_accuracy: passed / cases.length,
  valid_gtin_recall: validGtinFound / validGtin,
  invalid_gtin_acceptance: invalidAccepted,
  unsupported_price_acceptance: unsupportedPriceAccepted,
  unsafe_url_retention: unsafeUrlRetained,
  automatic_transmission_count: automaticTransmissionCount,
};
const t = manifest.thresholds;
assert.ok(metrics.case_accuracy >= t.case_accuracy_min);
assert.ok(metrics.valid_gtin_recall >= t.valid_gtin_recall_min);
assert.ok(metrics.invalid_gtin_acceptance <= t.invalid_gtin_acceptance_max);
assert.ok(metrics.unsupported_price_acceptance <= t.unsupported_price_acceptance_max);
assert.ok(metrics.unsafe_url_retention <= t.unsafe_url_retention_max);
assert.ok(metrics.automatic_transmission_count <= t.automatic_transmission_count_max);

const report = {
  schema_version: "extension-observation-quality-report/v1",
  dataset: manifest.dataset,
  cases_are_synthetic: true,
  external_human_ground_truth: false,
  status: "PASS",
  metrics,
};
const outputFlag = process.argv.indexOf("--output");
if (outputFlag >= 0) writeFileSync(resolve(process.argv[outputFlag + 1]), `${JSON.stringify(report, null, 2)}\n`);
console.log(`✓ extension Phase 12 benchmark : ${passed}/${cases.length}, GTIN recall=${metrics.valid_gtin_recall.toFixed(2)}, transmissions=${automaticTransmissionCount}`);
