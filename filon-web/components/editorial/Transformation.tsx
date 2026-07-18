"use client";

import { useEffect, useRef } from "react";

const FROM = 499;
const TO = 365;
const SOURCES = [
  { th: 0.3, label: "Cashback", v: "−6,5 %" },
  { th: 0.5, label: "Reconditionné", v: "−94 €" },
  { th: 0.7, label: "Code promo", v: "−15 €" },
];

export function Transformation() {
  const secRef = useRef<HTMLElement>(null);
  const toRef = useRef<HTMLSpanElement>(null);
  const fromRef = useRef<HTMLSpanElement>(null);
  const barRef = useRef<HTMLElement>(null);
  const srcRefs = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    const sec = secRef.current;
    if (!sec) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const apply = (prog: number) => {
      const val = Math.round(FROM - (FROM - TO) * prog);
      if (toRef.current) toRef.current.textContent = `${val} €`;
      if (fromRef.current) fromRef.current.style.setProperty("--strike", prog > 0.06 ? "1" : "0");
      if (barRef.current) barRef.current.style.width = `${prog * 100}%`;
      SOURCES.forEach((s, i) => srcRefs.current[i]?.classList.toggle("on", prog >= s.th));
    };

    if (reduce) {
      apply(1);
      return;
    }
    const onScroll = () => {
      const rect = sec.getBoundingClientRect();
      const h = sec.offsetHeight - window.innerHeight;
      const prog = Math.max(0, Math.min(1, -rect.top / h));
      apply(prog);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <section className="ed-transform" id="transform" ref={secRef}>
      <div className="pin">
        <span className="eyebrow">Le même achat. Deux prix.</span>
        <h2 className="serif">
          FILON transforme le prix affiché en <span className="it">prix réel</span>.
        </h2>
        <div className="ed-morph">
          <span className="from" ref={fromRef}>499 €</span>
          <span className="arrow">→</span>
          <span className="to mono" ref={toRef}>499 €</span>
        </div>
        <div className="ed-tsrc">
          {SOURCES.map((s, i) => (
            <div
              key={s.label}
              className="ed-src"
              ref={(el) => {
                srcRefs.current[i] = el;
              }}
            >
              <span className="dot" /> {s.label} <b>&nbsp;{s.v}</b>
            </div>
          ))}
        </div>
        <div className="ed-tbar">
          <i ref={barRef} />
        </div>
      </div>
    </section>
  );
}
