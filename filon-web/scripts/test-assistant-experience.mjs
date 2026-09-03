import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const assistant = readFileSync(join(root, "components/editorial/SearchAssistant.tsx"), "utf8");
const marketCss = readFileSync(join(root, "components/experience/search-market.module.css"), "utf8");

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
assert.ok(assistant.includes('data-market-state={phase}'), "la recherche doit rester un plan de marché continu");
assert.ok(assistant.includes("FILON / MARCHÉ 01"), "le chapitre recherche doit prolonger la grammaire immersive");
assert.doesNotMatch(assistant, /<video|sa-bg-poster|setFilmOpen/, "la recherche ne doit pas retomber sur un film ou une image d'ambiance générique");
assert.ok(marketCss.includes("prefers-reduced-motion: reduce"), "le plan de marché doit conserver un mode réduit");

console.log("✓ Phase 19 assistant : marché continu, offres courantes, sans ranking ni BUY/WAIT public");
