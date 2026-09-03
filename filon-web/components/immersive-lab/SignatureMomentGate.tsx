"use client";

import dynamic from "next/dynamic";
import type { CSSProperties } from "react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { ImmersiveExactProductProof } from "@/lib/immersive-proof";
import { useAdaptiveFrameBudget } from "./ImmersiveRuntime";
import styles from "./signature-commerce.module.css";

const SignatureCommerceCanvas = dynamic(
  () => import("./SignatureCommerceCanvas").then((module) => module.SignatureCommerceCanvas),
  { ssr: false, loading: () => null },
);

const MOMENTS = [
  { id: "market", code: "01", label: "Champ marchand", at: 0.06 },
  { id: "identity", code: "02", label: "Aperture d’identité", at: 0.34 },
  { id: "proof", code: "03", label: "Recuit de preuve", at: 0.62 },
  { id: "decision", code: "04", label: "Sceau de décision", at: 0.92 },
] as const;

const DURATION_MS = 10_000;

type Capability = "pending" | "webgl" | "fallback";

function shotFromProgress(progress: number) {
  if (progress < 0.24) return 0;
  if (progress < 0.5) return 1;
  if (progress < 0.77) return 2;
  return 3;
}

function StaticPhysicalFallback({ product, progress }: { product: ImmersiveExactProductProof | null; progress: number }) {
  return (
    <div className={styles.staticWorld} style={{ "--signature-progress": progress } as CSSProperties} aria-hidden="true">
      <div className={styles.staticGrid} />
      <div className={styles.staticFragments}>
        {Array.from({ length: product ? Math.min(8, product.offers.length) : 4 }, (_, index) => <i key={index} />)}
      </div>
      <div className={styles.staticCore} data-proven={Boolean(product)}>
        {product?.image ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={product.image} alt="" decoding="async" loading="lazy" fetchPriority="low" />
        ) : <span>?</span>}
      </div>
      <div className={styles.staticSeal}><i /><i /><i /></div>
    </div>
  );
}

