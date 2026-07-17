"use client";

import { useEffect, useRef } from "react";

/** Premium custom cursor: a dot + a lerp-trailing ring that grows on hover. */
export function Cursor() {
  const dot = useRef<HTMLDivElement>(null);
  const ring = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!window.matchMedia("(pointer:fine)").matches) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const d = dot.current!;
    const r = ring.current!;
    let x = window.innerWidth / 2;
    let y = window.innerHeight / 2;
    let rx = x;
    let ry = y;
    let raf = 0;

    const onMove = (e: MouseEvent) => {
      x = e.clientX;
      y = e.clientY;
      d.style.transform = `translate(${x}px, ${y}px) translate(-50%, -50%)`;
    };
    const isInteractive = (t: EventTarget | null) =>
      !!(t as HTMLElement)?.closest?.("a, button, [data-hover]");
    const onOver = (e: MouseEvent) => r.classList.toggle("fx-hot", isInteractive(e.target));

    const loop = () => {
      rx += (x - rx) * 0.18;
      ry += (y - ry) * 0.18;
      r.style.transform = `translate(${rx}px, ${ry}px) translate(-50%, -50%)`;
      raf = requestAnimationFrame(loop);
    };

    document.body.classList.add("fx-cursor-on");
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseover", onOver);
    loop();

    return () => {
      document.body.classList.remove("fx-cursor-on");
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseover", onOver);
      cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <>
      <div ref={dot} className="fx-cursor" aria-hidden="true" />
      <div ref={ring} className="fx-cursor-ring" aria-hidden="true" />
    </>
  );
}
