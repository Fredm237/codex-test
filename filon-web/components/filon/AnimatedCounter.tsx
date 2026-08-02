"use client";

// Compteur animé — les chiffres défilent de 0 à la valeur cible quand
// l'élément entre dans le viewport. L'effet est immédiatement visible et
// donne une sensation de "vie" au site.

import { useEffect, useRef, useState } from "react";

function easeOutExpo(t: number): number {
  return t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
}

export function AnimatedCounter({
  value,
  suffix = "",
  duration = 2000,
  locale = "fr-BE",
}: {
  value: number;
  suffix?: string;
  duration?: number;
  locale?: string;
}) {
  const [display, setDisplay] = useState("0");
  const ref = useRef<HTMLSpanElement>(null);
  const hasAnimated = useRef(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    // Respect des préférences utilisateur
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setDisplay(value.toLocaleString(locale));
      return;
    }

    const io = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting || hasAnimated.current) return;
        hasAnimated.current = true;
        io.disconnect();

        const start = performance.now();
        const animate = (now: number) => {
          const elapsed = now - start;
          const progress = Math.min(elapsed / duration, 1);
          const eased = easeOutExpo(progress);
          const current = Math.round(eased * value);
          setDisplay(current.toLocaleString(locale));
          if (progress < 1) requestAnimationFrame(animate);
        };
        requestAnimationFrame(animate);
      },
      { threshold: 0.3 }
    );
    io.observe(node);
    return () => io.disconnect();
  }, [value, duration, locale]);

  return (
    <span ref={ref} className="fx-counter">
      {display}{suffix}
    </span>
  );
}
