"use client";

import { useEffect, useRef } from "react";

const FROM = 499;
const TO = 365;

// Discount sources that orbit the core and get absorbed as you scroll.
const CHIPS = [
  { label: "Cashback", v: "−6,5 %", ang: -60, r: 1.0, tIn: 0.18, tSpan: 0.16 },
  { label: "Reconditionné", v: "−94 €", ang: 70, r: 1.12, tIn: 0.4, tSpan: 0.16 },
  { label: "Code promo", v: "−15 €", ang: 190, r: 0.9, tIn: 0.62, tSpan: 0.16 },
];

const easeInOut = (t: number) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
const clamp01 = (v: number) => Math.max(0, Math.min(1, v));

export function Transformation() {
  const secRef = useRef<HTMLElement>(null);
  const priceRef = useRef<HTMLSpanElement>(null);
  const coreRef = useRef<HTMLDivElement>(null);
  const finalRef = useRef<HTMLDivElement>(null);
  const chipRefs = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    const sec = secRef.current;
    if (!sec) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const R = () => Math.min(window.innerWidth, window.innerHeight) * 0.28;

    const apply = (prog: number) => {
      const p = clamp01(prog);
      const val = Math.round(FROM - (FROM - TO) * easeInOut(p));
      if (priceRef.current) priceRef.current.textContent = `${val} €`;
      if (coreRef.current) {
        coreRef.current.style.setProperty("--glow", `${0.4 + p * 0.6}`);
        coreRef.current.style.setProperty("--coreScale", `${1 + p * 0.22}`);
      }
      const radius = R();
      CHIPS.forEach((c, i) => {
        const el = chipRefs.current[i];
        if (!el) return;
        const t = easeInOut(clamp01((p - c.tIn) / c.tSpan));
        const ang = ((c.ang + p * 42) * Math.PI) / 180;
        const rad = radius * c.r * (1 - t);
        const x = Math.cos(ang) * rad;
        const y = Math.sin(ang) * rad;
        el.style.transform = `translate(-50%,-50%) translate(${x}px,${y}px) scale(${1 - 0.55 * t})`;
        el.style.opacity = `${1 - 0.9 * t}`;
        el.classList.toggle("absorbed", t > 0.02 && t < 0.98);
      });
      if (finalRef.current) {
        const fp = clamp01((p - 0.82) / 0.14);
        finalRef.current.style.opacity = `${fp}`;
        finalRef.current.style.setProperty("--fy", `${(1 - fp) * 16}px`);
      }
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
  }, []);

  return (
    <section className="ed-gravity" id="transform" ref={secRef}>
      <div className="pin">
        <div className="ed-grav-head">
          <span className="eyebrow">Le même achat. Deux prix.</span>
          <h2>
            Le prix affiché n&apos;est pas le <span className="it">vrai</span> prix.
          </h2>
        </div>

        <div className="ed-grav-stage" aria-hidden="true">
          <div className="core" ref={coreRef}>
            <span className="price mono" ref={priceRef}>499 €</span>
          </div>
          {CHIPS.map((c, i) => (
            <div
              className="ed-grav-chip"
              key={c.label}
              ref={(el) => {
                chipRefs.current[i] = el;
              }}
            >
              <span className="l">{c.label}</span>
              <b>{c.v}</b>
            </div>
          ))}
        </div>

        <div className="ed-grav-final" ref={finalRef}>
          <span className="tag">Votre prix réel</span>
          <span className="save mono">365 €</span>
          <span className="delta">−134 € · le filon</span>
        </div>
      </div>
    </section>
  );
}
