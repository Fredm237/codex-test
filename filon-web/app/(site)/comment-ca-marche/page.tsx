import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ClosingCta } from "@/components/editorial/ContentPage";
import { Method } from "@/components/editorial/EditorialSections";
import { InfoGrid } from "@/components/editorial/ContentPage";

export const metadata: Metadata = buildMetadata({
  path: "/comment-ca-marche",
  title: "Comment ça marche",
  description:
    "En trois secondes, FILON détecte votre produit, scanne cashback, reconditionné et codes promo, puis affiche votre prix réel le plus bas. Voici le fonctionnement, étape par étape.",
});

export default function CommentCaMarchePage() {
  return (
    <>
      <ContentHero
        eyebrow="Comment ça marche"
        title={<>Trois secondes entre vous et le <span className="it">meilleur prix</span>.</>}
        intro="Vous ne changez rien à vos habitudes d'achat. FILON travaille en arrière-plan, croise chaque source d'économie en temps réel, et vous présente un seul chiffre : votre prix réel le plus bas."
        breadcrumb={[{ name: "Comment ça marche", path: "/comment-ca-marche" }]}
      />

      <Method />

      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "20ch" }}>Ce que FILON analyse, à chaque fois.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "€", h: "Prix & marchands", p: "Le meilleur prix parmi des dizaines de marchands, en temps réel." },
              { n: "%", h: "Cashback", p: "Le taux le plus élevé du moment (iGraal, Poulpeo, Widilo, Joko, eBuyClub…)." },
              { n: "↻", h: "Reconditionné", p: "L'équivalent reconditionné garanti, souvent bien moins cher." },
              { n: "✓", h: "Codes promo", p: "Testés en direct sur votre panier — seul celui qui marche est appliqué." },
              { n: "★", h: "Fiabilité vendeur", p: "Réputation et garanties prises en compte dans le verdict." },
              { n: "↧", h: "Historique de prix", p: "Pour savoir s'il vaut mieux acheter maintenant ou attendre." },
            ]}
          />
        </div>
      </section>

      <ClosingCta title={<>Essayez, c&apos;est <span className="it">gratuit</span>.</>} sub="Ajoutez FILON et laissez-le trouver le filon avant chaque achat." />
    </>
  );
}
