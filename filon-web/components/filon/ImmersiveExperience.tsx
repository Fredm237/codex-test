"use client";

// ImmersiveExperience — Le site entier est un film piloté au scroll.
//
// 264 images, 5 chapitres. Chaque chapitre est un moment du film :
// 1. Entrée dans l'appartement (0-20%) — "Est-ce le bon moment pour acheter ?"
// 2. On s'approche de l'écran (20-40%) — "FILON compare les prix pour vous"
// 3. L'interface en plein écran (40-60%) — "Le meilleur prix, trouvé en secondes"
// 4. La personne satisfaite (60-80%) — "Économisez sans effort"
// 5. Retour large (80-100%) — CTA "Essayez maintenant"
//
// Le texte apparaît et disparaît à chaque chapitre.
// Le fond est TOUJOURS le film. Pas de sections blanches. Pas de rupture.

import { useEffect, useRef, useState } from "react";
import { HeroSearch } from "./HeroSearch";

const IMAGES = 264;
const BASE = "/seq/full";
const HEIGHT_VH = 1200; // 12x l'écran pour un scroll long et fluide

type Chapitre = {
  debut: number;
  fin: number;
  titre: string;
  sousTitre?: string;
  cta?: { label: string; href: string };
};

const CHAPITRES: Chapitre[] = [
  {
    debut: 0.0,
    fin: 0.2,
    titre: "Est-ce vraiment le bon prix ?",
  },
  {
    debut: 0.22,
    fin: 0.4,
    titre: "1,3 million d'offres. 207 marchands. Un seul verdict.",
  },
  {
    debut: 0.42,
    fin: 0.6,
    titre: "Le prix que personne d'autre ne vous montre.",
  },
  {
    debut: 0.62,
    fin: 0.8,
    titre: "Vous venez d'économiser 47€.",
  },
  {
    debut: 0.82,
    fin: 1.0,
    titre: "FILON.",
    cta: { label: "Essayer le copilote", href: "/recherche/" },
  },
];

export function ImmersiveExperience() {
  const hote = useRef<HTMLDivElement>(null);
  const toile = useRef<HTMLCanvasElement>(null);
  const cache = useRef<HTMLImageElement[]>([]);
  const dernier = useRef(-1);
  const [pret, setPret] = useState(false);
  const [actif, setActif] = useState(false);
  const [progression, setProgression] = useState(0);

  useEffect(() => {
    setActif(!window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }, []);

  // Préchargement progressif
  useEffect(() => {
    if (!actif) return;
    let vivant = true;
    let charges = 0;
    const tab: HTMLImageElement[] = new Array(IMAGES);
    for (let i = 0; i < IMAGES; i++) {
      const im = new Image();
      im.onload = () => {
        if (!vivant) return;
        tab[i] = im;
        if (++charges === IMAGES) {
          cache.current = tab;
          setPret(true);
        }
      };
      im.src = `${BASE}/${String(i).padStart(3, "0")}.jpg`;
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
      setProgression(p);
      const i = Math.round(p * (IMAGES - 1));
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
      <section className="fx-immersive-repli">
        <img src={`${BASE}/000.jpg`} alt="" className="fx-immersive-repli-img" />
        <div className="fx-immersive-repli-content">
          <h1>Est-ce vraiment le bon moment pour acheter ?</h1>
          <p>FILON compare les prix de vos produits préférés chez tous les marchands et vous dit quand acheter.</p>
          <HeroSearch />
        </div>
      </section>
    );
  }

  return (
    <section ref={hote} className="fx-immersive" style={{ height: `${HEIGHT_VH}vh` }}>
      <div className="fx-immersive-sticky">
        <canvas ref={toile} className="fx-immersive-canvas" aria-hidden="true" />
        <div className="fx-immersive-overlay" />

        {/* Barre de recherche toujours visible en haut */}
        <div className="fx-immersive-search">
          <HeroSearch />
        </div>

        {/* Chapitres — textes qui apparaissent/disparaissent */}
        {CHAPITRES.map((ch, idx) => {
          const visible = progression >= ch.debut && progression < ch.fin;
          const opacite = visible
            ? Math.min(
                (progression - ch.debut) / 0.04,
                (ch.fin - progression) / 0.04,
                1
              )
            : 0;

          return (
            <div
              key={idx}
              className="fx-immersive-chapitre"
              style={{ opacity: opacite, pointerEvents: visible ? "auto" : "none" }}
            >
              <h2 className="fx-immersive-titre">{ch.titre}</h2>
              {ch.sousTitre && <p className="fx-immersive-sous">{ch.sousTitre}</p>}
              {ch.cta && (
                <a href={ch.cta.href} className="fx-immersive-cta">
                  {ch.cta.label}
                </a>
              )}
            </div>
          );
        })}

        {/* Indicateur de scroll */}
        <div className="fx-immersive-scroll-hint" style={{ opacity: progression < 0.05 ? 1 : 0 }}>
          <span>Scrollez pour explorer</span>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 5v14M5 12l7 7 7-7" />
          </svg>
        </div>
      </div>
    </section>
  );
}
