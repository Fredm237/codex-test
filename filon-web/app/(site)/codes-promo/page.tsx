import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, InfoGrid, ClosingCta } from "@/components/editorial/ContentPage";
import { FaqBlock } from "@/components/editorial/Faq";

export const metadata: Metadata = buildMetadata({
  path: "/codes-promo",
  title: "Codes promo testés en direct",
  description:
    "Fini les « code expiré ». FILON teste chaque code promo en direct au moment du paiement et applique automatiquement celui qui offre la plus grosse réduction.",
});

const FAQ = [
  { q: "Pourquoi tant de codes promo ne fonctionnent-ils pas ?", a: "La plupart des codes trouvés en ligne sont périmés, réservés à certains produits, ou déjà utilisés. Les tester un par un est chronophage et décourageant. FILON les teste pour vous, en direct, et ne garde que celui qui marche." },
  { q: "Comment FILON trouve-t-il les bons codes ?", a: "Il rassemble les codes disponibles pour le marchand, les essaie automatiquement au moment du paiement, et applique celui qui offre la plus grosse réduction sur votre panier réel." },
  { q: "Un code promo se cumule-t-il avec le cashback ?", a: "Souvent oui. FILON calcule la combinaison la plus rentable entre code promo, cashback et prix reconditionné, puis affiche votre prix réel final." },
  { q: "Les codes sont-ils fiables et à jour ?", a: "Comme ils sont testés en direct sur votre panier, vous n'appliquez jamais un code mort : soit un code fonctionne et la réduction s'affiche, soit FILON passe au suivant." },
  { q: "Dois-je copier-coller les codes moi-même ?", a: "Non. Une fois l'extension active, FILON s'en charge automatiquement à l'étape du paiement. Vous voyez simplement le prix baisser." },
];

export default function CodesPromoPage() {
  return (
    <>
      <ContentHero
        eyebrow="Codes promo"
        title={<>Des codes promo qui fonctionnent <span className="it">vraiment</span>.</>}
        intro="« Code expiré », « non applicable à cet article »… tout le monde connaît la frustration. FILON teste chaque code en direct au moment du paiement et applique automatiquement celui qui offre la plus grosse réduction — sans que vous essayiez dix combinaisons."
        breadcrumb={[{ name: "Codes promo", path: "/codes-promo" }]}
      />

      <ProseBlock heading={<>Le code promo, sans la <span className="it">chasse</span> au code.</>}>
        <p>
          Chercher un code, ouvrir cinq sites de bons plans, coller, essuyer un « invalide », recommencer… Ce petit rituel
          coûte du temps et, souvent, on abandonne en payant plein tarif.
        </p>
        <p>
          FILON inverse la logique : il <b>teste tous les codes disponibles en direct</b> sur votre panier réel et applique
          le plus avantageux. Vous ne voyez qu'une chose : le prix qui baisse, tout seul.
        </p>
      </ProseBlock>

      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "18ch" }}>Trois secondes, zéro copier-coller.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "01", h: "Collecte", p: "FILON réunit les codes disponibles pour le marchand où vous êtes." },
              { n: "02", h: "Test en direct", p: "Chaque code est essayé sur votre panier réel, au moment du paiement." },
              { n: "03", h: "Meilleure réduction", p: "Le code le plus avantageux est appliqué — et cumulé au cashback si possible." },
            ]}
          />
        </div>
      </section>

      <FaqBlock items={FAQ} eyebrow="Codes promo · FAQ" title="Les codes promo, enfin sans frustration." />
      <ClosingCta title={<>Ne payez plus jamais <span className="it">avant</span> d&apos;avoir testé les codes.</>} sub="FILON le fait automatiquement, gratuitement, à chaque paiement." />
    </>
  );
}
