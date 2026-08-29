/**
 * Tests des fonctions de taxonomie du méga-menu.
 *
 * Ces trois fonctions décident *quoi* le visiteur voit dans le menu du
 * catalogue. Une régression y est silencieuse : le menu s'affiche, il est
 * simplement faux — c'est exactement ce qui a fait disparaître « Montres »
 * (18 662 produits) derrière « Boucles d'oreilles » (2 883) pendant des mois.
 * D'où ce garde-fou.
 *
 * `filon-web` n'a aucune infrastructure de test JS. Plutôt que d'imposer
 * vitest ou jest — leurs arbres de dépendances, leur configuration, leur
 * entretien — pour trois fonctions pures, on compile le composant avec le
 * TypeScript déjà présent, on retire ses imports (React et les alias `@/`
 * ne servent qu'au composant visuel, pas aux fonctions testées) et on
 * exécute les assertions avec `node:assert`. Aucune dépendance ajoutée.
 *
 * Usage : node scripts/test-megamenu.mjs   (ou `npm test`)
 */

import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const outDir = mkdtempSync(join(tmpdir(), "mm-test-"));

/** Compile le composant et en extrait un module exécutable sous Node.
 *
 *  Les erreurs TS2307 (« module @/lib/api introuvable ») sont attendues :
 *  on compile un fichier isolé, hors du contexte de résolution de Next.
 *  L'émission a lieu malgré tout, et les imports sont de toute façon retirés.
 */
function loadModule() {
  try {
    execFileSync(
      "npx",
      [
        "tsc",
        "components/editorial/MegaMenu.tsx",
        "--outDir", outDir,
        "--module", "esnext",
        "--target", "es2022",
        "--moduleResolution", "bundler",
        "--jsx", "react-jsx",
        "--skipLibCheck",
      ],
      { cwd: projectRoot, stdio: "pipe" }
    );
  } catch (err) {
    const output = String(err.stdout ?? "") + String(err.stderr ?? "");
    const unexpected = output
      .split("\n")
      .filter((line) => line.includes("error TS") && !line.includes("TS2307"));
    if (unexpected.length > 0) {
      throw new Error(`Compilation de MegaMenu.tsx en échec :\n${unexpected.join("\n")}`);
    }
  }

  const compiled = join(outDir, "MegaMenu.js");
  const stripped = readFileSync(compiled, "utf8").replace(/^import .*?;\s*$/gm, "");
  const runnable = join(outDir, "megamenu.mjs");
  writeFileSync(runnable, stripped);
  return import(runnable);
}

const { pickSubcategories, pickCategories, detailedCategorySlugs, balanceColumns } = await loadModule();

const tests = [];
const test = (name, fn) => tests.push([name, fn]);

const sub = (name, count) => ({ name, count });

/** Reproduit les slugs de l'API : accents dépliés, puis non-alphanumériques
 *  réduits à des tirets. « Téléphonie » donne bien `telephonie`, et non
 *  `t-l-phonie` — une translittération naïve rendait les tests faux plutôt
 *  que le code. Vérifié contre /api/catalog/categories en production. */
const slugify = (name) =>
  name
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");

const cat = (name, count, subcategories = []) => ({
  name,
  slug: slugify(name),
  count,
  subcategories,
});
const dep = (name, count, categories) => ({
  name,
  slug: slugify(name),
  count,
  categories,
});

/* ---------------------------------------------------------------- *
 * pickSubcategories : les plus gros, pas les premiers venus
 * ---------------------------------------------------------------- */

test("pickSubcategories retient les sous-rayons les plus fournis", () => {
  // Ordre volontairement trompeur : « Montres » arrive en dernier, comme
  // dans la réponse réelle de l'API où l'ancien slice(0, 4) le perdait.
  const bijoux = [
    sub("Boucles d'oreilles", 2883),
    sub("Colliers", 5464),
    sub("Bracelets", 6790),
    sub("Bagues", 8021),
    sub("Montres", 18662),
  ];
  assert.deepEqual(
    pickSubcategories(bijoux).map((s) => s.name),
    ["Montres", "Bagues", "Bracelets", "Colliers"]
  );
});

test("pickSubcategories n'écarte plus « Montres » (régression historique)", () => {
  const bijoux = [
    sub("Boucles d'oreilles", 2883),
    sub("Colliers", 5464),
    sub("Bracelets", 6790),
    sub("Bagues", 8021),
    sub("Montres", 18662),
  ];
  const noms = pickSubcategories(bijoux).map((s) => s.name);
  assert.ok(noms.includes("Montres"), "« Montres » doit figurer dans le menu");
  assert.ok(
    !noms.includes("Boucles d'oreilles"),
    "« Boucles d'oreilles » ne doit pas évincer un sous-rayon 6,5 fois plus gros"
  );
});

