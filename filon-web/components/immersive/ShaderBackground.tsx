"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";

// R3F Canvas is client + WebGL only — load it lazily, never on the server.
const ShaderCanvas = dynamic(() => import("./ShaderCanvas"), { ssr: false });

export function ShaderBackground() {
  const [enabled, setEnabled] = useState(false);

  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    // Only mount WebGL when it's actually available and motion is allowed.
    let webgl = false;
    try {
      const c = document.createElement("canvas");
      webgl = !!(c.getContext("webgl") || c.getContext("experimental-webgl"));
    } catch {
      webgl = false;
    }
    setEnabled(!reduce && webgl);
  }, []);

  return (
    <>
      {/* CSS fallback / base layer — always present, sits behind the canvas */}
      <div className="fx-bg-fallback" aria-hidden="true" />
      {enabled && <ShaderCanvas />}
    </>
  );
}
