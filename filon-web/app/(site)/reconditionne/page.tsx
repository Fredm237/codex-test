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
  { q: "Que veulent dire les grades A, A+, etc. ?", a: "Le grade décrit l'état esthétique : un grade A+ est quasi neuf, un grade B présente de légères marques d'usage sans impact sur le fonctionnement. FILON affiche le grade pour chaque offre afin que vous choisissiez en connaissance de cause." },
  { q: "Le reconditionné, est-ce vraiment plus écologique ?", a: "Oui : prolonger la vie d'un appareil évite la fabrication d'un neuf, gros consommateur de ressources et d'énergie. C'est l'un des gestes les plus efficaces pour réduire l'empreinte de vos achats tech." },
  { q: "Puis-je cumuler reconditionné et cashback ?", a: "Lorsqu’un avantage est vérifié et applicable à l’offre, FILON l’indique. Il ne le présente jamais comme acquis avant vérification." },
];

const FAQ_NL = [
  { q: "Is een refurbished product betrouwbaar ?", a: "Dat hangt af van de aanbieding en de verkoper. FILON helpt je de aangegeven staat, de garantie wanneer die wordt vermeld en de prijscontext te vergelijken voordat je beslist." },
  { q: "Hoeveel kun je echt besparen ?", a: "Dat hangt af van het product, de staat en de beschikbare aanbiedingen. FILON toont het verschil wanneer een vergelijkbare nieuwe aanbieding in de catalogus staat." },
  { q: "Wat betekenen de grades A, A+, enz. ?", a: "De grade beschrijft de esthetische staat: A+ is zo goed als nieuw, grade B vertoont lichte gebruikssporen zonder invloed op de werking. FILON toont de grade bij elke aanbieding zodat je met kennis van zaken kiest." },
  { q: "Is refurbished echt milieuvriendelijker ?", a: "Ja: het leven van een toestel verlengen vermijdt de productie van een nieuw toestel, dat veel grondstoffen en energie verbruikt. Het is een van de doeltreffendste gebaren om de voetafdruk van je tech-aankopen te verkleinen." },
  { q: "Kan ik refurbished en cashback combineren ?", a: "Wanneer een voordeel geverifieerd en toepasbaar is op de aanbieding, vermeldt FILON het. Het wordt nooit als verworven voorgesteld vóór verificatie." },
];

const FAQ_EN = [
  { q: "Is a refurbished product reliable ?", a: "It depends on the offer and the merchant. FILON helps you compare the stated condition, the warranty when supplied and the price context before you decide." },
  { q: "How much can you really save ?", a: "It depends on the product, its condition and the available offers. FILON shows the difference when a comparable new offer is indexed in the catalogue." },
  { q: "What do grades A, A+, etc. mean ?", a: "The grade describes the cosmetic condition: an A+ grade is almost new, a B grade shows slight signs of use with no impact on functioning. FILON displays the grade for each offer so you choose with full knowledge." },
  { q: "Is refurbished really more eco-friendly ?", a: "Yes: extending a device's life avoids manufacturing a new one, a heavy consumer of resources and energy. It's one of the most effective moves to reduce the footprint of your tech purchases." },
  { q: "Can I combine refurbished and cashback ?", a: "When a benefit is verified and applies to the offer, FILON indicates it. It is never presented as certain before verification." },
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
          la garantie, le vendeur, puis calculer l&apos;économie réelle.
        </p>
        <p>
          Lorsqu&apos;elles sont disponibles, FILON rapproche les offres <b>neuves</b>, les alternatives <b>reconditionnées</b>
          et les informations utiles à la comparaison. Vous décidez avec un contexte clair, sans passer votre soirée à chercher.
        </p>
      </ProseBlock>
      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "20ch" }}>Ce que FILON vérifie avant de vous le proposer.</h2>
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
      <FaqBlock items={FAQ_FR} eyebrow="Reconditionné · FAQ" title="Le reconditionné, en toute confiance." />
      <ClosingCta title={<>Payez le <span className="it">juste</span> prix. Pas le prix neuf.</>} sub="FILON compare neuf et reconditionné à chaque achat, gratuitement." />
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
          verkoper checken, en dan de echte besparing berekenen.
        </p>
        <p>
          Wanneer ze beschikbaar zijn, brengt FILON <b>nieuwe aanbiedingen</b>, <b>refurbished alternatieven</b> en de
          informatie voor een vergelijking samen. Zo beslis je met duidelijke context, zonder je hele avond te zoeken.
        </p>
      </ProseBlock>
      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "20ch" }}>Wat FILON controleert voordat het je iets aanbeveelt.</h2>
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
      <FaqBlock items={FAQ_NL} eyebrow="Refurbished · FAQ" title="Refurbished, met een gerust hart." />
      <ClosingCta title={<>Betaal de <span className="it">juiste</span> prijs. Niet de nieuwprijs.</>} sub="FILON vergelijkt nieuw en refurbished bij elke aankoop, gratis." />
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
          the seller, then calculating the real saving.
        </p>
        <p>
          When they are available, FILON brings together <b>new offers</b>, <b>refurbished alternatives</b> and the
          information needed for comparison. You decide with clear context, without spending your evening searching.
        </p>
      </ProseBlock>
      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "20ch" }}>What FILON checks before recommending it to you.</h2>
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
      <FaqBlock items={FAQ_EN} eyebrow="Refurbished · FAQ" title="Refurbished, with peace of mind." />
      <ClosingCta title={<>Pay the <span className="it">right</span> price. Not the new price.</>} sub="FILON compares new and refurbished on every purchase, free." />
    </>
  );
}

export default function ReconditionnePage() {
  return <Localized fr={<ReconditionneFR />} nl={<ReconditionneNL />} en={<ReconditionneEN />} />;
}
