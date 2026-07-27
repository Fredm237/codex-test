import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, InfoGrid, ClosingCta } from "@/components/editorial/ContentPage";
import { IcChat } from "@/components/editorial/icons";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/intelligence",
  title: "L'intelligence FILON",
  description:
    "Le prix le plus bas n'est pas toujours le meilleur achat. FILON regarde ce qui compte vraiment : le bon produit, au bon moment, qui dure.",
});

function IntelligenceFR() {
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
              { n: <IcChat />, h: "Les avis, en clair", p: "Des milliers d'avis résumés en une réponse. Le signal, pas le bruit." },
              { n: "✓", h: "La meilleure alternative", p: "Neuf, reconditionné, ailleurs : la meilleure option, quand elle existe." },
            ]}
          />
        </div>
      </section>
      <ClosingCta title={<>L&apos;intelligence au service de <span className="it">votre</span> achat.</>} sub="Une réponse claire, à chaque fois. Et gratuite." />
    </>
  );
}

function IntelligenceNL() {
  return (
    <>
      <ContentHero
        eyebrow="De FILON-intelligentie"
        title={<>Verder dan de <span className="it">prijs</span>.</>}
        intro="De laagste prijs is niet altijd de beste aankoop. FILON kijkt naar wat echt telt, om je slechte verrassingen te besparen."
        breadcrumb={[{ name: "Intelligentie", path: "/intelligence" }]}
      />
      <ProseBlock heading={<>De juiste aankoop, niet alleen de juiste <span className="it">prijs</span>.</>}>
        <p>
          Een goede aankoop is het juiste product, op het juiste moment, dat meegaat. FILON houdt met dat alles rekening,
          in jouw plaats, in enkele seconden.
        </p>
        <p>
          Jij krijgt een eenvoudig antwoord. Daarachter is veel voor je afgewogen.
        </p>
      </ProseBlock>
      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <span className="eyebrow" style={{ display: "block", marginBottom: 12 }}>Waar FILON voor jou naar kijkt</span>
            <h2 style={{ maxWidth: "20ch" }}>Veel meer dan een prijs.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "◷", h: "Het juiste moment", p: "Een bodemprijs, gemiddeld, of opgeblazen. Je weet of je moet kopen of wachten." },
              { n: "★", h: "Betrouwbaarheid", p: "Een product dat meegaat, met echte service erachter." },
              { n: "⌛", h: "De levensduur", p: "Hoelang het echt meegaat, in gebruik." },
              { n: "€", h: "De echte kost", p: "Niet alleen de getoonde prijs, maar wat het op termijn kost." },
              { n: <IcChat />, h: "Reviews, helder", p: "Duizenden reviews samengevat in één antwoord. Het signaal, niet de ruis." },
              { n: "✓", h: "Het beste alternatief", p: "Nieuw, refurbished, elders : de beste optie, wanneer die bestaat." },
            ]}
          />
        </div>
      </section>
      <ClosingCta title={<>Intelligentie ten dienste van <span className="it">jouw</span> aankoop.</>} sub="Een duidelijk antwoord, elke keer. En gratis." />
    </>
  );
}

function IntelligenceEN() {
  return (
    <>
      <ContentHero
        eyebrow="FILON intelligence"
        title={<>Beyond the <span className="it">price</span>.</>}
        intro="The lowest price isn't always the best purchase. FILON looks at what really matters, to spare you nasty surprises."
        breadcrumb={[{ name: "Intelligence", path: "/intelligence" }]}
      />
      <ProseBlock heading={<>The right purchase, not just the right <span className="it">price</span>.</>}>
        <p>
          A good purchase is the right product, at the right moment, that lasts. FILON takes all of that into
          account, for you, in a few seconds.
        </p>
        <p>You receive a simple answer. Behind it, a lot has been weighed up for you.</p>
      </ProseBlock>
      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <span className="eyebrow" style={{ display: "block", marginBottom: 12 }}>What FILON looks at for you</span>
            <h2 style={{ maxWidth: "20ch" }}>Much more than a price.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "◷", h: "The right moment", p: "A rock-bottom price, average, or inflated. You know whether to buy or wait." },
              { n: "★", h: "Reliability", p: "A product that holds up over time, with real service behind it." },
              { n: "⌛", h: "The lifespan", p: "How long it will really last, in use." },
              { n: "€", h: "The real cost", p: "Not just the displayed price, but what it costs over time." },
              { n: <IcChat />, h: "Reviews, made clear", p: "Thousands of reviews summed up in one answer. The signal, not the noise." },
              { n: "✓", h: "The best alternative", p: "New, refurbished, elsewhere: the best option, when it exists." },
            ]}
          />
        </div>
      </section>
      <ClosingCta title={<>Intelligence in service of <span className="it">your</span> purchase.</>} sub="A clear answer, every time. And free." />
    </>
  );
}

export default function IntelligencePage() {
  return <Localized fr={<IntelligenceFR />} nl={<IntelligenceNL />} en={<IntelligenceEN />} />;
}
