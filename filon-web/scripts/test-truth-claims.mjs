import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const webRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const repositoryRoot = join(webRoot, "..");
const paths = [
  "filon-web/lib/site.ts",
  "filon-web/lib/i18n.tsx",
  "filon-web/components/filon/ImmersiveExperience.tsx",
  "filon-web/components/filon/CategoryDetails.tsx",
  "filon-web/components/filon/Proof.tsx",
  "filon-web/components/filon/ProductDetails.tsx",
  "filon-web/components/filon/OfferProductDetails.tsx",
  "filon-web/components/editorial/EditorialSections.tsx",
  "filon-web/components/editorial/EditorialFooter.tsx",
  "filon-web/components/editorial/Faq.tsx",
  "filon-web/components/editorial/NeuralNetwork.tsx",
  "filon-web/components/editorial/Scenes.tsx",
  "filon-web/components/editorial/Transformation.tsx",
  "filon-web/app/(site)/page.tsx",
  "filon-web/app/(site)/cashback/page.tsx",
  "filon-web/app/(site)/codes-promo/page.tsx",
  "filon-web/app/(site)/comment-ca-marche/page.tsx",
  "filon-web/app/(site)/score/page.tsx",
  "filon-web/app/(site)/aide/page.tsx",
  "filon-web/app/(site)/extension/page.tsx",
  "filon-web/app/(site)/intelligence/page.tsx",
  "filon-web/app/(site)/tarifs/page.tsx",
  "filon-web/app/(site)/carrieres/page.tsx",
  "filon-web/app/(site)/a-propos/page.tsx",
  "filon-web/app/(site)/recherche/page.tsx",
  "filon-web/app/(site)/partenaires/page.tsx",
  "filon-web/app/(site)/catalogue/page.tsx",
  "filon-web/app/(site)/produits/[ean]/page.tsx",
  "filon-web/app/(site)/categorie/[slug]/page.tsx",
  "filon-web/app/(site)/produit/[id]/page.tsx",
  "filon-web/app/(site)/marchands/page.tsx",
  "filon-web/app/(site)/reconditionne/page.tsx",
  "filon-web/app/(site)/transparence/page.tsx",
  "filon-web/app/(site)/faq/page.tsx",
  "filon-web/app/(site)/cgu/page.tsx",
  "filon-web/app/(site)/mentions-legales/page.tsx",
  "filon-web/app/(site)/confidentialite/page.tsx",
  "filon-web/app/(site)/securite/page.tsx",
  "filon-web/app/(site)/presse/page.tsx",
  "filon-web/app/(site)/blog/page.tsx",
  "filon-web/app/(site)/blog/neuf-vs-reconditionne-economie-reelle/page.tsx",
  "filon-web/app/(site)/blog/black-friday-sans-se-faire-avoir/page.tsx",
  "filon-web/app/(site)/blog/quelle-app-cashback-paie-le-plus/page.tsx",
  "filon-extension/STORE-LISTING.md",
  "filon-extension/content.js",
  "filon-extension/README.md",
  "filon-extension/manifest.json",
  "filon-extension/popup.html",
  "filon-extension/_locales/fr/messages.json",
];

