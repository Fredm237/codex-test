import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ImmersiveExperience } from "@/components/filon/ImmersiveExperience";

export const revalidate = 3600;

export const metadata: Metadata = buildMetadata({
  path: "/",
  title: "FILON — Le copilote d'achat intelligent",
  description:
    "FILON compare les offres indexées, montre les prix observés et s'abstient quand les données ne suffisent pas.",
});

// La page entière EST l'expérience immersive.
// Un seul composant, un seul scroll, un seul film.
export default function HomePage() {
  return <ImmersiveExperience />;
}
