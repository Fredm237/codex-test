import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const extensionRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const contracts = join(extensionRoot, "..", "contracts", "v1");
const json = (relative) => JSON.parse(readFileSync(join(contracts, relative), "utf8"));

const manifest = json("manifest.json");
const context = json(manifest.examples.extension_search_context);
assert.equal(context.source, "extension");
assert.equal(context.medium, "fiche");
assert.ok(context.query.length <= 140);

const content = readFileSync(join(extensionRoot, "content.js"), "utf8");
const popup = readFileSync(join(extensionRoot, "popup.js"), "utf8");
assert.match(content, /slice\(0, 140\)/);
assert.match(content, /utm_source=extension&utm_medium=fiche/);
assert.match(popup, /utm_source=extension&utm_medium=popup/);

const publicCopy = [
  content,
  readFileSync(join(extensionRoot, "STORE-LISTING.md"), "utf8"),
  readFileSync(join(extensionRoot, "README.md"), "utf8"),
  readFileSync(join(extensionRoot, "manifest.json"), "utf8"),
  readFileSync(join(extensionRoot, "popup.html"), "utf8"),
  readFileSync(join(extensionRoot, "_locales/fr/messages.json"), "utf8"),
].join("\n").toLocaleLowerCase("fr");
for (const claim of [
  "tout le marché",
  "reconditionné certifié",
  "cashback maximal",
  "testé au paiement",
  "vrai prix le plus bas",
]) {
  assert.ok(!publicCopy.includes(claim), `claim non supporté : ${claim}`);
}
assert.match(publicCopy, /offres observées|offres indexées/);

console.log("✓ extension : contexte borné et claims publics sourcés");
