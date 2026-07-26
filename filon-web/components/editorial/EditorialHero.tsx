"use client";

import { useEffect, useRef } from "react";
import dynamic from "next/dynamic";
import { ChromeCta } from "./ChromeCta";
import { useLocale } from "@/lib/i18n";

const IntelligenceCore = dynamic(
  () => import("./IntelligenceCore").then((m) => m.IntelligenceCore),
  { ssr: false, loading: () => <div className="ed-core core-fallback" aria-hidden="true" /> }
);

export function EditorialHero() {
  const heroRef = useRef<HTMLElement>(null);
  const { t } = useLocale();

  useEffect(() => {
    const hero = heroRef.current;
    if (!hero) return;
    requestAnimationFrame(() => hero.classList.add("in"));
  }, []);

  return (
    <section className="ed-hero" ref={heroRef}>
      <div className="ed-core-wrap" aria-hidden="true">
        <div className="ed-core-glow" />
        <IntelligenceCore className="ed-core" />
      </div>

      <div className="ed-wrap ed-hero-grid">
        <div className="ed-hero-text">
          <span className="eyebrow ed-hero-eyebrow">
            <span className="dot" /> {t("hero.eyebrow")}
          </span>
          <h1 className="ed-h1" aria-label={t("hero.h1aria")}>
            <span className="l"><span>{t("hero.h1a")}</span></span>
            <span className="l"><span className="it">{t("hero.h1b")}</span></span>
            <span className="l"><span className="wave-text">{t("hero.h1c")}</span></span>
          </h1>
          <p className="ed-hero-sub">
            {t("hero.sub")}
          </p>
          <div className="ed-hero-actions">
            <a className="ed-btn wave" href="/recherche">{t("cta.try")}</a>
            <ChromeCta variant="ghost" label={t("cta.chrome")} />
          </div>
        </div>

        <div className="ed-hero-visual" aria-hidden="true" />
      </div>

      <a href="#transform" className="ed-scrollcue" aria-label={t("cta.discover")}>
        <span className="ln" />
        <span className="tx">{t("cta.discover")}</span>
      </a>
    </section>
  );
}
