import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const productionRoots = [join(root, "app/(site)"), join(root, "components")];
const excluded = [
  join(root, "app/(site)/laboratoire"),
  join(root, "components/immersive-lab"),
];

function sourceFiles(directory) {
  if (excluded.some((entry) => directory === entry || directory.startsWith(`${entry}/`))) return [];
  return readdirSync(directory).flatMap((name) => {
    const path = join(directory, name);
    if (statSync(path).isDirectory()) return sourceFiles(path);
    return /\.(?:ts|tsx)$/.test(name) ? [path] : [];
  });
}

const sources = productionRoots.flatMap(sourceFiles).map((path) => ({
  path: relative(root, path),
  source: readFileSync(path, "utf8"),
}));

for (const { path, source } of sources) {
  assert.doesNotMatch(source, /FILON \/ PLAN|LABORATOIRE|P19[A-Z]/, `${path} expose encore le vocabulaire de qualification`);
  assert.doesNotMatch(source, /@\/components\/immersive-lab/, `${path} dépend encore directement du laboratoire`);
}

const homeJourney = readFileSync(join(root, "components/experience/CommerceJourney.tsx"), "utf8");
const productVolume = readFileSync(join(root, "components/experience/signature/ProductIdentityVolume.tsx"), "utf8");
const signatureCanvas = readFileSync(join(root, "components/experience/signature/SignatureCommerceCanvas.tsx"), "utf8");
const webglContextLoss = readFileSync(join(root, "components/experience/signature/WebglContextLoss.mjs"), "utf8");
const sequenceRenderer = readFileSync(join(root, "components/cinematic/CinematicSequenceRenderer.tsx"), "utf8");
const filonCss = readFileSync(join(root, "components/filon/filon.css"), "utf8");
const productContrast = readFileSync(join(root, "components/filon/product-contrast.css"), "utf8");
const siteLayout = readFileSync(join(root, "app/(site)/layout.tsx"), "utf8");

assert.ok(productVolume.includes("./SignatureCommerceCanvas"), "le dossier produit doit consommer la même primitive de production");
assert.ok(homeJourney.includes('data-direction="industrial"'), "la home doit rester sur la direction cinématique qualifiée");
assert.doesNotMatch(homeJourney, /requestedDirection|HomeSignatureVolume/, "aucune variante de laboratoire ne doit survivre dans la home finale");
assert.doesNotMatch(productVolume, /world="grand-receipt"/, "le dossier produit doit conserver sa caméra d'identité dédiée");
assert.ok(signatureCanvas.includes("@react-three/fiber"), "la primitive finale doit rester une vraie scène R3F");
const spriteFrames = readdirSync(join(root, "public/cinematic/filon-scroll-story/desktop-v7-sprites4")).filter((name) => /^\d{4}\.webp$/.test(name));
assert.equal(spriteFrames.length, 91, "les 363 frames du film doivent être regroupées dans 91 planches bornées");
assert.ok(homeJourney.includes("<CinematicSequenceRenderer"), "la home doit lire le film image par image sur le canvas");
assert.ok(homeJourney.includes("frameProgress={progress}"), "le scroll doit sélectionner directement la frame du film");
assert.ok(sequenceRenderer.includes("assetWindow(targetAsset"), "le lecteur doit évincer les planches décodées hors de la fenêtre visible");
assert.ok(sequenceRenderer.includes("sequence.finalPoster ?? sequence.poster"), "le mouvement réduit doit montrer la décision finale statique");
assert.ok(homeJourney.includes("data-industrial-decision"), "le film doit conclure par une action honnête distincte d'un produit dynamique");
assert.ok(homeJourney.includes('href="/recherche/"'), "la décision du film doit conduire à une vraie recherche");
assert.ok(signatureCanvas.includes("THREE.OrthographicCamera"), "la décision doit conserver sa vraie caméra orthographique");
assert.ok(signatureCanvas.includes("bindWebglContextLoss(gl.domElement"), "le canvas actif doit armer son repli GPU");
assert.ok(webglContextLoss.includes('addEventListener("webglcontextlost"'), "une perte du contexte GPU doit être détectée");
assert.ok(webglContextLoss.includes("event.preventDefault()"), "la perte du contexte GPU doit rester restaurable par le navigateur");
assert.ok(webglContextLoss.includes('removeEventListener("webglcontextlost"'), "l'écouteur de perte GPU doit être nettoyé au démontage");
assert.ok(productVolume.includes('onFailure={() => setState("fallback")}'), "le dossier produit doit revenir au DOM après une perte GPU");

