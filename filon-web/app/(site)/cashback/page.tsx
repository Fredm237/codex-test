import type { Metadata } from "next";
import type { ReactNode } from "react";
import { breadcrumbSchema, buildMetadata, JsonLd } from "@/lib/seo";
import { ClosingCta } from "@/components/editorial/ContentPage";
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

function CashbackBody({ t, faq }: { t: {
  eyebrow: string; title: ReactNode; intro: string;
  stages: Array<[string, string]>; heading: ReactNode; bodyA: string; bodyB: string;
  faqEye: string; faqTitle: string; closing: ReactNode; closingSub: string;
}; faq: typeof FAQ_FR }) {
  return (
    <div className="p19-decision-surface p19-cashback-surface" data-decision-plan="cashback">
      <JsonLd data={breadcrumbSchema([{ name: "Accueil", path: "/" }, { name: "Cashback", path: "/cashback" }])} />
      <section className="p19-decision-hero">
        <div className="ed-wrap p19-decision-hero-grid">
          <div className="p19-decision-copy">
            <span className="eyebrow">{t.eyebrow}</span>
            <h1>{t.title}</h1>
            <p className="intro">{t.intro}</p>
          </div>
          <ol className="p19-cashback-gate" aria-label={t.eyebrow}>
            {t.stages.map(([label, state], index) => (
              <li key={label}>
                <span>0{index + 1}</span>
                <strong>{label}</strong>
                <small>{state}</small>
              </li>
            ))}
          </ol>
        </div>
      </section>
      <section className="p19-cashback-proof">
        <div className="ed-wrap p19-guardrail-grid">
          <h2>{t.heading}</h2>
          <div>
            <p>{t.bodyA}</p>
            <p>{t.bodyB}</p>
          </div>
        </div>
      </section>
      <div className="p19-decision-faq">
        <FaqBlock items={faq} eyebrow={t.faqEye} title={t.faqTitle} />
      </div>
      <div className="p19-decision-closing">
        <ClosingCta title={t.closing} sub={t.closingSub} />
      </div>
    </div>
  );
}

const FR = {
  eyebrow: "Cashback",
  title: <>Un avantage conditionnel, lorsqu&apos;il est <span className="it">documenté</span>.</>,
  intro: "Sur certains achats éligibles, une partie de la somme peut revenir après validation. FILON affiche l'avantage uniquement lorsqu'il est présent dans une source indexée.",
  stages: [["Source indexée", "requise"], ["Conditions", "à lire"], ["Versement", "à confirmer"]] as Array<[string, string]>,
  heading: <>De la preuve à <span className="it">l&apos;avantage réel</span>.</>,
  bodyA: "Beaucoup de gens laissent cet argent sur la table, simplement par manque de temps. C'est dommage, et c'est évitable.",
  bodyB: "FILON peut signaler un avantage documenté avec son périmètre. Le taux, le cumul, l'éligibilité et le versement restent soumis aux conditions de la plateforme concernée.",
  faqEye: "Cashback · FAQ", faqTitle: "Le cashback, sans zone d'ombre.",
  closing: <>Vérifiez les <span className="it">conditions</span> avant de payer.</>,
  closingSub: "FILON montre les avantages indexés lorsqu'ils sont documentés.",
};

const NL = {
  eyebrow: "Cashback",
  title: <>Een voorwaardelijk voordeel, wanneer het is <span className="it">gedocumenteerd</span>.</>,
  intro: "Bij sommige in aanmerking komende aankopen kan een deel na validatie terugkomen. FILON toont het voordeel alleen wanneer het in een geïndexeerde bron staat.",
  stages: [["Geïndexeerde bron", "vereist"], ["Voorwaarden", "te lezen"], ["Uitbetaling", "te bevestigen"]] as Array<[string, string]>,
  heading: <>Van bewijs naar het <span className="it">werkelijke voordeel</span>.</>,
  bodyA: "Veel mensen laten dat geld liggen, gewoon door tijdgebrek. Zonde, en vermijdbaar.",
  bodyB: "FILON kan een gedocumenteerd voordeel met zijn bereik tonen. Tarief, combinatie, geschiktheid en uitbetaling blijven onderworpen aan de voorwaarden van het betrokken platform.",
  faqEye: "Cashback · FAQ", faqTitle: "Cashback, zonder grijze zones.",
  closing: <>Controleer de <span className="it">voorwaarden</span> voordat je betaalt.</>,
  closingSub: "FILON toont geïndexeerde voordelen wanneer ze gedocumenteerd zijn.",
};

const EN = {
  eyebrow: "Cashback",
  title: <>A conditional benefit, when it is <span className="it">documented</span>.</>,
  intro: "On some eligible purchases, part of the amount may return after validation. FILON shows a benefit only when it is present in an indexed source.",
  stages: [["Indexed source", "required"], ["Terms", "to review"], ["Payment", "to confirm"]] as Array<[string, string]>,
  heading: <>From evidence to the <span className="it">real benefit</span>.</>,
  bodyA: "Many people leave that money on the table, simply for lack of time. It's a shame, and it's avoidable.",
  bodyB: "FILON can flag a documented benefit with its scope. Rate, combination, eligibility and payment remain subject to the relevant platform's terms.",
  faqEye: "Cashback · FAQ", faqTitle: "Cashback, with no grey areas.",
  closing: <>Check the <span className="it">terms</span> before you pay.</>,
  closingSub: "FILON shows indexed benefits when they are documented.",
};

export default function CashbackPage() {
  return <Localized fr={<CashbackBody t={FR} faq={FAQ_FR} />} nl={<CashbackBody t={NL} faq={FAQ_NL} />} en={<CashbackBody t={EN} faq={FAQ_EN} />} />;
}
