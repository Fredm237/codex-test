"use client";

import { Component, type ErrorInfo, type ReactNode, useEffect, useRef, useState } from "react";

export type ImmersiveState = "pending" | "webgl" | "fallback";
export type ImmersiveQuality = "full" | "degraded";

export const FRAME_RATE_DEGRADE = 45;
export const FRAME_RATE_FLOOR = 30;
const FRAME_SAMPLE_MS = 2_200;

export function useAdaptiveFrameBudget(enabled: boolean, onFailure: () => void) {
  const [quality, setQuality] = useState<ImmersiveQuality>("full");
  const [measuring, setMeasuring] = useState(false);
  const failureRef = useRef(onFailure);

  useEffect(() => {
    failureRef.current = onFailure;
  }, [onFailure]);

  useEffect(() => {
    if (!enabled) {
      setMeasuring(false);
      return;
    }
    setMeasuring(true);
    let frame = 0;
    let frames = 0;
    let startedAt = 0;
    let stopped = false;

    const tick = (now: number) => {
      if (document.visibilityState !== "visible") {
        startedAt = 0;
        frames = 0;
        frame = requestAnimationFrame(tick);
        return;
      }
      if (!startedAt) startedAt = now;
      frames += 1;
      const elapsed = now - startedAt;
      if (elapsed >= FRAME_SAMPLE_MS) {
        const fps = frames * 1_000 / elapsed;
        stopped = true;
        if (quality === "full" && fps < FRAME_RATE_DEGRADE) {
          setQuality("degraded");
        } else if (quality === "degraded" && fps < FRAME_RATE_FLOOR) {
          setMeasuring(false);
          failureRef.current();
        } else {
          setMeasuring(false);
        }
      }
      if (!stopped) frame = requestAnimationFrame(tick);
    };

    const warmup = window.setTimeout(() => {
      frame = requestAnimationFrame(tick);
    }, 700);
    return () => {
      window.clearTimeout(warmup);
      cancelAnimationFrame(frame);
    };
  }, [enabled, quality]);

  return { measuring, quality };
}

export function supportsImmersiveVolume() {
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

export function useImmersiveRuntime(reduced: boolean, delay = 1_500, visible = true) {
  const [state, setState] = useState<ImmersiveState>("pending");
  const [compact, setCompact] = useState(false);

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

    let timer: ReturnType<typeof setTimeout> | null = null;
    let idle = 0;
    const start = () => setState(supportsImmersiveVolume() ? "webgl" : "fallback");
    const schedule = () => {
      if ("requestIdleCallback" in window) idle = window.requestIdleCallback(start, { timeout: delay + 700 });
      else timer = setTimeout(start, delay);
    };
    if (document.readyState === "complete") schedule();
    else window.addEventListener("load", schedule, { once: true });
    return () => {
      window.removeEventListener("load", schedule);
      if (timer) clearTimeout(timer);
      if (idle && "cancelIdleCallback" in window) window.cancelIdleCallback(idle);
    };
  }, [delay, reduced]);

  const { measuring, quality } = useAdaptiveFrameBudget(state === "webgl" && visible, () => setState("fallback"));

  return { compact, measuring, quality, setState, state };
}

type BoundaryProps = { children: ReactNode; onFailure: () => void };
type BoundaryState = { failed: boolean };

export class ImmersiveBoundary extends Component<BoundaryProps, BoundaryState> {
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
