"use client";

import { useLocale, type Locale } from "@/lib/i18n";

const LANGS: Locale[] = ["fr", "nl", "en"];

/** Bascule FR / NL / EN, sobre, dans la barre de navigation. */
export function LanguageSwitcher() {
  const { locale, setLocale, t } = useLocale();
  return (
    <div className="ed-lang" role="group" aria-label={t("lang.aria")}>
      {LANGS.map((l, i) => (
        <span key={l} style={{ display: "contents" }}>
          {i > 0 && <span aria-hidden="true">·</span>}
          <button
            type="button"
            className={locale === l ? "on" : ""}
            aria-pressed={locale === l}
            onClick={() => setLocale(l)}
          >
            {l.toUpperCase()}
          </button>
        </span>
      ))}
    </div>
  );
}
