import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { Hero } from "@/components/filon/Hero";
import { Method, Closing } from "@/components/filon/Sections";
import { Faq } from "@/components/editorial/Faq";
import { getProof } from "@/lib/proof";
import { Showcase } from "@/components/filon/Showcase";
import { Pulse } from "@/components/filon/Pulse";
import { getPulse, getRails } from "@/lib/catalogue";

export const revalidate = 3600;

export const metadata: Metadata = buildMetadata({
  path: "/",
  title: "Est-ce vraiment le bon moment pour acheter ?",
  description:
    "FILON réunit les offres de nos marchands partenaires, conserve l'historique des prix et vous dit ce que vaut celui d'aujourd'hui.",
});

export default async function HomePage() {
  const [proof, pulse, rails] = await Promise.all([getProof(), getPulse(), getRails()]);

  const seen = new Set<number>();
  const showcase = rails
    .flatMap((section) => section.items || [])
    .filter((item) => {
      if (!item || seen.has(item.id)) return false;
      seen.add(item.id);
      return true;
    })
    .slice(0, 3);

  return (
    <>
      <Hero proof={proof} />

      {/* Pulse compact — preuve que le catalogue vit */}
      <div className="fx-container fx-home-pulse">
        <Pulse data={pulse} />
      </div>

      {/* Vidéo immersive — pas de texte, juste l'expérience */}
      <section className="fx-video-section">
        <video
          className="fx-video-hero"
          autoPlay
          muted
          loop
          playsInline
          poster="/img/closing-bg.png"
        >
          <source src="/video/filon_promo.mp4" type="video/mp4" />
        </video>
      </section>

      {/* Showcase — les vrais produits parlent */}
      {showcase.length > 0 && (
        <section className="fx-section">
          <div className="fx-container">
            <Showcase items={showcase} />
          </div>
        </section>
      )}

      {/* Method — 3 étapes visuelles, peu de texte */}
      <Method />

      {/* FAQ compacte */}
      <Faq />

      {/* Closing dramatique */}
      <Closing proof={proof} />
    </>
  );
}