test("pickSubcategories départage les égalités par ordre alphabétique", () => {
  // Sans cet ordre secondaire, deux chargements peuvent inverser deux entrées
  // et le menu paraît instable au visiteur.
  const egaux = [sub("Zèbre", 100), sub("Alpaga", 100), sub("Mouton", 100)];
  assert.deepEqual(
    pickSubcategories(egaux, 3).map((s) => s.name),
    ["Alpaga", "Mouton", "Zèbre"]
  );
});

test("pickSubcategories respecte la limite demandée", () => {
  const subs = Array.from({ length: 10 }, (_, i) => sub(`S${i}`, i));
  assert.equal(pickSubcategories(subs, 2).length, 2);
  assert.equal(pickSubcategories(subs).length, 4, "défaut attendu : 4");
});

test("pickSubcategories tolère l'absence de sous-rayons", () => {
  // L'API omet le champ pour les rayons plats : ne pas jeter d'exception.
  assert.deepEqual(pickSubcategories(undefined), []);
  assert.deepEqual(pickSubcategories([]), []);
});

test("pickSubcategories ne modifie pas le tableau reçu", () => {
  // Le tableau vient du rendu serveur et est partagé : le trier en place
  // ferait muter la donnée sous les autres consommateurs.
  const subs = [sub("A", 1), sub("B", 9)];
  const avant = subs.map((s) => s.name);
  pickSubcategories(subs);
  assert.deepEqual(subs.map((s) => s.name), avant);
});

/* ---------------------------------------------------------------- *
 * detailedCategorySlugs : détailler les rayons qui pèsent
 * ---------------------------------------------------------------- */

test("detailedCategorySlugs déploie les rayons les plus lourds", () => {
  // Chiffres de production pour High-Tech.
  const highTech = dep("High-Tech", 111296, [
    cat("Téléphonie", 72634),
    cat("Gaming", 20680),
    cat("Informatique", 15547),
    cat("Photo", 1261),
    cat("TV & Son", 1174),
  ]);
  const slugs = detailedCategorySlugs(highTech);
  assert.equal(slugs.size, 3);
  assert.ok(slugs.has("telephonie"));
  assert.ok(slugs.has("gaming"));
  assert.ok(slugs.has("informatique"));
  assert.ok(!slugs.has("photo"), "Photo (1 261 produits) reste en accès direct");
});

test("detailedCategorySlugs s'adapte aux départements courts", () => {
  const beaute = dep("Beauté & Santé", 68973, [cat("Beauté & Parfum", 68030), cat("Santé", 943)]);
  assert.equal(detailedCategorySlugs(beaute).size, 2);
});

test("detailedCategorySlugs ne modifie pas l'ordre des rayons du département", () => {
  // L'ordre d'affichage des rayons est celui de l'API ; seul le choix des
  // rayons détaillés dépend du poids.
  const d = dep("Maison", 24434, [cat("Petit", 10), cat("Gros", 9000), cat("Moyen", 500)]);
  detailedCategorySlugs(d);
  assert.deepEqual(d.categories.map((c) => c.name), ["Petit", "Gros", "Moyen"]);
});

/* ---------------------------------------------------------------- *
 * balanceColumns : trois colonnes de hauteur comparable
 * ---------------------------------------------------------------- */

/** Coût en lignes, reproduit indépendamment de l'implémentation. */
function measure(column) {
  return column.reduce((total, d) => {
    const categories = pickCategories(d.categories);
    const detailed = detailedCategorySlugs(d);
    return (
      total +
      1 +
      categories.length +
      categories.reduce(
        (n, c) => n + (detailed.has(c.slug) ? pickSubcategories(c.subcategories).length : 0),
        0
      )
    );
  }, 0);
}

