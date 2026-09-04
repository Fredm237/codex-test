import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const page = readFileSync(join(root, "app/(site)/page.tsx"), "utf8");
const experience = readFileSync(join(root, "components/experience/WebExperience.tsx"), "utf8");
const immersiveProof = readFileSync(join(root, "lib/immersive-proof.ts"), "utf8");
const homeVolume = readFileSync(join(root, "components/experience/HomeSignatureVolume.tsx"), "utf8");
const immersiveRuntime = readFileSync(join(root, "components/experience/signature/ImmersiveRuntime.tsx"), "utf8");
const primitives = readFileSync(join(root, "components/experience/DecisionPrimitives.tsx"), "utf8");
const css = readFileSync(join(root, "components/experience/web-experience.module.css"), "utf8");
const globalCss = readFileSync(join(root, "components/filon/filon.css"), "utf8");
const editorialCss = readFileSync(join(root, "components/editorial/editorial.css"), "utf8");
const forms = readFileSync(join(root, "components/editorial/Forms.tsx"), "utf8");
const editorialNav = readFileSync(join(root, "components/editorial/EditorialNav.tsx"), "utf8");
const languageSwitcher = readFileSync(join(root, "components/editorial/LanguageSwitcher.tsx"), "utf8");
const stickyCta = readFileSync(join(root, "components/editorial/StickyCta.tsx"), "utf8");
const skipToContent = readFileSync(join(root, "components/editorial/SkipToContent.tsx"), "utf8");
const skipLink = readFileSync(join(root, "components/editorial/SkipLink.tsx"), "utf8");
const merchantsPage = readFileSync(join(root, "app/(site)/marchands/page.tsx"), "utf8");
const categoryDetails = readFileSync(join(root, "components/filon/CategoryDetails.tsx"), "utf8");

assert.ok(page.includes("<WebExperience exactProduct={exactProduct} proof={proof} />"), "la home doit rendre l'expérience Phase 19");
assert.ok(page.includes("getProof(),"), "les chiffres home doivent venir du catalogue réel");
assert.ok(page.includes("getImmersiveExactProductProof()"), "l'objet caméra doit franchir une preuve produit détaillée");
assert.ok(immersiveProof.includes("EDITORIAL_CANDIDATE_QUERIES"), "l'objet phare doit être choisi dans des familles éditoriales réelles");
for (const family of ["montre connectée", "chaussures", "casque à conduction osseuse"])
  assert.ok(immersiveProof.includes(`"${family}"`), `la famille ${family} doit participer à la sélection réelle`);
assert.ok(immersiveProof.includes("dailyIndex(editorialProducts.length)"), "l'objet phare ne doit pas rester figé sur un produit permanent");
assert.ok(immersiveProof.includes("SECONDARY_PRODUCT_MARKERS"), "les accessoires ne doivent pas devenir l'objet phare");
assert.ok(immersiveProof.includes("priceMax > priceMin") && immersiveProof.includes("comparedMerchants >= 2"), "la sélection éditoriale doit conserver une comparaison mesurable");
assert.doesNotMatch(immersiveProof, /\b\d{13}\b/, "aucun EAN ne doit être fixé dans le sélecteur éditorial");
assert.ok(immersiveProof.includes("IMMERSIVE_TEXTURE_HOSTS") && immersiveProof.includes("IMMERSIVE_TEXTURE_MAX_BYTES"), "une image marchande ne doit devenir texture qu'après une frontière CDN bornée");
assert.ok(immersiveProof.includes("Buffer.from(bytes).toString(\"base64\")"), "la texture WebGL doit devenir locale au document pour ne pas dépendre du CORS marchand");
assert.ok(homeVolume.includes("product.textureImage ?? null"), "la Home ne doit jamais envoyer l'URL marchande brute au chargeur WebGL");
for (const forbidden of ["ImmersiveExperience", "/seq/", "canvas", "video", "three"])
  assert.doesNotMatch(page, new RegExp(forbidden, "i"), `la home ne doit pas charger ${forbidden}`);

for (const component of [
  "EvidenceBadge", "ConfidenceIndicator", "UnknownField", "OfferComparison",
  "DecisionCard", "TradeoffCard", "ConstraintSummary", "WhyThisResult",
]) assert.ok(primitives.includes(`function ${component}`), `primitive manquante : ${component}`);