const sources = paths.map((path) => ({
  path,
  value: readFileSync(join(repositoryRoot, path), "utf8").toLocaleLowerCase("fr"),
}));
const forbidden = [
  "tout le marché",
  "de hele markt",
  "the whole market",
  "chez tous les marchands",
  "vendeurs certifiés",
  "gecertificeerde verkopers",
  "certified sellers",
  "reconditionné certifié",
  "cashback maximal",
  "teste chaque code en direct",
  "test elke code live",
  "tests every code live",
  "testé au paiement",
  "verified at checkout",
  "ne payez plus jamais trop cher",
  "betaal nooit meer te veel",
  "never overpay again",
  "le vrai prix",
  "de echte prijs",
  "the real price",
  "marchands partenaires",
  "partnerwinkels",
  "partner merchants",
  "analyse complète",
  "analysis is complete",
  "augmente jamais le prix",
  "verhoogt nooit de prijs",
  "never increases the price",
  "sans jamais vous coûter plus cher",
  "without ever costing you more",
  "sans surcoût pour vous",
  "zonder extra kost voor jou",
  "at no additional cost to you",
  "entièrement gratuit",
  "volledig gratis",
  "entirely free",
  "gratuit pour toujours",
  "gratis voor altijd",
  "free forever",
  "restera gratuit",
  "will stay free",
  "aucune lecture automatique",
  "aucune donnée collectée",
  "no data collected",
  "avant chaque achat",
  "vóór elke aankoop",
  "before every purchase",
  "l'économie réelle",
  "l&apos;économie réelle",
  "de echte besparing",
  "the real saving",
  "il analyse prix, cashback",
  "aide chaque jour des personnes",
  "helps people buy better every day",
  "helpt elke dag mensen",
  "lorsqu’ils sont vérifiés pour l’achat",
  "once they have been verified for the purchase",
  "−134",
  "-€134",
];

for (const phrase of forbidden) {
  const locations = sources
    .filter((source) => source.value.includes(phrase))
    .map((source) => source.path);
  assert.deepEqual(locations, [], `claim non supporté « ${phrase} » dans ${locations.join(", ")}`);
}

const score = sources.find((source) => source.path.endsWith("/score/page.tsx")).value;
for (const evidence of ["comparaison de prix", "historique", "disponibilité", "fraîcheur", "largeur de comparaison"]) {
  assert.ok(score.includes(evidence), `la page Score doit documenter ${evidence}`);
}

const outfitStudio = readFileSync(
  join(repositoryRoot, "filon-web/components/intelligence/OutfitStudio.tsx"),
  "utf8",
);
assert.ok(
  outfitStudio.includes("confidence_not_calibrated:"),
  "Outfit Studio doit traduire l’unknown de confiance au lieu d’afficher sa clé brute",
);
for (const label of [
  "La confiance n’est pas encore mesurée sur un jeu indépendant",
  "Het vertrouwen is nog niet gemeten op een onafhankelijke dataset",
  "Confidence has not yet been measured on an independent dataset",
]) {
  assert.ok(outfitStudio.includes(label), `traduction de confiance manquante : ${label}`);
}
assert.ok(
  outfitStudio.includes("sanitizeOutfitResponse(await res.json(), trimmed)"),
  "Outfit Studio doit valider la réponse JSON avant de l'afficher",
);
assert.ok(
  !outfitStudio.includes("formatScore(solution.confidence_score"),
  "Outfit Studio ne doit jamais publier une confiance numérique non calibrée",
);
assert.ok(
  outfitStudio.includes("solution.confidence_band === \"not_calibrated\""),
  "Outfit Studio doit exiger explicitement une confiance non calibrée",
);

const decisionPanel = readFileSync(
  join(repositoryRoot, "filon-web/components/filon/DecisionPanel.tsx"),
  "utf8",
);
for (const proof of ["hasPrice", "hasAvailability", "hasFreshness", "hasCurrency", "hasComparison", "hasFavourableHistory"]) {
  assert.ok(decisionPanel.includes(proof), `DecisionPanel doit dégrader un claim favorable sans preuve ${proof}`);
}

const verdict = readFileSync(
  join(repositoryRoot, "filon-web/components/editorial/Verdict.tsx"),
  "utf8",
);
assert.ok(
  verdict.includes("observations en stock"),
  "Verdict doit qualifier le périmètre de l'historique affiché",
);

const recommendService = readFileSync(
  join(repositoryRoot, "filon-backend/app/services/recommend.py"),
  "utf8",
);
assert.ok(
  !recommendService.includes('"evidence_score":'),
  "L'assistant ne doit pas republier un score de preuve pondé non calibré",
);

console.log("✓ claims publics : périmètre observé, unknown et abstention conservés");
