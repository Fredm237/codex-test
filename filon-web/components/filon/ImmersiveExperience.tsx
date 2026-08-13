"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { HeroSearch } from "./HeroSearch";
import { useLocale } from "@/lib/i18n";

const TOTAL_FRAMES = 256;
const FRAME_BASE = "/seq/hero";
const SCROLL_HEIGHT = 1000;
const INITIAL_WINDOW = 24;
const PREFETCH_WINDOW = 30;

type ChapterText = {
  title: string;
  eyebrow?: string;
  cta?: { label: string; href: string };
};

const COPY: Record<"fr" | "nl" | "en", { chapters: ChapterText[]; scrollHint: string; loading: string }> = {
  fr: {
    chapters: [
      { title: "Prendre le temps\nde regarder.", eyebrow: "Votre copilote d’achat." },
      { title: "Les options deviennent\nplus claires." },
      { title: "Comparer. Vérifier.\nDécider." },
      { title: "FILON.", cta: { label: "Explorer le catalogue", href: "/recherche" } },
    ],
    scrollHint: "Scrollez pour explorer",
    loading: "Préparation de l’expérience...",
  },
  nl: {
    chapters: [
      { title: "Neem even de tijd\nom te kijken.", eyebrow: "Je aankoopcopiloot." },
      { title: "De opties worden\nduidelijker." },
      { title: "Vergelijk. Controleer.\nBeslis." },
      { title: "FILON.", cta: { label: "Ontdek de catalogus", href: "/recherche" } },
    ],
    scrollHint: "Scroll om te ontdekken",
    loading: "Ervaring voorbereiden...",
  },
  en: {
    chapters: [
      { title: "Take a moment\nto look.", eyebrow: "Your shopping copilot." },
      { title: "The options become\nclearer." },
      { title: "Compare. Verify.\nDecide." },
      { title: "FILON.", cta: { label: "Explore the catalogue", href: "/recherche" } },
    ],
    scrollHint: "Scroll to explore",
    loading: "Preparing the experience...",
  },
};

function frameSource(index: number) {
  return `${FRAME_BASE}/${String(index + 1).padStart(3, "0")}.jpg`;
}

function closestFrame(images: Array<HTMLImageElement | null>, target: number, previous: number) {
  if (images[target]) return images[target];
  for (let distance = 1; distance < TOTAL_FRAMES; distance += 1) {
    const before = target - distance;
    const after = target + distance;
    if (before >= 0 && images[before]) return images[before];
    if (after < TOTAL_FRAMES && images[after]) return images[after];
  }
  return images[previous];
}

