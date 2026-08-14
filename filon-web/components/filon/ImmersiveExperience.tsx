"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { HeroSearch } from "./HeroSearch";
import { useLocale } from "@/lib/i18n";

const DESKTOP_TOTAL_FRAMES = 320;
const MOBILE_TOTAL_FRAMES = 192;
const DESKTOP_FRAME_BASE = "/seq/hero";
const MOBILE_FRAME_BASE = "/seq-mobile/frames";
const DESKTOP_SCROLL_HEIGHT = 1000;
const MOBILE_SCROLL_HEIGHT = 640;

type ChapterText = {
  title: string;
  eyebrow?: string;
  cta?: { label: string; href: string };
};

type NetworkConnection = {
  saveData?: boolean;
  effectiveType?: string;
  addEventListener?: (type: "change", listener: () => void) => void;
  removeEventListener?: (type: "change", listener: () => void) => void;
};

const COPY: Record<"fr" | "nl" | "en", { chapters: ChapterText[]; scrollHint: string; loading: string }> = {
  fr: {
    chapters: [
      { title: "Est-ce vraiment le bon moment\npour acheter ?", eyebrow: "FILON vous donne la réponse." },
      { title: "On compare les prix\npour vous." },
      { title: "Le meilleur prix,\ntrouvé en secondes." },
      { title: "Décidez avec\nle contexte." },
      { title: "Prêt à trouver\nle bon prix ?", cta: { label: "Explorer le catalogue", href: "/recherche" } },
    ],
    scrollHint: "Scrollez pour explorer",
    loading: "Préparation de l’expérience...",
  },
  nl: {
    chapters: [
      { title: "Is dit echt het juiste moment\nom te kopen?", eyebrow: "FILON geeft je het antwoord." },
      { title: "Wij vergelijken de prijzen\nvoor jou." },
      { title: "De beste prijs,\ngevonden in seconden." },
      { title: "Beslis met\nde juiste context." },
      { title: "Klaar om de juiste prijs\nte vinden?", cta: { label: "Ontdek de catalogus", href: "/recherche" } },
    ],
    scrollHint: "Scroll om te ontdekken",
    loading: "Ervaring voorbereiden...",
  },
  en: {
    chapters: [
      { title: "Is this really the right time\nto buy?", eyebrow: "FILON gives you the answer." },
      { title: "We compare prices\nfor you." },
      { title: "The best price,\nfound in seconds." },
      { title: "Decide with\ncontext." },
      { title: "Ready to find\nthe right price?", cta: { label: "Explore the catalogue", href: "/recherche" } },
    ],
    scrollHint: "Scroll to explore",
    loading: "Preparing the experience...",
  },
};

function frameSource(index: number, mobile = false) {
  const base = mobile ? MOBILE_FRAME_BASE : DESKTOP_FRAME_BASE;
  return `${base}/${String(index + 1).padStart(3, "0")}.jpg`;
}

function closestFrame(images: Array<HTMLImageElement | null>, target: number, previous: number, totalFrames: number) {
  if (images[target]) return images[target];
  for (let distance = 1; distance < totalFrames; distance += 1) {
    const before = target - distance;
    const after = target + distance;
    if (before >= 0 && images[before]) return images[before];
    if (after < totalFrames && images[after]) return images[after];
  }
  return images[previous];
}

function deviceConnection() {
  if (typeof navigator === "undefined") return null;
  return (navigator as Navigator & { connection?: NetworkConnection }).connection ?? null;
}

/**
 * La même séquence existe sur tous les écrans, mais mobile ne doit jamais
 * être un film desktop rogné et préchargé à 40 Mo. Le portrait lit les
 * frames par échantillonnage, sans couper les côtés, autour du scroll réel.
 */
