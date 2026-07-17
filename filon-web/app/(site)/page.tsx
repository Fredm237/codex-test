import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { Hero } from "@/components/site/Hero";
import { Stats, Steps, Transparency, FinalCta } from "@/components/site/Sections";

export const metadata: Metadata = buildMetadata({
  path: "/",
  description:
    "FILON compare automatiquement cashback, reconditionné et codes promo avant chaque achat. Une seule expérience, zéro effort, un maximum d'économies — en toute transparence.",
});

export default function HomePage() {
  return (
    <>
      <Hero />
      <Stats />
      <Steps />
      <Transparency />
      <FinalCta />
    </>
  );
}
