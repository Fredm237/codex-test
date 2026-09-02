import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { WebExperience } from "@/components/experience/WebExperience";
import { getProof } from "@/lib/proof";

export const revalidate = 600;

export const metadata: Metadata = buildMetadata({
  path: "/",
  title: "FILON — Le copilote d'achat intelligent",
  description:
    "FILON compare les offres indexées, montre les prix observés et s'abstient quand les données ne suffisent pas.",
});

// Phase 11 : l'accueil canonique reste léger et evidence-first. Les anciens
// assets immersifs ne sont plus dans le graphe d'import de la home tant que la
// gate Core UX/Immersive n'est pas explicitement ouverte.
export default async function HomePage() {
  const proof = await getProof();
  return <WebExperience proof={proof} />;
}
