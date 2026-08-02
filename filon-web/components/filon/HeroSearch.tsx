"use client";

// Champ de recherche du hero.
//
// Formulaire GET vers /recherche : la question part dans l'URL, donc elle
// survit au changement de page, se partage et se met en favori. Un champ qui
// perd la question de l'utilisateur au premier clic est un défaut, pas un
// détail — l'assistant la relit et lance l'analyse tout seul.

import { useState } from "react";
import { useLocale } from "@/lib/i18n";

const SUGGESTION_KEYS = ["hero.sug1", "hero.sug2", "hero.sug3"];

export function HeroSearch() {
  const { t } = useLocale();
  const [query, setQuery] = useState("");

  return (
    <div className="fx-hero-search">
      <form className="fx-field" action="/recherche/" method="get" role="search">
        <svg viewBox="0 0 24 24" aria-hidden="true" width="19" height="19" className="fx-field-icon">
          <circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" strokeWidth="1.8" />
          <path d="m21 21-4.2-4.2" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
        <input
          type="search"
          name="q"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t("hero.ask")}
          aria-label={t("hero.ask")}
          autoComplete="off"
        />
        <button className="fx-btn primary" type="submit">
          {t("hero.askBtn")}
        </button>
      </form>

      <div className="fx-hero-suggestions">
        {SUGGESTION_KEYS.map((key) => {
          const label = t(key);
          return (
            <a key={key} className="fx-chip" href={`/recherche/?q=${encodeURIComponent(label)}`}>
              {label}
            </a>
          );
        })}
      </div>
    </div>
  );
}