/** Taxonomie proche de la production : 6 départements très inégaux. */
function productionTaxonomy() {
  const withSubs = (name, count, nSubs) =>
    cat(name, count, Array.from({ length: nSubs }, (_, i) => sub(`${name} ${i}`, (i + 1) * 100)));
  return [
    dep("Mode & Accessoires", 365129, [
      withSubs("Mode femme", 99298, 6),
      withSubs("Mode homme", 118399, 6),
      withSubs("Bijoux & Montres", 47180, 5),
      withSubs("Mode enfant", 24092, 4),
      withSubs("Chaussures", 40000, 4),
      withSubs("Accessoires", 20000, 5),
      withSubs("Bagages", 8000, 3),
      withSubs("Lingerie", 8160, 3),
    ]),
    dep("Famille & Quotidien", 210701, [
      withSubs("Auto & Moto", 168082, 5),
      withSubs("Animalerie", 26050, 4),
      withSubs("Bébé & Puériculture", 10388, 4),
      withSubs("Fournitures", 6181, 3),
    ]),
    dep("High-Tech", 111296, [
      withSubs("Téléphonie", 72634, 5),
      withSubs("Gaming", 20680, 4),
      withSubs("Informatique", 15547, 5),
      withSubs("Photo", 1261, 3),
      withSubs("TV & Son", 1174, 3),
    ]),
    dep("Sport & Loisirs", 69429, [
      withSubs("Sport & Plein air", 44420, 5),
      withSubs("Jeux & Jouets", 25009, 4),
    ]),
    dep("Beauté & Santé", 68973, [withSubs("Beauté & Parfum", 68030, 5), withSubs("Santé", 943, 3)]),
    dep("Maison", 24434, [
      withSubs("Maison & Déco", 14850, 5),
      withSubs("Électroménager", 4276, 4),
      withSubs("Jardin & Bricolage", 5308, 4),
    ]),
  ];
}

test("balanceColumns égalise la hauteur des colonnes", () => {
  const cols = balanceColumns(productionTaxonomy());
  assert.equal(cols.length, 3);
  const charges = cols.map(measure);
  const ecart = Math.max(...charges) - Math.min(...charges);
  // Sans équilibrage, l'écart atteignait 30 lignes (36 contre 6).
  assert.ok(ecart <= 12, `écart entre colonnes trop grand : ${ecart} lignes (${charges})`);
});

test("balanceColumns ne perd ni ne duplique aucun département", () => {
  const departements = productionTaxonomy();
  const noms = balanceColumns(departements)
    .flat()
    .map((d) => d.name)
    .sort();
  assert.deepEqual(noms, departements.map((d) => d.name).sort());
});

test("balanceColumns est déterministe", () => {
  // Un menu qui change de disposition à chaque rendu donne une impression
  // de désordre, et casse l'hydratation React (serveur ≠ client).
  const a = balanceColumns(productionTaxonomy()).map((c) => c.map((d) => d.name));
  const b = balanceColumns(productionTaxonomy()).map((c) => c.map((d) => d.name));
  assert.deepEqual(a, b);
});

test("balanceColumns ne rend aucune colonne vide", () => {
  const cols = balanceColumns([dep("Seul", 10, [cat("R", 10)])]);
  assert.ok(cols.every((c) => c.length > 0));
  assert.equal(cols.length, 1);
});

test("balanceColumns tolère une taxonomie vide", () => {
  // Le backend peut répondre une liste vide ; le menu doit rester silencieux
  // plutôt que d'échouer au rendu.
  assert.deepEqual(balanceColumns([]), []);
});

test("balanceColumns accepte un nombre de colonnes différent", () => {
  // Le rendu passe à 2 colonnes puis 1 sur écran étroit.
  assert.equal(balanceColumns(productionTaxonomy(), 2).length, 2);
  assert.equal(balanceColumns(productionTaxonomy(), 1).length, 1);
});

test("balanceColumns ne modifie pas la liste reçue", () => {
  const departements = productionTaxonomy();
  const avant = departements.map((d) => d.name);
  balanceColumns(departements);
  assert.deepEqual(departements.map((d) => d.name), avant);
});

/* ---------------------------------------------------------------- *
 * Densité : le menu doit tenir sur un écran de portable
 * ---------------------------------------------------------------- */

test("le menu tient dans la hauteur d'un panneau de 780 px", () => {
  // Le panneau plafonne à min(calc(100vh - 120px), 780px) ; une ligne de menu
  // occupe environ 26 px, soit à peu près 30 lignes par colonne. Ce test fixe
  // la limite au-delà de laquelle le visiteur devrait faire défiler.
  const cols = balanceColumns(productionTaxonomy());
  const lignesMax = Math.max(...cols.map(measure));
  assert.ok(lignesMax <= 34, `colonne la plus haute : ${lignesMax} lignes, plafond 34`);
});

/* ---------------------------------------------------------------- *
 * Exécution
 * ---------------------------------------------------------------- */

let echecs = 0;
for (const [name, fn] of tests) {
  try {
    fn();
    console.log(`  ok    ${name}`);
  } catch (err) {
    echecs += 1;
    console.error(`  ÉCHEC ${name}`);
    console.error(`        ${err.message.split("\n").join("\n        ")}`);
  }
}

rmSync(outDir, { recursive: true, force: true });

const total = tests.length;
console.log(
  echecs === 0
    ? `\n${total} tests, tous réussis.`
    : `\n${total} tests, ${echecs} en échec.`
);
process.exit(echecs === 0 ? 0 : 1);
