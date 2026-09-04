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

const homeVolume = readFileSync(join(root, "components/experience/HomeSignatureVolume.tsx"), "utf8");
const productVolume = readFileSync(join(root, "components/experience/signature/ProductIdentityVolume.tsx"), "utf8");
const signatureCanvas = readFileSync(join(root, "components/experience/signature/SignatureCommerceCanvas.tsx"), "utf8");
const webglContextLoss = readFileSync(join(root, "components/experience/signature/WebglContextLoss.mjs"), "utf8");
const filonCss = readFileSync(join(root, "components/filon/filon.css"), "utf8");

assert.ok(homeVolume.includes("components/experience/signature/SignatureCommerceCanvas"), "la home doit consommer la primitive de production");
assert.ok(productVolume.includes("./SignatureCommerceCanvas"), "le dossier produit doit consommer la même primitive de production");
assert.ok(signatureCanvas.includes("@react-three/fiber"), "la primitive finale doit rester une vraie scène R3F");
assert.ok(signatureCanvas.includes("THREE.OrthographicCamera"), "la décision doit conserver sa vraie caméra orthographique");
assert.ok(signatureCanvas.includes("bindWebglContextLoss(gl.domElement"), "le canvas actif doit armer son repli GPU");
assert.ok(webglContextLoss.includes('addEventListener("webglcontextlost"'), "une perte du contexte GPU doit être détectée");
assert.ok(webglContextLoss.includes("event.preventDefault()"), "la perte du contexte GPU doit rester restaurable par le navigateur");
assert.ok(webglContextLoss.includes('removeEventListener("webglcontextlost"'), "l'écouteur de perte GPU doit être nettoyé au démontage");
assert.ok(homeVolume.includes('onFailure={() => setState("fallback")}'), "la home doit revenir au DOM après une perte GPU");
assert.ok(productVolume.includes('onFailure={() => setState("fallback")}'), "le dossier produit doit revenir au DOM après une perte GPU");

const { bindWebglContextLoss } = await import("../components/experience/signature/WebglContextLoss.mjs");
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
assert.match(
  filonCss,
  /\.p19-product-surface \.pg-offer\s*\{[^}]*background:/s,
  "les offres du dossier sombre doivent imposer un fond lisible, indépendant du thème éditorial",
);
assert.match(
  filonCss,
  /\.p19-product-surface \.filon-decision-evidence li,[\s\S]*?color:\s*rgba\(255, 248, 239,/,
  "les preuves de décision doivent conserver un contraste explicite sur le dossier sombre",
);

console.log("✓ Frontière finale : laboratoire isolé, primitives 3D réutilisables, aucun label de démonstration public");
