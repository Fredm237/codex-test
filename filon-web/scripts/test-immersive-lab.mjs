import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const page = readFileSync(join(root, "app/(site)/laboratoire/experience/page.tsx"), "utf8");
const lab = readFileSync(join(root, "components/immersive-lab/ImmersiveLab.tsx"), "utf8");
const gate = readFileSync(join(root, "components/immersive-lab/FounderStoryGate.tsx"), "utf8");
const canvas = readFileSync(join(root, "components/immersive-lab/FounderStoryCanvas.tsx"), "utf8");
const css = readFileSync(join(root, "components/immersive-lab/founder-story.module.css"), "utf8");
const labCss = readFileSync(join(root, "components/immersive-lab/immersive-lab.module.css"), "utf8");
const runtime = readFileSync(join(root, "components/experience/signature/ImmersiveRuntime.tsx"), "utf8");
const labAccess = readFileSync(join(root, "lib/immersive-lab-access.ts"), "utf8");
const exactProof = readFileSync(join(root, "lib/immersive-proof.ts"), "utf8");
const fonts = readFileSync(join(root, "app/fonts.ts"), "utf8");

assert.ok(page.includes("getProof(),") && page.includes("await Promise.all"), "les preuves doivent être lues côté serveur sans cascade réseau");
assert.ok(page.includes("getImmersiveExactProductProof"), "le produit exact doit franchir une frontière de preuve dédiée");
assert.match(page, /robots:\s*\{\s*index:\s*false,\s*follow:\s*false\s*\}/, "le laboratoire ne doit pas être indexé");
assert.ok(page.includes("if (!isImmersiveLabEnabled()) notFound()"), "la route doit être fermée hors environnement autorisé");
assert.ok(labAccess.includes('environment.VERCEL_ENV === "preview"'), "une Preview doit pouvoir qualifier le laboratoire");
assert.ok(labAccess.includes('environment.NODE_ENV === "development"'), "le développement local doit pouvoir ouvrir le laboratoire");
assert.ok(labAccess.includes("if (explicit !== undefined) return ENABLED.has(explicit)"), "un override invalide doit fermer le laboratoire");

