"use client";

import { useEffect, useState } from "react";

/**
 * Bouton "Retour en haut" qui apparaît après un certain scroll.
 * 
 * Pourquoi :
 * - Sur les pages longues (catalogue, produit), l'utilisateur a besoin
 *   d'un raccourci pour revenir en haut.
 * - L'animation d'apparition (opacity + translateY) donne une sensation
 *   de vie et de réactivité.
 * - Le bouton disparaît quand il n'est pas utile (pas de pollution visuelle).
 */
export function ScrollToTop() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const onScroll = () => {
      setVisible(window.scrollY > 600);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const scrollUp = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <button
      className={`fx-scroll-top ${visible ? "visible" : ""}`}
      onClick={scrollUp}
      aria-label="Retour en haut de page"
      type="button"
    >
      <svg viewBox="0 0 16 16" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M8 12V4M4.5 7.5 8 4l3.5 3.5" />
      </svg>
    </button>
  );
}
