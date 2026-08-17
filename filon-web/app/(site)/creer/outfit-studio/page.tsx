import type { Metadata } from "next";
import { OutfitStudio } from "@/components/intelligence/OutfitStudio";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  path: "/creer/outfit-studio",
  title: "Outfit Studio · FILON",
  description:
    "Décrivez une intention. FILON compose une solution avec des offres réelles et distingue clairement ce qui est vérifié de ce qui reste à confirmer.",
});

export default function OutfitStudioPage() {
  return <OutfitStudio />;
}