assert.ok(lab.includes("FounderStoryGate"), "le laboratoire doit rendre la séquence fondateur finale");
assert.doesNotMatch(lab, /CinematicJourney|SignatureMomentGate|type Direction/, "les anciennes démonstrations abstraites ne doivent plus être rendues");
assert.ok(lab.includes("formatSupportedMoney"), "les prix doivent respecter la frontière devise");
assert.doesNotMatch(lab, /currency\s*(?:\|\||\?\?)\s*["']EUR["']/, "aucune devise de secours n'est autorisée");
assert.ok(lab.includes("product.offers.map") && lab.includes("product.latestObservedAt"), "les offres et leur fraîcheur doivent rester visibles dans le DOM");
assert.ok(lab.includes("PerformanceObserver") && lab.includes('"largest-contentful-paint"'), "le laboratoire doit mesurer le LCP");
assert.ok(lab.includes('"layout-shift"') && lab.includes('"longtask"') && lab.includes('"event"'), "stabilité, tâches longues et interactions doivent être mesurées");
assert.ok(lab.includes('data-metric="immersive-longtask"') && lab.includes("filon-immersive-init-start"), "l'initialisation 3D doit être mesurable séparément");
assert.doesNotMatch(lab, /BUY_NOW|\bWAIT\b/, "aucun verdict shadow ne doit entrer dans le laboratoire");

assert.ok(gate.includes('dynamic(') && gate.includes('ssr: false'), "WebGL doit rester un enrichissement client différé");
assert.ok(gate.includes("IntersectionObserver") && gate.includes('rootMargin: "420px 0px"'), "le moteur ne doit charger qu'à proximité");
assert.ok(gate.includes("supportsImmersiveVolume"), "les appareils contraints doivent employer le récit statique");
assert.ok(gate.includes("product?.textureImage"), "seule la texture sûre doit entrer dans WebGL");
assert.ok(gate.includes("StaticStory"), "le récit doit survivre sans WebGL");
assert.ok(gate.includes("ImmersiveBoundary") && gate.includes("onFailure={failRuntime}"), "une erreur GPU ou texture doit rendre le récit statique");
assert.ok(gate.includes("hasPlayedRef") && gate.includes('capability === "webgl"'), "la scène doit s'exécuter à son entrée à l'écran");
assert.equal((gate.match(/label: "/g) || []).length, 6, "la séquence doit rester bornée à six battements lisibles");
assert.ok(gate.includes('type="range"') && gate.includes("Passer l’expérience"), "la séquence doit être contrôlable et évitable");
assert.ok(gate.includes('href="/recherche/"') && gate.includes("ProductJourneyLink"), "recherche et fiche produit doivent rester accessibles");
assert.ok(gate.includes("Le même produit. Des réponses différentes."), "la confusion marchande doit être compréhensible sans jargon");
assert.ok(gate.includes("Le bruit disparaît. Les preuves restent."), "la résolution doit être expliquée en langage humain");
assert.ok(gate.includes("product.offers.length") && gate.includes("product.ean"), "le résultat final doit refléter la preuve courante");
assert.doesNotMatch(gate, /LABORATOIRE|P19|PLAN 0|SHADOW|BUY_NOW|\bWAIT\b/, "la scène jugée ne doit exposer aucun vocabulaire de chantier");

assert.ok(canvas.includes("<Canvas") && canvas.includes("CameraJourney"), "le récit doit employer une vraie scène et une vraie caméra");
assert.ok(canvas.includes('style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}'), "le canvas doit occuper une surface mesurable même lorsque la scène repose sur une hauteur minimale");
assert.ok(canvas.includes("LaptopPortal") && canvas.includes("ShopBuilding"), "le monde doit réellement passer de l'ordinateur à la ville marchande");
assert.ok(canvas.includes("HeroProduct") && canvas.includes("ProductImage"), "le même produit texturé doit survivre à tous les plans");
assert.ok(canvas.includes("OfferMatter") && canvas.includes("wireframe={!admitted}"), "les offres inadmissibles doivent avoir une matérialité distincte");
assert.ok(canvas.includes("WorldToInterface"), "le monde doit se transformer en surface d'interface");
assert.ok(canvas.includes('next === "orthographic"'), "la décision doit employer une vraie projection orthographique");
assert.ok(canvas.includes("roughness") && canvas.includes("metalness"), "la preuve doit changer de matière, pas seulement d'opacité");
assert.ok(canvas.includes("useTexture(image)") && canvas.includes("map={texture}"), "l'image du produit réel doit devenir texture 3D");
assert.ok(canvas.includes("bindWebglContextLoss(gl.domElement"), "une perte GPU doit fermer proprement la scène");
assert.ok(canvas.includes('props.quality === "degraded" ? 1 : [1, 1.35]'), "la résolution GPU doit être adaptative");
assert.ok(canvas.includes('frameloop={props.playing ? "always" : "demand"}'), "une scène en pause ne doit pas maintenir une boucle GPU");
assert.ok(runtime.includes("FRAME_RATE_DEGRADE = 45") && runtime.includes("FRAME_RATE_FLOOR = 30"), "les seuils de dégradation et de repli doivent rester explicites");
assert.ok(gate.includes('capability === "webgl" && visible') && gate.includes("if (!visible) stop()"), "la boucle doit s'arrêter hors écran");

assert.ok(css.includes("min-height: 48px"), "les actions doivent conserver des cibles tactiles suffisantes");
assert.ok(css.includes("prefers-reduced-motion: reduce") && labCss.includes("prefers-reduced-motion: reduce"), "les deux couches CSS doivent neutraliser les mouvements réduits");
assert.doesNotMatch(css + labCss, /3000vh|1200vh|position:\s*sticky/, "la nouvelle histoire ne doit pas recréer un tunnel de scroll");
assert.ok(css.includes("#f5efe4") && css.includes("#53644d") && css.includes("#c85b3f"), "la palette doit rester claire, naturelle et identifiable");

assert.ok(exactProof.includes("evidence_current !== true"), "une offre non courante doit être exclue");
assert.ok(exactProof.includes("isFreshObservation") && exactProof.includes("currencies.size !== 1"), "fraîcheur et devise doivent fermer la comparaison");
assert.ok(exactProof.includes("merchants.size < 2"), "une source unique ne doit pas devenir une comparaison");
assert.doesNotMatch(exactProof, /currency\s*(?:\|\||\?\?)\s*["']EUR["']/, "la preuve exacte ne doit contenir aucune devise de secours");
assert.equal((fonts.match(/preload:\s*false/g) || []).length, 2, "les fontes secondaires ne doivent pas bloquer le premier rendu");
assert.doesNotMatch(fonts, /\.ttf["']/, "le graphe de fontes ne doit pas charger de TTF lourde");

console.log("✓ Récit fondateur : ordinateur, ville, produit continu, preuve, décision et interface réelle");
