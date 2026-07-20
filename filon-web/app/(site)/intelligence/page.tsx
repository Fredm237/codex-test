import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, InfoGrid, ClosingCta } from "@/components/editorial/ContentPage";

export const metadata: Metadata = buildMetadata({
  path: "/intelligence",
  title: "L'intelligence FILON",
  description:
    "Le prix le plus bas n'est pas toujours le meilleur achat. FILON regarde ce qui compte vraiment : le bon produit, au bon moment, qui dure.",
});

export default function IntelligencePage() {
  return (
    <>
      <ContentHero
        eyebrow="L'intelligence FILON"
        title={<>Plus loin que le <span className="it">prix</span>.</>}
        intro="Le prix le plus bas n'est pas toujours le meilleur achat. FILON regarde ce qui compte vraiment, pour vous éviter les mauvaises surprises."
        breadcrumb={[{ name: "Intelligence", path: "/intelligence" }]}
      />

      <ProseBlock heading={<>Le bon achat, pas juste le bon <span className="it">prix</span>.</>}>
        <p>
          Un bon achat, c&apos;est le bon produit, au bon moment, qui dure. FILON tient compte de tout ça, à votre place,
          en quelques secondes.
        </p>
        <p>
          Vous recevez une réponse simple. Derrière, beaucoup de choses ont été pesées pour vous.
        </p>
      </ProseBlock>

      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <span className="eyebrow" style={{ display: "block", marginBottom: 12 }}>Ce que FILON regarde pour vous</span>
            <h2 style={{ maxWidth: "20ch" }}>Bien plus qu&apos;un prix.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "◷", h: "Le bon moment", p: "Un prix au plancher, dans la moyenne, ou gonflé. Vous savez s'il faut acheter ou attendre." },
              { n: "★", h: "La fiabilité", p: "Un produit qui tient dans le temps, avec un vrai service derrière." },
              { n: "⌛", h: "La durée de vie", p: "Combien de temps il va vraiment durer, à l'usage." },
              { n: "€", h: "Le coût réel", p: "Pas seulement le prix affiché, mais ce qu'il coûte sur la durée." },
              { n: "💬", h: "Les avis, en clair", p: "Des milliers d'avis résumés en une réponse. Le signal, pas le bruit." },
              { n: "✓", h: "La meilleure alternative", p: "Neuf, reconditionné, ailleurs : la meilleure option, quand elle existe." },
            ]}
          />
        </div>
      </section>

      <ClosingCta title={<>L&apos;intelligence au service de <span className="it">votre</span> achat.</>} sub="Une réponse claire, à chaque fois. Et gratuite." />
    </>
  );
}
