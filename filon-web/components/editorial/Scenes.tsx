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
    netEye: "En temps réel",
    netH1: "Pendant que vous hésitez,", netH2: "FILON a déjà comparé.",
    netSub: "Il regarde partout, à votre place. Vous n'avez plus qu'à dire oui.",
    graphEye: "L'intelligence",
    graphH1: "Il ne compare pas des prix.", graphH2: "Il comprend les produits.",
    graphSub: "Ce qu'un produit vaut vraiment, et combien de temps il durera. Il l'apprend à chaque achat.",
    graphCta: "En savoir plus",
    finalEye: "Ne payez plus jamais trop cher",
    finalH1: "Demandez à FILON ", finalH2: "avant d'acheter",
    finalNote: "Gratuit, pour toujours. Sans carte bancaire. Vos données restent chez vous.",
  },
  nl: {
    netEye: "In realtime",
    netH1: "Terwijl jij twijfelt,", netH2: "heeft FILON al vergeleken.",
    netSub: "Hij kijkt overal, in jouw plaats. Jij hoeft alleen ja te zeggen.",
    graphEye: "De intelligentie",
    graphH1: "Hij vergelijkt geen prijzen.", graphH2: "Hij begrijpt producten.",
    graphSub: "Wat een product echt waard is, en hoelang het meegaat. Hij leert het bij elke aankoop.",
    graphCta: "Meer weten",
    finalEye: "Betaal nooit meer te veel",
    finalH1: "Vraag het aan FILON ", finalH2: "voordat je koopt",
    finalNote: "Gratis, voor altijd. Geen bankkaart. Je gegevens blijven van jou.",
  },
  en: {
    netEye: "In real time",
    netH1: "While you hesitate,", netH2: "FILON has already compared.",
    netSub: "It looks everywhere, for you. All you have to do is say yes.",
    graphEye: "The intelligence",
    graphH1: "It doesn't compare prices.", graphH2: "It understands products.",
    graphSub: "What a product is really worth, and how long it will last. It learns with every purchase.",
    graphCta: "Learn more",
    finalEye: "Never overpay again",
    finalH1: "Ask FILON ", finalH2: "before you buy",
    finalNote: "Free, forever. No credit card. Your data stays yours.",
  },
};

/** Scene — the AI comparing the whole market in real time. */
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
