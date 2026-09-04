import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const transition = readFileSync(join(root, "components/filon/PageTransition.tsx"), "utf8");
const rootLayout = readFileSync(join(root, "app/layout.tsx"), "utf8");
const productJourney = readFileSync(join(root, "components/experience/ProductJourneyLink.tsx"), "utf8");
const productCard = readFileSync(join(root, "components/filon/ProductCard.tsx"), "utf8");
const exactProductPage = readFileSync(join(root, "app/(site)/produits/[ean]/page.tsx"), "utf8");
const css = readFileSync(join(root, "components/filon/filon.css"), "utf8");
const catalogue = readFileSync(join(root, "app/(site)/catalogue/page.tsx"), "utf8");
const catalogueHeader = readFileSync(join(root, "components/filon/CatalogueHeader.tsx"), "utf8");
const score = readFileSync(join(root, "app/(site)/score/page.tsx"), "utf8");
const cashback = readFileSync(join(root, "app/(site)/cashback/page.tsx"), "utf8");
const outfit = readFileSync(join(root, "components/intelligence/OutfitStudio.tsx"), "utf8");
const outfitPage = readFileSync(join(root, "app/(site)/creer/outfit-studio/page.tsx"), "utf8");
const outfitCss = readFileSync(join(root, "components/intelligence/outfit-studio.css"), "utf8");
const merchantsPage = readFileSync(join(root, "app/(site)/marchands/page.tsx"), "utf8");
const merchants = readFileSync(join(root, "components/editorial/MerchantsBrowser.tsx"), "utf8");
const category = readFileSync(join(root, "components/filon/CategoryDetails.tsx"), "utf8");
const offerPage = readFileSync(join(root, "app/(site)/produit/[id]/page.tsx"), "utf8");
const offerDetails = readFileSync(join(root, "components/filon/OfferProductDetails.tsx"), "utf8");
const priceLandscape = readFileSync(join(root, "components/experience/PriceTimeLandscape.tsx"), "utf8");
const footer = readFileSync(join(root, "components/editorial/EditorialFooter.tsx"), "utf8");
const reveal = readFileSync(join(root, "components/editorial/Reveal.tsx"), "utf8");
const seo = readFileSync(join(root, "lib/seo.tsx"), "utf8");
const signalPages = [
  "a-propos", "aide", "blog", "carrieres", "cgu",
  "confidentialite", "contact", "cookies", "extension", "faq", "mentions-legales",
  "partenaires", "presse", "tarifs",
];

for (const chapter of ["signal", "market", "identity", "proof", "decision", "compose"]) {
  assert.ok(transition.includes(`"${chapter}"`), `le chapitre ${chapter} doit appartenir au parcours`);
}

