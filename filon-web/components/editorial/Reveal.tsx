"use client";

import { useEffect, useRef, type CSSProperties, type ReactNode } from "react";

/** Lightweight scroll reveal (IntersectionObserver adds `.in`). */
export function Reveal({
  children,
  className = "",
  style,
}: {
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      el.classList.add("in");
      return;
    }
    // A Reveal can wrap a whole ledger (blog, merchants, FAQ). A fixed ratio
    // would require hundreds of invisible pixels to enter the viewport before
    // the first item appears on mobile. Keep the same choreography, but cap the
    // visible distance needed to start it.
    const threshold = Math.min(0.16, 96 / Math.max(el.offsetHeight, 1));
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            el.classList.add("in");
            io.unobserve(el);
          }
        });
      },
      { threshold, rootMargin: "0px 0px -8% 0px" }
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return (
    <div ref={ref} className={`rv ${className}`} style={style}>
      {children}
    </div>
  );
}
