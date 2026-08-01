"use client";

import { useEffect, useRef, useState } from "react";
import { BrandLogo } from "./Brand";
import { LanguageSwitcher } from "./LanguageSwitcher";
import { MegaMenu } from "./MegaMenu";
import { NAV_KEYS, useLocale } from "@/lib/i18n";

const DESKTOP = NAV_KEYS.slice(0, 5);

export function EditorialNav() {
  const ref = useRef<HTMLElement>(null);
  const [open, setOpen] = useState(false);
  const { t } = useLocale();

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let last = 0;
    const onScroll = () => {
      const y = window.scrollY;
      el.classList.toggle("stuck", y > 8);
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
          <BrandLogo onClick={() => setOpen(false)} />
          <div className="ed-nav-mid">
            <MegaMenu />
            {DESKTOP.filter((n) => n.href !== "/catalogue").map((n) => (
              <a key={n.href} href={n.href}>
                {t(n.key)}
              </a>
            ))}
          </div>
          <div className="ed-nav-right">
            <LanguageSwitcher />
            <a className="ed-nav-cta" href="/recherche">
              {t("cta.try")}
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
          {NAV_KEYS.map((n) => (
            <a key={n.href} href={n.href} onClick={() => setOpen(false)}>
              {t(n.key)}
            </a>
          ))}
          <a className="ed-btn wave" href="/recherche" onClick={() => setOpen(false)} style={{ marginTop: 12 }}>
            {t("cta.try")}
          </a>
          <div style={{ marginTop: 16 }}><LanguageSwitcher /></div>
        </nav>
      </div>
    </>
  );
}
