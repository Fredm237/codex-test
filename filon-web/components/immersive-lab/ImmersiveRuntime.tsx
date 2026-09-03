"use client";

import { Component, type ErrorInfo, type ReactNode, useEffect, useState } from "react";

export type ImmersiveState = "pending" | "webgl" | "fallback";

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

export function useImmersiveRuntime(reduced: boolean, delay = 1_500) {
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

  return { compact, setState, state };
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
