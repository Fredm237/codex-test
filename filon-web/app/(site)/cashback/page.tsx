import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, ClosingCta } from "@/components/editorial/ContentPage";
import { FaqBlock } from "@/components/editorial/Faq";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/cashback",
  title: "Cashback : de l'argent qui revient",
  description:
    "Avec FILON, récupérez le maximum sur vos achats, automatiquement. Sans chercher, sans comparer.",
});

const FAQ_FR = [
  { q: "Le cashback, c'est quoi au juste ?", a: "Une partie de votre achat qui vous revient après coup. Avec FILON, vous obtenez le maximum, sans rien faire." },
  { q: "Dois-je comparer moi-même ?", a: "Non. FILON trouve la meilleure offre du moment à votre place, et vous y emmène." },
  { q: "C'est cumulable avec une promo ?", a: "Souvent oui. FILON vous indique simplement le meilleur prix final." },
  { q: "Quand est-ce que je le reçois ?", a: "Selon la boutique, de quelques jours à quelques semaines. FILON vous indique les conditions avant que vous ne décidiez." },
];

const FAQ_NL = [
  { q: "Wat is cashback precies ?", a: "Een deel van je aankoop dat je achteraf terugkrijgt. Met FILON krijg je het maximum, zonder iets te doen." },
  { q: "Moet ik zelf vergelijken ?", a: "Nee. FILON vindt de beste aanbieding van het moment in jouw plaats, en brengt je erheen." },
  { q: "Is het te combineren met een promo ?", a: "Vaak wel. FILON toont je gewoon de beste eindprijs." },
  { q: "Wanneer krijg ik het ?", a: "Afhankelijk van de winkel, van enkele dagen tot enkele weken. FILON toont de voorwaarden voordat je beslist." },
];

function CashbackFR() {
  return (
    <>
      <ContentHero
        eyebrow="Cashback"
        title={<>De l&apos;argent qui revient. À chaque <span className="it">achat</span>.</>}
        intro="Sur beaucoup d'achats, une partie de la somme peut vous revenir. FILON récupère le maximum pour vous, automatiquement. Vous n'avez rien à chercher."
        breadcrumb={[{ name: "Cashback", path: "/cashback" }]}
        photo="/img/video-cashback-poster.webp"
        video="/video/cashback-coin.mp4"
      />
      <ProseBlock heading={<>L&apos;argent que vous oubliez de <span className="it">récupérer</span>.</>}>
        <p>
          Beaucoup de gens laissent cet argent sur la table, simplement par manque de temps. C&apos;est dommage, et
          c&apos;est évitable.
        </p>
        <p>
          FILON s&apos;en occupe. Au bon moment, il vous obtient la meilleure offre et vous encaissez plus. Vous gardez
          vos habitudes, vous payez moins.
        </p>
      </ProseBlock>
      <FaqBlock items={FAQ_FR} eyebrow="Cashback · FAQ" title="Le cashback, sans zone d'ombre." />
      <ClosingCta title={<>Ne cliquez plus jamais « payer » <span className="it">sans</span> FILON.</>} sub="Il s'en occupe pour vous, gratuitement, à chaque achat." />
    </>
  );
}

function CashbackNL() {
  return (
    <>
      <ContentHero
        eyebrow="Cashback"
        title={<>Geld dat terugkomt. Bij elke <span className="it">aankoop</span>.</>}
        intro="Bij veel aankopen kan een deel van het bedrag naar jou terugvloeien. FILON haalt het maximum voor je binnen, automatisch. Jij hoeft niets te zoeken."
        breadcrumb={[{ name: "Cashback", path: "/cashback" }]}
        photo="/img/video-cashback-poster.webp"
        video="/video/cashback-coin.mp4"
      />
      <ProseBlock heading={<>Het geld dat je vergeet <span className="it">terug te halen</span>.</>}>
        <p>
          Veel mensen laten dat geld liggen, gewoon door tijdgebrek. Zonde, en vermijdbaar.
        </p>
        <p>
          FILON regelt het. Op het juiste moment krijg je de beste aanbieding en houd je meer over. Je behoudt je
          gewoontes, je betaalt minder.
        </p>
      </ProseBlock>
      <FaqBlock items={FAQ_NL} eyebrow="Cashback · FAQ" title="Cashback, zonder grijze zones." />
      <ClosingCta title={<>Klik nooit meer op « betalen » <span className="it">zonder</span> FILON.</>} sub="Hij regelt het voor jou, gratis, bij elke aankoop." />
    </>
  );
}

export default function CashbackPage() {
  return <Localized fr={<CashbackFR />} nl={<CashbackNL />} />;
}
