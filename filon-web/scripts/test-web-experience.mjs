import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const page = readFileSync(join(root, "app/(site)/page.tsx"), "utf8");
const experience = readFileSync(join(root, "components/experience/WebExperience.tsx"), "utf8");
const primitives = readFileSync(join(root, "components/experience/DecisionPrimitives.tsx"), "utf8");
const css = readFileSync(join(root, "components/experience/web-experience.module.css"), "utf8");
const globalCss = readFileSync(join(root, "components/filon/filon.css"), "utf8");

assert.ok(page.includes("<WebExperience proof={proof} />"), "la home doit rendre l'expérience Phase 11");
assert.ok(page.includes("await getProof()"), "les chiffres home doivent venir du catalogue réel");
for (const forbidden of ["ImmersiveExperience", "/seq/", "canvas", "video", "three"])
  assert.doesNotMatch(page, new RegExp(forbidden, "i"), `la home ne doit pas charger ${forbidden}`);

for (const component of [
  "EvidenceBadge", "ConfidenceIndicator", "UnknownField", "OfferComparison",
  "DecisionCard", "TradeoffCard", "ConstraintSummary", "WhyThisResult",
]) assert.ok(primitives.includes(`function ${component}`), `primitive manquante : ${component}`);

assert.ok(experience.includes('role="search"'), "le parcours principal doit exposer une recherche accessible");
assert.ok(experience.includes('htmlFor="p11-query"'), "la recherche doit avoir un label explicite");
assert.ok(experience.includes("p11-web-experience"), "la home doit annoncer sa surface au header global");
assert.ok(globalCss.includes("body:has(.p11-web-experience) .ed-header"), "le header Phase 11 doit conserver un contraste explicite");
assert.ok(experience.includes("formatSupportedMoney"), "aucun montant ne doit contourner la frontière devise");
assert.ok(experience.includes("<UnknownField"), "l'indisponibilité live doit rester explicitement inconnue");
assert.ok(experience.includes('state={comparable ? "verified" : "unknown"}'), "la carte doit être fail-closed");
assert.doesNotMatch(experience, /BUY_NOW|\bWAIT\b/, "les lecteurs BUY/WAIT shadow restent hors du web public");
assert.doesNotMatch(experience, /currency\s*(?:\|\||\?\?)\s*["']EUR["']/, "aucune devise de secours");
assert.doesNotMatch(css, /--font-(?:fraunces|outfit|inter)\b/, "la page doit utiliser les variables de fontes réellement déclarées");
assert.ok(css.includes("prefers-reduced-motion: reduce"), "la politique reduced-motion doit être explicite");
const animationDeclarations = [...css.matchAll(/animation(?:-[a-z-]+)?\s*:\s*([^;}]+)/gi)]
  .map((match) => match[1].trim());
assert.ok(
  animationDeclarations.every((value) => /^none(?:\s*!important)?$/i.test(value)),
  "la home Phase 11 ne doit pas dépendre d'une animation",
);

console.log("✓ Phase 11 web : evidence-first, fail-closed, accessible et sans séquence immersive");