const publicSource = sources.map(({ source }) => source).join("\n");
for (const obsolete of [
  "/seq/", "/seq-light/", "/seq-mobile/", "/seq-light-mobile/", "/film/", "/immersive/",
  "/cinematic/interior-city/", "/cinematic/filon-industrial-world/", "/cinematic/filon-world/", "/cinematic/actors/",
]) assert.doesNotMatch(publicSource, new RegExp(obsolete.replaceAll("/", "\\/")), `l'expérience publique ne doit plus charger l'asset supersédé ${obsolete}`);

const { bindWebglContextLoss } = await import("../components/experience/signature/WebglContextLoss.mjs");
const { frameWindow, shouldRetainFrame } = await import("../components/cinematic/FrameWindow.mjs");
const firstWindow = frameWindow(0, 363, 1);
const middleWindow = frameWindow(181, 363, 1);
const finalWindow = frameWindow(362, 363, 1);
assert.deepEqual(firstWindow, { from: 0, to: 24 }, "le démarrage ne doit précharger qu'une fenêtre bornée");
assert.deepEqual(middleWindow, { from: 173, to: 205 }, "la fenêtre médiane doit rester bornée à 33 images");
assert.deepEqual(finalWindow, { from: 354, to: 362 }, "la fin ne doit pas dépasser la séquence");
assert.equal(shouldRetainFrame(170, middleWindow), false, "une image décodée éloignée doit être évincée");
assert.equal(shouldRetainFrame(0, middleWindow), true, "la première image de repli doit rester disponible");
const contextTarget = new EventTarget();
let failureCount = 0;
const unbindContextLoss = bindWebglContextLoss(contextTarget, () => { failureCount += 1; });
const lostEvent = new Event("webglcontextlost", { cancelable: true });
contextTarget.dispatchEvent(lostEvent);
assert.equal(failureCount, 1, "une perte GPU doit déclencher exactement un repli");
assert.equal(lostEvent.defaultPrevented, true, "la restauration native du contexte doit rester autorisée");
unbindContextLoss();
contextTarget.dispatchEvent(new Event("webglcontextlost", { cancelable: true }));
assert.equal(failureCount, 1, "le listener GPU doit disparaître avec le canvas");
assert.ok(siteLayout.includes('product-contrast.css'), "la palette finale de contraste doit être chargée après la grammaire P19");
assert.match(productContrast, /\.p19-offer-title,[\s\S]*?color:\s*#2a211c\s*!important/, "le titre d'une offre doit rester sombre sur le dossier clair");
assert.match(productContrast, /\[data-experience-chapter="decision"\][\s\S]*?\.ed-content-hero h1\s*\{\s*color:\s*#2a211c/, "les chapitres Décision doivent conserver un titre lisible sur l'argile claire");
assert.match(productContrast, /\.p19-cashback-gate li\s*\{\s*color:\s*#2a211c/, "les étapes Cashback doivent conserver un contraste explicite");
assert.match(productContrast, /@media \(max-width:\s*760px\)[\s\S]*?\.ed-content-photo\s*\{[\s\S]*?position:\s*relative/, "la photo Décision doit passer sous le texte avant de pouvoir le masquer");

console.log("✓ Frontière finale : laboratoire isolé, primitives 3D réutilisables, aucun label de démonstration public");
