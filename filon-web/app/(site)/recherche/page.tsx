import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { SearchAssistant } from "@/components/editorial/SearchAssistant";

export const metadata: Metadata = buildMetadata({
  path: "/recherche",
  title: "L'assistant d'achat",
  description:
    "Recherchez les offres indexées dans FILON et consultez les prix, avantages et signaux disponibles, avec leurs limites.",
});

export default function RecherchePage() {
  return <SearchAssistant />;
}
