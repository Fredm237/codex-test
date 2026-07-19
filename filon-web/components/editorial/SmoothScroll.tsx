"use client";

import { useEffect } from "react";

/**
 * Premium inertial smooth-scroll (Lenis). Disabled under prefers-reduced-motion
 * and on coarse/touch pointers where native momentum already feels right.
 */
export function SmoothScroll() {
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (window.matchMedia("(pointer: coarse)").matches) return;

    let lenis: import("lenis").default | null = null;
    let raf = 0;
    let cancelled = false;

    import("lenis").then(({ default: Lenis }) => {
      if (cancelled) return;
      lenis = new Lenis({ duration: 1.1, lerp: 0.09, wheelMultiplier: 1, smoothWheel: true });
      const loop = (t: number) => {
        lenis?.raf(t);
        raf = requestAnimationFrame(loop);
      };
      raf = requestAnimationFrame(loop);

      // in-page anchor links glide instead of jumping
      const onClick = (e: MouseEvent) => {
        const a = (e.target as HTMLElement)?.closest?.('a[href^="#"]') as HTMLAnchorElement | null;
        if (!a) return;
        const id = a.getAttribute("href");
        if (!id || id === "#") return;
        const el = document.querySelector(id);
        if (el) {
          e.preventDefault();
          lenis?.scrollTo(el as HTMLElement, { offset: -70, duration: 1.4 });
        }
      };
      document.addEventListener("click", onClick);
      (lenis as unknown as { _onClick?: typeof onClick })._onClick = onClick;
    });

    return () => {
      cancelled = true;
      cancelAnimationFrame(raf);
      const onClick = (lenis as unknown as { _onClick?: (e: MouseEvent) => void })?._onClick;
      if (onClick) document.removeEventListener("click", onClick);
      lenis?.destroy();
    };
  }, []);

  return null;
}
