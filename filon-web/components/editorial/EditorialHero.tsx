"use client";

import { useEffect, useRef } from "react";
import dynamic from "next/dynamic";

const IntelligenceCore = dynamic(
  () => import("./IntelligenceCore").then((m) => m.IntelligenceCore),
  { ssr: false, loading: () => <div className="ed-core core-fallback" aria-hidden="true" /> }
);

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

    // pointer parallax on the floating verdict card
    const card = hero.querySelector<HTMLElement>(".ed-verdict");
    let rafP = 0;
    const onMove = (e: PointerEvent) => {
      if (reduce || window.innerWidth < 860) return;
      cancelAnimationFrame(rafP);
      rafP = requestAnimationFrame(() => {
        const cx = (e.clientX / window.innerWidth - 0.5) * 2;
        const cy = (e.clientY / window.innerHeight - 0.5) * 2;
        if (card) card.style.transform = `perspective(1000px) rotateY(${cx * 4}deg) rotateX(${-cy * 4}deg) translateY(var(--float,0px))`;
      });
    };
    window.addEventListener("pointermove", onMove, { passive: true });

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

    return () => {
      cio.disconnect();
      window.removeEventListener("pointermove", onMove);
      cancelAnimationFrame(rafP);
    };
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
          <div className="ed-verdict glass">
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
            </div>
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
