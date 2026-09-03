"use client";

import dynamic from "next/dynamic";
import { Component, type ErrorInfo, type ReactNode, useEffect, useRef, useState } from "react";
import type { ProofProduct } from "@/lib/proof";
import styles from "./web-experience.module.css";

const SignatureCommerceCanvas = dynamic(
  () => import("@/components/immersive-lab/SignatureCommerceCanvas")
    .then((module) => module.SignatureCommerceCanvas),
  { ssr: false, loading: () => null },
);

export type HomeVolumeState = "pending" | "webgl" | "fallback";

type Props = {
  onStateChange: (state: HomeVolumeState) => void;
  product: ProofProduct | null;
  progress: number;
  reduced: boolean;
};

type BoundaryProps = {
  children: ReactNode;
  onFailure: () => void;
};

type BoundaryState = { failed: boolean };

class ImmersiveBoundary extends Component<BoundaryProps, BoundaryState> {
  state: BoundaryState = { failed: false };

  static getDerivedStateFromError(): BoundaryState {
    return { failed: true };
  }

  componentDidCatch(_error: Error, _info: ErrorInfo) {
    this.props.onFailure();
  }

  render() {
    return this.state.failed ? null : this.props.children;
  }
}

function supportsHomeVolume() {
  const navigatorWithSignals = navigator as Navigator & {
    connection?: { effectiveType?: string; saveData?: boolean };
    deviceMemory?: number;
  };
  const connection = navigatorWithSignals.connection;
  if (
    connection?.saveData
    || connection?.effectiveType === "slow-2g"
    || connection?.effectiveType === "2g"
    || (typeof navigatorWithSignals.deviceMemory === "number" && navigatorWithSignals.deviceMemory < 4)
  ) return false;

  try {
    const canvas = document.createElement("canvas");
    const context = canvas.getContext("webgl2", { failIfMajorPerformanceCaveat: true })
      || canvas.getContext("webgl", { failIfMajorPerformanceCaveat: true });
    if (!context) return false;
    context.getExtension("WEBGL_lose_context")?.loseContext();
    return true;
  } catch {
    return false;
  }
}

/**
 * La home conserve son DOM complet et ne charge le volume qu'après le contenu
 * critique. Une incapacité GPU, un réseau contraint ou une erreur de chunk
 * laisse simplement la chorégraphie DOM/CSS qualifiée reprendre la scène.
 */
export function HomeSignatureVolume({ onStateChange, product, progress, reduced }: Props) {
  const [state, setState] = useState<HomeVolumeState>("pending");
  const [compact, setCompact] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const idleRef = useRef(0);

  useEffect(() => {
    const media = window.matchMedia("(max-width: 820px)");
    const update = () => setCompact(media.matches);
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    if (reduced) {
      setState("fallback");
      return;
    }

    const start = () => setState(supportsHomeVolume() ? "webgl" : "fallback");
    const schedule = () => {
      if ("requestIdleCallback" in window) {
        idleRef.current = window.requestIdleCallback(start, { timeout: 2_200 });
      } else {
        timerRef.current = setTimeout(start, 1_500);
      }
    };
    if (document.readyState === "complete") schedule();
    else window.addEventListener("load", schedule, { once: true });
    return () => {
      window.removeEventListener("load", schedule);
      if (timerRef.current) clearTimeout(timerRef.current);
      if (idleRef.current && "cancelIdleCallback" in window) window.cancelIdleCallback(idleRef.current);
    };
  }, [reduced]);

  useEffect(() => onStateChange(state), [onStateChange, state]);

  if (state !== "webgl") return null;

  return (
    <div className={styles.heroVolume} aria-hidden="true" data-home-signature-volume="webgl">
      <ImmersiveBoundary onFailure={() => setState("fallback")}>
        <SignatureCommerceCanvas
          compact={compact}
          offerCount={product?.merchants ?? 0}
          playing={false}
          product={product ? { image: product.image, name: product.name } : null}
          progress={progress}
        />
      </ImmersiveBoundary>
    </div>
  );
}
