"use client";

import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";
import { useLocale } from "@/lib/i18n";

/** Persistent bottom CTA on mobile — appears once past the first viewport. */
export function StickyCta() {
  const ref = useRef<HTMLAnchorElement>(null);
  const pathname = usePathname();
  const { t } = useLocale();
  const redundantOnSearch = pathname === "/recherche" || pathname.startsWith("/recherche/");
  useEffect(() => {
    const el = ref.current;
    if (!el || redundantOnSearch) return;
    const immersiveJourney = document.querySelector<HTMLElement>("[data-immersive-journey]");
    let fieldHasFocus = false;
    const onScroll = () => {
      const journeyIsComplete = !immersiveJourney
        || immersiveJourney.getBoundingClientRect().bottom <= window.innerHeight;
      // Certaines surfaces apparaissent après l'hydratation (historique,
      // composeur). On les relit à chaque scroll plutôt que de figer la liste
      // lors du montage du layout.
      const safeZoneIsVisible = Array.from(document.querySelectorAll<HTMLElement>("[data-sticky-cta-avoid]"))
        .some((zone) => {
          const bounds = zone.getBoundingClientRect();
          return bounds.bottom > 0 && bounds.top < window.innerHeight;
        });
      el.classList.toggle(
        "show",
        window.scrollY > window.innerHeight * 0.9
          && journeyIsComplete
          && !safeZoneIsVisible
          && !fieldHasFocus,
      );
    };
    const onFocusIn = (event: FocusEvent) => {
      fieldHasFocus = event.target instanceof HTMLElement
        && event.target.matches("input, textarea, select, [contenteditable='true']");
      onScroll();
    };
    const onFocusOut = () => {
      fieldHasFocus = false;
      onScroll();
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    document.addEventListener("focusin", onFocusIn);
    document.addEventListener("focusout", onFocusOut);
    onScroll();
    return () => {
      window.removeEventListener("scroll", onScroll);
      document.removeEventListener("focusin", onFocusIn);
      document.removeEventListener("focusout", onFocusOut);
    };
  }, [redundantOnSearch]);
  if (redundantOnSearch) return null;
  return (
    <a className="ed-sticky-cta" href="/recherche" ref={ref}>
      {t("cta.try")}
    </a>
  );
}
