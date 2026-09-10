"use client";

import dynamic from "next/dynamic";
import { createPortal } from "react-dom";
import { Component, useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import type { WorldMode } from "./SpatialShell";
import { useLocale } from "@/lib/i18n";

const Scene = dynamic(() => import("./FilonSculpture"), { ssr: false });
class SceneBoundary extends Component<{ children: ReactNode; fallback: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() { return this.state.failed ? this.props.fallback : this.props.children; }
}

export function World({ mode = "home" }: { mode?: WorldMode }) {
  const { locale } = useLocale();
  const host = useRef<HTMLDivElement>(null);
  const [enabled, setEnabled] = useState(false);
  const [visible, setVisible] = useState(true);
  const [paused, setPaused] = useState(false);
  const [reduced, setReduced] = useState(false);
  const [failed, setFailed] = useState(false);
  const [texture, setTexture] = useState<string|null>(null);
  const [angle, setAngle] = useState(false);
  useEffect(()=>{
    const receive=(event:Event)=>setTexture((event as CustomEvent<{texture:string|null}>).detail?.texture ?? null);
    window.addEventListener("filon:spatial-product",receive);
    return()=>window.removeEventListener("filon:spatial-product",receive);
  },[]);
  const onFailure = useCallback(() => setFailed(true), []);
  useEffect(() => {
    const media = matchMedia("(prefers-reduced-motion: reduce)");
    const saveData = (navigator as Navigator & { connection?: { saveData?: boolean } }).connection?.saveData;
    setEnabled(!saveData);
    const updateMotion = () => setReduced(media.matches);
    updateMotion();
    media.addEventListener("change", updateMotion);
    const el = host.current;
    let inView = true;
    const update = () => setVisible(inView && !document.hidden);
    const observer = new IntersectionObserver(([entry]) => { inView = entry.isIntersecting; update(); }, { rootMargin: "80px" });
    if (el) observer.observe(el);
    document.addEventListener("visibilitychange", update);
    return () => { observer.disconnect(); media.removeEventListener("change", updateMotion); document.removeEventListener("visibilitychange", update); };
  }, []);
  const fallback = <div className="fn-world-fallback" aria-hidden="true">F<span>↗</span></div>;
  const label = locale === "fr" ? (paused ? "Animer la 3D" : "Mettre la 3D en pause") : locale === "nl" ? (paused ? "3D afspelen" : "3D pauzeren") : (paused ? "Play 3D" : "Pause 3D");
  return (
    <div className="fn-world" ref={host}>
      <div className="fn-world-object" aria-hidden="true">
        {enabled && !failed ? <SceneBoundary fallback={fallback}><Scene active={visible && !paused && !reduced} onFailure={onFailure} mode={mode} texture={mode==="product"?texture:null} angle={angle} /></SceneBoundary> : fallback}
      </div>
      <div className="fn-world-coordinate"><span>F / 01</span><span>FILON EXPLORER</span></div>
      {enabled && !failed && createPortal(<div className="fn-scene-controls">
        <button onClick={()=>setAngle(!angle)} aria-pressed={angle}>{locale==="fr"?"Changer de vue":locale==="nl"?"Andere weergave":"Change view"} ↻</button>
        {!reduced && <button onClick={()=>setPaused(!paused)} aria-label={label} aria-pressed={paused}>{paused ? "▶" : "Ⅱ"}</button>}
      </div>,document.body)}
    </div>
  );
}
