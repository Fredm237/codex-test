import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { PageShell } from "@/components/site/PageShell";

export const metadata: Metadata = buildMetadata({
  path: "/codes-promo",
  title: "Codes promo testés en direct",
  description:
    "Fini les « code expiré ». FILON teste chaque code promo en direct et applique automatiquement celui qui offre la plus grosse réduction.",
});

export default function CodesPromoPage() {
  return (
    <PageShell
      eyebrow="Codes promo"
      title={<>Des codes promo qui fonctionnent vraiment.</>}
      intro="La plupart des codes trouvés en ligne sont expirés ou inapplicables. FILON teste chaque code en direct au moment du paiement et applique celui qui offre la plus grosse réduction — sans que vous ayez à essayer dix combinaisons."
      breadcrumb={[{ name: "Codes promo", path: "/codes-promo" }]}
    />
  );
}
