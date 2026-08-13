"use client";

import { useEffect, useRef, useState } from "react";
import { useLocale } from "@/lib/i18n";
import { HeroSearch } from "./HeroSearch";

const IMAGES = 256;
const BASE = "/seq/full";
const HEIGHT_VH = 800;
const PRELOAD_CONCURRENCY = 8;
const INITIAL_PRELOAD = 24;

type Copy = {
  fallbackTitle: string;
  fallbackText: string;
  scrollHint: string;
  chapters: Array<{ start: number; end: number; title: string; cta?: { label: string; href: string } }>;
};

const COPY: Record<"fr" | "nl" | "en", Copy> = {
  fr: {
    fallbackTitle: "Est-ce le bon moment pour acheter ?",
    fallbackText: "FILON vous aide à explorer, comparer et décider avec des offres vérifiables.",
    scrollHint: "Scrollez pour explorer",
    chapters: [
      { start: 0, end: 0.22, title: "Prendre le temps de regarder." },
      { start: 0.25, end: 0.45, title: "Les options deviennent plus claires." },
      { start: 0.49, end: 0.70, title: "Comparer. Vérifier. Décider." },
      { start: 0.74, end: 1, title: "FILON.", cta: { label: "Explorer le catalogue", href: "/recherche/" } },
    ],
  },
  nl: {
    fallbackTitle: "Is dit het juiste moment om te kopen?",
    fallbackText: "FILON helpt je om verifieerbare aanbiedingen te ontdekken, te vergelijken en een keuze te maken.",
    scrollHint: "Scroll om te ontdekken",
    chapters: [
      { start: 0, end: 0.22, title: "Neem even de tijd om te kijken." },
      { start: 0.25, end: 0.45, title: "De opties worden duidelijker." },
      { start: 0.49, end: 0.70, title: "Vergelijk. Controleer. Beslis." },
      { start: 0.74, end: 1, title: "FILON.", cta: { label: "Ontdek de catalogus", href: "/recherche/" } },
    ],
  },
  en: {
    fallbackTitle: "Is this the right time to buy?",
    fallbackText: "FILON helps you explore, compare and decide with verifiable offers.",
    scrollHint: "Scroll to explore",
    chapters: [
      { start: 0, end: 0.22, title: "Take a moment to look." },
      { start: 0.25, end: 0.45, title: "The options become clearer." },
      { start: 0.49, end: 0.70, title: "Compare. Verify. Decide." },
      { start: 0.74, end: 1, title: "FILON.", cta: { label: "Explore the catalogue", href: "/recherche/" } },
    ],
  },
};

function framePath(index: number) {
  return `${BASE}/${String(index + 1).padStart(3, "0")}.jpg`;
}

function closestLoadedFrame(frames: Array<HTMLImageElement | undefined>, target: number) {
  if (frames[target]) return frames[target];
  for (let distance = 1; distance < IMAGES; distance += 1) {
    const before = target - distance;
    const after = target + distance;
    if (before >= 0 && frames[before]) return frames[before];
    if (after < IMAGES && frames[after]) return frames[after];
  }
  return undefined;
}

