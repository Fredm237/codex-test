import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { EditorialHero } from "@/components/editorial/EditorialHero";
import { Transformation } from "@/components/editorial/Transformation";
import { Method, Transparency } from "@/components/editorial/EditorialSections";
import { NetworkScene, GraphScene, ClosingScene } from "@/components/editorial/Scenes";
import { ProofSection } from "@/components/editorial/ProofSection";
import { Faq } from "@/components/editorial/Faq";
import { getProof } from "@/lib/proof";

// La home lit le catalogue au rendu : les preuves affichées sont les chiffres
// réels, régénérés périodiquement plutôt qu'à chaque visite.
export const revalidate = 3600;

export const metadata: Metadata = buildMetadata({
  path: "/",
  title: "Est-ce vraiment le bon prix ?",
  description:
    "FILON, l'assistant d'achat malin. Avant chaque achat, il compare cashback, reconditionné et codes promo, et vous dit s'il existe mieux. Ne payez plus jamais trop cher.",
});

export default async function HomePage() {
  const proof = await getProof();
  return (
    <>
      <EditorialHero />
      <Transformation />
      <Method />
      <NetworkScene />
      <ProofSection live={proof} />
      <Transparency />
      <GraphScene />
      <Faq />
      <ClosingScene />
    </>
  );
}
