"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { MagneticButton } from "./MagneticButton";
import { Counter } from "./Counter";

const LINES = ["Ne payez plus", "jamais le", "prix fort."];

export function ImmersiveHero() {
  const root = useRef<HTMLElement>(null);

  useEffect(() => {
    const el = root.current;
    if (!el) return;
    const spans = el.querySelectorAll<HTMLElement>(".fx-line > span");
    const rest = el.querySelectorAll<HTMLElement>(".fx-hero-sub, .fx-hero-cta, .fx-hero-stats");

    // The CSS initial state is `transform: translateY(105%)`, which GSAP reads
    // as a `y` px offset (not yPercent) — so we animate `y` to 0 to reveal.
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      gsap.set(spans, { y: 0 });
      return;
    }

    gsap.to(spans, { y: 0, duration: 1, ease: "power4.out", stagger: 0.08, delay: 0.2, overwrite: "auto" });
    gsap.from(rest, { opacity: 0, y: 20, duration: 0.9, stagger: 0.15, delay: 0.55, ease: "power3.out", overwrite: "auto" });
  }, []);

  return (
    <section className="fx-hero wrap" ref={root}>
      <span className="fx-tagpill">
        <span className="fx-b">2026</span> L&apos;assistant qui trouve le filon avant chaque achat
      </span>
      <h1 className="fx-h1" aria-label="Ne payez plus jamais le prix fort.">
        {LINES.map((line, i) => (
          <span className="fx-line" key={i}>
            <span className={i === LINES.length - 1 ? "gradient-text" : undefined}>{line}</span>
          </span>
        ))}
      </h1>
      <p className="fx-hero-sub">
        FILON compare en une seconde le meilleur cashback, le reconditionné équivalent et les codes promo qui
        marchent — puis vous révèle votre prix réel. Silencieux. Transparent. Redoutable.
      </p>
      <div className="fx-hero-cta">
        <MagneticButton href="#final" className="fx-btn fx-solid fx-big">
          Ajouter à mon navigateur
        </MagneticButton>
        <a className="fx-btn fx-line-btn fx-big" data-hover href="#story">
          Voir le principe
        </a>
      </div>
      <div className="fx-hero-stats">
        <div className="fx-hstat">
          <div className="fx-n mono">
            <Counter to={12} suffix=" M+" />
          </div>
          <div className="fx-l">utilisateurs cashback en francophonie</div>
        </div>
        <div className="fx-hstat">
          <div className="fx-n mono">200–450 €</div>
          <div className="fx-l">économisés par foyer, chaque année</div>
        </div>
        <div className="fx-hstat">
          <div className="fx-n mono">
            <Counter to={50} suffix=" %" />
          </div>
          <div className="fx-l">d&apos;économie en cumulant reconditionné + cashback</div>
        </div>
      </div>
    </section>
  );
}