assert.ok(experience.includes('role="search"'), "le parcours principal doit exposer une recherche accessible");
assert.ok(experience.includes('htmlFor="home-query"'), "la recherche doit avoir un label explicite");
assert.ok(experience.includes("p11-web-experience"), "la home doit annoncer sa surface au header global");
assert.ok(experience.includes("data-shot={journeyShot}"), "la home doit être pilotée comme une suite de plans");
assert.ok(experience.includes("requestAnimationFrame(update)"), "le scroll ne doit pas provoquer de travail hors trame");
assert.ok(experience.includes('targetId="home-after-journey"'), "le chapitre immersif doit être évitable au clavier");
assert.ok(experience.includes('id="home-after-journey"') && experience.includes("tabIndex={-1}"), "la sortie du chapitre home doit recevoir le focus");
assert.ok(experience.includes('aria-labelledby="home-example-title"'), "la sélection phare doit référencer son vrai titre accessible");
assert.ok(experience.includes("prefers-reduced-motion: reduce"), "la home doit détecter le mouvement réduit");
assert.ok(experience.includes("connection?.saveData"), "la home doit respecter l'économie de données");
assert.ok(experience.includes("data-immersive-journey"), "le chapitre doit exposer sa frontière aux contrôles globaux");
assert.ok(experience.includes("<HomeSignatureVolume"), "la home validée doit exécuter la caméra causale réelle");
assert.doesNotMatch(experience, /FILON \/ PLAN|LABORATOIRE|P19[A-Z]/, "la home finale ne doit pas exposer le vocabulaire du laboratoire");
assert.doesNotMatch(experience, /shotRail|\["CHAOS", "IDENTITÉ", "MARCHÉ", "DÉCISION"\]/, "la home finale doit faire vivre la séquence sans afficher son storyboard");
assert.ok(experience.includes("setJourneyProgress(progress)"), "la caméra réelle doit suivre la progression continue du chapitre");
assert.ok(homeVolume.includes('dynamic('), "le moteur spatial doit rester dans un chunk différé");
assert.ok(homeVolume.includes('ssr: false'), "le moteur WebGL ne doit pas entrer dans le rendu serveur");
assert.ok(immersiveRuntime.includes("requestIdleCallback"), "la couche spatiale doit attendre le temps navigateur disponible");
assert.ok(immersiveRuntime.includes('(max-width: 820px)'), "la caméra doit employer sa composition mobile autonome");
assert.ok(immersiveRuntime.includes("connection?.saveData"), "la couche spatiale doit respecter l'économie de données");
assert.ok(immersiveRuntime.includes("deviceMemory < 4"), "la couche spatiale doit refuser les appareils contraints");
assert.ok(immersiveRuntime.includes('getContext("webgl2"'), "la capacité WebGL doit être testée avant chargement");
assert.ok(homeVolume.includes("ImmersiveBoundary"), "une erreur 3D doit retomber sur le parcours DOM qualifié");
assert.ok(stickyCta.includes('querySelector<HTMLElement>("[data-immersive-journey]")'), "le CTA mobile ne doit pas couvrir le chapitre immersif");
assert.ok(stickyCta.includes("journeyIsComplete"), "le CTA mobile doit attendre la fin du chapitre immersif");
assert.ok(stickyCta.includes('pathname.startsWith("/recherche/")'), "le CTA ne doit pas répéter la destination sur la recherche");
assert.match(stickyCta, /querySelectorAll(?:<HTMLElement>)?\("\[data-sticky-cta-avoid\]"\)/, "le CTA doit céder la place aux outils interactifs mobiles");
assert.ok(stickyCta.includes("!safeZoneIsVisible"), "une zone interactive visible doit masquer le CTA fixe");
assert.ok(stickyCta.includes("getBoundingClientRect()"), "les zones hydratées tardivement doivent être réévaluées au scroll");
assert.ok(stickyCta.includes('document.addEventListener("focusin"'), "le CTA doit disparaître pendant une saisie mobile");
assert.ok(experience.includes("comparable ? copy.journey : copy.journeyUnknown"), "la narration doit s'abstenir si le produit exact n'est pas comparable");
assert.ok(experience.includes("FILON vous le dit clairement."), "l'unknown doit être expliqué dans un langage accessible");
for (const jargon of ["identité exacte survit", "périmètre disponible", "devise explicitement supportée", "données live"])
  assert.doesNotMatch(experience, new RegExp(jargon, "i"), `le langage public ne doit pas exposer le jargon « ${jargon} »`);
