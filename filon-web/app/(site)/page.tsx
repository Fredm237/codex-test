import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { EditorialHero } from "@/components/editorial/EditorialHero";
import { Transformation } from "@/components/editorial/Transformation";
import { Method, Transparency, Partners, Closing } from "@/components/editorial/EditorialSections";
import { Faq } from "@/components/editorial/Faq";

export const metadata: Metadata = buildMetadata({
  path: "/",
  title: "Est-ce vraiment le bon prix ?",
  description:
    "FILON, l'assistant d'achat malin. Avant chaque achat, il compare cashback, reconditionné et codes promo — et vous dit s'il existe mieux. Ne payez plus jamais trop cher.",
});

export default function HomePage() {
  return (
    <>
      <EditorialHero />
      <Transformation />
      <Method />
      <Transparency />
      <Partners />
      <Faq />
      <Closing />
    </>
  );
}
