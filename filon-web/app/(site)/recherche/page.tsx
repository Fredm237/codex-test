import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { SearchAssistant } from "@/components/editorial/SearchAssistant";

export const metadata: Metadata = buildMetadata({
  path: "/recherche",
  title: "Assistant d'achat IA — que souhaitez-vous acheter ?",
  description:
    "Demandez à FILON avant d'acheter : il analyse prix, cashback, reconditionné et codes promo, puis vous conseille en langage clair. L'assistant d'achat intelligent, gratuit.",
});

export default function RecherchePage() {
  return <SearchAssistant />;
}
