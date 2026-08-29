import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, ClosingCta } from "@/components/editorial/ContentPage";
import { FaqBlock } from "@/components/editorial/Faq";
import { Reveal } from "@/components/editorial/Reveal";
import { ChromeCta } from "@/components/editorial/ChromeCta";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/tarifs",
  title: "Tarifs",
  description:
    "L'accès public actuel à FILON est à 0 € et ne demande pas de carte bancaire. Cette page décrit l'offre actuellement publiée.",
});

const INCLUS_FR = [
  "Les offres indexées, réunies au même endroit",
  "Un verdict lorsque l’historique disponible le permet",
  "Le contexte utile pour comparer avant d’acheter",
  "Des alternatives comparables, lorsqu’elles sont disponibles",
  "La page de présentation de l’extension Chrome",
  "Un accès actuel sans paiement ni carte bancaire",
  "Une politique de confidentialité et des droits documentés",
];

const INCLUS_NL = [
  "Geïndexeerde aanbiedingen, op één plek verzameld",
  "Een oordeel wanneer de beschikbare geschiedenis dit toelaat",
  "Nuttige context om te vergelijken vóór je koopt",
  "Vergelijkbare alternatieven, wanneer ze beschikbaar zijn",
  "De presentatiepagina van de Chrome-extensie",
  "Huidige toegang zonder betaling of bankkaart",
  "Een gedocumenteerd privacybeleid en rechten",
];

const INCLUS_EN = [
  "Indexed offers, gathered in one place",
  "A verdict when the available history supports it",
  "Useful context to compare before you buy",
  "Comparable alternatives, when they are available",
  "The Chrome extension presentation page",
  "Current access with no payment or card",
  "A documented privacy policy and rights",
];

const FAQ_FR = [
  { q: "Quel est le tarif actuel ?", a: "L'accès public affiché sur cette page est actuellement à 0 € et ne demande pas de carte bancaire." },
  { q: "La commission influence-t-elle le score actuel ?", a: "Non : le taux de commission n'est pas un champ du score actuel. Le classement reste borné aux offres éligibles et aux preuves disponibles." },
  { q: "Le tarif peut-il évoluer ?", a: "Oui. Cette page et les conditions publiées constituent la référence si l'offre change." },
  { q: "Comment mes données sont-elles traitées ?", a: "La politique de confidentialité décrit les données traitées, les destinataires éventuels et vos droits." },
];

const FAQ_NL = [
  { q: "Wat is het huidige tarief ?", a: "De publieke toegang op deze pagina kost momenteel 0 € en vraagt geen bankkaart." },
  { q: "Beïnvloedt commissie de huidige score ?", a: "Nee: het commissietarief is geen veld van de huidige score. De rangschikking blijft beperkt tot geschikte aanbiedingen en beschikbaar bewijs." },
  { q: "Kan het tarief veranderen ?", a: "Ja. Deze pagina en de gepubliceerde voorwaarden zijn de referentie als het aanbod verandert." },
  { q: "Hoe worden mijn gegevens verwerkt ?", a: "Het privacybeleid beschrijft verwerkte gegevens, mogelijke ontvangers en je rechten." },
];

const FAQ_EN = [
  { q: "What is the current price ?", a: "Public access shown on this page currently costs €0 and requires no payment card." },
  { q: "Does commission influence the current score ?", a: "No: commission rate is not a field in the current score. Ranking remains bounded to eligible offers and available evidence." },
  { q: "Can pricing change ?", a: "Yes. This page and the published terms are the reference if the offering changes." },
  { q: "How is my data processed ?", a: "The privacy policy describes processed data, possible recipients and your rights." },
];

