import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const assistant = readFileSync(join(root, "components/editorial/SearchAssistant.tsx"), "utf8");

assert.ok(assistant.includes("normalizeSupportedMoney"), "l'assistant doit normaliser montant et devise");
assert.ok(assistant.includes("hasCurrentOfferEvidence"), "l'assistant doit exiger une preuve courante");
assert.ok(assistant.includes("ev.data.real"), "les estimations ne doivent pas devenir des offres FILON");
assert.ok(assistant.includes("verifiedCards.length === 0"), "zéro offre vérifiée doit rester un échec honnête");
assert.ok(assistant.includes("displayedPrice === null) return null"), "une carte sans prix admissible doit rester masquée");
assert.ok(assistant.includes("currentEvidence"), "la carte doit annoncer uniquement la preuve courante");
assert.ok(assistant.includes("verifiedOffer"), "la carte doit utiliser un libellé factuel");
assert.doesNotMatch(assistant, /\bc\.buy\b/, "aucun lecteur BUY/WAIT ne doit piloter l'assistant public");
assert.doesNotMatch(assistant, /\bc\.rank\b/, "aucun lecteur Product Ranking ne doit classer l'assistant public");
assert.doesNotMatch(assistant, /currency\s*(?:\|\||\?\?)\s*["']EUR["']/, "aucune devise de secours");
assert.doesNotMatch(assistant, /<video[^>]+autoPlay/i, "le film facultatif ne doit jamais démarrer seul");

console.log("✓ Phase 11 assistant : offres courantes, sans ranking ni BUY/WAIT public");
