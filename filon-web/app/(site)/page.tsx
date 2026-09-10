import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { CommerceJourney } from "@/components/experience/CommerceJourney";
import { getDepartments, getOffers, resolve } from "@/lib/catalogue";
import { getProof } from "@/lib/proof";

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
  const departments = await getDepartments();
  const [proof, offers] = await Promise.all([getProof(), getOffers({ per: "24" }, resolve(departments, {}))]);
  return <CommerceJourney proof={proof} departments={departments} offers={offers?.items.slice(0, 4) ?? []} />;
}
