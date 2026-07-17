import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { PageShell } from "@/components/site/PageShell";

export const metadata: Metadata = buildMetadata({
  path: "/cashback",
  title: "Cashback : toujours le meilleur taux",
  description:
    "FILON compare les taux de cashback d'iGraal, Poulpeo, Widilo, Joko et eBuyClub pour chaque marchand, et applique automatiquement le plus rémunérateur.",
});

export default function CashbackPage() {
  return (
    <PageShell
      eyebrow="Cashback"
      title={<>Le meilleur taux de cashback, sans le chercher.</>}
      intro="Un même marchand peut offrir 5 % sur une plateforme, 7 % sur une autre et 4 % sur une troisième le même jour. FILON compare iGraal, Poulpeo, Widilo, Joko et eBuyClub en temps réel, et vous oriente vers le taux le plus élevé — automatiquement."
      breadcrumb={[{ name: "Cashback", path: "/cashback" }]}
    />
  );
}