for (const promise of ["Le bon produit.", "Les prix sous les yeux.", "FILON vérifie avant de comparer."])
  assert.ok(experience.includes(promise), `la Home doit conserver le message direct « ${promise} »`);
assert.ok(globalCss.includes("body:has(.p11-web-experience) .ed-header"), "le header Phase 11 doit conserver un contraste explicite");
assert.ok(experience.includes("formatSupportedMoney"), "aucun montant ne doit contourner la frontière devise");
assert.ok(experience.includes("<UnknownField"), "l'indisponibilité live doit rester explicitement inconnue");
assert.ok(experience.includes('state={comparable ? "verified" : "unknown"}'), "la carte doit être fail-closed");
assert.doesNotMatch(experience, /BUY_NOW|\bWAIT\b/, "les lecteurs BUY/WAIT shadow restent hors du web public");
assert.doesNotMatch(experience, /currency\s*(?:\|\||\?\?)\s*["']EUR["']/, "aucune devise de secours");
assert.doesNotMatch(css, /--font-(?:fraunces|outfit|inter)\b/, "la page doit utiliser les variables de fontes réellement déclarées");
assert.ok(css.includes("prefers-reduced-motion: reduce"), "la politique reduced-motion doit être explicite");
assert.match(css, /\.hero\s*\{[^}]*height:\s*360vh/s, "le scroll doit piloter un plan continu, pas une pile de sections");
assert.match(css, /\.heroSticky\s*\{[^}]*position:\s*sticky/s, "la caméra DOM doit rester stable entre les plans");
assert.match(css, /\.hero\[data-reduced="true"\]\s*\{[^}]*height:\s*auto/s, "le mouvement réduit ne doit pas conserver un tunnel de scroll");
assert.match(css, /\.proofBand \.sectionHead h2\s*\{[^}]*color:\s*#fff8ef/s, "le titre de preuve doit rester lisible sur le plan sombre");
assert.match(editorialCss, /\.ed-lang-trigger\s*\{[^}]*min-height:\s*44px/s, "le sélecteur de langue doit garder une cible tactile de 44 px");
assert.match(editorialCss, /\.ed-lang-opt\s*\{[^}]*min-height:\s*44px/s, "chaque option de langue doit garder une cible tactile de 44 px");
assert.match(forms, /<input name="email" type="email" aria-label=\{T\.email\}/, "le champ newsletter doit conserver un nom accessible");
assert.match(editorialNav, /aria-controls="filon-mobile-navigation"/, "le bouton mobile doit désigner le panneau contrôlé");
assert.match(editorialNav, /event\.key !== "Escape"/, "le menu mobile doit pouvoir être fermé au clavier");
assert.match(editorialNav, /burgerRef\.current\?\.focus\(\)/, "le menu mobile doit restituer le focus à sa fermeture");
assert.match(languageSwitcher, /aria-controls=\{listboxId\}/, "le sélecteur de langue doit désigner sa liste");
assert.match(languageSwitcher, /tabIndex=\{open \? 0 : -1\}/, "les langues masquées doivent rester hors du parcours clavier");
assert.match(languageSwitcher, /triggerRef\.current\?\.focus\(\)/, "Échap doit restituer le focus au sélecteur de langue");
assert.ok(skipToContent.includes('targetId="main-content"'), "le lien global doit cibler le contenu principal");
assert.ok(skipLink.includes("target.focus({ preventScroll: true })"), "chaque lien d’évitement doit transférer le focus");
assert.ok(skipLink.includes('target.scrollIntoView({ block: "start" })'), "chaque lien d’évitement doit cadrer sa destination");
assert.doesNotMatch(merchantsPage, /<main\b/, "la page marchands ne doit pas imbriquer un second main dans le layout");
assert.doesNotMatch(categoryDetails, /<main\b/, "une catégorie ne doit pas imbriquer un second main dans le layout");
const animationDeclarations = [...css.matchAll(/animation(?:-[a-z-]+)?\s*:\s*([^;}]+)/gi)]
  .map((match) => match[1].trim());
assert.ok(
  animationDeclarations.every((value) => /^none(?:\s*!important)?$/i.test(value)),
  "la home Phase 11 ne doit pas dépendre d'une animation",
);

console.log("✓ Phase 19 home : chorégraphie de preuve fail-closed, accessible et bornée");
