"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { HeroSearch } from "./HeroSearch";
import { useLocale } from "@/lib/i18n";

const TOTAL_FRAMES = 271;
const SCROLL_HEIGHT = 1400; // vh — hauteur totale du scroll

type ChapterTexts = {
  titre: string;
  cta?: { label: string; href: string };
};

const CHAPTERS_I18N: Record<string, ChapterTexts[]> = {
  fr: [
    { titre: "Est-ce vraiment\nle bon prix ?" },
    { titre: "1,3 million d'offres.\n207 marchands." },
    { titre: "Le prix que personne\nd'autre ne vous montre." },
    { titre: "Vous venez\nd'économiser 47€." },
    { titre: "FILON.", cta: { label: "Essayer le copilote", href: "/recherche" } },
  ],
  nl: [
    { titre: "Is dit echt\nde juiste prijs?" },
    { titre: "1,3 miljoen aanbiedingen.\n207 winkels." },
    { titre: "De prijs die niemand\nanders je laat zien." },
    { titre: "Je hebt zojuist\n47€ bespaard." },
    { titre: "FILON.", cta: { label: "Probeer de copiloot", href: "/recherche" } },
  ],
  en: [
    { titre: "Is this really\nthe right price?" },
    { titre: "1.3 million offers.\n207 merchants." },
    { titre: "The price no one\nelse shows you." },
    { titre: "You just\nsaved €47." },
    { titre: "FILON.", cta: { label: "Try the copilot", href: "/recherche" } },
  ],
};

const CHAPTER_RANGES = [
  { start: 0, end: 20 },
  { start: 20, end: 40 },
  { start: 40, end: 60 },
  { start: 60, end: 80 },
  { start: 80, end: 100 },
];

const SCROLL_HINT: Record<string, string> = {
  fr: "Scrollez pour explorer",
  nl: "Scroll om te ontdekken",
  en: "Scroll to explore",
};

const LOADING_TEXT: Record<string, string> = {
  fr: "Chargement de l'expérience...",
  nl: "Ervaring laden...",
  en: "Loading experience...",
};

export function ImmersiveExperience() {
  const { locale } = useLocale();
  const chapters = CHAPTERS_I18N[locale] || CHAPTERS_I18N.fr;

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
    for (let i = 0; i < CHAPTER_RANGES.length; i++) {
      if (pct >= CHAPTER_RANGES[i].start && pct < CHAPTER_RANGES[i].end) {
        setActiveChapter(i);
        const chapterProgress = (pct - CHAPTER_RANGES[i].start) / (CHAPTER_RANGES[i].end - CHAPTER_RANGES[i].start);
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

  const chapter = chapters[activeChapter];

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
          <div className="fx-imm-loading">{LOADING_TEXT[locale] || LOADING_TEXT.fr}</div>
        ) : (
          <div className="fx-imm-scroll-hint">
            <span>{SCROLL_HINT[locale] || SCROLL_HINT.fr}</span>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 3v10M4 9l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
          </div>
        )}
      </div>
    </div>
  );
}