function Plan({ tag, price, lede, items, chromeLabel }: { tag: string; price: React.ReactNode; lede: string; items: string[]; chromeLabel: string }) {
  return (
    <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
      <div className="ed-wrap">
        <Reveal>
          <div className="ed-plan featured" style={{ maxWidth: 620, margin: "0 auto" }}>
            <span className="tag">{tag}</span>
            <div className="name">Filon</div>
            <div className="price">{price}</div>
            <p className="lede">{lede}</p>
            <ul>
              {items.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
            <div className="cta-wrap">
              <ChromeCta variant="wave" label={chromeLabel} style={{ textDecoration: "none" }} />
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

function TarifsFR() {
  return (
    <>
      <ContentHero
        eyebrow="Tarifs"
        title={<>Accès public actuel. <span className="it">0 €.</span></>}
        intro="La version publique affichée aujourd'hui ne demande ni paiement ni carte bancaire. Cette page reste la référence si l'offre évolue."
        breadcrumb={[{ name: "Tarifs", path: "/tarifs" }]}
      />
      <Plan
        tag="Offre publique actuelle"
        price={<>0€ <small>/ aujourd'hui · sans carte bancaire</small></>}
        lede="Tout FILON. Décrivez un besoin, parcourez les offres indexées et consultez le verdict lorsque les données disponibles le permettent."
        items={INCLUS_FR}
        chromeLabel="Découvrir l’extension"
      />
      <p style={{ textAlign: "center", color: "var(--ink-3)", fontSize: 13.5, marginTop: -20 }}>
        Le taux de commission n'entre pas dans le score actuel. Confirmez le prix, les frais et le total chez le marchand.
      </p>
      <ProseBlock heading={<>Un tarif actuel <span className="it">explicite</span>.</>} alt>
        <p>
          L'accès public actuel est proposé à 0 €. Une évolution future doit être publiée sur cette page et dans les conditions applicables.
        </p>
        <p>
          Certains liens peuvent générer une commission. Cette commission n'entre pas dans les dimensions du score actuel.
        </p>
      </ProseBlock>
      <FaqBlock items={FAQ_FR} eyebrow="Tarifs · FAQ" title="Ce que « gratuit » veut vraiment dire." />
      <ClosingCta title={<>Consultez l&apos;offre <span className="it">actuelle</span>.</>} sub="L'accès public est actuellement à 0 € et sans carte bancaire." />
    </>
  );
}

function TarifsNL() {
  return (
    <>
      <ContentHero
        eyebrow="Tarieven"
        title={<>Huidige publieke toegang. <span className="it">0 €.</span></>}
        intro="De huidige publieke versie vraagt geen betaling of bankkaart. Deze pagina blijft de referentie als het aanbod verandert."
        breadcrumb={[{ name: "Tarieven", path: "/tarifs" }]}
      />
      <Plan
        tag="Huidig publiek aanbod"
        price={<>0€ <small>/ vandaag · zonder bankkaart</small></>}
        lede="Heel FILON. Beschrijf een behoefte, bekijk geïndexeerde aanbiedingen en raadpleeg het oordeel wanneer de beschikbare gegevens dit toelaten."
        items={INCLUS_NL}
        chromeLabel="Ontdek de extensie"
      />
      <p style={{ textAlign: "center", color: "var(--ink-3)", fontSize: 13.5, marginTop: -20 }}>
        Het commissietarief telt niet mee in de huidige score. Bevestig prijs, kosten en totaal bij de winkel.
      </p>
      <ProseBlock heading={<>Een expliciet huidig <span className="it">tarief</span>.</>} alt>
        <p>
          De huidige publieke toegang kost 0 €. Een toekomstige wijziging moet op deze pagina en in de toepasselijke voorwaarden worden gepubliceerd.
        </p>
        <p>
          Sommige links kunnen een commissie opleveren. Die commissie is geen dimensie van de huidige score.
        </p>
      </ProseBlock>
      <FaqBlock items={FAQ_NL} eyebrow="Tarieven · FAQ" title="Wat « gratis » echt betekent." />
      <ClosingCta title={<>Bekijk het huidige <span className="it">aanbod</span>.</>} sub="De publieke toegang kost momenteel 0 € en vraagt geen bankkaart." />
    </>
  );
}

function TarifsEN() {
  return (
    <>
      <ContentHero
        eyebrow="Pricing"
        title={<>Current public access. <span className="it">€0.</span></>}
        intro="The current public version requires no payment or card. This page remains the reference if the offering changes."
        breadcrumb={[{ name: "Pricing", path: "/tarifs" }]}
      />
      <Plan
        tag="Current public offering"
        price={<>€0 <small>/ today · no payment card</small></>}
        lede="All of FILON. Describe a need, browse indexed offers and consult the verdict when the available data supports it."
        items={INCLUS_EN}
        chromeLabel="Discover the extension"
      />
      <p style={{ textAlign: "center", color: "var(--ink-3)", fontSize: 13.5, marginTop: -20 }}>
        Commission rate is not part of the current score. Confirm price, fees and total with the merchant.
      </p>
      <ProseBlock heading={<>An explicit current <span className="it">price</span>.</>} alt>
        <p>
          Current public access costs €0. A future change must be published on this page and in the applicable terms.
        </p>
        <p>
          Some links may generate a commission. That commission is not a dimension of the current score.
        </p>
      </ProseBlock>
      <FaqBlock items={FAQ_EN} eyebrow="Pricing · FAQ" title="What « free » really means." />
      <ClosingCta title={<>See the current <span className="it">offering</span>.</>} sub="Public access currently costs €0 and requires no payment card." />
    </>
  );
}

export default function TarifsPage() {
  return <Localized fr={<TarifsFR />} nl={<TarifsNL />} en={<TarifsEN />} />;
}
