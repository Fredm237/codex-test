"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useLocale } from "@/lib/i18n";
import { CinematicOverlay } from "./CinematicOverlay";
import { CinematicSequenceRenderer } from "./CinematicSequenceRenderer";
import { resolveTimeline } from "./engine/timeline";
import { filonHomeScene } from "./scenes/filon-home";

function networkSaveData() {
  if (typeof navigator === "undefined") return false;
  const connection = (navigator as Navigator & { connection?: { saveData?: boolean; effectiveType?: string } }).connection;
  return Boolean(connection?.saveData) || connection?.effectiveType === "slow-2g" || connection?.effectiveType === "2g";
}

/**
 * Public integration boundary for the cinematic layer. The homepage, catalogue,
 * assistant and search remain fully usable if this component is disabled or if
 * the visitor receives the static accessibility fallback.
 */
export function CinematicExperience() {
  const { locale } = useLocale();
  const containerRef = useRef<HTMLElement>(null);
  const rafRef = useRef(0);
  const [progress, setProgress] = useState(0);
  const [mobile, setMobile] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);
  const [saveData, setSaveData] = useState(false);

  useEffect(() => {
    const media = window.matchMedia("(max-width: 768px)");
    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => {
      setMobile(media.matches);
      setReducedMotion(motion.matches);
      setSaveData(networkSaveData());
    };
    update();
    media.addEventListener("change", update);
    motion.addEventListener("change", update);
    return () => {
      media.removeEventListener("change", update);
      motion.removeEventListener("change", update);
    };
  }, []);

  useEffect(() => {
    if (reducedMotion || saveData) return;
    const updateProgress = () => {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = requestAnimationFrame(() => {
        const element = containerRef.current;
        if (!element) return;
        const rect = element.getBoundingClientRect();
        const max = Math.max(1, rect.height - window.innerHeight);
        setProgress(Math.max(0, Math.min(1, -rect.top / max)));
      });
    };
    updateProgress();
    window.addEventListener("scroll", updateProgress, { passive: true });
    window.addEventListener("resize", updateProgress);
    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener("scroll", updateProgress);
      window.removeEventListener("resize", updateProgress);
    };
  }, [reducedMotion, saveData]);

  const sequence = mobile ? filonHomeScene.mobile : filonHomeScene.desktop;
  const timeline = useMemo(() => resolveTimeline(filonHomeScene, progress), [progress]);
  // Stabilisation publique : la scène reste visible, mais aucun scroll narratif
  // incomplet ne peut consommer l’accueil avant la reconstruction frame-par-frame.
  const fallback = true;
  const height = 100;

  const skip = () => {
    const element = containerRef.current;
    if (!element) return;
    window.scrollTo({ top: element.offsetTop + element.offsetHeight - window.innerHeight, behavior: "smooth" });
  };

  return (
    <section ref={containerRef} className={`ce-experience${mobile ? " is-mobile" : ""}${fallback ? " is-static" : ""}`} style={{ height: `${height}vh` }}>
      <div className="ce-sticky">
        <CinematicSequenceRenderer sequence={sequence} frameProgress={timeline.frameProgress} cameraProgress={timeline.progress} reducedMotion={fallback} className="ce-renderer" />
        <div className="ce-atmosphere" aria-hidden="true" />
        <CinematicOverlay locale={locale} timeline={timeline} onSkip={skip} />
      </div>
    </section>
  );
}
