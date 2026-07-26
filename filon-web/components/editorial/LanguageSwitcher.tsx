"use client";

import { useLocale } from "@/lib/i18n";

/** Bascule FR / NL, sobre, dans la barre de navigation. */
export function LanguageSwitcher() {
  const { locale, setLocale, t } = useLocale();
  return (
    <div className="ed-lang" role="group" aria-label={t("lang.aria")}>
      <button
        type="button"
        className={locale === "fr" ? "on" : ""}
        aria-pressed={locale === "fr"}
        onClick={() => setLocale("fr")}
      >
        FR
      </button>
      <span aria-hidden="true">·</span>
      <button
        type="button"
        className={locale === "nl" ? "on" : ""}
        aria-pressed={locale === "nl"}
        onClick={() => setLocale("nl")}
      >
        NL
      </button>
    </div>
  );
}
