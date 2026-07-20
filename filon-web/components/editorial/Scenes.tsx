"use client";

import dynamic from "next/dynamic";
import { Reveal } from "./Reveal";

const NeuralNetwork = dynamic(() => import("./NeuralNetwork").then((m) => m.NeuralNetwork), {
  ssr: false,
  loading: () => <div className="ed-net" aria-hidden="true" />,
});

/** Scene — the AI comparing the whole market in real time. */
export function NetworkScene() {
  return (
    <section className="ed-scene dark" id="reseau">
      <div className="ed-wrap ed-scene-grid">
        <div className="ed-scene-inner">
          <Reveal>
            <span className="eyebrow">En temps réel</span>
            <h2>
              Pendant que vous hésitez,<br />
              <span className="it">FILON a déjà comparé.</span>
            </h2>
            <p className="ed-scene-sub">Il regarde partout, à votre place. Vous n&apos;avez plus qu&apos;à dire oui.</p>
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
  return (
    <section className="ed-scene dark flip" id="graph-scene">
      <div className="ed-wrap ed-scene-grid">
        <div className="ed-net-cell">
          <NeuralNetwork variant="graph" className="ed-net" />
        </div>
        <div className="ed-scene-inner">
          <Reveal>
            <span className="eyebrow">L&apos;intelligence</span>
            <h2>
              Il ne compare pas des prix.<br />
              <span className="it">Il comprend les produits.</span>
            </h2>
            <p className="ed-scene-sub">Ce qu&apos;un produit vaut vraiment, et combien de temps il durera. Il l&apos;apprend à chaque achat.</p>
            <a className="ed-btn ghostlight" href="/intelligence">Voir l&apos;Intelligence Graph</a>
          </Reveal>
        </div>
      </div>
    </section>
  );
}

/** Final immersive CTA. */
export function ClosingScene() {
  return (
    <section className="ed-final dark" id="installer">
      <div className="ed-final-glow" aria-hidden="true" />
      <div className="ed-wrap ed-final-inner">
        <Reveal>
          <span className="eyebrow">Ne payez plus jamais trop cher</span>
          <h2>
            Demandez à FILON <span className="it">avant d&apos;acheter</span>.
          </h2>
          <div className="ed-final-actions">
            <a className="ed-btn wave" href="/recherche">Essayer le copilote</a>
            <a className="ed-btn ghostlight" href="/#top">Ajouter gratuitement</a>
          </div>
          <p className="ed-final-note">Gratuit, pour toujours. Sans carte bancaire. Vos données restent chez vous.</p>
        </Reveal>
      </div>
    </section>
  );
}
