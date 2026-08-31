"use client";

import dynamic from "next/dynamic";
import { Reveal } from "./Reveal";
import { ChromeCta } from "./ChromeCta";
import { useLocale } from "@/lib/i18n";

const NeuralNetwork = dynamic(() => import("./NeuralNetwork").then((m) => m.NeuralNetwork), {
  ssr: false,
  loading: () => <div className="ed-net" aria-hidden="true" />,
});

const L = {
  fr: {
    netEye: "Dans le catalogue",
    netH1: "Pendant que vous hésitez,", netH2: "FILON compare son index.",
    netSub: "Il montre le périmètre observé et laisse les inconnues visibles.",
    graphEye: "L'intelligence",
    graphH1: "Il ne résume pas la preuve à un prix.", graphH2: "Il relie les signaux disponibles.",
    graphSub: "Prix observé, historique disponible, stock et fraîcheur : chaque signal garde sa source et sa limite.",
    graphCta: "En savoir plus",
    finalEye: "Comparez avant de payer",
    finalH1: "Demandez à FILON ", finalH2: "avant d'acheter",
    finalNote: "Gratuit dans la version actuelle. Sans carte bancaire. Consultez la politique de confidentialité pour le traitement des données.",
  },
  nl: {
    netEye: "In de catalogus",
    netH1: "Terwijl jij twijfelt,", netH2: "vergelijkt FILON zijn index.",
    netSub: "Hij toont het bekeken bereik en laat onbekenden zichtbaar.",
    graphEye: "De intelligentie",
    graphH1: "Hij beperkt bewijs niet tot een prijs.", graphH2: "Hij verbindt beschikbare signalen.",
    graphSub: "Bekeken prijs, beschikbare historiek, voorraad en actualiteit: elk signaal behoudt bron en grens.",
    graphCta: "Meer weten",
    finalEye: "Vergelijk voordat je betaalt",
    finalH1: "Vraag het aan FILON ", finalH2: "voordat je koopt",
    finalNote: "Gratis in de huidige versie. Geen bankkaart. Raadpleeg het privacybeleid voor de gegevensverwerking.",
  },
  en: {
    netEye: "In the catalogue",
    netH1: "While you hesitate,", netH2: "FILON compares its index.",
    netSub: "It shows the observed scope and keeps unknowns visible.",
    graphEye: "The intelligence",
    graphH1: "It does not reduce evidence to a price.", graphH2: "It connects available signals.",
    graphSub: "Observed price, available history, stock and freshness: each signal keeps its source and limit.",
    graphCta: "Learn more",
    finalEye: "Compare before you pay",
    finalH1: "Ask FILON ", finalH2: "before you buy",
    finalNote: "Free in the current version. No credit card. See the privacy policy for data processing details.",
  },
};

/** Scene — comparaison du périmètre actuellement indexé. */
export function NetworkScene() {
  const { locale } = useLocale();
  const x = L[locale];
  return (
    <section className="ed-scene dark" id="reseau">
      <div className="ed-wrap ed-scene-grid">
        <div className="ed-scene-inner">
          <Reveal>
            <span className="eyebrow">{x.netEye}</span>
            <h2>
              {x.netH1}<br />
              <span className="it">{x.netH2}</span>
            </h2>
            <p className="ed-scene-sub">{x.netSub}</p>
          </Reveal>
        </div>
        <div className="ed-net-cell">
          <NeuralNetwork variant="merchants" className="ed-net" />
        </div>
      </div>
    </section>
  );
}

/** Scene — the proprietary knowledge that keeps learning. */
export function GraphScene() {
  const { locale } = useLocale();
  const x = L[locale];
  return (
    <section className="ed-scene dark flip" id="graph-scene">
      <div className="ed-wrap ed-scene-grid">
        <div className="ed-net-cell">
          <NeuralNetwork variant="graph" className="ed-net" />
        </div>
        <div className="ed-scene-inner">
          <Reveal>
            <span className="eyebrow">{x.graphEye}</span>
            <h2>
              {x.graphH1}<br />
              <span className="it">{x.graphH2}</span>
            </h2>
            <p className="ed-scene-sub">{x.graphSub}</p>
            <a className="ed-btn ghostlight" href="/intelligence">{x.graphCta}</a>
          </Reveal>
        </div>
      </div>
    </section>
  );
}

/** Final immersive CTA. */
export function ClosingScene() {
  const { locale, t } = useLocale();
  const x = L[locale];
  return (
    <section className="ed-final dark" id="installer">
      <div className="ed-final-glow" aria-hidden="true" />
      <div className="ed-wrap ed-final-inner">
        <Reveal>
          <span className="eyebrow">{x.finalEye}</span>
          <h2>
            {x.finalH1}<span className="it">{x.finalH2}</span>.
          </h2>
          <div className="ed-final-actions">
            <a className="ed-btn wave" href="/recherche">{t("cta.try")}</a>
            <ChromeCta variant="ghostlight" label={t("cta.chrome")} />
          </div>
          <p className="ed-final-note">{x.finalNote}</p>
        </Reveal>
      </div>
    </section>
  );
}
