"use client";

import { Reveal } from "./Reveal";
import { useLocale } from "@/lib/i18n";

const STEP_ICONS = [
  // Reconnaît le produit — cadre de scan
  <svg key="i" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M4 8V5.5A1.5 1.5 0 0 1 5.5 4H8" />
    <path d="M16 4h2.5A1.5 1.5 0 0 1 20 5.5V8" />
    <path d="M20 16v2.5a1.5 1.5 0 0 1-1.5 1.5H16" />
    <path d="M8 20H5.5A1.5 1.5 0 0 1 4 18.5V16" />
    <rect x="9" y="9" width="6" height="6" rx="1.4" />
  </svg>,
  // Regarde partout — globe
  <svg key="ii" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <circle cx="12" cy="12" r="8.2" />
    <path d="M12 3.8v16.4M3.8 12h16.4" />
    <ellipse cx="12" cy="12" rx="4" ry="8.2" />
  </svg>,
  // Tranche — verdict validé
  <svg key="iii" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <circle cx="12" cy="12" r="8.2" />
    <path d="M8.5 12.2 11 14.7 15.7 9.6" />
  </svg>,
];

const L = {
  fr: {
    mIdx: "3 étapes",
    mH1: "Une réponse, en ", mH2: "trois gestes",
    steps: [
      ["Il repère le produit", "Sur une page prise en charge, il extrait les informations disponibles."],
      ["Il compare son index", "Il rapproche les offres comparables présentes dans le catalogue FILON."],
      ["Il explique", "Prix observé, périmètre et inconnues : FILON s'abstient si la preuve manque."],
    ],
    tEye: "Notre principe",
    tH1: "De votre côté. ", tH2: "Uniquement.",
    tP1: "Le score actuel utilise les prix observés, l'historique disponible, le stock, la fraîcheur et le périmètre de comparaison. Une commission n'entre pas dans ce calcul.",
    tP2: "La confiance ne se déclare pas. Elle se prouve, à chaque conseil.",
    pledge: [
      ["01", "Un calcul documenté.", "La commission n'est pas une entrée du score de décision actuel."],
      ["02", "Sources visibles.", "Chaque offre conserve le marchand dont elle provient."],
      ["03", "Confidentialité documentée.", "La politique de confidentialité décrit les données traitées et vos droits."],
      ["04", "Accès actuel gratuit.", "La version publique actuelle ne demande ni paiement ni carte bancaire."],
    ],
    cEye: "Comparez avant de payer",
    cH1: "Demandez à FILON ", cH2: "avant d'acheter.",
  },
  nl: {
    mIdx: "3 stappen",
    mH1: "Eén antwoord, in ", mH2: "drie stappen",
    steps: [
      ["Hij herkent het product", "Op een ondersteunde pagina leest hij de beschikbare productinformatie."],
      ["Hij vergelijkt zijn index", "Hij vergelijkt soortgelijke aanbiedingen in de FILON-catalogus."],
      ["Hij legt uit", "Bekeken prijs, bereik en onbekenden: FILON onthoudt zich als bewijs ontbreekt."],
    ],
    tEye: "Ons principe",
    tH1: "Aan jouw kant. ", tH2: "Enkel dat.",
    tP1: "De huidige score gebruikt bekeken prijzen, beschikbare historiek, voorraad, actualiteit en vergelijkingsbereik. Een commissie telt niet mee in die berekening.",
    tP2: "Vertrouwen verklaar je niet. Je bewijst het, bij elk advies.",
    pledge: [
      ["01", "Een gedocumenteerde berekening.", "Commissie is geen invoer voor de huidige beslissingsscore."],
      ["02", "Zichtbare bronnen.", "Elke aanbieding behoudt de winkel waar ze vandaan komt."],
      ["03", "Privacy gedocumenteerd.", "Het privacybeleid beschrijft verwerkte gegevens en je rechten."],
      ["04", "Huidige toegang gratis.", "De huidige publieke versie vraagt geen betaling of bankkaart."],
    ],
    cEye: "Vergelijk voordat je betaalt",
    cH1: "Vraag het aan FILON ", cH2: "voordat je koopt.",
  },
  en: {
    mIdx: "3 steps",
    mH1: "One answer, in ", mH2: "three moves",
    steps: [
      ["It identifies the product", "On a supported page, it reads the available product information."],
      ["It compares its index", "It compares matching offers present in the FILON catalogue."],
      ["It explains", "Observed price, scope and unknowns: FILON abstains when evidence is missing."],
    ],
    tEye: "Our principle",
    tH1: "On your side. ", tH2: "Only.",
    tP1: "The current score uses observed prices, available history, stock, freshness and comparison scope. Commission is not an input to that calculation.",
    tP2: "Trust isn't declared. It's proven, with every recommendation.",
    pledge: [
      ["01", "A documented calculation.", "Commission is not an input to the current decision score."],
      ["02", "Visible sources.", "Each offer retains the merchant it came from."],
      ["03", "Privacy documented.", "The privacy policy describes processed data and your rights."],
      ["04", "Current access is free.", "The current public version requires no payment or card."],
    ],
    cEye: "Compare before you pay",
    cH1: "Ask FILON ", cH2: "before you buy.",
  },
};

export function Method() {
  const { locale } = useLocale();
  const x = L[locale];
  return (
    <section className="ed-band" id="comment">
      <div className="ed-wrap">
        <Reveal>
          <div className="ed-lead">
            <span className="idx">{x.mIdx}</span>
            <h2>
              {x.mH1}<span className="it">{x.mH2}</span>.
            </h2>
          </div>
        </Reveal>
        <div className="ed-steps">
          {x.steps.map(([h, p], i) => (
            <Reveal className="ed-step" key={h} style={{ transitionDelay: `${i * 90}ms` }}>
              <span className="ed-step-ico">{STEP_ICONS[i]}</span>
              <h3>{h}</h3>
              <p>{p}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

export function Transparency() {
  const { locale } = useLocale();
  const x = L[locale];
  return (
    <section className="ed-band alt" id="transparence">
      <div className="ed-wrap">
        <div className="ed-mgrid">
          <Reveal className="ed-manifesto">
            <span className="eyebrow" style={{ display: "block", marginBottom: 24 }}>{x.tEye}</span>
            <h2>
              {x.tH1}<span className="it">{x.tH2}</span>
            </h2>
          </Reveal>
          <Reveal className="ed-mbody">
            <p>{x.tP1}</p>
            <p>{x.tP2}</p>
            <div className="ed-pledge">
              {x.pledge.map(([n, b, t]) => (
                <div key={n}>
                  <span>{n}</span>
                  <p><b>{b}</b> {t}</p>
                </div>
              ))}
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}

export function Closing() {
  const { locale, t } = useLocale();
  const x = L[locale];
  return (
    <section className="ed-closing" id="installer">
      <div className="ed-wrap">
        <Reveal>
          <span className="eyebrow" style={{ display: "block", marginBottom: 26 }}>{x.cEye}</span>
          <h2>
            {x.cH1}<span className="it">{x.cH2}</span>
          </h2>
          <a className="ed-btn dark" href="/recherche" style={{ marginTop: "clamp(34px,5vw,50px)" }}>
            {t("cta.try")}
          </a>
        </Reveal>
      </div>
    </section>
  );
}