export function ImmersiveExperience() {
  const { locale } = useLocale();
  const copy = COPY[locale] ?? COPY.fr;
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imagesRef = useRef<Array<HTMLImageElement | null>>(Array(DESKTOP_TOTAL_FRAMES).fill(null));
  const requestedRef = useRef(new Set<number>());
  const prefetchRef = useRef<(frame: number) => void>(() => {});
  const drawRef = useRef<() => void>(() => {});
  const readyRef = useRef(false);
  const paintedRef = useRef(false);
  const lastFrameRef = useRef(0);
  const lastChapterRef = useRef(-1);
  const lastOpacityRef = useRef(-1);
  const rafRef = useRef(0);
  const [ready, setReady] = useState(false);
  const [canvasPainted, setCanvasPainted] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [saveData, setSaveData] = useState(false);
  const [deviceReady, setDeviceReady] = useState(false);
  const [activeChapter, setActiveChapter] = useState(0);
  const [chapterOpacity, setChapterOpacity] = useState(1);

  useEffect(() => {
    const compact = window.matchMedia("(max-width: 768px)");
    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const connection = deviceConnection();
    const update = () => {
      setIsMobile(compact.matches);
      setReducedMotion(motion.matches);
      setSaveData(Boolean(connection?.saveData) || connection?.effectiveType === "slow-2g" || connection?.effectiveType === "2g");
      setDeviceReady(true);
    };
    update();
    compact.addEventListener("change", update);
    motion.addEventListener("change", update);
    connection?.addEventListener?.("change", update);
    return () => {
      compact.removeEventListener("change", update);
      motion.removeEventListener("change", update);
      connection?.removeEventListener?.("change", update);
    };
  }, []);

  const totalFrames = isMobile ? MOBILE_TOTAL_FRAMES : DESKTOP_TOTAL_FRAMES;
  const sequenceKey = isMobile ? "mobile" : "desktop";
  const frameStride = isMobile ? (saveData ? 6 : 2) : 1;
  const initialFrameCount = isMobile ? 4 : 12;
  const prefetchWindow = isMobile ? (saveData ? 12 : 20) : 30;

  // Au changement de format, repartir d’un cache de frames cohérent avec la séquence active.
  useEffect(() => {
    if (!deviceReady) return;
    imagesRef.current = Array(totalFrames).fill(null);
    requestedRef.current.clear();
    readyRef.current = false;
    paintedRef.current = false;
    lastFrameRef.current = 0;
    setReady(false);
    setCanvasPainted(false);
  }, [deviceReady, sequenceKey, totalFrames]);

  useEffect(() => {
    if (!deviceReady) return;
    if (reducedMotion || saveData) {
      // Le poster reste le rendu intentionnel sur connexion lente ou mouvement réduit.
      readyRef.current = true;
      setReady(true);
      return;
    }

    let mounted = true;
    const loadFrame = (index: number) => {
      if (index < 0 || index >= totalFrames || requestedRef.current.has(index)) return;
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
        if (!mounted || index !== 0) return;
        // Le poster reste visible : l'expérience ne bascule jamais sur un écran noir.
        readyRef.current = true;
        setReady(true);
      };
      image.src = frameSource(index, isMobile);
    };

    prefetchRef.current = (frame: number) => {
      const from = Math.max(0, frame - frameStride * 2);
      const to = Math.min(totalFrames - 1, frame + prefetchWindow);
      for (let index = from; index <= to; index += frameStride) loadFrame(index);
    };

    for (let index = 0; index < initialFrameCount * frameStride; index += frameStride) loadFrame(index);

    return () => {
      mounted = false;
      prefetchRef.current = () => {};
    };
  }, [deviceReady, frameStride, initialFrameCount, isMobile, prefetchWindow, reducedMotion, saveData, totalFrames]);

  const draw = useCallback(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas || !ready || reducedMotion || saveData) return;

    const rect = container.getBoundingClientRect();
    const maxScroll = Math.max(1, rect.height - window.innerHeight);
    const progress = Math.max(0, Math.min(1, -rect.top / maxScroll));
    const rawFrame = Math.min(totalFrames - 1, Math.floor(progress * (totalFrames - 1)));
    const targetFrame = isMobile
      ? Math.min(totalFrames - 1, Math.round(rawFrame / frameStride) * frameStride)
      : rawFrame;
    prefetchRef.current(targetFrame);

    const image = closestFrame(imagesRef.current, targetFrame, lastFrameRef.current, totalFrames);
    const context = canvas.getContext("2d", { alpha: false });
    if (context && image) {
      const density = isMobile ? 1 : Math.min(window.devicePixelRatio || 1, 2);
      const width = Math.round(window.innerWidth * density);
      const height = Math.round(window.innerHeight * density);
      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
      }
      // Chaque séquence est composée pour son format : le mobile portrait remplit
      // réellement l’écran, sans les bandes d’un média paysage contenu.
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
    const clampedOpacity = Math.max(0, Math.min(1, opacity));
    if (Math.abs(clampedOpacity - lastOpacityRef.current) > 0.025) {
      lastOpacityRef.current = clampedOpacity;
      setChapterOpacity(clampedOpacity);
    }
  }, [copy.chapters.length, frameStride, isMobile, ready, reducedMotion, saveData, totalFrames]);

  drawRef.current = draw;

  useEffect(() => {
    if (!ready || reducedMotion || saveData) return;
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
  }, [draw, ready, reducedMotion, saveData]);

  const chapter = copy.chapters[activeChapter];
  const scrollHeight = isMobile
    ? (saveData || reducedMotion ? 100 : MOBILE_SCROLL_HEIGHT)
    : DESKTOP_SCROLL_HEIGHT;

  return (
    <div ref={containerRef} className={`fx-imm-wrap${isMobile ? " is-mobile" : ""}`} style={{ height: `${scrollHeight}vh` }}>
      <div className="fx-imm-sticky">
        {/* Poster prioritaire : la première image est déjà adaptée au format du visiteur. */}
        <picture>
          <source media="(max-width: 768px)" srcSet={frameSource(0, true)} />
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img className={`fx-imm-poster${canvasPainted ? " is-hidden" : ""}`} src={frameSource(0)} alt="" aria-hidden="true" fetchPriority="high" decoding="async" />
        </picture>
        <canvas ref={canvasRef} className={`fx-imm-canvas${canvasPainted ? " is-visible" : ""}`} aria-hidden="true" />
        <div className="fx-imm-overlay" />
        <div className="fx-imm-chapter" style={{ opacity: chapterOpacity }}>
          {chapter.eyebrow && <p className="fx-imm-eyebrow">{chapter.eyebrow}</p>}
          <h2 className="fx-imm-titre" aria-live="polite">{chapter.title}</h2>
          {chapter.cta && <a href={chapter.cta.href} className="fx-imm-cta">{chapter.cta.label}</a>}
        </div>
        <div className="fx-imm-search"><HeroSearch /></div>
        {!ready && !saveData ? <div className="fx-imm-loading">{copy.loading}</div> : !saveData && !reducedMotion && activeChapter === 0 && chapterOpacity > 0.65 ? <div className="fx-imm-scroll-hint"><span>{copy.scrollHint}</span><svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M8 3v10M4 9l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /></svg></div> : null}
      </div>
    </div>
  );
}
