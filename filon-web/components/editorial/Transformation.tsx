"use client";

import { useEffect, useRef } from "react";
import { useLocale } from "@/lib/i18n";

// Discount sources orbit the LOWER half of the orb (never near the title) and
// get absorbed as you scroll. No amount is simulated: each condition remains
// qualitative until a real offer documents it.
const CHIPS = [
  { id: "cashback", v: "si documenté", ang: 22, r: 1.0, tIn: 0.18, tSpan: 0.16 },
  { id: "promo", v: "si applicable", ang: 90, r: 1.12, tIn: 0.4, tSpan: 0.16 },
  { id: "refurb", v: "offre distincte", ang: 158, r: 1.0, tIn: 0.62, tSpan: 0.16 },
];

const L = {
  fr: {
    eye: "Une offre. Plusieurs conditions.",
    h1: "Le prix affiché n'est pas toujours le ", h2: "total", h3: " connu.",
    start: "Prix observé", end: "Total à confirmer",
    cap: "livraison · promotion · éligibilité",
    labels: { cashback: "Cashback", promo: "Code promo", refurb: "Reconditionné" } as Record<string, string>,
  },
  nl: {
    eye: "Eén aanbieding. Meerdere voorwaarden.",
    h1: "De getoonde prijs is niet altijd het bekende ", h2: "totaal", h3: ".",
    start: "Bekeken prijs", end: "Totaal te bevestigen",
    cap: "levering · promotie · geschiktheid",
    labels: { cashback: "Cashback", promo: "Kortingscode", refurb: "Refurbished" } as Record<string, string>,
  },
  en: {
    eye: "One offer. Several conditions.",
    h1: "The listed price is not always the known ", h2: "total", h3: ".",
    start: "Observed price", end: "Total to confirm",
    cap: "shipping · promotion · eligibility",
    labels: { cashback: "Cashback", promo: "Promo code", refurb: "Refurbished" } as Record<string, string>,
  },
};

const easeInOut = (t: number) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
const clamp01 = (v: number) => Math.max(0, Math.min(1, v));

export function Transformation() {
  const { locale } = useLocale();
  const x = L[locale];
  const secRef = useRef<HTMLElement>(null);
  const priceRef = useRef<HTMLSpanElement>(null);
  const coreRef = useRef<HTMLDivElement>(null);
  const capRef = useRef<HTMLSpanElement>(null);
  const chipRefs = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    const sec = secRef.current;
    if (!sec) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    // orbit radius keyed to the orb's on-screen size, so chips sit just outside it
    const orbRadius = () => Math.min(460, Math.min(window.innerWidth, window.innerHeight) * 0.5) * 0.5;

    const apply = (prog: number) => {
      const p = clamp01(prog);
      if (priceRef.current) {
        priceRef.current.textContent = p < 0.86 ? x.start : x.end;
      }
      if (coreRef.current) {
        coreRef.current.style.setProperty("--glow", `${0.4 + p * 0.6}`);
        coreRef.current.style.setProperty("--coreScale", `${1 + p * 0.14}`);
      }
      const R = orbRadius() * 1.18;
      CHIPS.forEach((c, i) => {
        const el = chipRefs.current[i];
        if (!el) return;
        const t = easeInOut(clamp01((p - c.tIn) / c.tSpan));
        const ang = ((c.ang + p * 30) * Math.PI) / 180;
        const rad = R * c.r * (1 - t);
        const x = Math.cos(ang) * rad;
        const y = Math.sin(ang) * rad;
        el.style.transform = `translate(-50%,-50%) translate(${x}px,${y}px) scale(${1 - 0.55 * t})`;
        el.style.opacity = `${1 - 0.9 * t}`;
        el.classList.toggle("absorbed", t > 0.02 && t < 0.98);
      });
      if (capRef.current) capRef.current.style.opacity = `${clamp01((p - 0.86) / 0.12)}`;
    };

    if (reduce) {
      apply(1);
      return;
    }
    let raf = 0;
    const onScroll = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const rect = sec.getBoundingClientRect();
        const h = sec.offsetHeight - window.innerHeight;
        apply(-rect.top / h);
      });
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });
    onScroll();
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      cancelAnimationFrame(raf);
    };
  }, [x.end, x.start]);

  return (
    <section className="ed-gravity" id="transform" ref={secRef}>
      <div className="pin">
        <div className="ed-grav-head">
          <span className="eyebrow">{x.eye}</span>
          <h2>
            {x.h1}<span className="it">{x.h2}</span>{x.h3}
          </h2>
        </div>

        <div className="ed-grav-stage" aria-hidden="true">
          <div className="core" ref={coreRef}>
            <span className="price mono" ref={priceRef}>{x.start}</span>
            <span className="cap" ref={capRef}>{x.cap}</span>
          </div>
          {CHIPS.map((c, i) => (
            <div
              className="ed-grav-chip"
              key={c.id}
              ref={(el) => {
                chipRefs.current[i] = el;
              }}
            >
              <span className="l">{x.labels[c.id]}</span>
              <b>{c.v}</b>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
