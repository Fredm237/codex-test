"use client";

// Effet de scroll sur la navigation : la barre se compacte et gagne un
// backdrop-filter quand l'utilisateur descend. L'effet est immédiatement
// visible et donne une sensation de sophistication.

import { useEffect } from "react";

export function NavScrollEffect() {
  useEffect(() => {
    const nav = document.querySelector(".ed-nav");
    if (!nav) return;

    const onScroll = () => {
      if (window.scrollY > 60) {
        nav.classList.add("scrolled");
      } else {
        nav.classList.remove("scrolled");
      }
    };

    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll(); // état initial
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return null;
}