assert.ok(transition.includes("data-experience-chapter"), "chaque route doit exposer son chapitre sémantique");
assert.ok(rootLayout.includes('data-scroll-behavior="smooth"'), "le layout doit annoncer son défilement fluide à Next.js");
assert.ok(transition.includes('aria-hidden="true"'), "la matière de transition doit rester décorative");
assert.ok(transition.includes("resolveJourneyChapter"), "la continuité doit être déterministe et testable");
assert.ok(transition.includes("PRODUCT_JOURNEY_EVENT") && transition.includes("fx-product-handoff"), "le passage produit doit transporter le même objet entre deux chapitres");
assert.ok(productJourney.includes("next/link") && productJourney.includes("CustomEvent<ProductJourneyDetail>"), "la continuité produit doit conserver une navigation interne progressive");
assert.ok(productJourney.includes('prefers-reduced-motion: reduce'), "le transport produit doit s'effacer en mouvement réduit");
assert.ok(productCard.includes("ProductJourneyLink"), "les cartes catalogue doivent ouvrir le dossier sans casser la continuité d'objet");
assert.ok(exactProductPage.includes("data-product-transition-target"), "le dossier exact doit recevoir l'objet transporté");
assert.ok(css.includes("prefers-reduced-motion: reduce"), "le mouvement réduit doit supprimer le balayage");
assert.ok(css.includes("pointer-events: none"), "la transition ne doit jamais bloquer un contrôle");
assert.doesNotMatch(transition, /canvas|WebGL|three/i, "la continuité globale ne doit pas imposer de moteur 3D");
assert.doesNotMatch(catalogue, /CataloguePlanMarker/, "le catalogue final ne doit pas exposer une navigation de démonstration");
assert.doesNotMatch(catalogueHeader, /FILON \/ \{MARKET_CHAPTER\[locale\]\} \d/, "le catalogue final ne doit pas exposer un numéro de plan");
assert.match(css, /\.fx-catalogue \.fx-catalogue-intro::before/, "le catalogue doit prolonger la géométrie du marché");
for (const [name, source] of [["Score", score], ["Cashback", cashback]]) {
  assert.ok(source.includes("p19-decision-surface"), `${name} doit appartenir à la même chambre de décision`);
  assert.ok(source.includes("data-decision-plan"), `${name} doit annoncer son plan sémantique`);
}
assert.ok(score.includes("p19-signal-ledger"), "le Score doit exposer ses cinq preuves dans un registre DOM");
assert.ok(cashback.includes("p19-cashback-gate"), "Cashback doit exposer ses conditions avant l'action");
assert.doesNotMatch(cashback, /cashback-coin|LifeVideo|<video/, "Cashback ne doit plus dépendre d'une vidéo décorative");
assert.ok(css.includes(".p19-score-instrument"), "le plan Score doit matérialiser la convergence des preuves");
assert.ok(css.includes(".p19-cashback-gate"), "le plan Cashback doit partager la grammaire de décision");
assert.match(css, /prefers-reduced-motion[\s\S]*\.p19-decision-copy/, "l'arrivée du plan décision doit disparaître en mouvement réduit");
assert.ok(outfit.includes("p19-compose-surface"), "Outfit Studio doit prolonger le parcours dans le chapitre compose");
assert.ok(outfit.includes('data-compose-plan="outfit"'), "la surface compose doit annoncer sa fonction");
assert.ok(outfit.includes("p19-compose-path"), "intention, offres vérifiées et solution doivent rester lisibles dans le DOM");
assert.doesNotMatch(outfitPage, /title:\s*["']Outfit Studio · FILON/, "le titre de la table de composition ne doit pas doubler la marque");
assert.ok(outfitCss.includes(".os-shell.p19-compose-surface"), "la table de composition doit rester isolée au studio");
assert.match(outfitCss, /prefers-reduced-motion[\s\S]*\.p19-compose-surface \.os-intro-copy/, "l'arrivée compose doit disparaître en mouvement réduit");
assert.ok(css.includes('[data-experience-chapter="proof"] .ed-content-hero'), "les routes de preuve doivent partager une même chambre");
assert.ok(css.includes('[data-experience-chapter="proof"] .ed-infogrid'), "les preuves éditoriales doivent devenir un registre continu");
assert.ok(css.includes('[data-experience-chapter="proof"] .ed-steps'), "la méthode doit suivre la même géométrie de preuve");
assert.match(css, /prefers-reduced-motion[\s\S]*\[data-experience-chapter="proof"\]/, "la chambre de preuve doit neutraliser ses transitions en mouvement réduit");
assert.ok(css.includes('[data-experience-chapter="decision"]:has(.ed-content-hero) .ed-content-hero'), "les utilitaires d'achat doivent prolonger la chambre de décision");
assert.ok(css.includes('[data-experience-chapter="decision"]:has(.ed-content-hero) .ed-infogrid'), "les contrôles de décision doivent devenir un registre continu");
assert.ok(css.includes('[data-experience-chapter="decision"]:has(.ed-content-hero) .ed-faq'), "la FAQ décision doit rester dans le même plan de vérification");
assert.match(css, /prefers-reduced-motion[\s\S]*\[data-experience-chapter="decision"\]/, "les utilitaires de décision doivent neutraliser leurs transitions en mouvement réduit");
assert.ok(merchantsPage.includes('data-market-plan="merchants"'), "le registre marchand doit prolonger le marché");
assert.ok(merchants.includes("p19-merchant-ledger"), "les marchands doivent rester une liste filtrable dans le DOM");
assert.ok(merchants.includes("p19-market-state"), "les états vide et indisponible du marché doivent rester explicites");
assert.ok(category.includes('data-market-plan="category"'), "un rayon doit être un zoom du même marché");
assert.doesNotMatch(category, /FILON \/ (?:MARCHÉ|MARKT|MARKET)/, "le rayon final ne doit pas exposer un repère de laboratoire");
assert.ok(css.includes(".p19-merchant-grid"), "le registre marchand doit partager la grille de marché");
assert.ok(css.includes(".p19-category-market .fx-product-grid"), "les produits d'un rayon doivent rester dans la table de marché");
assert.match(css, /prefers-reduced-motion[\s\S]*\.p19-category-market/, "le marché étendu doit neutraliser ses transitions en mouvement réduit");
assert.ok(offerPage.includes('data-product-evidence="offer"'), "l'URL d'offre historique doit annoncer son périmètre exact");
assert.ok(offerPage.includes("p19-offer-media"), "l'offre observée doit rester le même objet physique que le dossier exact");
assert.ok(offerDetails.includes("p19-offer-dossier"), "prix, marchand, verdict et décision doivent partager le même dossier DOM");
assert.ok(offerDetails.includes("data-purchasable={canBuy || undefined}"), "la scène ne doit afficher un état achetable qu'après la garde métier");
assert.ok(offerDetails.includes("PriceTimeLandscape"), "l'historique admissible doit devenir un paysage prix-temps réel");
assert.ok(offerDetails.includes("ProductJourneyLink"), "l'offre groupée doit transporter le même produit vers son dossier exact");
assert.ok(priceLandscape.includes('type="range"') && priceLandscape.includes("aria-live=\"polite\""), "le paysage prix-temps doit rester parcourable au clavier");
assert.ok(priceLandscape.includes("data-sticky-cta-avoid"), "le CTA mobile ne doit pas recouvrir le paysage prix-temps");
assert.ok(outfit.includes("data-sticky-cta-avoid"), "le CTA mobile ne doit pas recouvrir la table Outfit Studio");
assert.ok(priceLandscape.includes("<table>"), "chaque relief doit conserver un tableau accessible de ses relevés réels");
assert.doesNotMatch(priceLandscape, /Math\.random|setInterval|requestAnimationFrame/, "l'historique ne doit ni inventer ni faire défiler des relevés");
assert.ok(css.includes(".p19-offer-history"), "l'historique disponible doit rester une pièce du dossier offre");
assert.ok(css.includes(".p19-price-landscape-cursor"), "le relevé actif doit avoir une position spatiale visible");
assert.match(css, /prefers-reduced-motion[\s\S]*\.p19-offer-dossier/, "le dossier offre doit neutraliser son arrivée en mouvement réduit");
for (const slug of signalPages) {
  const source = readFileSync(join(root, `app/(site)/${slug}/page.tsx`), "utf8");
  assert.ok(source.includes("ContentHero"), `${slug} doit conserver le hero éditorial raccordé au champ signal`);
}
assert.ok(css.includes('[data-experience-chapter="signal"] .ed-content-hero'), "les pages publiques éditoriales doivent partager le champ signal");
assert.ok(css.includes('[data-experience-chapter="signal"] .ed-blog'), "l'index des guides doit être une séquence de dossiers");
assert.ok(css.includes('[data-experience-chapter="signal"] .ed-article-hero'), "les guides doivent prolonger le champ signal en lecture longue");
assert.ok(css.includes('[data-experience-chapter="signal"] .ed-legal'), "les contrats publics doivent rester dans la même géométrie lisible");
assert.ok(css.includes('form:not(.ed-news)'), "les formulaires publics doivent appartenir au champ éditorial sans modifier leur transport");
assert.match(css, /prefers-reduced-motion[\s\S]*\[data-experience-chapter="signal"\]/, "le champ signal doit neutraliser ses transitions en mouvement réduit");
assert.ok(footer.includes('data-experience-exit="continuation"'), "le footer doit prolonger le parcours au lieu de le rompre");
assert.ok(footer.includes("data-sticky-cta-avoid"), "le CTA mobile ne doit pas recouvrir la newsletter ni les liens de sortie");
assert.ok(footer.includes("p19-footer-coordinate"), "la sortie globale doit annoncer sa coordonnée dans les trois langues");
assert.ok(css.includes(".p19-global-footer .ed-newsblock"), "la newsletter doit appartenir au dernier plan de l'expérience");
assert.ok(css.includes(".p19-global-footer .ed-foot .ed-foot-links"), "les prochains chemins doivent former un registre navigable");
assert.match(css, /prefers-reduced-motion[\s\S]*\.p19-global-footer/, "la sortie globale doit neutraliser ses transitions en mouvement réduit");
assert.match(css, /prefers-reduced-motion[\s\S]*\.fx-product-handoff/, "le transfert d'objet doit disparaître en mouvement réduit");
assert.ok(reveal.includes("96 / Math.max(el.offsetHeight, 1)"), "un registre long doit se révéler dès ses premiers pixels visibles");
assert.ok(reveal.includes("Math.min(0.16"), "les blocs courts doivent conserver la chorégraphie de révélation existante");
assert.ok(seo.includes("requestedTitle.includes(site.name)"), "un titre qui porte déjà FILON ne doit pas doubler la marque");

console.log("✓ Continuité FILON : routes en chapitres, matière décorative et mouvement réduit");
