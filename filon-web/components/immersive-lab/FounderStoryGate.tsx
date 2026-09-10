"use client";

import dynamic from "next/dynamic";
import type { CSSProperties } from "react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ProductJourneyLink } from "@/components/experience/ProductJourneyLink";
import {
  ImmersiveBoundary,
  supportsImmersiveVolume,
  useAdaptiveFrameBudget,
} from "@/components/experience/signature/ImmersiveRuntime";
import { formatSupportedMoney } from "@/lib/currency";
import type { ImmersiveExactProductProof } from "@/lib/immersive-proof";
import styles from "./founder-story.module.css";

const FounderStoryCanvas = dynamic(
  () => import("./FounderStoryCanvas").then((module) => module.FounderStoryCanvas),
  { ssr: false, loading: () => null },
);

const DURATION_MS = 16_000;
const BEATS = ["Chercher", "Entrer", "Distinguer", "Vérifier", "Écarter", "Comparer"] as const;

type Capability = "pending" | "webgl" | "fallback";

function beatFromProgress(progress: number) {
  if (progress < 0.17) return 0;
  if (progress < 0.32) return 1;
  if (progress < 0.53) return 2;
  if (progress < 0.72) return 3;
  if (progress < 0.88) return 4;
  return 5;
}

function StaticStory({ product, progress }: { product: ImmersiveExactProductProof | null; progress: number }) {
  return (
    <div className={styles.staticStory} style={{ "--story-progress": progress } as CSSProperties} aria-hidden="true">
      <div className={styles.staticRoom} />
      <div className={styles.staticLaptop}>
        {product?.image ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={product.image} alt="" decoding="async" fetchPriority="low" />
        ) : <span>?</span>}
      </div>
      <div className={styles.staticCity}>
        {Array.from({ length: 6 }, (_, index) => <i key={index} />)}
      </div>
      <div className={styles.staticProduct}>
        {product?.image ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={product.image} alt="" decoding="async" fetchPriority="low" />
        ) : <span>?</span>}
      </div>
    </div>
  );
}

