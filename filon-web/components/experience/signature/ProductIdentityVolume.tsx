"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";
import { ImmersiveBoundary, useImmersiveRuntime } from "./ImmersiveRuntime";

const SignatureCommerceCanvas = dynamic(
  () => import("./SignatureCommerceCanvas").then((module) => module.SignatureCommerceCanvas),
  { ssr: false, loading: () => null },
);

type Props = {
  image: string | null;
  name: string;
  offerCount: number;
};

const PRODUCT_SEQUENCE_START = 0.2;
const PRODUCT_SEQUENCE_END = 0.92;

export function ProductIdentityVolume({ image, name, offerCount }: Props) {
  const [reduced, setReduced] = useState(false);
  const [visible, setVisible] = useState(false);
  const [progress, setProgress] = useState(PRODUCT_SEQUENCE_START);
  const frameRef = useRef(0);
  const progressRef = useRef(PRODUCT_SEQUENCE_START);
  const rootRef = useRef<HTMLDivElement | null>(null);
  const { compact, measuring, quality, setState, state } = useImmersiveRuntime(reduced, 1_800, visible);

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduced(media.matches);
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
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
    if (state !== "webgl" || reduced || !visible || progressRef.current >= PRODUCT_SEQUENCE_END) return;
    const from = progressRef.current;
    const started = performance.now();
    const remaining = (PRODUCT_SEQUENCE_END - from) / (PRODUCT_SEQUENCE_END - PRODUCT_SEQUENCE_START);
    const tick = (now: number) => {
      const elapsed = Math.min(1, (now - started) / Math.max(1, 3_800 * remaining));
      const eased = elapsed * elapsed * (3 - 2 * elapsed);
      const next = from + eased * (PRODUCT_SEQUENCE_END - from);
      progressRef.current = next;
      setProgress(next);
      if (elapsed < 1) frameRef.current = requestAnimationFrame(tick);
    };
    frameRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frameRef.current);
  }, [reduced, state, visible]);

  if (state !== "webgl") return null;

  return (
    <div ref={rootRef} className="p19-product-volume" aria-hidden="true" data-product-identity-volume="webgl">
      <ImmersiveBoundary onFailure={() => setState("fallback")}>
        <SignatureCommerceCanvas
          compact={compact}
          offerCount={offerCount}
          onFailure={() => setState("fallback")}
          playing={visible && measuring}
          product={{ image, name }}
          progress={progress}
          quality={quality}
        />
      </ImmersiveBoundary>
    </div>
  );
}
