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

function frameSource(sequence: SequenceDefinition, index: number) {
  return `${sequence.frameBase}/${String(index + 1).padStart(4, "0")}.webp`;
}

function assetIndex(sequence: SequenceDefinition, frame: number) {
  return sequence.sprite ? Math.floor(frame / sequence.sprite.framesPerSheet) : frame;
}

function assetCount(sequence: SequenceDefinition) {
  return sequence.sprite ? Math.ceil(sequence.frames / sequence.sprite.framesPerSheet) : sequence.frames;
}

function assetWindow(target: number, count: number) {
  return { from: Math.max(0, target - 1), to: Math.min(count - 1, target + 1) };
}

/**
 * Renderer adapter. The CinematicEngine does not know how a world is rendered;
 * this adapter currently paints the dedicated cinematic frame sequence and can
 * later be replaced by an R3F renderer without changing Timeline or Scene data.
 */
export function CinematicSequenceRenderer({ sequence, frameProgress, reducedMotion, className, cameraProgress = 0 }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imagesRef = useRef<Array<HTMLImageElement | null>>(Array(assetCount(sequence)).fill(null));
  const requestedRef = useRef(new Set<number>());
  const drawRef = useRef<(index: number) => void>(() => {});
  const targetFrameRef = useRef(0);
  const windowRef = useRef(assetWindow(0, assetCount(sequence)));
  const rafRef = useRef(0);
  const [ready, setReady] = useState(false);
  const [painted, setPainted] = useState(false);

  useEffect(() => {
    const count = assetCount(sequence);
    imagesRef.current = Array(count).fill(null);
    requestedRef.current.clear();
    windowRef.current = assetWindow(0, count);
    setReady(false);
    setPainted(false);

    if (reducedMotion) {
      setReady(true);
      return;
    }

    let mounted = true;
    const load = (index: number) => {
      if (index < 0 || index >= count || requestedRef.current.has(index)) return;
      requestedRef.current.add(index);
      const image = new Image();
      image.decoding = "async";
      image.onload = () => {
        if (!mounted) return;
        if (index !== 0 && (index < windowRef.current.from || index > windowRef.current.to)) {
          requestedRef.current.delete(index);
          return;
        }
        imagesRef.current[index] = image;
        if (index === 0) setReady(true);
        requestAnimationFrame(() => drawRef.current(targetFrameRef.current));
      };
      image.onerror = () => {
        requestedRef.current.delete(index);
        if (index === 0 && mounted) setReady(true);
      };
      image.src = frameSource(sequence, index);
    };

    load(0);
    if (count > 1) load(1);
    return () => { mounted = false; };
  }, [reducedMotion, sequence]);

  const draw = useCallback((index: number) => {
    if (reducedMotion) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const wantedAsset = assetIndex(sequence, index);
    const image = imagesRef.current[wantedAsset];
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
    const sourceWidth = sequence.sprite?.tileWidth ?? image.width;
    const sourceHeight = sequence.sprite?.tileHeight ?? image.height;
    const scale = Math.max(width / sourceWidth, height / sourceHeight);
    const drawWidth = sourceWidth * scale;
    const drawHeight = sourceHeight * scale;
    context.fillStyle = "#d9c6a5";
    context.fillRect(0, 0, width, height);
    if (sequence.sprite) {
      const slot = index % sequence.sprite.framesPerSheet;
      const sourceX = (slot % sequence.sprite.columns) * sequence.sprite.tileWidth;
      const sourceY = Math.floor(slot / sequence.sprite.columns) * sequence.sprite.tileHeight;
      context.drawImage(
        image,
        sourceX,
        sourceY,
        sequence.sprite.tileWidth,
        sequence.sprite.tileHeight,
        (width - drawWidth) / 2,
        (height - drawHeight) / 2,
        drawWidth,
        drawHeight,
      );
    } else {
      context.drawImage(image, (width - drawWidth) / 2, (height - drawHeight) / 2, drawWidth, drawHeight);
    }
    setPainted(true);
  }, [reducedMotion, sequence]);

  drawRef.current = draw;

  useEffect(() => {
    if (!ready || reducedMotion) return;
    const raw = Math.round(clamp(frameProgress) * (sequence.frames - 1));
    const frame = Math.min(sequence.frames - 1, Math.round(raw / sequence.frameStride) * sequence.frameStride);
    targetFrameRef.current = frame;
    const targetAsset = assetIndex(sequence, frame);
    const { from, to } = assetWindow(targetAsset, assetCount(sequence));
    windowRef.current = { from, to };
    for (let index = 0; index < imagesRef.current.length; index += 1) {
      if (index === 0 || (index >= from && index <= to)) continue;
      imagesRef.current[index] = null;
      requestedRef.current.delete(index);
    }
    for (let index = from; index <= to; index += 1) {
      if (requestedRef.current.has(index)) continue;
      requestedRef.current.add(index);
      const image = new Image();
      image.decoding = "async";
      image.onload = () => {
        if (index !== 0 && (index < windowRef.current.from || index > windowRef.current.to)) {
          requestedRef.current.delete(index);
          return;
        }
        imagesRef.current[index] = image;
        requestAnimationFrame(() => drawRef.current(targetFrameRef.current));
      };
      image.onerror = () => requestedRef.current.delete(index);
      image.src = frameSource(sequence, index);
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
      <img className={`ce-poster${painted ? " is-hidden" : ""}`} src={reducedMotion ? (sequence.finalPoster ?? sequence.poster) : sequence.poster} alt="" fetchPriority="high" decoding="async" />
      <canvas ref={canvasRef} className={`ce-canvas${painted ? " is-visible" : ""}`} />
      {!ready && <span className="ce-loading" />}
    </div>
  );
}
