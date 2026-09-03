"use client";

import dynamic from "next/dynamic";
import { useEffect } from "react";
import type { ProofProduct } from "@/lib/proof";
import { ImmersiveBoundary, type ImmersiveState, useImmersiveRuntime } from "@/components/immersive-lab/ImmersiveRuntime";
import styles from "./web-experience.module.css";

const SignatureCommerceCanvas = dynamic(
  () => import("@/components/immersive-lab/SignatureCommerceCanvas")
    .then((module) => module.SignatureCommerceCanvas),
  { ssr: false, loading: () => null },
);

export type HomeVolumeState = ImmersiveState;

type Props = {
  onStateChange: (state: HomeVolumeState) => void;
  product: ProofProduct | null;
  progress: number;
  reduced: boolean;
};

/**
 * La home conserve son DOM complet et ne charge le volume qu'après le contenu
 * critique. Une incapacité GPU, un réseau contraint ou une erreur de chunk
 * laisse simplement la chorégraphie DOM/CSS qualifiée reprendre la scène.
 */
export function HomeSignatureVolume({ onStateChange, product, progress, reduced }: Props) {
  const { compact, setState, state } = useImmersiveRuntime(reduced, 1_500);

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
