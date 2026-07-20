"use client";

import { useEffect, useRef } from "react";
import dynamic from "next/dynamic";

const IntelligenceCore = dynamic(
  () => import("./IntelligenceCore").then((m) => m.IntelligenceCore),
  { ssr: false, loading: () => <div className="ed-core core-fallback" aria-hidden="true" /> }
);

export function EditorialHero() {
  const heroRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const hero = heroRef.current;
    if (!hero) return;
    requestAnimationFrame(() => hero.classList.add("in"));
  }, []);

  return (
    <section className="ed-hero" ref={heroRef}>
      <div className="ed-wrap ed-hero-grid">
        <div className="ed-hero-text">
          <span className="eyebrow ed-hero-eyebrow">
            <span className="dot" /> Copilote d&apos;achat propulsé par l&apos;IA
          </span>
          <h1 className="ed-h1" aria-label="Est-ce vraiment le bon prix ?">
            <span className="l"><span>Est-ce</span></span>
            <span className="l"><span className="it">vraiment</span></span>
            <span className="l"><span className="wave-text">le bon prix&nbsp;?</span></span>
          </h1>
          <p className="ed-hero-sub">
            Décrivez ce que vous cherchez. FILON vous dit quoi acheter, et quand.
          </p>
          <div className="ed-hero-actions">
            <a className="ed-btn dark" href="/recherche">Essayer le copilote</a>
            <a className="ed-btn ghost" href="/#installer">Ajouter — gratuit</a>
          </div>
        </div>

        <div className="ed-hero-visual">
          <div className="ed-core-wrap" aria-hidden="true">
            <div className="ed-core-glow" />
            <IntelligenceCore className="ed-core" />
          </div>
        </div>
      </div>

      <a href="#transform" className="ed-scrollcue" aria-label="Défiler">
        <span className="ln" />
        <span className="tx">Découvrir</span>
      </a>
    </section>
  );
}
