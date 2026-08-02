import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { Hero } from "@/components/filon/Hero";
import { Method, Closing } from "@/components/filon/Sections";
import { Transparency } from "@/components/editorial/EditorialSections";
import { Proof } from "@/components/filon/Proof";
import { Faq } from "@/components/editorial/Faq";
import { getProof } from "@/lib/proof";
import { Showcase } from "@/components/filon/Showcase";
import { Pulse } from "@/components/filon/Pulse";
import { Marquee } from "@/components/filon/Marquee";
import { getPulse, getRails } from "@/lib/catalogue";

// La home lit le catalogue au rendu : les preuves affichées sont les chiffres
// réels, régénérés périodiquement plutôt qu'à chaque visite.
export const revalidate = 3600;

export const metadata: Metadata = buildMetadata({
  path: "/",
  title: "Est-ce vraiment le bon moment pour acheter ?",
  description:
    "FILON réunit les offres de nos marchands partenaires, conserve l'historique des prix et vous dit ce que vaut celui d'aujourd'hui. Le copilote d'achat qui tranche, avant que vous ne payiez.",
});

// Les scènes WebGL défilantes (Transformation, NetworkScene, GraphScene,
// ClosingScene) sont retirées de la home : mesurées à 390 px de large, elles
// portaient la page à 11 202 px de haut, dont plusieurs milliers de pixels de
// dégradés sans contenu. Elles restent dans le dépôt pour d'autres surfaces.
export default async function HomePage() {
  const [proof, pulse, rails] = await Promise.all([getProof(), getPulse(), getRails()]);

  // Les démonstrations s'appuient sur de vrais produits : on prend les
  // premiers des rangées, en évitant de répéter deux fois le même article.
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

      {/* Le pouls juste sous le hero : la première chose qu'on lit après la
          promesse, c'est la preuve que le catalogue tourne aujourd'hui. */}
      <div className="fx-container fx-home-pulse">
        <Pulse data={pulse} />
      </div>

      {/* Bandeau de marchands défilant — mouvement continu visible */}
      {proof?.merchants && proof.merchants.length > 0 && (
        <Marquee merchants={proof.merchants} />
      )}

      {showcase.length > 0 && (
        <section className="fx-section">
          <div className="fx-container">
            <Showcase items={showcase} />
          </div>
        </section>
      )}

      <Method />
      <Proof live={proof} />
      <Transparency />
      <Faq />
      <Closing proof={proof} />
    </>
  );
}
