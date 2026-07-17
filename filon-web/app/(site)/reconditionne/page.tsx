import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { PageShell } from "@/components/site/PageShell";

export const metadata: Metadata = buildMetadata({
  path: "/reconditionne",
  title: "Reconditionné : le même produit, jusqu'à 50 % moins cher",
  description:
    "FILON compare le prix neuf au reconditionné équivalent (grade vérifié, garanti) et calcule l'économie réelle — meilleure pour votre budget et pour la planète.",
});

export default function ReconditionnePage() {
  return (
    <PageShell
      eyebrow="Reconditionné"
      title={<>Le même produit. Jusqu&apos;à 50 % moins cher.</>}
      intro="Un smartphone haut de gamme reconditionné se négocie environ 40 % sous le neuf ; en ajoutant un cashback partenaire, l'économie totale atteint 45 à 50 %. FILON réunit prix neuf, équivalent reconditionné garanti et cashback dans une seule vue — meilleur pour votre budget, et pour la planète."
      breadcrumb={[{ name: "Reconditionné", path: "/reconditionne" }]}
    />
  );
}
