import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, InfoGrid, ClosingCta } from "@/components/editorial/ContentPage";
import { FaqBlock } from "@/components/editorial/Faq";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/reconditionne",
  title: "Reconditionné : comparer avant d’acheter",
  description:
    "Neuf ou reconditionné ? FILON aide à comparer les offres indexées, leur état, leur garantie lorsqu’elle est fournie et leur contexte de prix.",
});

const FAQ_FR = [
  { q: "Un produit reconditionné, est-ce fiable ?", a: "Cela dépend de l’offre et du vendeur. FILON vous aide à comparer l’état indiqué, la garantie lorsqu’elle est fournie et le contexte de prix avant de décider." },
  { q: "Quelle économie peut-on vraiment espérer ?", a: "Elle dépend du produit, de son état et des offres disponibles. FILON affiche l’écart lorsqu’une offre neuve comparable est présente dans le catalogue." },
  { q: "Que veulent dire les grades A, A+, etc. ?", a: "Les définitions varient selon les vendeurs. FILON restitue le grade annoncé lorsqu'il est disponible ; consultez les critères et exclusions du marchand avant de choisir." },
  { q: "Le reconditionné, est-ce vraiment plus écologique ?", a: "L'impact dépend notamment de la durée d'usage, du reconditionnement, du transport et du remplacement évité. FILON ne calcule actuellement pas d'empreinte environnementale par offre." },
  { q: "Puis-je cumuler reconditionné et cashback ?", a: "Lorsqu’un avantage est documenté pour l’offre, FILON peut l’indiquer. Son éligibilité et son cumul restent à confirmer selon les conditions du marchand." },
];

const FAQ_NL = [
  { q: "Is een refurbished product betrouwbaar ?", a: "Dat hangt af van de aanbieding en de verkoper. FILON helpt je de aangegeven staat, de garantie wanneer die wordt vermeld en de prijscontext te vergelijken voordat je beslist." },
  { q: "Hoeveel kun je echt besparen ?", a: "Dat hangt af van het product, de staat en de beschikbare aanbiedingen. FILON toont het verschil wanneer een vergelijkbare nieuwe aanbieding in de catalogus staat." },
  { q: "Wat betekenen de grades A, A+, enz. ?", a: "De definities verschillen per verkoper. FILON toont de vermelde grade wanneer die beschikbaar is; controleer de criteria en uitsluitingen van de winkel." },
  { q: "Is refurbished echt milieuvriendelijker ?", a: "De impact hangt onder meer af van gebruiksduur, refurbishing, vervoer en de vermeden vervanging. FILON berekent momenteel geen milieuvoetafdruk per aanbieding." },
  { q: "Kan ik refurbished en cashback combineren ?", a: "Wanneer een voordeel voor de aanbieding is gedocumenteerd, kan FILON het tonen. Controleer de voorwaarden van de winkel voor geschiktheid en combineerbaarheid." },
];

const FAQ_EN = [
  { q: "Is a refurbished product reliable ?", a: "It depends on the offer and the merchant. FILON helps you compare the stated condition, the warranty when supplied and the price context before you decide." },
  { q: "How much can you really save ?", a: "It depends on the product, its condition and the available offers. FILON shows the difference when a comparable new offer is indexed in the catalogue." },
  { q: "What do grades A, A+, etc. mean ?", a: "Definitions vary by seller. FILON displays the stated grade when available; check the merchant's criteria and exclusions before choosing." },
  { q: "Is refurbished really more eco-friendly ?", a: "The impact depends on factors including usage life, refurbishment, transport and avoided replacement. FILON does not currently calculate an environmental footprint per offer." },
  { q: "Can I combine refurbished and cashback ?", a: "When a benefit is documented for the offer, FILON may display it. Verify eligibility and compatibility in the merchant's terms." },
];

function ReconditionneFR() {
  return (
    <>
      <ContentHero
        eyebrow="Reconditionné"
        title={<>Le même produit. <span className="it">Comparer</span> avant d&apos;acheter.</>}
        intro="FILON vous aide à comparer les offres neuves et reconditionnées indexées : leur prix, leur état indiqué, leur garantie lorsqu’elle est disponible et les alternatives comparables."
        breadcrumb={[{ name: "Reconditionné", path: "/reconditionne" }]}
        photo="/img/page-reconditionne.webp"
      />
      <ProseBlock heading={<>Neuf ou reconditionné ? FILON vous <span className="it">éclaire</span>.</>}>
        <p>
          Comparer soi-même le neuf et le reconditionné, c&apos;est fastidieux : trouver l&apos;équivalent exact, vérifier
          la garantie et le vendeur, puis comparer l&apos;écart de prix affiché.
        </p>
        <p>
          Lorsqu&apos;elles sont disponibles, FILON rapproche les offres <b>neuves</b>, les alternatives <b>reconditionnées</b>
          et les informations utiles à la comparaison. Vous décidez avec un contexte clair, sans passer votre soirée à chercher.
        </p>
      </ProseBlock>
      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "20ch" }}>Ce que l&apos;offre peut documenter.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "✓", h: "État indiqué", p: "La condition esthétique et fonctionnelle annoncée par le marchand (A+, A, B…) est lisible avant votre choix." },
              { n: "✓", h: "Garantie affichée", p: "La garantie est présentée lorsqu’elle est communiquée par le marchand." },
              { n: "✓", h: "Écart comparable", p: "La différence avec le neuf est indiquée lorsqu’une offre comparable est disponible." },
            ]}
          />
        </div>
      </section>
      <FaqBlock items={FAQ_FR} eyebrow="Reconditionné · FAQ" title="Le reconditionné, preuves visibles et inconnues assumées." />
      <ClosingCta title={<>Comparez le <span className="it">contexte</span> disponible.</>} sub="FILON rapproche les offres neuves et reconditionnées indexées lorsqu'elles sont comparables." />
    </>
  );
}

