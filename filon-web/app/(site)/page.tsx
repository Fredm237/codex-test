import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { WebExperience } from "@/components/experience/WebExperience";
import { getProof } from "@/lib/proof";
import { getImmersiveExactProductProof } from "@/lib/immersive-proof";

export const revalidate = 600;

export const metadata: Metadata = buildMetadata({
  path: "/",
  title: "FILON — Le copilote d'achat intelligent",
  description:
    "FILON compare les offres indexées, montre les prix observés et s'abstient quand les données ne suffisent pas.",
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
