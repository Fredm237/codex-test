import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, InfoGrid, ClosingCta } from "@/components/editorial/ContentPage";
import { IcChat } from "@/components/editorial/icons";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/intelligence",
  title: "L'intelligence FILON",
  description:
    "FILON expose les signaux disponibles pour une offre : prix observé, historique, stock, fraîcheur, périmètre et inconnues.",
});

function IntelligenceFR() {
  return (
    <>
      <ContentHero
        eyebrow="L'intelligence FILON"
        title={<>Plus loin que le <span className="it">prix</span>.</>}
        intro="Le prix affiché ne suffit pas toujours pour comparer. FILON met en regard les informations disponibles sur une offre, pour vous aider à décider avec plus de contexte."
        breadcrumb={[{ name: "Intelligence", path: "/intelligence" }]}
      />
      <ProseBlock heading={<>Le bon achat, pas juste le bon <span className="it">prix</span>.</>}>
        <p>
          Une offre ne contient pas toujours toutes les informations utiles. FILON organise ce qui est disponible dans
          son catalogue afin de rendre la comparaison plus lisible.
        </p>
        <p>
          Prix affiché, marchand, cashback, codes promo et score peuvent être présentés selon l&apos;offre. La décision et la
          vérification finale restent entre vos mains.
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
              { n: "€", h: "Le prix affiché", p: "Le prix indiqué par le marchand dans le catalogue ; il peut évoluer avant votre commande." },
              { n: "◷", h: "Le contexte de prix", p: "Lorsqu'un historique ou un score est disponible, FILON l'affiche avec ses limites de données." },
              { n: "★", h: "Le marchand", p: "Le nom, la région et le secteur de la source marchande quand ces informations sont renseignées." },
              { n: "⌁", h: "Le cashback", p: "Le cashback et ses conditions lorsqu'ils sont transmis pour l'offre concernée." },
              { n: <IcChat />, h: "Les codes promo", p: "Les codes ou avantages disponibles lorsqu'ils sont indiqués dans les données de l'offre." },
              { n: "✓", h: "Les alternatives", p: "D'autres offres correspondant à votre recherche, sans promettre un classement universel." },
            ]}
          />
        </div>
      </section>
      <ClosingCta title={<>Les preuves au service de <span className="it">votre</span> choix.</>} sub="Un point de départ borné avant votre décision. Consultez la page Tarifs pour l'accès actuel." />
    </>
  );
}

function IntelligenceNL() {
  return (
    <>
      <ContentHero
        eyebrow="De FILON-intelligentie"
        title={<>Verder dan de <span className="it">prijs</span>.</>}
        intro="De getoonde prijs alleen volstaat niet altijd om te vergelijken. FILON zet de beschikbare informatie over een aanbod naast elkaar, zodat je met meer context kunt beslissen."
        breadcrumb={[{ name: "Intelligentie", path: "/intelligence" }]}
      />
      <ProseBlock heading={<>De juiste aankoop, niet alleen de juiste <span className="it">prijs</span>.</>}>
        <p>
          Een aanbod bevat niet altijd alle nuttige informatie. FILON ordent wat er in zijn catalogus beschikbaar is om
          vergelijken duidelijker te maken.
        </p>
        <p>
          Getoonde prijs, winkel, cashback, kortingscodes en score kunnen per aanbod worden getoond. De uiteindelijke
          beslissing en controle blijven bij jou.
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
              { n: "€", h: "De getoonde prijs", p: "De prijs die de winkel in de catalogus aangeeft; die kan vóór je bestelling veranderen." },
              { n: "◷", h: "Prijscontext", p: "Wanneer een historiek of score beschikbaar is, toont FILON die met de beperkingen van de gegevens." },
              { n: "★", h: "De winkel", p: "Naam, regio en sector van de winkelbron wanneer die informatie vermeld is." },
              { n: "⌁", h: "Cashback", p: "Cashback en voorwaarden wanneer ze voor het betrokken aanbod worden doorgestuurd." },
              { n: <IcChat />, h: "Kortingscodes", p: "Beschikbare codes of voordelen wanneer ze in de aanbodgegevens staan." },
              { n: "✓", h: "Alternatieven", p: "Andere aanbiedingen die bij je zoekopdracht passen, zonder een universele rangschikking te beloven." },
            ]}
          />
        </div>
      </section>
      <ClosingCta title={<>Bewijs ten dienste van <span className="it">jouw</span> keuze.</>} sub="Een afgebakend vertrekpunt vóór je beslist. Raadpleeg Tarieven voor de huidige toegang." />
    </>
  );
}

function IntelligenceEN() {
  return (
    <>
      <ContentHero
        eyebrow="FILON intelligence"
        title={<>Beyond the <span className="it">price</span>.</>}
        intro="The displayed price alone is not always enough to compare. FILON puts the available information about an offer side by side, so you can decide with more context."
        breadcrumb={[{ name: "Intelligence", path: "/intelligence" }]}
      />
      <ProseBlock heading={<>The right purchase, not just the right <span className="it">price</span>.</>}>
        <p>
          An offer does not always include every useful detail. FILON organises what is available in its catalogue to
          make comparison clearer.
        </p>
        <p>Displayed price, merchant, cashback, promo codes and a score may be shown depending on the offer. The final decision and verification remain yours.</p>
      </ProseBlock>
      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <span className="eyebrow" style={{ display: "block", marginBottom: 12 }}>What FILON looks at for you</span>
            <h2 style={{ maxWidth: "20ch" }}>Much more than a price.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "€", h: "The displayed price", p: "The price listed by the merchant in the catalogue; it can change before you order." },
              { n: "◷", h: "Price context", p: "When a history or score is available, FILON shows it with its data limitations." },
              { n: "★", h: "The merchant", p: "The merchant source's name, region and sector when this information is listed." },
              { n: "⌁", h: "Cashback", p: "Cashback and its terms when they are supplied for the relevant offer." },
              { n: <IcChat />, h: "Promo codes", p: "Available codes or benefits when they are listed in the offer data." },
              { n: "✓", h: "Alternatives", p: "Other offers matching your search, without promising a universal ranking." },
            ]}
          />
        </div>
      </section>
      <ClosingCta title={<>Evidence in service of <span className="it">your</span> choice.</>} sub="A bounded starting point before you decide. See Pricing for current access." />
    </>
  );
}

export default function IntelligencePage() {
  return <Localized fr={<IntelligenceFR />} nl={<IntelligenceNL />} en={<IntelligenceEN />} />;
}
