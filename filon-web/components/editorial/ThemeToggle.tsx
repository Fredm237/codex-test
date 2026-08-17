"use client";

import { useEffect, useState } from "react";
import { useLocale } from "@/lib/i18n";

type Tone = "dark" | "light";

function labels(locale: string, tone: Tone) {
  const isLight = tone === "light";
  if (locale === "nl") return isLight ? "Donker thema inschakelen" : "Licht thema inschakelen";
  if (locale === "en") return isLight ? "Use dark theme" : "Use light theme";
  return isLight ? "Activer le thème sombre" : "Activer le thème clair";
}

function applyTone(tone: Tone) {
  const root = document.documentElement;
  root.dataset.tone = tone;
  root.style.colorScheme = tone;
  document.querySelector('meta[name="theme-color"]')?.setAttribute("content", tone === "light" ? "#e7e2d8" : "#0e0c0b");
  window.localStorage.setItem("filon-tone", tone);
}

/** Préférence visuelle globale. Sans choix explicite, l’amorçage du layout
 * suit le réglage système avant l’hydratation ; ce bouton rend ensuite le
 * choix volontaire et persistant. */
export function ThemeToggle({ compact = false }: { compact?: boolean }) {
  const { locale } = useLocale();
  const [tone, setTone] = useState<Tone>("dark");

  useEffect(() => {
    setTone(document.documentElement.dataset.tone === "light" ? "light" : "dark");
  }, []);

  const next = tone === "dark" ? "light" : "dark";
  const label = labels(locale, tone);
  const shortLabel = locale === "nl"
    ? tone === "dark" ? "Licht" : "Donker"
    : locale === "en"
      ? tone === "dark" ? "Light" : "Dark"
      : tone === "dark" ? "Clair" : "Sombre";

  return (
    <button
      type="button"
      className={`ed-theme-toggle${compact ? " ed-theme-toggle-mobile" : ""}`}
      aria-label={label}
      title={label}
      aria-pressed={tone === "light"}
      onClick={() => {
        applyTone(next);
        setTone(next);
      }}
    >
      {tone === "dark" ? (
        <svg aria-hidden="true" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="3.5" stroke="currentColor" strokeWidth="1.7" /><path d="M12 2.5v2M12 19.5v2M21.5 12h-2M4.5 12h-2M18.72 5.28l-1.42 1.42M6.7 17.3l-1.42 1.42M18.72 18.72l-1.42-1.42M6.7 6.7 5.28 5.28" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" /></svg>
      ) : (
        <svg aria-hidden="true" viewBox="0 0 24 24" fill="none"><path d="M20.4 15.1A8.2 8.2 0 0 1 8.9 3.6 8.2 8.2 0 1 0 20.4 15.1Z" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" /></svg>
      )}
      <span>{shortLabel}</span>
    </button>
  );
}
