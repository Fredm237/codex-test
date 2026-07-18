"use client";

import { useEffect, useRef } from "react";
import { LiquidMetal } from "./LiquidMetal";

function animateNumber(el: HTMLElement) {
  const to = parseFloat(el.getAttribute("data-to") || "0");
  const suf = el.getAttribute("data-suffix") || "";
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    el.textContent = `${to}${suf}`;
    return;
  }
  const t0 = performance.now();
  const d = 1100;
  const tick = (n: number) => {
    const p = Math.min((n - t0) / d, 1);
    const e = 1 - Math.pow(1 - p, 3);
    el.textContent = `${Math.round(to * e)}${suf}`;
    if (p < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

export function EditorialHero() {
  const heroRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const hero = heroRef.current;
    if (!hero) return;
    requestAnimationFrame(() => hero.classList.add("in"));

    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    // count-ups
    const cio = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            animateNumber(e.target as HTMLElement);
            cio.unobserve(e.target);
          }
        });
      },
      { threshold: 0.6 }
    );
    hero.querySelectorAll<HTMLElement>("[data-to]").forEach((el) => cio.observe(el));

    // verdict choreography
    const vc = hero.querySelector(".ed-verdict");
    if (vc) {
      const vio = new IntersectionObserver(
        (entries) => {
          entries.forEach((e) => {
            if (!e.isIntersecting) return;
            vio.disconnect();
            const rows = vc.querySelectorAll(".ed-vrow");
            const ans = vc.querySelector(".ed-verdict-answer");
            if (reduce) {
              rows.forEach((r) => r.classList.add("show"));
              ans?.classList.add("show");
              return;
            }
            rows.forEach((r, i) => setTimeout(() => r.classList.add("show"), 250 + i * 180));
            setTimeout(() => ans?.classList.add("show"), 250 + rows.length * 180 + 150);
          });
        },
        { threshold: 0.35 }
      );
      vio.observe(vc);
    }

    return () => cio.disconnect();
  }, []);

  return (
    <section className="ed-hero" ref={heroRef}>
      <LiquidMetal className="ed-coin" />
      <div className="ed-wrap inner">
        <span className="eyebrow" style={{ display: "block", marginBottom: "clamp(24px,4vw,40px)" }}>
          L&apos;assistant d&apos;achat malin
        </span>
        <h1 className="ed-h1" aria-label="Est-ce vraiment le bon prix ?">
          <span className="l"><span>Est-ce</span></span>
          <span className="l"><span className="it">vraiment</span></span>
          <span className="l"><span className="wave-text">le bon prix&nbsp;?</span></span>
        </h1>
        <div className="ed-hero-foot">
          <div>
            <p className="ed-hero-sub">
              Avant chaque achat, FILON compare le meilleur cashback, le reconditionné équivalent et les codes promo —
              puis vous dit, en une seconde, <b>s&apos;il existe mieux</b>. Ne payez plus jamais trop cher.
            </p>
            <div className="ed-hero-actions">
              <a className="ed-btn dark" href="/#installer">Ajouter FILON — gratuit</a>
              <span className="ed-cap">Extension &amp; app · données non revendues</span>
            </div>
          </div>

          <div className="ed-verdict">
            <div className="ed-verdict-top">
              <span className="q">« Faut-il l&apos;acheter&nbsp;? »</span>
              <span>Casque Aura X1</span>
            </div>
            <div className="ed-verdict-body">
              <div className="ed-vrow">
                <span className="who"><b>Prix neuf affiché</b>vendu par la boutique</span>
                <span className="amt old">499 €</span>
              </div>
              <div className="ed-vrow">
                <span className="who"><b>Reconditionné A+</b>garanti 24 mois · Back Market</span>
                <span className="amt new" data-to="405" data-suffix=" €">—</span>
              </div>
              <div className="ed-vrow">
                <span className="who"><b>Cashback + code</b>iGraal · code vérifié en direct</span>
                <span className="amt new">−40 €</span>
              </div>
              <div className="ed-verdict-answer">
                <span className="label">Votre prix réel</span>
                <span className="val">
                  <span className="mono" data-to="365">—</span> €<small>−134 € · le filon</small>
                </span>
              </div>
              <p className="ed-verdict-note">
                Lien affilié · FILON perçoit une part de la commission d&apos;apport de la plateforme. Jamais un centime de votre poche.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
