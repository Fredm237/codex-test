"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { HeroSearch } from "./HeroSearch";
import { useLocale } from "@/lib/i18n";

const TOTAL_FRAMES = 271;
const SCROLL_HEIGHT = 1400;

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
  fr: "Préparation de l'expérience...",
  nl: "Ervaring voorbereiden...",
  en: "Preparing the experience...",
};

export function ImmersiveExperience() {
  const { locale } = useLocale();
  const chapters = CHAPTERS_I18N[locale] || CHAPTERS_I18N.fr;
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imagesRef = useRef<(HTMLImageElement | null)[]>(Array(TOTAL_FRAMES).fill(null));
  const [ready, setReady] = useState(false);
  const [activeChapter, setActiveChapter] = useState(0);
  const [chapterOpacity, setChapterOpacity] = useState(1);
  const rafRef = useRef<number>(0);
  const lastFrameRef = useRef(0);

  // La première image débloque l'expérience immédiatement. Les autres images
  // continuent ensuite à se charger en arrière-plan, sans écran noir.
  useEffect(() => {
    let mounted = true;
    const loadFrame = (index: number) => {
      const image = new Image();
      image.decoding = "async";
      image.onload = () => {
        imagesRef.current[index] = image;
        if (index === 0 && mounted) setReady(true);
      };
      // Une image manquante ne doit jamais bloquer toute la page.
      image.onerror = () => {
        imagesRef.current[index] = null;
        if (index === 0 && mounted) setReady(true);
      };
      image.src = `/seq/hero/${String(index + 1).padStart(3, "0")}.jpg`;
    };

    // La première frame est prioritaire, puis la suite du film arrive en tâche de fond.
    loadFrame(0);
    for (let index = 1; index < TOTAL_FRAMES; index++) loadFrame(index);
    return () => { mounted = false; };
  }, []);

  const draw = useCallback(() => {
    if (!containerRef.current || !canvasRef.current || !ready) return;
    const rect = containerRef.current.getBoundingClientRect();
    const maxScroll = Math.max(1, rect.height - window.innerHeight);
    const progress = Math.max(0, Math.min(1, -rect.top / maxScroll));
    const targetFrame = Math.min(TOTAL_FRAMES - 1, Math.floor(progress * (TOTAL_FRAMES - 1)));

    // On utilise la frame demandée, sinon la plus proche déjà chargée : le film
    // reste visible même si une image est encore en téléchargement.
    let frame = targetFrame;
    if (!imagesRef.current[frame]) {
      for (let distance = 1; distance < TOTAL_FRAMES; distance++) {
        const before = targetFrame - distance;
        const after = targetFrame + distance;
        if (before >= 0 && imagesRef.current[before]) { frame = before; break; }
        if (after < TOTAL_FRAMES && imagesRef.current[after]) { frame = after; break; }
      }
    }
    const image = imagesRef.current[frame] || imagesRef.current[lastFrameRef.current];
    const canvas = canvasRef.current;
    const context = canvas.getContext("2d");
    if (context && image) {
      const width = 1280;
      const height = 720;
      canvas.width = width;
      canvas.height = height;
      context.drawImage(image, 0, 0, width, height);
      lastFrameRef.current = frame;
    }

    const percent = progress * 100;
    for (let index = 0; index < CHAPTER_RANGES.length; index++) {
      const range = CHAPTER_RANGES[index];
      if (percent >= range.start && percent < range.end) {
        setActiveChapter(index);
        const chapterProgress = (percent - range.start) / (range.end - range.start);
        // Le premier message doit déjà être visible dès l'arrivée sur la page.
        // Les chapitres suivants entrent et sortent avec un fondu court.
        const opacity = index === 0
          ? (chapterProgress > 0.85 ? (1 - chapterProgress) / 0.15 : 1)
          : (chapterProgress < 0.15 ? chapterProgress / 0.15
            : chapterProgress > 0.85 ? (1 - chapterProgress) / 0.15
            : 1);
        setChapterOpacity(Math.max(0, Math.min(1, opacity)));
        break;
      }
    }
  }, [ready]);

  useEffect(() => {
    if (!ready) return;
    const onScrollOrResize = () => {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = requestAnimationFrame(draw);
    };
    onScrollOrResize();
    window.addEventListener("scroll", onScrollOrResize, { passive: true });
    window.addEventListener("resize", onScrollOrResize);
    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener("scroll", onScrollOrResize);
      window.removeEventListener("resize", onScrollOrResize);
    };
  }, [ready, draw]);

  const chapter = chapters[activeChapter];

  return (
    <div ref={containerRef} className="fx-imm-wrap" style={{ height: `${SCROLL_HEIGHT}vh` }}>
      <div className="fx-imm-sticky">
        <canvas ref={canvasRef} className="fx-imm-canvas" />
        <div className="fx-imm-overlay" />
        <div className="fx-imm-chapter" style={{ opacity: chapterOpacity }}>
          <h2 className="fx-imm-titre">{chapter.titre}</h2>
          {chapter.cta && <a href={chapter.cta.href} className="fx-imm-cta">{chapter.cta.label}</a>}
        </div>
        <div className="fx-imm-search"><HeroSearch /></div>
        {!ready ? (
          <div className="fx-imm-loading">{LOADING_TEXT[locale] || LOADING_TEXT.fr}</div>
        ) : (
          <div className="fx-imm-scroll-hint">
            <span>{SCROLL_HINT[locale] || SCROLL_HINT.fr}</span>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M8 3v10M4 9l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /></svg>
          </div>
        )}
      </div>
    </div>
  );
}