function ReconditionneNL() {
  return (
    <>
      <ContentHero
        eyebrow="Refurbished"
        title={<>Hetzelfde product. <span className="it">Vergelijk</span> vóór je koopt.</>}
        intro="FILON helpt je geïndexeerde nieuwe en refurbished aanbiedingen te vergelijken: prijs, aangegeven staat, garantie wanneer beschikbaar en vergelijkbare alternatieven."
        breadcrumb={[{ name: "Refurbished", path: "/reconditionne" }]}
        photo="/img/page-reconditionne.webp"
      />
      <ProseBlock heading={<>Nieuw of refurbished ? FILON helpt je <span className="it">kiezen</span>.</>}>
        <p>
          Zelf nieuw en refurbished vergelijken is bewerkelijk : het exacte equivalent vinden, de garantie en de
          verkoper controleren en daarna het getoonde prijsverschil vergelijken.
        </p>
        <p>
          Wanneer ze beschikbaar zijn, brengt FILON <b>nieuwe aanbiedingen</b>, <b>refurbished alternatieven</b> en de
          informatie voor een vergelijking samen. Zo beslis je met duidelijke context, zonder je hele avond te zoeken.
        </p>
      </ProseBlock>
      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "20ch" }}>Wat de aanbieding kan documenteren.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "✓", h: "Aangegeven staat", p: "De door de winkel vermelde esthetische en functionele staat (A+, A, B…) is leesbaar vóór je kiest." },
              { n: "✓", h: "Getoonde garantie", p: "De garantie wordt vermeld wanneer de winkel die verstrekt." },
              { n: "✓", h: "Vergelijkbaar verschil", p: "Het verschil met nieuw wordt getoond wanneer een vergelijkbare aanbieding beschikbaar is." },
            ]}
          />
        </div>
      </section>
      <FaqBlock items={FAQ_NL} eyebrow="Refurbished · FAQ" title="Refurbished, met zichtbare bewijzen en benoemde onbekenden." />
      <ClosingCta title={<>Vergelijk de beschikbare <span className="it">context</span>.</>} sub="FILON brengt geïndexeerde nieuwe en refurbished aanbiedingen samen wanneer ze vergelijkbaar zijn." />
    </>
  );
}

function ReconditionneEN() {
  return (
    <>
      <ContentHero
        eyebrow="Refurbished"
        title={<>The same product. <span className="it">Compare</span> before you buy.</>}
        intro="FILON helps you compare indexed new and refurbished offers: their price, stated condition, warranty when available and comparable alternatives."
        breadcrumb={[{ name: "Refurbished", path: "/reconditionne" }]}
        photo="/img/page-reconditionne.webp"
      />
      <ProseBlock heading={<>New or refurbished ? FILON helps you <span className="it">choose</span>.</>}>
        <p>
          Comparing new and refurbished yourself is tedious: finding the exact equivalent, checking the warranty,
          the seller, then comparing the displayed price gap.
        </p>
        <p>
          When they are available, FILON brings together <b>new offers</b>, <b>refurbished alternatives</b> and the
          information needed for comparison. You decide with clear context, without spending your evening searching.
        </p>
      </ProseBlock>
      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "20ch" }}>What the offer can document.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "✓", h: "Stated condition", p: "The cosmetic and functional condition stated by the merchant (A+, A, B…) is clear before you choose." },
              { n: "✓", h: "Displayed warranty", p: "The warranty is shown when it is supplied by the merchant." },
              { n: "✓", h: "Comparable difference", p: "The difference versus new is shown when a comparable offer is available." },
            ]}
          />
        </div>
      </section>
      <FaqBlock items={FAQ_EN} eyebrow="Refurbished · FAQ" title="Refurbished, with visible evidence and named unknowns." />
      <ClosingCta title={<>Compare the available <span className="it">context</span>.</>} sub="FILON brings together indexed new and refurbished offers when they are comparable." />
    </>
  );
}

export default function ReconditionnePage() {
  return <Localized fr={<ReconditionneFR />} nl={<ReconditionneNL />} en={<ReconditionneEN />} />;
}
