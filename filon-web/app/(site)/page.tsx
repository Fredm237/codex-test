import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { WebExperience } from "@/components/experience/WebExperience";
import { getProof } from "@/lib/proof";
import { getImmersiveExactProductProof } from "@/lib/immersive-proof";

export const revalidate = 600;

export const metadata: Metadata = buildMetadata({
  path: "/",
  title: "FILON — Comparez le bon produit et ses prix",
  description:
    "FILON vérifie qu'il s'agit du même produit, compare les offres disponibles et vous montre clairement d'où viennent les prix.",
});

// La preuve reste rendue côté serveur. La couche spatiale Phase 19 est différée,
// adaptative et strictement facultative : le DOM qualifié demeure le parcours.
export default async function HomePage() {
  const [proof, exactProduct] = await Promise.all([
    getProof(),
    getImmersiveExactProductProof(),
  ]);
  return <WebExperience exactProduct={exactProduct} proof={proof} />;
}