export function SignatureMomentGate({ product, reduced }: { product: ImmersiveExactProductProof | null; reduced: boolean }) {
  const rootRef = useRef<HTMLElement | null>(null);
  const frameRef = useRef(0);
  const startedAtRef = useRef(0);
  const hasAutoPlayedRef = useRef(false);
  const [near, setNear] = useState(false);
  const [visible, setVisible] = useState(false);
  const [capability, setCapability] = useState<Capability>("pending");
  const [compact, setCompact] = useState(false);
  const [progress, setProgress] = useState(reduced ? 1 : 0);
  const [playing, setPlaying] = useState(false);
  const failRuntime = useCallback(() => setCapability("fallback"), []);
  const markRuntimeReady = useCallback(() => {
    performance.mark("filon-immersive-init-ready");
  }, []);
  const { measuring, quality } = useAdaptiveFrameBudget(capability === "webgl" && visible, failRuntime);
  const shot = shotFromProgress(progress);
  const moment = MOMENTS[shot];

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;
    const observer = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting)) {
        setNear(true);
        observer.disconnect();
      }
    }, { rootMargin: "500px 0px" });
    observer.observe(root);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;
    const observer = new IntersectionObserver(([entry]) => {
      setVisible(Boolean(entry?.isIntersecting));
    }, { threshold: 0.02 });
    observer.observe(root);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const media = window.matchMedia("(max-width: 820px)");
    const update = () => setCompact(media.matches);
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    if (!near || reduced) {
      if (reduced) setCapability("fallback");
      return;
    }
    const connection = (navigator as Navigator & { connection?: { saveData?: boolean; effectiveType?: string }; deviceMemory?: number }).connection;
    const memory = (navigator as Navigator & { deviceMemory?: number }).deviceMemory;
    const constrained = connection?.saveData
      || connection?.effectiveType === "slow-2g"
      || connection?.effectiveType === "2g"
      || (typeof memory === "number" && memory < 4);
    if (constrained) {
      setCapability("fallback");
      return;
    }
    try {
      const canvas = document.createElement("canvas");
      const context = canvas.getContext("webgl2", { failIfMajorPerformanceCaveat: true })
        || canvas.getContext("webgl", { failIfMajorPerformanceCaveat: true })
        || canvas.getContext("webgl2")
        || canvas.getContext("webgl");
      if (context) {
        performance.clearMarks("filon-immersive-init-start");
        performance.clearMarks("filon-immersive-init-ready");
        performance.mark("filon-immersive-init-start");
      }
      setCapability(context ? "webgl" : "fallback");
      context?.getExtension("WEBGL_lose_context")?.loseContext();
    } catch {
      setCapability("fallback");
    }
  }, [near, reduced]);

  const stop = useCallback(() => {
    cancelAnimationFrame(frameRef.current);
    setPlaying(false);
  }, []);

  useEffect(() => {
    if (!visible) stop();
  }, [stop, visible]);

  const tick = useCallback((now: number) => {
    const next = Math.min(1, (now - startedAtRef.current) / DURATION_MS);
    setProgress(next);
    if (next < 1) frameRef.current = requestAnimationFrame(tick);
    else setPlaying(false);
  }, []);

  const play = useCallback(() => {
    stop();
    if (reduced) {
      setProgress(1);
      return;
    }
    setProgress(0);
    setPlaying(true);
    startedAtRef.current = performance.now();
    frameRef.current = requestAnimationFrame(tick);
  }, [reduced, stop, tick]);

  useEffect(() => () => cancelAnimationFrame(frameRef.current), []);
  useEffect(() => {
    if (near && visible && capability === "webgl" && !reduced && !hasAutoPlayedRef.current) {
      hasAutoPlayedRef.current = true;
      play();
    }
  }, [capability, near, play, reduced, visible]);
  useEffect(() => {
    if (reduced) {
      stop();
      setProgress(1);
    }
  }, [reduced, stop]);

  const productLabel = useMemo(
    () => product ? [product.brand, product.name].filter(Boolean).join(" · ") : "Identité insuffisante",
    [product],
  );

  return (
    <section ref={rootRef} className={styles.signature} aria-labelledby="lab-signature-title">
      <header className={styles.heading}>
        <p>ESCALADE IMMERSIVE / SIGNATURE FILON</p>
        <h2 id="lab-signature-title">Le commerce devient un espace physique.</h2>
        <div>
          <span>CAMÉRA CAUSALE</span>
          <span>MATIÈRE DE PREUVE</span>
          <span>OBJET CONTINU</span>
        </div>
      </header>

      <div
        className={styles.stage}
        data-shot={shot}
        data-renderer={capability}
        data-quality={quality}
        data-proof={product ? "qualified" : "unknown"}
      >
        {near && capability === "webgl" ? (
          <SignatureCommerceCanvas
            compact={compact}
            offerCount={product?.offers.length ?? 0}
            playing={visible && (playing || measuring)}
            product={product ? { image: product.image, name: productLabel } : null}
            progress={progress}
            quality={quality}
            onReady={markRuntimeReady}
          />
        ) : <StaticPhysicalFallback product={product} progress={progress} />}

        <div className={styles.readout}>
          <span>PLAN {moment.code} / {capability === "webgl" ? "VOLUME TEMPS RÉEL" : "TABLEAU STATIQUE"}</span>
          <h3>{moment.label}</h3>
          <p>{shot === 0
            ? "Une offre n’est encore qu’un fragment autour d’un produit à résoudre."
            : shot === 1
              ? "Le même produit survit au bruit pendant que l’identité devient nette."
              : shot === 2
                ? "Les observations admissibles changent de matière et deviennent preuves."
                : "Le marché se stabilise en un plan de décision, sans fabriquer de verdict."}</p>
        </div>

        <div className={styles.truthPlate}>
          <span>{product ? "PREUVE EXACTE COURANTE" : "ABSTENTION"}</span>
          <strong>{productLabel}</strong>
          <small>{product
            ? `${product.offers.length} offres · ${product.merchants} marchands · EAN ${product.ean}`
            : "Aucun produit, prix ou marchand synthétique n’entre dans la scène."}</small>
        </div>
      </div>

      <div className={styles.transport}>
        <div className={styles.momentButtons} role="group" aria-label="Plans de la séquence signature">
          {MOMENTS.map((item, index) => (
            <button
              key={item.id}
              type="button"
              aria-pressed={shot === index}
              onClick={() => { stop(); setProgress(item.at); }}
            ><span>{item.code}</span>{item.label}</button>
          ))}
        </div>
        <button className={styles.play} type="button" onClick={playing ? stop : play} disabled={reduced}>
          {reduced ? "Mouvement réduit · histoire complète" : playing ? "Pause" : "Rejouer la séquence"}
        </button>
        <label>
          <span>Progression caméra</span>
          <input
            type="range"
            min="0"
            max="100"
            value={Math.round(progress * 100)}
            aria-valuetext={`${moment.label}, ${Math.round(progress * 100)} %`}
            onChange={(event) => { stop(); setProgress(Number(event.target.value) / 100); }}
          />
        </label>
      </div>

      <div className={styles.semanticLedger} aria-label="Lecture accessible de la séquence signature">
        <article><span>01 / WIDE</span><h3>Marché</h3><p>Le champ ne contient que les offres qualifiées du produit exact.</p></article>
        <article><span>02 / MACRO</span><h3>Identité</h3><p>L’objet central reste le même pendant le changement de point de vue.</p></article>
        <article><span>03 / ORBIT</span><h3>Preuve</h3><p>La matière ne se stabilise que si identité, devise et fraîcheur sont admissibles.</p></article>
        <article><span>04 / ORTHOGRAPHIQUE</span><h3>Décision</h3><p>La scène s’arrête sur des faits ; elle n’invente ni confiance ni recommandation.</p></article>
      </div>
    </section>
  );
}
