"use client";

// Séquence pilotée au défilement — la technique des pages produit d'Apple.
//
// Le film est calculé HORS LIGNE, découpé en images, et le défilement choisit
// laquelle dessiner dans un canvas. Aucun WebGL : le photoréalisme ne dépend
// donc plus de la carte graphique du visiteur, et il n'y a plus de plafond de
// qualité. C'est ce qui distingue ce montage d'une scène temps réel, où l'on
// demande à un navigateur de produire en seize millisecondes ce qu'un moteur
// de rendu met des minutes à calculer par image.
//
// Trois choix méritent d'être connus plutôt que subis :
//
// 1. Un <canvas>, pas une <video> dont on pilote currentTime. Le seek vidéo
//    est saccadé en marche arrière sur plusieurs navigateurs ; une image
//    décodée se redessine instantanément, dans les deux sens.
// 2. Toutes les images sont préchargées avant le premier rendu. Une séquence
//    qui se charge pendant qu'on défile saute, et le saut se voit.
// 3. Le composant ne rend rien tant que les images ne sont pas prêtes : le
//    contenu de repli reste visible, plutôt qu'un carré noir.
//
// Sous « mouvement réduit », la séquence ne se monte pas du tout : une seule
// image fixe est servie et le texte reste entier. La page n'a jamais besoin
// de la 3D ni de l'animation pour être lisible.

import { useEffect, useRef, useState } from "react";

export type Chapitre = {
  /** Position d'entrée dans la course, entre 0 et 1. */
  a: number;
  /** Position de sortie. */
  z: number;
  titre: string;
  suite: string;
};

export function SequenceScroll({
  base,
  images,
  chapitres,
  hauteurVh = 460,
}: {
  /** Dossier public des images, sans barre finale. */
  base: string;
  images: number;
  chapitres: Chapitre[];
  hauteurVh?: number;
}) {
  const hote = useRef<HTMLDivElement>(null);
  const toile = useRef<HTMLCanvasElement>(null);
  const cache = useRef<HTMLImageElement[]>([]);
  const dernier = useRef(-1);
  const [pret, setPret] = useState(false);
  const [actif, setActif] = useState(false);
  const [courant, setCourant] = useState(0);

  useEffect(() => {
    setActif(!window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }, []);

  // Préchargement complet : une séquence qui se charge en défilant saute.
  useEffect(() => {
    if (!actif) return;
    let vivant = true;
    let charges = 0;
    const tab: HTMLImageElement[] = new Array(images);
    for (let i = 0; i < images; i++) {
      const im = new Image();
      im.onload = () => {
        if (!vivant) return;
        tab[i] = im;
        if (++charges === images) {
          cache.current = tab;
          setPret(true);
        }
      };
      im.src = `${base}/${String(i).padStart(3, "0")}.jpg`;
    }
    return () => {
      vivant = false;
    };
  }, [actif, base, images]);

  useEffect(() => {
    if (!pret) return;

    const dessiner = () => {
      const cv = toile.current;
      const el = hote.current;
      if (!cv || !el) return;
      const r = el.getBoundingClientRect();
      const course = r.height - window.innerHeight;
      const p = course > 0 ? Math.min(Math.max(-r.top / course, 0), 1) : 0;
      const i = Math.round(p * (images - 1));
      const im = cache.current[i];
      if (!im || i === dernier.current) return;
      dernier.current = i;
      const ctx = cv.getContext("2d", { alpha: false });
      if (!ctx) return;
      // Recadrage « cover » : l'image couvre l'écran sans jamais se déformer.
      const e = Math.max(cv.width / im.width, cv.height / im.height);
      const w = im.width * e;
      const h = im.height * e;
      ctx.drawImage(im, (cv.width - w) / 2, (cv.height - h) / 2, w, h);
      setCourant(p);
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
  }, [pret, images]);

  // Repli : une image fixe et le texte, en pile. Rien ne disparaît.
  if (!actif) {
    return (
      <section className="fx-seq-repli">
        <img src={`${base}/000.jpg`} alt="" aria-hidden="true" />
        <div className="fx-container">
          {chapitres.map((c) => (
            <h2 key={c.titre} className="fx-chapter-title">
              {c.titre} <em>{c.suite}</em>
            </h2>
          ))}
        </div>
      </section>
    );
  }

  return (
    <section ref={hote} className="fx-seq" style={{ height: `${hauteurVh}vh` }}>
      <div className="fx-seq-collee">
        <canvas ref={toile} className="fx-seq-toile" aria-hidden="true" />
        {chapitres.map((c) => (
          <div
            key={c.titre}
            className="fx-seq-texte"
            data-on={courant >= c.a - 0.03 && courant < c.z ? "true" : undefined}
          >
            <div className="fx-container">
              <h2 className="fx-chapter-title">
                {c.titre} <em>{c.suite}</em>
              </h2>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
