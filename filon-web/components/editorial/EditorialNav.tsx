"use client";

import { useEffect, useRef } from "react";
import { primaryNav, site } from "@/lib/site";

const NAV = primaryNav.slice(0, 3);

export function EditorialNav() {
  const ref = useRef<HTMLElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let last = 0;
    const onScroll = () => {
      const y = window.scrollY;
      el.classList.toggle("stuck", y > 8);
      el.classList.toggle("hide", y > last && y > 420);
      last = y;
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header className="ed-header" ref={ref}>
      <nav className="ed-nav">
        <a className="ed-brand" href="/">
          {site.name}
        </a>
        <div className="ed-nav-mid">
          {NAV.map((n) => (
            <a key={n.href} href={n.href}>
              {n.label}
            </a>
          ))}
        </div>
        <a className="ed-nav-cta" href="/#installer">
          Ajouter FILON
        </a>
      </nav>
    </header>
  );
}
