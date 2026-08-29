import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, ClosingCta } from "@/components/editorial/ContentPage";
import { FaqBlock } from "@/components/editorial/Faq";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/cashback",
  title: "Cashback : de l'argent qui revient",
  description:
    "FILON affiche un cashback lorsqu'un avantage indexé documente son taux et ses conditions. La validation finale appartient à la plateforme concernée.",
});

const FAQ_FR = [
  { q: "Le cashback, c'est quoi au juste ?", a: "Un avantage conditionnel versé après un achat éligible. Son taux, son délai et sa validation dépendent de la plateforme et du marchand." },
  { q: "FILON compare-t-il toutes les plateformes ?", a: "Non. FILON ne peut montrer que les avantages présents dans ses sources indexées. Le périmètre disponible doit rester visible." },
  { q: "C'est cumulable avec une promo ?", a: "Cela dépend des conditions de l'avantage. Une compatibilité inconnue n'est pas présentée comme acquise." },
  { q: "Quand est-ce que je le reçois ?", a: "Le délai et la validation sont fixés par la plateforme concernée. Vérifiez ses conditions avant l'achat." },
];

const FAQ_NL = [
  { q: "Wat is cashback precies ?", a: "Een voorwaardelijk voordeel dat na een in aanmerking komende aankoop wordt uitbetaald. Tarief, termijn en validatie hangen af van platform en winkel." },
  { q: "Vergelijkt FILON alle platforms ?", a: "Nee. FILON kan alleen voordelen tonen die in zijn geïndexeerde bronnen staan. Het beschikbare bereik moet zichtbaar blijven." },
  { q: "Is het te combineren met een promo ?", a: "Dat hangt af van de voorwaarden. Een onbekende combinatie wordt niet als geldig voorgesteld." },
  { q: "Wanneer krijg ik het ?", a: "Termijn en validatie worden door het betrokken platform bepaald. Controleer de voorwaarden voor de aankoop." },
];

const FAQ_EN = [
  { q: "What exactly is cashback ?", a: "A conditional benefit paid after an eligible purchase. Its rate, timing and validation depend on the platform and merchant." },
  { q: "Does FILON compare every platform ?", a: "No. FILON can only show benefits present in its indexed sources. The available scope must remain visible." },
  { q: "Can it be combined with a promo ?", a: "That depends on the benefit terms. An unknown combination is not presented as valid." },
  { q: "When do I receive it ?", a: "Timing and validation are set by the relevant platform. Check its terms before buying." },
];

function CashbackFR() {
  return (
    <>
      <ContentHero
        eyebrow="Cashback"
        title={<>Un avantage conditionnel, lorsqu&apos;il est <span className="it">documenté</span>.</>}
        intro="Sur certains achats éligibles, une partie de la somme peut revenir après validation. FILON affiche l'avantage uniquement lorsqu'il est présent dans une source indexée."
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
          FILON peut signaler un avantage documenté avec son périmètre. Le taux,
          le cumul, l&apos;éligibilité et le versement restent soumis aux conditions
          de la plateforme concernée.
        </p>
      </ProseBlock>
      <FaqBlock items={FAQ_FR} eyebrow="Cashback · FAQ" title="Le cashback, sans zone d'ombre." />
      <ClosingCta title={<>Vérifiez les <span className="it">conditions</span> avant de payer.</>} sub="FILON montre les avantages indexés lorsqu'ils sont documentés." />
    </>
  );
}

function CashbackNL() {
  return (
    <>
      <ContentHero
        eyebrow="Cashback"
        title={<>Een voorwaardelijk voordeel, wanneer het is <span className="it">gedocumenteerd</span>.</>}
        intro="Bij sommige in aanmerking komende aankopen kan een deel na validatie terugkomen. FILON toont het voordeel alleen wanneer het in een geïndexeerde bron staat."
        breadcrumb={[{ name: "Cashback", path: "/cashback" }]}
        photo="/img/video-cashback-poster.webp"
        video="/video/cashback-coin.mp4"
      />
      <ProseBlock heading={<>Het geld dat je vergeet <span className="it">terug te halen</span>.</>}>
        <p>
          Veel mensen laten dat geld liggen, gewoon door tijdgebrek. Zonde, en vermijdbaar.
        </p>
        <p>
          FILON kan een gedocumenteerd voordeel met zijn bereik tonen. Tarief,
          combinatie, geschiktheid en uitbetaling blijven onderworpen aan de
          voorwaarden van het betrokken platform.
        </p>
      </ProseBlock>
      <FaqBlock items={FAQ_NL} eyebrow="Cashback · FAQ" title="Cashback, zonder grijze zones." />
      <ClosingCta title={<>Controleer de <span className="it">voorwaarden</span> voordat je betaalt.</>} sub="FILON toont geïndexeerde voordelen wanneer ze gedocumenteerd zijn." />
    </>
  );
}

function CashbackEN() {
  return (
    <>
      <ContentHero
        eyebrow="Cashback"
        title={<>A conditional benefit, when it is <span className="it">documented</span>.</>}
        intro="On some eligible purchases, part of the amount may return after validation. FILON shows a benefit only when it is present in an indexed source."
        breadcrumb={[{ name: "Cashback", path: "/cashback" }]}
        photo="/img/video-cashback-poster.webp"
        video="/video/cashback-coin.mp4"
      />
      <ProseBlock heading={<>The money you forget to <span className="it">reclaim</span>.</>}>
        <p>
          Many people leave that money on the table, simply for lack of time. It&apos;s a shame, and it&apos;s
          avoidable.
        </p>
        <p>
          FILON can flag a documented benefit with its scope. Rate, combination,
          eligibility and payment remain subject to the relevant platform&apos;s terms.
        </p>
      </ProseBlock>
      <FaqBlock items={FAQ_EN} eyebrow="Cashback · FAQ" title="Cashback, with no grey areas." />
      <ClosingCta title={<>Check the <span className="it">terms</span> before you pay.</>} sub="FILON shows indexed benefits when they are documented." />
    </>
  );
}

export default function CashbackPage() {
  return <Localized fr={<CashbackFR />} nl={<CashbackNL />} en={<CashbackEN />} />;
}
