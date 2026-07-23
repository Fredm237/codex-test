"use client";

import { useEffect, useRef, useState } from "react";
import { primaryNav, site } from "@/lib/site";

const DESKTOP = primaryNav.slice(0, 5);

export function EditorialNav() {
  const ref = useRef<HTMLElement>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let last = 0;
    // The homepage opens on a dark hero; the nav sits light-on-transparent over
    // it, then flips to its frosted light bar (dark text) once scrolled.
    const darkHero = !!document.querySelector(".ed-hero");
    const onScroll = () => {
      const y = window.scrollY;
      const stuck = y > 8;
      el.classList.toggle("stuck", stuck);
      el.classList.toggle("on-dark", darkHero && !stuck);
      el.classList.toggle("hide", y > last && y > 420 && !open);
      last = y;
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [open]);

  // Lock scroll while the mobile menu is open
  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <>
      <header className="ed-header" ref={ref}>
        <nav className="ed-nav">
          <a className="ed-brand" href="/" onClick={() => setOpen(false)}>
            {site.name}
          </a>
          <div className="ed-nav-mid">
            {DESKTOP.map((n) => (
              <a key={n.href} href={n.href}>
                {n.label}
              </a>
            ))}
          </div>
          <div className="ed-nav-right">
            <a className="ed-nav-cta" href="/recherche">
              Essayer le copilote
            </a>
            <button
              className="ed-burger"
              aria-label={open ? "Fermer le menu" : "Ouvrir le menu"}
              aria-expanded={open}
              onClick={() => setOpen((v) => !v)}
            >
              <span className={open ? "open" : ""} />
            </button>
          </div>
        </nav>
      </header>

      {/* Sibling of <header> so the fixed panel is relative to the viewport,
          not trapped by the header's backdrop-filter containing block. */}
      <div className={`ed-mobile ${open ? "show" : ""}`} aria-hidden={!open}>
        <nav className="ed-mobile-nav">
          {primaryNav.map((n) => (
            <a key={n.href} href={n.href} onClick={() => setOpen(false)}>
              {n.label}
            </a>
          ))}
          <a className="ed-btn wave" href="/recherche" onClick={() => setOpen(false)} style={{ marginTop: 12 }}>
            Essayer le copilote
          </a>
        </nav>
      </div>
    </>
  );
}
