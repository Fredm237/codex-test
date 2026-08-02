import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { Hero } from "@/components/filon/Hero";
import { Method, Closing } from "@/components/filon/Sections";
import { Transparency } from "@/components/editorial/EditorialSections";
import { Proof } from "@/components/filon/Proof";
import { Faq } from "@/components/editorial/Faq";
import { getProof } from "@/lib/proof";

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
  const proof = await getProof();
  return (
    <>
      <Hero proof={proof} />
      <Method />
      <Proof live={proof} />
      <Transparency />
      <Faq />
      <Closing proof={proof} />
    </>
  );
}
