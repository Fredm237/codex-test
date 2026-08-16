"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { SequenceDefinition } from "./types";

type Props = {
  sequence: SequenceDefinition;
  frameProgress: number;
  reducedMotion: boolean;
  className?: string;
  cameraProgress?: number;
};

const clamp = (value: number) => Math.max(0, Math.min(1, value));

function source(sequence: SequenceDefinition, index: number) {
  return `${sequence.frameBase}/${String(index + 1).padStart(3, "0")}.jpg`;
}

function nearest(images: Array<HTMLImageElement | null>, target: number, previous: number) {
  if (images[target]) return images[target];
  for (let distance = 1; distance < images.length; distance += 1) {
    const before = target - distance;
    const after = target + distance;
    if (before >= 0 && images[before]) return images[before];
    if (after < images.length && images[after]) return images[after];
  }
  return images[previous];
}

/**
 * Renderer adapter. The CinematicEngine does not know how a world is rendered;
 * this adapter currently paints the dedicated cinematic frame sequence and can
 * later be replaced by an R3F renderer without changing Timeline or Scene data.
 */
export function CinematicSequenceRenderer({ sequence, frameProgress, reducedMotion, className, cameraProgress = 0 }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imagesRef = useRef<Array<HTMLImageElement | null>>(Array(sequence.frames).fill(null));
  const requestedRef = useRef(new Set<number>());
  const drawRef = useRef<(index: number) => void>(() => {});
  const lastFrameRef = useRef(0);
  const targetFrameRef = useRef(0);
  const rafRef = useRef(0);
  const [ready, setReady] = useState(false);
  const [painted, setPainted] = useState(false);

  useEffect(() => {
    imagesRef.current = Array(sequence.frames).fill(null);
    requestedRef.current.clear();
    lastFrameRef.current = 0;
    setReady(false);
    setPainted(false);

    if (reducedMotion) {
      setReady(true);
      return;
    }

    let mounted = true;
    const load = (index: number) => {
      if (index < 0 || index >= sequence.frames || requestedRef.current.has(index)) return;
      requestedRef.current.add(index);
      const image = new Image();
      image.decoding = "async";
      image.onload = () => {
        if (!mounted) return;
        imagesRef.current[index] = image;
        if (index === 0) setReady(true);
        requestAnimationFrame(() => drawRef.current(targetFrameRef.current));
      };
      image.onerror = () => {
        if (index === 0 && mounted) setReady(true);
      };
      image.src = source(sequence, index);
    };

    for (let index = 0; index < Math.min(sequence.frames, 16 * sequence.frameStride); index += sequence.frameStride) load(index);
    return () => { mounted = false; };
  }, [reducedMotion, sequence]);

  const draw = useCallback((index: number) => {
    if (reducedMotion) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const image = nearest(imagesRef.current, index, lastFrameRef.current);
    if (!image) return;
    const context = canvas.getContext("2d", { alpha: false });
    if (!context) return;
    const density = Math.min(window.devicePixelRatio || 1, 2);
    const width = Math.round(window.innerWidth * density);
    const height = Math.round(window.innerHeight * density);
    if (canvas.width !== width || canvas.height !== height) {
      canvas.width = width;
      canvas.height = height;
    }
    const scale = Math.max(width / image.width, height / image.height);
    const drawWidth = image.width * scale;
    const drawHeight = image.height * scale;
    context.fillStyle = "#d9c6a5";
    context.fillRect(0, 0, width, height);
    context.drawImage(image, (width - drawWidth) / 2, (height - drawHeight) / 2, drawWidth, drawHeight);
    lastFrameRef.current = index;
    setPainted(true);
  }, [reducedMotion]);

  drawRef.current = draw;

  useEffect(() => {
    if (!ready || reducedMotion) return;
    const raw = Math.round(clamp(frameProgress) * (sequence.frames - 1));
    const frame = Math.min(sequence.frames - 1, Math.round(raw / sequence.frameStride) * sequence.frameStride);
    targetFrameRef.current = frame;
    const from = Math.max(0, frame - sequence.frameStride * 3);
    const to = Math.min(sequence.frames - 1, frame + sequence.frameStride * 28);
    for (let index = from; index <= to; index += sequence.frameStride) {
      if (requestedRef.current.has(index)) continue;
      requestedRef.current.add(index);
      const image = new Image();
      image.decoding = "async";
      image.onload = () => {
        imagesRef.current[index] = image;
        requestAnimationFrame(() => drawRef.current(targetFrameRef.current));
      };
      image.src = source(sequence, index);
    }
    cancelAnimationFrame(rafRef.current);
    rafRef.current = requestAnimationFrame(() => drawRef.current(frame));
    return () => cancelAnimationFrame(rafRef.current);
  }, [frameProgress, ready, reducedMotion, sequence]);

  const cameraStyle = {
    transform: `scale(${1 + cameraProgress * 0.085}) translate3d(${(0.5 - cameraProgress) * 3.5}%, ${-cameraProgress * 1.8}%, 0)`,
  };

  return (
    <div className={className} aria-hidden="true" style={cameraStyle}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img className={`ce-poster${painted ? " is-hidden" : ""}`} src={sequence.poster} alt="" fetchPriority="high" decoding="async" />
      <canvas ref={canvasRef} className={`ce-canvas${painted ? " is-visible" : ""}`} />
      {!ready && <span className="ce-loading" />}
    </div>
  );
}
