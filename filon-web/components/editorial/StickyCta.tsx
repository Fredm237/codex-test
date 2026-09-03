"use client";

import { useEffect, useRef } from "react";
import { useLocale } from "@/lib/i18n";

/** Persistent bottom CTA on mobile — appears once past the first viewport. */
export function StickyCta() {
  const ref = useRef<HTMLAnchorElement>(null);
  const { t } = useLocale();
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const immersiveJourney = document.querySelector<HTMLElement>("[data-immersive-journey]");
    const onScroll = () => {
      const journeyIsComplete = !immersiveJourney
        || immersiveJourney.getBoundingClientRect().bottom <= window.innerHeight;
      el.classList.toggle("show", window.scrollY > window.innerHeight * 0.9 && journeyIsComplete);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  return (
    <a className="ed-sticky-cta" href="/recherche" ref={ref}>
      {t("cta.try")}
    </a>
  );
}
