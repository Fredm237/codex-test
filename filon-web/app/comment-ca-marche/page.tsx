import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { PageShell } from "@/components/site/PageShell";
import { Steps } from "@/components/site/Sections";

export const metadata: Metadata = buildMetadata({
  path: "/comment-ca-marche",
  title: "Comment ça marche",
  description:
    "En trois secondes, FILON détecte votre produit, scanne cashback, reconditionné et codes promo, puis affiche votre prix réel le plus bas.",
});

export default function CommentCaMarchePage() {
  return (
    <PageShell
      eyebrow="Comment ça marche"
      title={<>Trois secondes entre vous et le meilleur prix.</>}
      intro="Vous ne changez rien à vos habitudes d'achat. FILON travaille en arrière-plan, croise chaque source d'économie en temps réel, et vous présente un seul chiffre : votre prix réel le plus bas."
      breadcrumb={[{ name: "Comment ça marche", path: "/comment-ca-marche" }]}
    >
      <Steps />
    </PageShell>
  );
}