export function FounderStoryGate({ product, reduced }: { product: ImmersiveExactProductProof | null; reduced: boolean }) {
  const rootRef = useRef<HTMLElement | null>(null);
  const stageRef = useRef<HTMLDivElement | null>(null);
  const frameRef = useRef(0);
  const startedAtRef = useRef(0);
  const hasPlayedRef = useRef(false);
  const [near, setNear] = useState(false);
  const [visible, setVisible] = useState(false);
  const [compact, setCompact] = useState(false);
  const [capability, setCapability] = useState<Capability>("pending");
  const [progress, setProgress] = useState(reduced ? 1 : 0);
  const [playing, setPlaying] = useState(false);
  const failRuntime = useCallback(() => setCapability("fallback"), []);
  const { measuring, quality } = useAdaptiveFrameBudget(capability === "webgl" && visible, failRuntime);
  const beat = beatFromProgress(progress);

  useEffect(() => {
    const root = rootRef.current;
    const stage = stageRef.current;
    if (!root || !stage) return;
    const proximity = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting)) {
        setNear(true);
        proximity.disconnect();
      }
    }, { rootMargin: "420px 0px" });
    const visibility = new IntersectionObserver(
      ([entry]) => setVisible(Boolean(entry?.isIntersecting && entry.intersectionRatio >= 0.45)),
      { threshold: [0, 0.45] },
    );
    proximity.observe(root);
    visibility.observe(stage);
    return () => {
      proximity.disconnect();
      visibility.disconnect();
    };
  }, []);

  useEffect(() => {
    const media = window.matchMedia("(max-width: 820px)");
    const update = () => setCompact(media.matches);
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    if (!near || reduced || !product?.textureImage) {
      if (reduced || (near && !product?.textureImage)) setCapability("fallback");
      return;
    }
    if (!supportsImmersiveVolume()) {
      setCapability("fallback");
      return;
    }
    performance.clearMarks("filon-immersive-init-start");
    performance.clearMarks("filon-immersive-init-ready");
    performance.mark("filon-immersive-init-start");
    setCapability("webgl");
  }, [near, product?.textureImage, reduced]);

  const stop = useCallback(() => {
    cancelAnimationFrame(frameRef.current);
    setPlaying(false);
  }, []);

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
    if (!visible) stop();
  }, [stop, visible]);
  useEffect(() => {
    if (near && visible && capability === "webgl" && !reduced && !hasPlayedRef.current) {
      hasPlayedRef.current = true;
      play();
    }
  }, [capability, near, play, reduced, visible]);
  useEffect(() => {
    if (reduced) {
      stop();
      setProgress(1);
    }
  }, [reduced, stop]);

  const productName = useMemo(
    () => product ? [product.brand, product.name].filter(Boolean).join(" ") : "Produit non démontré",
    [product],
  );
  const priceLow = product ? formatSupportedMoney(product.priceMin, product.currency, "fr") : null;
  const priceHigh = product ? formatSupportedMoney(product.priceMax, product.currency, "fr") : null;
  const line = [
    "Vous cherchez un produit.",
    "Le marché s’ouvre.",
    "Les offres se ressemblent. Pas toujours les produits.",
    "FILON vérifie chaque correspondance.",
    "Les mauvaises pistes s’effacent.",
    "Il ne reste que ce que vous pouvez vraiment comparer.",
  ][beat];

  return (
    <section ref={rootRef} className={styles.story} aria-labelledby="founder-story-title">
      <a className={styles.skip} href="#p19-lab-after-journey">Passer l’expérience</a>
      <div ref={stageRef} className={styles.stage} data-beat={beat} data-renderer={capability} data-quality={quality}>
        {near && capability === "webgl" && product?.textureImage ? (
          <ImmersiveBoundary onFailure={failRuntime}>
            <FounderStoryCanvas
              compact={compact}
              offerCount={product.offers.length}
              onFailure={failRuntime}
              onReady={() => performance.mark("filon-immersive-init-ready")}
              playing={visible && (playing || measuring)}
              product={{ image: product.textureImage, name: productName }}
              progress={progress}
              quality={quality}
            />
          </ImmersiveBoundary>
        ) : <StaticStory product={product} progress={progress} />}

        <header className={styles.intro}>
          <p>Une seule recherche.</p>
          <h1 id="founder-story-title">Du marché entier<br />à votre meilleur choix.</h1>
        </header>

        <div className={styles.storyLine} aria-live="polite">
          <p>{line}</p>
        </div>

        <div className={styles.finalCard} aria-hidden={beat < 5}>
          <span>{product ? "Comparaison vérifiée" : "Preuve insuffisante"}</span>
          <div className={styles.finalProduct}>
            {product?.image ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={product.image} alt="" decoding="async" fetchPriority="low" />
            ) : <div className={styles.unknown}>?</div>}
            <div>
              <h2>{productName}</h2>
              <p>{product && priceLow && priceHigh
                ? `${priceLow} — ${priceHigh} · ${product.merchants} marchands`
                : "FILON ne fabrique ni prix ni disponibilité."}</p>
            </div>
          </div>
          {product ? (
            <ProductJourneyLink href={`/produits/${encodeURIComponent(product.ean)}`} image={product.image} label={product.name}>
              Voir la comparaison
            </ProductJourneyLink>
          ) : <a href="/recherche/">Faire une recherche</a>}
        </div>

        <nav className={styles.actions} aria-label="Actions de la séquence">
          <a href="/recherche/">Rechercher</a>
          <button type="button" onClick={() => { stop(); setProgress(1); }}>Voir le résultat</button>
        </nav>

        <div className={styles.transport}>
          <button type="button" onClick={playing ? stop : play} disabled={reduced}>
            {reduced ? "Image fixe" : playing ? "Pause" : progress >= 1 ? "Rejouer" : "Continuer"}
          </button>
          <label>
            <span>Progression de l’histoire</span>
          <input
            type="range"
            min="0"
            max="100"
            value={Math.round(progress * 100)}
              aria-valuetext={`${BEATS[beat]}, ${Math.round(progress * 100)} %`}
            onChange={(event) => { stop(); setProgress(Number(event.target.value) / 100); }}
          />
          </label>
          <span className={styles.progressValue} aria-hidden="true">{String(beat + 1).padStart(2, "0")} / 06</span>
        </div>
      </div>

      <p className={styles.accessibleStory}>
        Une recherche ouvre un marché inspiré de Bruxelles. Le même produit apparaît chez plusieurs marchands. FILON sépare les variantes incompatibles, retire les offres qui ne peuvent pas être prouvées et conserve une comparaison vérifiable. La scène se transforme ensuite en interface utilisable.
      </p>
    </section>
  );
}
