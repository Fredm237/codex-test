"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { HeroSearch } from "./HeroSearch";

const TOTAL_FRAMES = 271;
const SCROLL_HEIGHT = 1400; // vh — hauteur totale du scroll

type Chapter = {
  start: number; // % du scroll
  end: number;
  titre: string;
  sousTitre?: string;
  cta?: { label: string; href: string };
};

const CHAPTERS: Chapter[] = [
  { start: 0, end: 20, titre: "Est-ce vraiment\nle bon prix ?" },
  { start: 20, end: 40, titre: "1,3 million d'offres.\n207 marchands." },
  { start: 40, end: 60, titre: "Le prix que personne\nd'autre ne vous montre." },
  { start: 60, end: 80, titre: "Vous venez\nd'économiser 47€." },
  { start: 80, end: 100, titre: "FILON.", cta: { label: "Essayer le copilote", href: "/recherche" } },
];

export function ImmersiveExperience() {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imagesRef = useRef<HTMLImageElement[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [activeChapter, setActiveChapter] = useState(0);
  const [chapterOpacity, setChapterOpacity] = useState(1);
  const rafRef = useRef<number>(0);

  // Précharger toutes les images
  useEffect(() => {
    let loadedCount = 0;
    const images: HTMLImageElement[] = [];
    for (let i = 1; i <= TOTAL_FRAMES; i++) {
      const img = new Image();
      img.src = `/seq/hero/${String(i).padStart(3, "0")}.jpg`;
      img.onload = () => {
        loadedCount++;
        if (loadedCount === TOTAL_FRAMES) setLoaded(true);
      };
      images.push(img);
    }
    imagesRef.current = images;
  }, []);

  // Dessiner le frame correspondant au scroll
  const draw = useCallback(() => {
    if (!containerRef.current || !canvasRef.current || !loaded) return;
    const rect = containerRef.current.getBoundingClientRect();
    const scrolled = -rect.top;
    const maxScroll = rect.height - window.innerHeight;
    const progress = Math.max(0, Math.min(1, scrolled / maxScroll));

    // Frame index
    const frameIndex = Math.min(TOTAL_FRAMES - 1, Math.floor(progress * TOTAL_FRAMES));
    const ctx = canvasRef.current.getContext("2d");
    if (ctx && imagesRef.current[frameIndex]) {
      canvasRef.current.width = 1280;
      canvasRef.current.height = 720;
      ctx.drawImage(imagesRef.current[frameIndex], 0, 0, 1280, 720);
    }

    // Chapitre actif
    const pct = progress * 100;
    for (let i = 0; i < CHAPTERS.length; i++) {
      if (pct >= CHAPTERS[i].start && pct < CHAPTERS[i].end) {
        setActiveChapter(i);
        // Fade in/out aux bords du chapitre
        const chapterProgress = (pct - CHAPTERS[i].start) / (CHAPTERS[i].end - CHAPTERS[i].start);
        const fade = chapterProgress < 0.15 ? chapterProgress / 0.15
          : chapterProgress > 0.85 ? (1 - chapterProgress) / 0.15
          : 1;
        setChapterOpacity(Math.max(0, Math.min(1, fade)));
        break;
      }
    }

    rafRef.current = requestAnimationFrame(draw);
  }, [loaded]);

  useEffect(() => {
    if (loaded) {
      rafRef.current = requestAnimationFrame(draw);
      window.addEventListener("scroll", () => {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = requestAnimationFrame(draw);
      });
    }
    return () => cancelAnimationFrame(rafRef.current);
  }, [loaded, draw]);

  const chapter = CHAPTERS[activeChapter];

  return (
    <div ref={containerRef} className="fx-imm-wrap" style={{ height: `${SCROLL_HEIGHT}vh` }}>
      <div className="fx-imm-sticky">
        {/* Canvas plein écran */}
        <canvas ref={canvasRef} className="fx-imm-canvas" />

        {/* Overlay sombre */}
        <div className="fx-imm-overlay" />

        {/* Texte du chapitre */}
        <div className="fx-imm-chapter" style={{ opacity: chapterOpacity }}>
          <h2 className="fx-imm-titre">{chapter.titre}</h2>
          {chapter.sousTitre && <p className="fx-imm-sous">{chapter.sousTitre}</p>}
          {chapter.cta && (
            <a href={chapter.cta.href} className="fx-imm-cta">{chapter.cta.label}</a>
          )}
        </div>

        {/* Barre de recherche fixe en bas */}
        <div className="fx-imm-search">
          <HeroSearch />
        </div>

        {/* Indicateur de scroll */}
        {!loaded ? (
          <div className="fx-imm-loading">Chargement de l&apos;expérience...</div>
        ) : (
          <div className="fx-imm-scroll-hint">
            <span>Scrollez pour explorer</span>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 3v10M4 9l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
          </div>
        )}
      </div>
    </div>
  );
}
