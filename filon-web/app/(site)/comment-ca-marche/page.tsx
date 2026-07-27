import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ClosingCta, InfoGrid } from "@/components/editorial/ContentPage";
import { Method } from "@/components/editorial/EditorialSections";
import { IcHeart } from "@/components/editorial/icons";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/comment-ca-marche",
  title: "Comment ça marche",
  description:
    "En quelques secondes, FILON vous donne votre vrai prix et vous dit s'il faut acheter ou attendre. Voici l'expérience.",
});

function CommentFR() {
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
              { n: <IcHeart />, h: "Zéro effort", p: "Vous décrivez, FILON tranche. C'est tout." },
            ]}
          />
        </div>
      </section>
      <ClosingCta title={<>Essayez, c&apos;est <span className="it">gratuit</span>.</>} sub="Ajoutez FILON et laissez-le trouver le filon avant chaque achat." />
    </>
  );
}

function CommentNL() {
  return (
    <>
      <ContentHero
        eyebrow="Hoe het werkt"
        title={<>Drie seconden tussen jou en de <span className="it">beste prijs</span>.</>}
        intro="Je verandert niets aan je gewoontes. FILON werkt voor jou en toont je één cijfer : je echte prijs. En één antwoord : kopen, of wachten."
        breadcrumb={[{ name: "Hoe het werkt", path: "/comment-ca-marche" }]}
      />
      <Method />
      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "20ch" }}>Wat je krijgt.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "€", h: "Je echte prijs", p: "Eén cijfer, alles inbegrepen. Geen rekenwerk meer." },
              { n: "◷", h: "Kopen of wachten", p: "Een duidelijk antwoord, om op het juiste moment te kopen." },
              { n: "✓", h: "De beste optie", p: "Nieuw, refurbished, elders : de beste keuze, wanneer die bestaat." },
              { n: "★", h: "Een betrouwbare verkoper", p: "Betrouwbaarheid en garanties tellen mee, niet alleen de prijs." },
              { n: "↧", h: "Zonder iets te veranderen", p: "Je behoudt je gewoontes. FILON werkt op de achtergrond." },
              { n: <IcHeart />, h: "Nul moeite", p: "Jij beschrijft, FILON beslist. Meer niet." },
            ]}
          />
        </div>
      </section>
      <ClosingCta title={<>Probeer het, het is <span className="it">gratis</span>.</>} sub="Voeg FILON toe en laat het de vondst vinden vóór elke aankoop." />
    </>
  );
}

function CommentEN() {
  return (
    <>
      <ContentHero
        eyebrow="How it works"
        title={<>Three seconds between you and the <span className="it">best price</span>.</>}
        intro="You change nothing about your habits. FILON works for you and shows you a single number: your real price. And one answer: buy, or wait."
        breadcrumb={[{ name: "How it works", path: "/comment-ca-marche" }]}
      />
      <Method />
      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "20ch" }}>What you get.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "€", h: "Your real price", p: "A single number, all in. No more back-of-the-envelope maths." },
              { n: "◷", h: "Buy or wait", p: "A clear answer, to buy at the right moment." },
              { n: "✓", h: "The best option", p: "New, refurbished, elsewhere: the best choice, when it exists." },
              { n: "★", h: "A reliable seller", p: "Reliability and warranties are taken into account, not just the price." },
              { n: "↧", h: "Without changing a thing", p: "You keep your habits. FILON works in the background." },
              { n: <IcHeart />, h: "Zero effort", p: "You describe, FILON decides. That's all." },
            ]}
          />
        </div>
      </section>
      <ClosingCta title={<>Try it, it&apos;s <span className="it">free</span>.</>} sub="Add FILON and let it find the deal before every purchase." />
    </>
  );
}

export default function CommentCaMarchePage() {
  return <Localized fr={<CommentFR />} nl={<CommentNL />} en={<CommentEN />} />;
}