export function ImmersiveExperience() {
  const { locale } = useLocale();
  const copy = COPY[locale] ?? COPY.fr;
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imagesRef = useRef<Array<HTMLImageElement | null>>(Array(TOTAL_FRAMES).fill(null));
  const requestedRef = useRef(new Set<number>());
  const prefetchRef = useRef<(frame: number) => void>(() => {});
  const drawRef = useRef<() => void>(() => {});
  const readyRef = useRef(false);
  const paintedRef = useRef(false);
  const lastFrameRef = useRef(0);
  const lastChapterRef = useRef(-1);
  const rafRef = useRef(0);
  const [ready, setReady] = useState(false);
  const [canvasPainted, setCanvasPainted] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(() =>
    typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches,
  );
  const [activeChapter, setActiveChapter] = useState(0);
  const [chapterOpacity, setChapterOpacity] = useState(1);

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReducedMotion(media.matches);
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    if (reducedMotion) {
      readyRef.current = true;
      setReady(true);
      return;
    }

    let mounted = true;
    const loadFrame = (index: number) => {
      if (index < 0 || index >= TOTAL_FRAMES || requestedRef.current.has(index)) return;
      requestedRef.current.add(index);
      const image = new Image();
      image.decoding = "async";
      image.onload = () => {
        if (!mounted) return;
        imagesRef.current[index] = image;
        if (index === 0) {
          readyRef.current = true;
          setReady(true);
        }
        if (readyRef.current) requestAnimationFrame(() => drawRef.current());
      };
      image.onerror = () => {
        if (!mounted) return;
        if (index === 0) {
          // Le poster reste visible : l'expérience ne bascule jamais sur un écran noir.
          readyRef.current = true;
          setReady(true);
        }
      };
      image.src = frameSource(index);
    };

    prefetchRef.current = (frame: number) => {
      const from = Math.max(0, frame - 4);
      const to = Math.min(TOTAL_FRAMES - 1, frame + PREFETCH_WINDOW);
      for (let index = from; index <= to; index += 1) loadFrame(index);
    };

    for (let index = 0; index < INITIAL_WINDOW; index += 1) loadFrame(index);
    let nextFrame = INITIAL_WINDOW;
    const progressiveLoader = window.setInterval(() => {
      if (!mounted || nextFrame >= TOTAL_FRAMES) {
        window.clearInterval(progressiveLoader);
        return;
      }
      const until = Math.min(TOTAL_FRAMES, nextFrame + 6);
      for (; nextFrame < until; nextFrame += 1) loadFrame(nextFrame);
    }, 220);

    return () => {
      mounted = false;
      window.clearInterval(progressiveLoader);
      prefetchRef.current = () => {};
    };
  }, [reducedMotion]);

  const draw = useCallback(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas || !ready) return;

    const rect = container.getBoundingClientRect();
    const maxScroll = Math.max(1, rect.height - window.innerHeight);
    const progress = Math.max(0, Math.min(1, -rect.top / maxScroll));
    const targetFrame = Math.min(TOTAL_FRAMES - 1, Math.floor(progress * (TOTAL_FRAMES - 1)));
    prefetchRef.current(targetFrame);

    const image = closestFrame(imagesRef.current, targetFrame, lastFrameRef.current);
    const context = canvas.getContext("2d", { alpha: false });
    if (context && image) {
      const density = Math.min(window.devicePixelRatio || 1, 2);
      const width = Math.round(window.innerWidth * density);
      const height = Math.round(window.innerHeight * density);
      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
      }
      const scale = Math.max(width / image.width, height / image.height);
      const drawWidth = image.width * scale;
      const drawHeight = image.height * scale;
      context.fillStyle = "#0e0c0b";
      context.fillRect(0, 0, width, height);
      context.drawImage(image, (width - drawWidth) / 2, (height - drawHeight) / 2, drawWidth, drawHeight);
      lastFrameRef.current = targetFrame;
      if (!paintedRef.current) {
        paintedRef.current = true;
        setCanvasPainted(true);
      }
    }

    const chapterIndex = Math.min(copy.chapters.length - 1, Math.floor(progress * copy.chapters.length));
    const chapterProgress = (progress * copy.chapters.length) % 1;
    const opacity = chapterIndex === 0
      ? (chapterProgress > 0.85 ? (1 - chapterProgress) / 0.15 : 1)
      : chapterProgress < 0.15
        ? chapterProgress / 0.15
        : chapterProgress > 0.85
          ? (1 - chapterProgress) / 0.15
          : 1;
    if (chapterIndex !== lastChapterRef.current) {
      lastChapterRef.current = chapterIndex;
      setActiveChapter(chapterIndex);
    }
    setChapterOpacity(Math.max(0, Math.min(1, opacity)));
  }, [copy.chapters.length, ready]);

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

  const chapter = copy.chapters[activeChapter];

  return (
    <div ref={containerRef} className="fx-imm-wrap" style={{ height: `${SCROLL_HEIGHT}vh` }}>
      <div className="fx-imm-sticky">
        {/* Poster prioritaire : aucune zone noire avant le premier dessin réel. */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img className={`fx-imm-poster${canvasPainted ? " is-hidden" : ""}`} src={frameSource(0)} alt="" aria-hidden="true" fetchPriority="high" decoding="async" />
        <canvas ref={canvasRef} className={`fx-imm-canvas${canvasPainted ? " is-visible" : ""}`} aria-hidden="true" />
        <div className="fx-imm-overlay" />
        <div className="fx-imm-chapter" style={{ opacity: chapterOpacity }}>
          {chapter.eyebrow && <p className="fx-imm-eyebrow">{chapter.eyebrow}</p>}
          <h2 className="fx-imm-titre" aria-live="polite">{chapter.title}</h2>
          {chapter.cta && <a href={chapter.cta.href} className="fx-imm-cta">{chapter.cta.label}</a>}
        </div>
        <div className="fx-imm-search"><HeroSearch /></div>
        {!ready ? <div className="fx-imm-loading">{copy.loading}</div> : activeChapter === 0 && chapterOpacity > 0.65 ? <div className="fx-imm-scroll-hint"><span>{copy.scrollHint}</span><svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M8 3v10M4 9l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /></svg></div> : null}
      </div>
    </div>
  );
}
