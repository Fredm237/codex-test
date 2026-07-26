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
    mH1: "Trois secondes entre vous et ", mH2: "le meilleur prix",
    steps: [
      ["Il reconnaît le produit", "Sur n'importe quelle page, il comprend ce que vous regardez."],
      ["Il regarde partout", "En une seconde, tout le marché passé au crible."],
      ["Il tranche", "Un chiffre : votre vrai prix. Une réponse : acheter, ou attendre."],
    ],
    tEye: "Notre principe",
    tH1: "De votre côté. ", tH2: "Uniquement.",
    tP1: "FILON travaille pour vous, pas pour une marque. Ce qu'il vous montre, c'est ce qui est vraiment le mieux pour vous. Rien d'autre n'entre en jeu.",
    tP2: "La confiance ne se déclare pas. Elle se prouve, à chaque conseil.",
    pledge: [
      ["01", "De votre côté.", "Aucune marque ne peut acheter sa place dans un conseil FILON."],
      ["02", "Sans publicité.", "Rien ne vient troubler la réponse que vous recevez."],
      ["03", "Vos données restent les vôtres.", "Pas de profil publicitaire, pas de revente. RGPD par défaut."],
      ["04", "Gratuit, pour de vrai.", "Aucune carte, aucun abonnement. Vous ne payez jamais."],
    ],
    cEye: "Ne payez plus jamais trop cher",
    cH1: "Demandez à FILON ", cH2: "avant d'acheter.",
  },
  nl: {
    mIdx: "3 stappen",
    mH1: "Drie seconden tussen jou en ", mH2: "de beste prijs",
    steps: [
      ["Hij herkent het product", "Op elke pagina begrijpt hij wat je bekijkt."],
      ["Hij kijkt overal", "In één seconde de hele markt doorzocht."],
      ["Hij beslist", "Eén cijfer: je echte prijs. Eén antwoord: kopen of wachten."],
    ],
    tEye: "Ons principe",
    tH1: "Aan jouw kant. ", tH2: "Enkel dat.",
    tP1: "FILON werkt voor jou, niet voor een merk. Wat hij je toont, is wat echt het beste is voor jou. Niets anders speelt mee.",
    tP2: "Vertrouwen verklaar je niet. Je bewijst het, bij elk advies.",
    pledge: [
      ["01", "Aan jouw kant.", "Geen enkel merk kan zijn plaats kopen in een FILON-advies."],
      ["02", "Zonder reclame.", "Niets verstoort het antwoord dat je krijgt."],
      ["03", "Je gegevens blijven van jou.", "Geen advertentieprofiel, geen doorverkoop. AVG standaard."],
      ["04", "Echt gratis.", "Geen kaart, geen abonnement. Je betaalt nooit."],
    ],
    cEye: "Betaal nooit meer te veel",
    cH1: "Vraag het aan FILON ", cH2: "voordat je koopt.",
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
