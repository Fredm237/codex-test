"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";
import { ImmersiveBoundary, useImmersiveRuntime } from "./ImmersiveRuntime";

const SignatureCommerceCanvas = dynamic(
  () => import("./SignatureCommerceCanvas").then((module) => module.SignatureCommerceCanvas),
  { ssr: false, loading: () => null },
);

type Props = {
  image: string;
  name: string;
  offerCount: number;
};

const PRODUCT_SEQUENCE_START = 0.2;
const PRODUCT_SEQUENCE_END = 0.92;

export function ProductIdentityVolume({ image, name, offerCount }: Props) {
  const [reduced, setReduced] = useState(false);
  const [progress, setProgress] = useState(PRODUCT_SEQUENCE_START);
  const frameRef = useRef(0);
  const { compact, measuring, quality, setState, state } = useImmersiveRuntime(reduced, 1_800);

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduced(media.matches);
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    if (state !== "webgl" || reduced) return;
    const started = performance.now();
    const tick = (now: number) => {
      const elapsed = Math.min(1, (now - started) / 3_800);
      const eased = elapsed * elapsed * (3 - 2 * elapsed);
      setProgress(PRODUCT_SEQUENCE_START + eased * (PRODUCT_SEQUENCE_END - PRODUCT_SEQUENCE_START));
      if (elapsed < 1) frameRef.current = requestAnimationFrame(tick);
    };
    frameRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frameRef.current);
  }, [reduced, state]);

  if (state !== "webgl") return null;

  return (
    <div className="p19-product-volume" aria-hidden="true" data-product-identity-volume="webgl">
      <ImmersiveBoundary onFailure={() => setState("fallback")}>
        <SignatureCommerceCanvas
          compact={compact}
          offerCount={offerCount}
          playing={measuring}
          product={{ image, name }}
          progress={progress}
          quality={quality}
        />
      </ImmersiveBoundary>
    </div>
  );
}
