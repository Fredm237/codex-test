"use client";

import { useEffect, useRef } from "react";

/** Thin gradient progress bar tracking scroll position. */
export function ScrollProgress() {
  const bar = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = bar.current!;
    let raf = 0;
    const update = () => {
      const h = document.documentElement.scrollHeight - window.innerHeight;
      el.style.width = `${h > 0 ? (window.scrollY / h) * 100 : 0}%`;
      raf = 0;
    };
    const onScroll = () => {
      if (!raf) raf = requestAnimationFrame(update);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    update();
    return () => {
      window.removeEventListener("scroll", onScroll);
      cancelAnimationFrame(raf);
    };
  }, []);

  return <div ref={bar} className="fx-progress" aria-hidden="true" />;
}
