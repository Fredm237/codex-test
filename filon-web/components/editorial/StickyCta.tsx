"use client";

import { useEffect, useRef } from "react";

/** Persistent bottom CTA on mobile — appears once past the first viewport. */
export function StickyCta() {
  const ref = useRef<HTMLAnchorElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const onScroll = () => {
      el.classList.toggle("show", window.scrollY > window.innerHeight * 0.9);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  return (
    <a className="ed-sticky-cta" href="/#installer" ref={ref}>
      Ajouter FILON — gratuit
    </a>
  );
}
