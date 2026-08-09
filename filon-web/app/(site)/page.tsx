import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { Hero } from "@/components/filon/Hero";
import { Method, Closing } from "@/components/filon/Sections";
import { Faq } from "@/components/editorial/Faq";
import { getProof } from "@/lib/proof";
import { Showcase } from "@/components/filon/Showcase";
import { CostStack3D } from "@/components/filon/CostStack3D";
import { Pulse } from "@/components/filon/Pulse";
import { getPulse, getRails } from "@/lib/catalogue";

export const revalidate = 3600;

export const metadata: Metadata = buildMetadata({
  path: "/",
  title: "Est-ce vraiment le bon moment pour acheter ?",
  description:
    "FILON réunit les offres de nos marchands partenaires, conserve l'historique des prix et vous dit ce que vaut celui d'aujourd'hui.",
});

export default async function HomePage() {
  const [proof, pulse, rails] = await Promise.all([getProof(), getPulse(), getRails()]);

  const seen = new Set<number>();
  const showcase = rails
    .flatMap((section) => section.items || [])
    .filter((item) => {
      if (!item || seen.has(item.id)) return false;
      seen.add(item.id);
      return true;
    })
    .slice(0, 3);

  return (
    <>
      <Hero proof={proof} />

      {/* Chapitre clair — la coupe franche après le hero sombre.
          Le chiffre porte seul, comme le « 2 500+ » du transporteur :
          il vient du catalogue, il n'est pas rédigé. */}
      {proof?.stats && (
        <section className="fx-chapter" data-tone="light">
          <div className="fx-container">
            <p className="fx-chapter-figure mono">
              {new Intl.NumberFormat("fr-BE").format(proof.stats.offers)}
            </p>
            <p className="fx-chapter-figure-label fx-lede">
              offres relevées chez {proof.stats.merchants} marchands partenaires,
              comparées à l&apos;article près.
            </p>
          </div>
        </section>
      )}

      {/* Pulse compact — preuve que le catalogue vit */}
      <div className="fx-container fx-home-pulse">
        <Pulse data={pulse} />
      </div>


      {/* Showcase — les vrais produits parlent */}
      {showcase.length > 0 && (
        <section className="fx-section">
          <div className="fx-container">
            <Showcase items={showcase} />
          </div>
        </section>
      )}

      {/* Pile de coût — la scène 3D au défilement.
          Elle ne s'affiche qu'avec un produit réellement multi-marchands
          dont l'écart est mesuré : sans écart, il n'y a rien à démontrer,
          et on ne fabrique pas un exemple pour faire tourner une animation. */}
      {proof?.product && proof.product.priceMax > proof.product.priceMin && (
        <CostStack3D
          title={
            <>
              Le même article, <em>selon le marchand.</em>
            </>
          }
          layers={[
            { label: "Le plus cher constaté", amount: proof.product.priceMax },
            {
              label: `Écart sur ${proof.product.merchants} marchands`,
              amount: proof.product.priceMin - proof.product.priceMax,
            },
            { label: "Le moins cher constaté", amount: proof.product.priceMin },
          ]}
        />
      )}

      {/* Method — 3 étapes visuelles, peu de texte */}
      <Method />

      {/* FAQ compacte */}
      <Faq />

      {/* Closing dramatique */}
      <Closing proof={proof} />
    </>
  );
}
