"use client";

import { useEffect, useRef, useState } from "react";
import { useLocale, type Locale } from "@/lib/i18n";

const LANGS: Array<{ code: Locale; short: string; label: string }> = [
  { code: "fr", short: "FR", label: "Français" },
  { code: "nl", short: "NL", label: "Nederlands" },
  { code: "en", short: "EN", label: "English" },
];

function Globe() {
  return (
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true">
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18" strokeLinecap="round" />
      <path d="M12 3c2.5 2.5 3.8 5.6 3.8 9s-1.3 6.5-3.8 9c-2.5-2.5-3.8-5.6-3.8-9S9.5 5.5 12 3z" />
    </svg>
  );
}

/** Sélecteur de langue déroulant FR / NL / EN, sobre, dans la barre de navigation. */
export function LanguageSwitcher() {
  const { locale, setLocale, t } = useLocale();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const current = LANGS.find((l) => l.code === locale) ?? LANGS[0];

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div className={`ed-lang${open ? " open" : ""}`} ref={ref}>
      <button
        type="button"
        className="ed-lang-trigger"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={t("lang.aria")}
        onClick={() => setOpen((o) => !o)}
      >
        <Globe />
        <span className="code">{current.short}</span>
        <svg className="chev" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <path d="m6 9 6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
      <div className="ed-lang-menu" role="listbox" aria-label={t("lang.aria")}>
        {LANGS.map((l) => (
          <button
            key={l.code}
            type="button"
            role="option"
            aria-selected={l.code === locale}
            className={`ed-lang-opt${l.code === locale ? " on" : ""}`}
            onClick={() => {
              setLocale(l.code);
              setOpen(false);
            }}
          >
            <span className="s">{l.short}</span>
            <span className="l">{l.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
