"use client";

// Hero — CLAIR dès la première seconde.
//
// Le visiteur doit comprendre en 2 secondes ce que fait FILON :
// "Je compare les prix pour toi et je te dis si c'est le bon moment d'acheter."
//
// La séquence en fond montre un écran avec une interface de comparaison de prix.
// Le titre est explicite. La barre de recherche invite à l'action.

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import type { Proof } from "@/lib/proof";
import { useLocale } from "@/lib/i18n";
import { HeroSearch } from "./HeroSearch";

const HERO_IMAGES = 60;
const HERO_BASE = "/seq/hero";
const HERO_HEIGHT_VH = 250;

export function Hero({ proof }: { proof: Proof | null }) {
  const { t } = useLocale();
  const hote = useRef<HTMLDivElement>(null);
  const toile = useRef<HTMLCanvasElement>(null);
  const cache = useRef<HTMLImageElement[]>([]);
  const dernier = useRef(-1);
  const [pret, setPret] = useState(false);
  const [actif, setActif] = useState(false);

  useEffect(() => {
    setActif(!window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }, []);

  useEffect(() => {
    if (!actif) return;
    let vivant = true;
    let charges = 0;
    const tab: HTMLImageElement[] = new Array(HERO_IMAGES);
    for (let i = 0; i < HERO_IMAGES; i++) {
      const im = new Image();
      im.onload = () => {
        if (!vivant) return;
        tab[i] = im;
        if (++charges === HERO_IMAGES) {
          cache.current = tab;
          setPret(true);
        }
      };
      im.src = `${HERO_BASE}/${String(i).padStart(3, "0")}.jpg`;
    }
    return () => { vivant = false; };
  }, [actif]);

  useEffect(() => {
    if (!pret) return;

    const dessiner = () => {
      const cv = toile.current;
      const el = hote.current;
      if (!cv || !el) return;
      const r = el.getBoundingClientRect();
      const course = r.height - window.innerHeight;
      const p = course > 0 ? Math.min(Math.max(-r.top / course, 0), 1) : 0;
      const i = Math.round(p * (HERO_IMAGES - 1));
      const im = cache.current[i];
      if (!im || i === dernier.current) return;
      dernier.current = i;
      const ctx = cv.getContext("2d", { alpha: false });
      if (!ctx) return;
      const e = Math.max(cv.width / im.width, cv.height / im.height);
      const w = im.width * e;
      const h = im.height * e;
      ctx.drawImage(im, (cv.width - w) / 2, (cv.height - h) / 2, w, h);
    };

    const dimensionner = () => {
      const cv = toile.current;
      if (!cv) return;
      const d = Math.min(window.devicePixelRatio || 1, 2);
      cv.width = window.innerWidth * d;
      cv.height = window.innerHeight * d;
      cv.style.width = `${window.innerWidth}px`;
      cv.style.height = `${window.innerHeight}px`;
      dernier.current = -1;
      dessiner();
    };

    let raf = 0;
    const file = () => {
      if (!raf) raf = requestAnimationFrame(() => { dessiner(); raf = 0; });
    };
    window.addEventListener("scroll", file, { passive: true });
    window.addEventListener("resize", dimensionner);
    dimensionner();
    return () => {
      window.removeEventListener("scroll", file);
      window.removeEventListener("resize", dimensionner);
      if (raf) cancelAnimationFrame(raf);
    };
  }, [pret]);

  // Repli sans animation
  if (!actif) {
    return (
      <section className="fx-hero">
        <img
          src={`${HERO_BASE}/000.jpg`}
          alt=""
          aria-hidden="true"
          className="fx-hero-bg-img"
        />
        <div className="fx-hero-overlay" />
        <div className="fx-hero-content">
          <h1 className="fx-hero-title">
            {t("hero.l1")} {t("hero.l2")} <em>{t("hero.l3")}</em>
          </h1>
          <p className="fx-hero-subtitle">
            FILON compare les prix de vos produits préférés chez tous les marchands et vous dit quand acheter.
          </p>
          <HeroSearch />
        </div>
      </section>
    );
  }

  return (
    <section ref={hote} className="fx-hero fx-hero--seq" style={{ height: `${HERO_HEIGHT_VH}vh` }}>
      <div className="fx-hero-sticky">
        <canvas ref={toile} className="fx-hero-canvas" aria-hidden="true" />
        <div className="fx-hero-overlay" />
        <div className="fx-hero-content">
          <motion.h1
            className="fx-hero-title"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          >
            {t("hero.l1")} {t("hero.l2")} <em>{t("hero.l3")}</em>
          </motion.h1>

          <motion.p
            className="fx-hero-subtitle"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          >
            FILON compare les prix de vos produits préférés chez tous les marchands et vous dit quand acheter.
          </motion.p>

          <motion.div
            className="fx-hero-search-wrap"
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          >
            <HeroSearch />
          </motion.div>

          {proof?.stats && (
            <motion.div
              className="fx-hero-stats"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6, duration: 0.5 }}
            >
              <span><b>{new Intl.NumberFormat("fr-BE").format(proof.stats.offers)}</b> offres suivies</span>
              <span className="fx-hero-stats-sep" />
              <span><b>{proof.stats.merchants}</b> marchands</span>
            </motion.div>
          )}
        </div>
      </div>
    </section>
  );
}
