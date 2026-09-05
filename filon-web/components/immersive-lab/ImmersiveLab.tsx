"use client";

import { useEffect, useState } from "react";
import { ProductJourneyLink } from "@/components/experience/ProductJourneyLink";
import { formatSupportedMoney } from "@/lib/currency";
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

function formatObservation(value: string): string {
  try {
    return new Intl.DateTimeFormat("fr-BE", {
      dateStyle: "medium", timeStyle: "short", timeZone: "Europe/Brussels",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

function EvidenceLedger({ product }: { product: ImmersiveExactProductProof | null }) {
  const low = product ? formatSupportedMoney(product.priceMin, product.currency, "fr") : null;
  const high = product ? formatSupportedMoney(product.priceMax, product.currency, "fr") : null;
  return (
    <section className={styles.evidence} aria-labelledby="lab-evidence-title">
      <header>
        <p className={styles.eyebrow}>La scène repose sur ces faits</p>
        <h2 id="lab-evidence-title">Ce que le mouvement ne change jamais.</h2>
        <p>Le produit, les prix, les marchands et l’heure d’observation viennent de la même preuve serveur.</p>
      </header>
      {product ? (
        <div className={styles.evidenceGrid}>
          <article className={styles.productCard}>
            {product.image ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={product.image} alt={product.name} decoding="async" loading="lazy" fetchPriority="low" />
            ) : <div className={styles.unknownProduct} aria-label="Image indisponible">?</div>}
            <div>
              <span>Produit exact</span>
              <h3>{[product.brand, product.name].filter(Boolean).join(" · ")}</h3>
              <p>EAN {product.ean}</p>
              <p>Observé le {formatObservation(product.latestObservedAt)}</p>
              <ProductJourneyLink href={`/produits/${encodeURIComponent(product.ean)}`} image={product.image} label={product.name}>
                Ouvrir la fiche réelle
              </ProductJourneyLink>
            </div>
          </article>
          <div className={styles.priceCard}>
            <span>Comparaison admissible</span>
            <strong>{low && high ? `${low} — ${high}` : "Prix non démontré"}</strong>
            <small>{product.offers.length} offres · {product.merchants} marchands</small>
          </div>
          <div className={styles.offerList} role="list" aria-label="Offres utilisées dans la scène">
            {product.offers.map((offer) => (
              <div key={offer.id} role="listitem">
                <span><b>{offer.merchant}</b><small>{formatObservation(offer.observedAt)}</small></span>
                <strong>{formatSupportedMoney(offer.price, offer.currency, "fr") ?? "Prix inconnu"}</strong>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <p className={styles.failClosed}>Aucun produit n’a franchi les vérifications d’identité, de devise, de fraîcheur et de pluralité marchande. FILON s’abstient.</p>
      )}
    </section>
  );
}

function LabTelemetry() {
  const [metrics, setMetrics] = useState<LabMetrics | null>(null);
  useEffect(() => {
    let lcp: number | null = null;
    let cls = 0;
    let inp: number | null = null;
    let longestTask = 0;
    const observers: PerformanceObserver[] = [];
    const observe = (type: string, onEntries: (entries: PerformanceEntry[]) => void, options: PerformanceObserverInit = { type, buffered: true }) => {
      try {
        const observer = new PerformanceObserver((list) => onEntries(list.getEntries()));
        observer.observe(options);
        observers.push(observer);
      } catch {
        // Une mesure absente reste inconnue.
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
        cls: Number(cls.toFixed(4)), immersiveLongestTask: immersiveLongestTask === null ? null : Math.round(immersiveLongestTask),
        inp: inp === null ? null : Math.round(inp), lcp: lcp === null ? null : Math.round(lcp),
        longestTask: Math.round(longestTask),
        transferKb: Math.round(resources.reduce((total, entry) => total + (entry.transferSize || 0), 0) / 1024),
      });
    };
    const timer = window.setTimeout(sample, 2_600);
    const interval = window.setInterval(sample, 1_500);
    return () => {
      window.clearTimeout(timer); window.clearInterval(interval);
      observers.forEach((observer) => observer.disconnect());
    };
  }, []);
  const value = (metric: number | null | undefined, suffix: string) => metric === null || metric === undefined ? "non mesuré" : `${metric}${suffix}`;
  return (
    <section className={styles.telemetry} aria-labelledby="lab-telemetry-title">
      <div><p className={styles.eyebrow}>Contrôle du prototype</p><h2 id="lab-telemetry-title">La beauté reste sous budget.</h2></div>
      <dl data-lab-metrics-ready={metrics !== null}>
        <div><dt>LCP</dt><dd data-metric="lcp">{value(metrics?.lcp, " ms")}</dd></div>
        <div><dt>CLS</dt><dd data-metric="cls">{metrics ? metrics.cls : "non mesuré"}</dd></div>
        <div><dt>Interaction</dt><dd data-metric="inp">{value(metrics?.inp, " ms")}</dd></div>
        <div><dt>Tâche longue</dt><dd data-metric="longtask">{value(metrics?.longestTask, " ms")}</dd></div>
        <div><dt>Initialisation 3D</dt><dd data-metric="immersive-longtask">{value(metrics?.immersiveLongestTask, " ms")}</dd></div>
        <div><dt>Transfert</dt><dd data-metric="transfer">{value(metrics?.transferKb, " Ko")}</dd></div>
      </dl>
    </section>
  );
}

export function ImmersiveLab({ proof, exactProduct }: { proof: Proof | null; exactProduct: ImmersiveExactProductProof | null }) {
  const reduced = useReducedExperience();
  return (
    <main className={`${styles.page} p19-immersive-lab`}>
      <FounderStoryGate product={exactProduct} reduced={reduced} />
      <div id="p19-lab-after-journey" tabIndex={-1}>
        <EvidenceLedger product={exactProduct} />
        <section className={styles.boundaries} aria-labelledby="lab-boundaries-title">
          <p className={styles.eyebrow}>Ce que FILON garantit</p>
          <h2 id="lab-boundaries-title">Le spectacle ne dépasse jamais la preuve.</h2>
          <div>
            <article><span>01</span><h3>Un produit réel</h3><p>La scène n’apparaît que si une identité exacte peut être conservée du début à la fin.</p></article>
            <article><span>02</span><h3>Des prix comparables</h3><p>Une devise inconnue, une offre périmée ou une variante incompatible disparaît au lieu d’être arrangée.</p></article>
            <article><span>03</span><h3>Une sortie complète</h3><p>Sans 3D, avec mouvement réduit ou sur appareil contraint, le produit et les actions restent accessibles. {proof ? `${proof.stats.offers.toLocaleString("fr-BE")} offres alimentent actuellement la preuve agrégée.` : "Les agrégats restent inconnus si l’API est indisponible."}</p></article>
          </div>
        </section>
        <LabTelemetry />
      </div>
    </main>
  );
}
