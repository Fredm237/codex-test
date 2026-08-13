"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { HeroSearch } from "./HeroSearch";
import { useLocale } from "@/lib/i18n";

const TOTAL_FRAMES = 271;
const SCROLL_HEIGHT = 1400;
const INITIAL_WINDOW = 24;
const PREFETCH_WINDOW = 30;

type ChapterTexts = {
  titre: string;
  eyebrow?: string;
  cta?: { label: string; href: string };
};

const CHAPTERS_I18N: Record<string, ChapterTexts[]> = {
  fr: [
    { titre: "Est-ce vraiment\nle bon prix ?", eyebrow: "Votre copilote d’achat." },
    { titre: "1,3 million d'offres.\n207 marchands." },
    { titre: "Le prix que personne\nd'autre ne vous montre." },
    { titre: "Vous venez\nd'économiser 47€." },
    { titre: "FILON.", cta: { label: "Essayer le copilote", href: "/recherche" } },
  ],
  nl: [
    { titre: "Is dit echt\nde juiste prijs?", eyebrow: "Je aankoopcopiloot." },
    { titre: "1,3 miljoen aanbiedingen.\n207 winkels." },
    { titre: "De prijs die niemand\nanders je laat zien." },
    { titre: "Je hebt zojuist\n47€ bespaard." },
    { titre: "FILON.", cta: { label: "Probeer de copiloot", href: "/recherche" } },
  ],
  en: [
    { titre: "Is this really\nthe right price?", eyebrow: "Your shopping copilot." },
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
  const requestedRef = useRef(new Set<number>());
  const prefetchRef = useRef<(frame: number) => void>(() => {});
  const drawRef = useRef<() => void>(() => {});
  const readyRef = useRef(false);
  const [ready, setReady] = useState(false);
  const [activeChapter, setActiveChapter] = useState(0);
  const [chapterOpacity, setChapterOpacity] = useState(1);
  const rafRef = useRef<number>(0);
  const lastFrameRef = useRef(0);

  // La scène n’ouvre plus 271 téléchargements d’un coup. La première image et
  // les premières secondes sont prioritaires ; le reste arrive progressivement
  // et la fenêtre autour du frame visé est priorisée pendant le scroll.
  useEffect(() => {
    let mounted = true;
    const loadFrame = (index: number) => {
      if (index < 0 || index >= TOTAL_FRAMES || requestedRef.current.has(index)) return;
      requestedRef.current.add(index);
      const image = new Image();
      image.decoding = "async";
      image.onload = () => {
        imagesRef.current[index] = image;
        if (index === 0 && mounted) {
          readyRef.current = true;
          setReady(true);
        }
        if (mounted && readyRef.current) requestAnimationFrame(() => drawRef.current());
      };
      image.onerror = () => {
        imagesRef.current[index] = null;
        if (index === 0 && mounted) {
          readyRef.current = true;
          setReady(true);
        }
      };
      image.src = `/seq/hero/${String(index + 1).padStart(3, "0")}.jpg`;
    };

    prefetchRef.current = (frame: number) => {
      const from = Math.max(0, frame - 4);
      const to = Math.min(TOTAL_FRAMES - 1, frame + PREFETCH_WINDOW);
      for (let index = from; index <= to; index++) loadFrame(index);
    };

    for (let index = 0; index < INITIAL_WINDOW; index++) loadFrame(index);
    let nextFrame = INITIAL_WINDOW;
    const progressiveLoader = window.setInterval(() => {
      if (!mounted || nextFrame >= TOTAL_FRAMES) {
        window.clearInterval(progressiveLoader);
        return;
      }
      const until = Math.min(TOTAL_FRAMES, nextFrame + 6);
      for (; nextFrame < until; nextFrame++) loadFrame(nextFrame);
    }, 220);

    return () => {
      mounted = false;
      window.clearInterval(progressiveLoader);
      prefetchRef.current = () => {};
    };
  }, []);

  const draw = useCallback(() => {
    if (!containerRef.current || !canvasRef.current || !ready) return;
    const rect = containerRef.current.getBoundingClientRect();
    const maxScroll = Math.max(1, rect.height - window.innerHeight);
    const progress = Math.max(0, Math.min(1, -rect.top / maxScroll));
    const targetFrame = Math.min(TOTAL_FRAMES - 1, Math.floor(progress * (TOTAL_FRAMES - 1)));
    prefetchRef.current(targetFrame);

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
      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
      }
      context.drawImage(image, 0, 0, width, height);
      lastFrameRef.current = frame;
    }

    const percent = progress * 100;
    for (let index = 0; index < CHAPTER_RANGES.length; index++) {
      const range = CHAPTER_RANGES[index];
      if (percent >= range.start && percent < range.end) {
        setActiveChapter(index);
        const chapterProgress = (percent - range.start) / (range.end - range.start);
        const opacity = index === 0
          ? (chapterProgress > 0.85 ? (1 - chapterProgress) / 0.15 : 1)
          : (chapterProgress < 0.15 ? chapterProgress / 0.15 : chapterProgress > 0.85 ? (1 - chapterProgress) / 0.15 : 1);
        setChapterOpacity(Math.max(0, Math.min(1, opacity)));
        break;
      }
    }
  }, [ready]);

  drawRef.current = draw;

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
        {/* Poster prioritaire : aucune zone noire pendant l’initialisation JavaScript. */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img className="fx-imm-poster" src="/seq/hero/001.jpg" alt="" aria-hidden="true" fetchPriority="high" decoding="async" />
        <canvas ref={canvasRef} className="fx-imm-canvas" />
        <div className="fx-imm-overlay" />
        <div className="fx-imm-chapter" style={{ opacity: chapterOpacity }}>
          {chapter.eyebrow && <p className="fx-imm-eyebrow">{chapter.eyebrow}</p>}
          <h2 className="fx-imm-titre" aria-live="polite">{chapter.titre}</h2>
          {chapter.cta && <a href={chapter.cta.href} className="fx-imm-cta">{chapter.cta.label}</a>}
        </div>
        <div className="fx-imm-search"><HeroSearch /></div>
        {!ready ? <div className="fx-imm-loading">{LOADING_TEXT[locale] || LOADING_TEXT.fr}</div> : activeChapter === 0 && chapterOpacity > 0.65 ? <div className="fx-imm-scroll-hint"><span>{SCROLL_HINT[locale] || SCROLL_HINT.fr}</span><svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M8 3v10M4 9l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /></svg></div> : null}
      </div>
    </div>
  );
}
