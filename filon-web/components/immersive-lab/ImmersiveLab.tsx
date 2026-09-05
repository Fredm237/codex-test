"use client";

import { useEffect, useState } from "react";
import type { ImmersiveExactProductProof } from "@/lib/immersive-proof";
import type { Proof } from "@/lib/proof";
import { FounderStoryGate } from "./FounderStoryGate";
import styles from "./immersive-lab.module.css";

type LabMetrics = {
  cls: number;
  immersiveLongestTask: number | null;
  inp: number | null;
  lcp: number | null;
  longestTask: number;
  transferKb: number;
};

function useReducedExperience() {
  const [reduced, setReduced] = useState(true);
  useEffect(() => {
    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const connection = (navigator as Navigator & { connection?: { saveData?: boolean; effectiveType?: string } }).connection;
    const update = () => setReduced(
      motion.matches || Boolean(connection?.saveData)
      || connection?.effectiveType === "slow-2g" || connection?.effectiveType === "2g",
    );
    update();
    motion.addEventListener("change", update);
    return () => motion.removeEventListener("change", update);
  }, []);
  return reduced;
}

function SilentTelemetry() {
  const [metrics, setMetrics] = useState<LabMetrics | null>(null);
  useEffect(() => {
    let lcp: number | null = null;
    let cls = 0;
    let inp: number | null = null;
    let longestTask = 0;
    const observers: PerformanceObserver[] = [];
    const observe = (
      type: string,
      onEntries: (entries: PerformanceEntry[]) => void,
      options: PerformanceObserverInit = { type, buffered: true },
    ) => {
      try {
        const observer = new PerformanceObserver((list) => onEntries(list.getEntries()));
        observer.observe(options);
        observers.push(observer);
      } catch {
        // Une mesure non disponible reste inconnue et n'entre pas dans le récit.
      }
    };
    observe("largest-contentful-paint", (entries) => { const last = entries.at(-1); if (last) lcp = last.startTime; });
    observe("layout-shift", (entries) => {
      for (const entry of entries as Array<PerformanceEntry & { hadRecentInput?: boolean; value?: number }>) {
        if (!entry.hadRecentInput && Number.isFinite(entry.value)) cls += entry.value ?? 0;
      }
    });
    observe("longtask", (entries) => { for (const entry of entries) longestTask = Math.max(longestTask, entry.duration); });
    observe("event", (entries) => { for (const entry of entries) inp = Math.max(inp ?? 0, entry.duration); }, { type: "event", buffered: true, durationThreshold: 40 } as PerformanceObserverInit);
    const sample = () => {
      const resources = performance.getEntriesByType("resource") as PerformanceResourceTiming[];
      const start = performance.getEntriesByName("filon-immersive-init-start").at(-1);
      const ready = performance.getEntriesByName("filon-immersive-init-ready").at(-1);
      const immersiveLongestTask = start && ready
        ? Math.max(0, ...performance.getEntriesByType("longtask")
          .filter((entry) => entry.startTime >= start.startTime && entry.startTime <= ready.startTime)
          .map((entry) => entry.duration))
        : null;
      setMetrics({
        cls: Number(cls.toFixed(4)),
        immersiveLongestTask: immersiveLongestTask === null ? null : Math.round(immersiveLongestTask),
        inp: inp === null ? null : Math.round(inp),
        lcp: lcp === null ? null : Math.round(lcp),
        longestTask: Math.round(longestTask),
        transferKb: Math.round(resources.reduce((total, entry) => total + (entry.transferSize || 0), 0) / 1024),
      });
    };
    const timer = window.setTimeout(sample, 2_600);
    const interval = window.setInterval(sample, 1_500);
    return () => {
      window.clearTimeout(timer);
      window.clearInterval(interval);
      observers.forEach((observer) => observer.disconnect());
    };
  }, []);

  return (
    <output className={styles.srOnly} data-lab-metrics-ready={metrics !== null} aria-hidden="true">
      <span data-metric="lcp">{metrics?.lcp ?? "unknown"}</span>
      <span data-metric="cls">{metrics?.cls ?? "unknown"}</span>
      <span data-metric="inp">{metrics?.inp ?? "unknown"}</span>
      <span data-metric="longtask">{metrics?.longestTask ?? "unknown"}</span>
      <span data-metric="immersive-longtask">{metrics?.immersiveLongestTask ?? "unknown"}</span>
      <span data-metric="transfer">{metrics?.transferKb ?? "unknown"}</span>
    </output>
  );
}

export function ImmersiveLab({ proof, exactProduct }: { proof: Proof | null; exactProduct: ImmersiveExactProductProof | null }) {
  const reduced = useReducedExperience();
  return (
    <main
      className={`${styles.page} p19-immersive-lab`}
      data-proof-state={proof ? "available" : "unknown"}
    >
      <FounderStoryGate product={exactProduct} reduced={reduced} />
      <div id="p19-lab-after-journey" className={styles.srOnly} tabIndex={-1}>
        Fin de l’expérience. La recherche et la fiche produit restent accessibles dans la scène.
      </div>
      <SilentTelemetry />
    </main>
  );
}
