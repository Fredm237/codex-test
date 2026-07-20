import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ClosingCta } from "@/components/editorial/ContentPage";
import { Method } from "@/components/editorial/EditorialSections";
import { InfoGrid } from "@/components/editorial/ContentPage";

export const metadata: Metadata = buildMetadata({
  path: "/comment-ca-marche",
  title: "Comment ça marche",
  description:
    "En quelques secondes, FILON vous donne votre vrai prix et vous dit s'il faut acheter ou attendre. Voici l'expérience.",
});

export default function CommentCaMarchePage() {
  return (
    <>
      <ContentHero
        eyebrow="Comment ça marche"
        title={<>Trois secondes entre vous et le <span className="it">meilleur prix</span>.</>}
        intro="Vous ne changez rien à vos habitudes. FILON travaille pour vous et vous présente un seul chiffre : votre vrai prix. Et une réponse : acheter, ou attendre."
        breadcrumb={[{ name: "Comment ça marche", path: "/comment-ca-marche" }]}
      />

      <Method />

      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "20ch" }}>Ce que vous obtenez.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "€", h: "Votre vrai prix", p: "Un seul chiffre, tout compris. Fini les calculs de coin de table." },
              { n: "◷", h: "Acheter ou attendre", p: "Une réponse claire, pour acheter au bon moment." },
              { n: "✓", h: "La meilleure option", p: "Neuf, reconditionné, ailleurs : le meilleur choix, quand il existe." },
              { n: "★", h: "Un vendeur fiable", p: "La fiabilité et les garanties sont prises en compte, pas seulement le prix." },
              { n: "↧", h: "Sans rien changer", p: "Vous gardez vos habitudes. FILON travaille en arrière-plan." },
              { n: "♥", h: "Zéro effort", p: "Vous décrivez, FILON tranche. C'est tout." },
            ]}
          />
        </div>
      </section>

      <ClosingCta title={<>Essayez, c&apos;est <span className="it">gratuit</span>.</>} sub="Ajoutez FILON et laissez-le trouver le filon avant chaque achat." />
    </>
  );
}