export function ImmersiveExperience() {
  const { locale } = useLocale();
  const copy = COPY[locale] ?? COPY.fr;
  const host = useRef<HTMLElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const cache = useRef<Array<HTMLImageElement | undefined>>([]);
  const lastFrame = useRef(-1);
  const lastProgress = useRef(-1);
  const [active, setActive] = useState(false);
  const [firstFrameReady, setFirstFrameReady] = useState(false);
  const [firstFrameDrawn, setFirstFrameDrawn] = useState(false);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    setActive(!window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }, []);

  useEffect(() => {
    if (!active) return;

    let alive = true;
    let cursor = 0;
    let pending = 0;
    const order = [
      ...Array.from({ length: INITIAL_PRELOAD }, (_, index) => index),
      ...Array.from({ length: IMAGES - INITIAL_PRELOAD }, (_, index) => index + INITIAL_PRELOAD),
    ];

    const loadNext = () => {
      while (alive && pending < PRELOAD_CONCURRENCY && cursor < order.length) {
        const index = order[cursor++];
        const image = new Image();
        pending += 1;
        image.onload = () => {
          if (!alive) return;
          cache.current[index] = image;
          pending -= 1;
          if (index === 0) setFirstFrameReady(true);
          window.dispatchEvent(new Event("filon:immersive-frame"));
          loadNext();
        };
        image.onerror = () => {
          if (!alive) return;
          pending -= 1;
          loadNext();
        };
        image.src = framePath(index);
      }
    };

    loadNext();
    return () => {
      alive = false;
    };
  }, [active]);

  useEffect(() => {
    if (!active || !firstFrameReady) return;

    const draw = () => {
      const targetCanvas = canvas.current;
      const targetHost = host.current;
      if (!targetCanvas || !targetHost) return;

      const rect = targetHost.getBoundingClientRect();
      const run = rect.height - window.innerHeight;
      const nextProgress = run > 0 ? Math.min(Math.max(-rect.top / run, 0), 1) : 0;
      if (Math.abs(nextProgress - lastProgress.current) >= 0.002) {
        lastProgress.current = nextProgress;
        setProgress(nextProgress);
      }

      const index = Math.round(nextProgress * (IMAGES - 1));
      const image = closestLoadedFrame(cache.current, index);
      if (!image || index === lastFrame.current) return;

      const context = targetCanvas.getContext("2d", { alpha: false });
      if (!context) return;
      const scale = Math.max(targetCanvas.width / image.width, targetCanvas.height / image.height);
      const width = image.width * scale;
      const height = image.height * scale;
      context.fillStyle = "#0e0c0b";
      context.fillRect(0, 0, targetCanvas.width, targetCanvas.height);
      context.drawImage(image, (targetCanvas.width - width) / 2, (targetCanvas.height - height) / 2, width, height);
      lastFrame.current = index;
      setFirstFrameDrawn(true);
    };

    const resize = () => {
      const targetCanvas = canvas.current;
      if (!targetCanvas) return;
      const density = Math.min(window.devicePixelRatio || 1, 2);
      targetCanvas.width = Math.round(window.innerWidth * density);
      targetCanvas.height = Math.round(window.innerHeight * density);
      targetCanvas.style.width = `${window.innerWidth}px`;
      targetCanvas.style.height = `${window.innerHeight}px`;
      lastFrame.current = -1;
      draw();
    };

    let animationFrame = 0;
    const queueDraw = () => {
      if (!animationFrame) {
        animationFrame = requestAnimationFrame(() => {
          draw();
          animationFrame = 0;
        });
      }
    };

    window.addEventListener("scroll", queueDraw, { passive: true });
    window.addEventListener("resize", resize);
    window.addEventListener("filon:immersive-frame", queueDraw);
    resize();
    return () => {
      window.removeEventListener("scroll", queueDraw);
      window.removeEventListener("resize", resize);
      window.removeEventListener("filon:immersive-frame", queueDraw);
      if (animationFrame) cancelAnimationFrame(animationFrame);
    };
  }, [active, firstFrameReady]);

  if (!active) {
    return (
      <section className="fx-immersive-repli">
        <img src={framePath(0)} alt="" className="fx-immersive-repli-img" />
        <div className="fx-immersive-repli-content">
          <h1>{copy.fallbackTitle}</h1>
          <p>{copy.fallbackText}</p>
          <HeroSearch />
        </div>
      </section>
    );
  }

  return (
    <section ref={host} className="fx-immersive" style={{ height: `${HEIGHT_VH}vh` }}>
      <div className="fx-immersive-sticky">
        <img
          src={framePath(0)}
          alt=""
          className={`fx-immersive-poster${firstFrameDrawn ? " is-hidden" : ""}`}
        />
        <canvas ref={canvas} className={`fx-immersive-canvas${firstFrameDrawn ? " is-visible" : ""}`} aria-hidden="true" />
        <div className="fx-immersive-overlay" />

        <div className="fx-immersive-search">
          <HeroSearch />
        </div>

        {copy.chapters.map((chapter, index) => {
          const visible = progress >= chapter.start && progress < chapter.end;
          const opacity = visible
            ? Math.min((progress - chapter.start) / 0.04, (chapter.end - progress) / 0.04, 1)
            : 0;
          return (
            <div
              key={index}
              className="fx-immersive-chapitre"
              style={{ opacity, pointerEvents: visible ? "auto" : "none" }}
            >
              <h2 className="fx-immersive-titre">{chapter.title}</h2>
              {chapter.cta && <a href={chapter.cta.href} className="fx-immersive-cta">{chapter.cta.label}</a>}
            </div>
          );
        })}

        <div className="fx-immersive-scroll-hint" style={{ opacity: progress < 0.05 ? 1 : 0 }}>
          <span>{copy.scrollHint}</span>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <path d="M12 5v14M5 12l7 7 7-7" />
          </svg>
        </div>
      </div>
    </section>
  );
}
