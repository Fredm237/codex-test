"use client";

import type { CSSProperties } from "react";

const clamp = (value: number) => Math.max(0, Math.min(1, value));
const between = (value: number, start: number, end: number) => clamp((value - start) / (end - start));
const ease = (value: number) => value * value * (3 - 2 * value);

type ActorTransform = {
  x: number;
  y: number;
  z: number;
  scale: number;
  rotate: number;
  opacity: number;
};

function mokaTransform(progress: number, side: "left" | "right"): ActorTransform {
  const emergence = ease(between(progress, side === "left" ? 0.14 : 0.25, side === "left" ? 0.38 : 0.49));
  const comparison = ease(between(progress, 0.55, 0.74));
  const resolution = ease(between(progress, 0.78, 0.95));
  const targetX = side === "left" ? 47 : 57;
  const compareX = side === "left" ? 36 : 66;
  const restingY = side === "left" ? 58 : 56;
  const finalX = side === "left" ? 48 : 72;
  const opacity = side === "right" ? emergence * (1 - resolution * 0.72) : emergence;

  return {
    x: 50 + (targetX - 50) * emergence + (compareX - targetX) * comparison + (finalX - compareX) * resolution,
    y: 64 + (restingY - 64) * emergence - comparison * 1.2,
    z: 10 + emergence * 110 + comparison * 45 - resolution * 35,
    scale: 0.24 + emergence * 0.72 - comparison * 0.08 + resolution * (side === "left" ? 0.12 : -0.12),
    rotate: (side === "left" ? -16 : 16) * (1 - emergence) + (side === "left" ? -5 : 5) * comparison,
    opacity,
  };
}

function styleFor(transform: ActorTransform): CSSProperties {
  return {
    left: `${transform.x}%`,
    top: `${transform.y}%`,
    opacity: transform.opacity,
    transform: `translate3d(-50%, -50%, ${transform.z}px) rotateZ(${transform.rotate}deg) scale(${transform.scale})`,
  };
}

export function CinematicProductActors({ progress }: { progress: number }) {
  const left = mokaTransform(progress, "left");
  const right = mokaTransform(progress, "right");

  return (
    <div className="ce-product-world" aria-hidden="true">
      <div className="ce-laptop-portal" style={{ opacity: ease(between(progress, 0.08, 0.22)) }} />
      <figure className="ce-product-actor ce-product-actor--left" style={styleFor(left)}>
        <img src="/cinematic/actors/moka-babubas.png" alt="" />
        <span className="ce-product-shadow" />
      </figure>
      <figure className="ce-product-actor ce-product-actor--right" style={styleFor(right)}>
        <img src="/cinematic/actors/moka-bazta.png" alt="" />
        <span className="ce-product-shadow" />
      </figure>
    </div>
  );
}
