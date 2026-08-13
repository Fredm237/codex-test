"use client";

import { useLocale } from "@/lib/i18n";

const COPY = {
  fr: "Aller directement au contenu",
  nl: "Ga rechtstreeks naar de inhoud",
  en: "Skip to content",
} as const;

/** Lien visible uniquement au clavier : la navigation reste rapide et fiable. */
export function SkipToContent() {
  const { locale } = useLocale();
  return (
    <a className="fx-skip-link" href="#main-content">
      {COPY[locale]}
    </a>
  );
}
