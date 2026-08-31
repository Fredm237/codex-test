"use client";

import { faqSchema, JsonLd } from "@/lib/seo";
import { Reveal } from "./Reveal";
import { useLocale } from "@/lib/i18n";

export type QA = { q: string; a: string };

export const HOME_FAQ: QA[] = [
  {
    q: "FILON est-il vraiment gratuit ?",
    a: "L'accès public actuel ne demande ni paiement ni carte bancaire. Consultez la page Tarifs pour l'offre à jour et la politique de confidentialité pour les données traitées.",
  },
  {
    q: "Puis-je faire confiance à sa recommandation ?",
    a: "FILON montre le périmètre comparé, la fraîcheur et les informations manquantes. Une commission n'entre pas dans le score actuel, et FILON s'abstient si les données ne suffisent pas.",
  },
  {
    q: "Le reconditionné proposé est-il fiable ?",
    a: "Une offre reconditionnée peut apparaître lorsqu'elle est indexée. Son état, sa garantie, son retour et son vendeur restent à vérifier dans les conditions de l'offre.",
  },
  {
    q: "Mes données sont-elles revendues ?",
    a: "La politique de confidentialité décrit les données traitées, les destinataires éventuels et vos droits. Elle constitue la référence à jour.",
  },
  {
    q: "Quand arrivent l'extension et l'application ?",
    a: "Le catalogue et l'assistant sont accessibles sur le site. L'extension Chrome sera annoncée après sa publication ; les autres surfaces sont annoncées lorsqu'elles deviennent disponibles.",
  },
];

const HOME_FAQ_NL: QA[] = [
  { q: "Is FILON echt gratis?", a: "De huidige publieke toegang vraagt geen betaling of bankkaart. Raadpleeg Tarieven voor het actuele aanbod en het privacybeleid voor verwerkte gegevens." },
  { q: "Kan ik zijn aanbeveling vertrouwen?", a: "FILON toont het vergeleken bereik, de actualiteit en ontbrekende gegevens. Commissie telt niet mee in de huidige score, en FILON onthoudt zich wanneer bewijs ontbreekt." },
  { q: "Is het aangeboden refurbished betrouwbaar?", a: "Een refurbished aanbieding kan verschijnen wanneer ze geïndexeerd is. Controleer staat, garantie, retour en verkoper in de voorwaarden van de aanbieding." },
  { q: "Worden mijn gegevens doorverkocht?", a: "Het privacybeleid beschrijft verwerkte gegevens, mogelijke ontvangers en je rechten. Dat is de actuele referentie." },
  { q: "Wanneer komen de extensie en de app?", a: "Catalogus en assistent zijn beschikbaar op de site. De Chrome-extensie wordt na publicatie aangekondigd; andere oppervlakken worden aangekondigd wanneer ze beschikbaar zijn." },
];

const HOME_FAQ_EN: QA[] = [
  { q: "Is FILON really free?", a: "Current public access requires no payment or card. See Pricing for the current offer and the privacy policy for processed data." },
  { q: "Can I trust its recommendation?", a: "FILON shows the comparison scope, freshness and missing data. Commission is not part of the current score, and FILON abstains when evidence is insufficient." },
  { q: "Is the refurbished offered reliable?", a: "A refurbished offer may appear when it is indexed. Check its condition, warranty, returns and seller in the offer terms." },
  { q: "Is my data resold?", a: "The privacy policy describes processed data, possible recipients and your rights. It is the current reference." },
  { q: "When do the extension and the app arrive?", a: "The catalogue and assistant are available on the site. The Chrome extension will be announced after publication; other surfaces are announced when available." },
];

export function FaqBlock({
  items,
  id = "faq",
  eyebrow = "FAQ",
  title = "Les questions que vous vous posez.",
}: {
  items: QA[];
  id?: string;
  eyebrow?: string;
  title?: string;
}) {
  return (
    <section className="ed-band" id={id}>
      <JsonLd data={faqSchema(items)} />
      <div className="ed-wrap">
        <Reveal>
          <div className="ed-lead">
            <span className="idx">{eyebrow}</span>
            <h2>{title}</h2>
          </div>
        </Reveal>
        <div className="ed-faq">
          {items.map((it) => (
            <details className="ed-qa" key={it.q}>
              <summary>
                {it.q}
                <span className="pl" aria-hidden="true" />
              </summary>
              <div className="a">{it.a}</div>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}

export function Faq() {
  const { locale } = useLocale();
  const items = locale === "nl" ? HOME_FAQ_NL : locale === "en" ? HOME_FAQ_EN : HOME_FAQ;
  const title =
    locale === "nl" ? "De vragen die je je stelt." : locale === "en" ? "The questions you're asking." : "Les questions que vous vous posez.";
  return <FaqBlock items={items} title={title} />;
}
