"use client";

// Champ de recherche du hero.
//
// Formulaire GET vers /recherche : la question part dans l'URL, donc elle
// survit au changement de page, se partage et se met en favori. Un champ qui
// perd la question de l'utilisateur au premier clic est un défaut, pas un
// détail — l'assistant la relit et lance l'analyse tout seul.

import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useLocale } from "@/lib/i18n";

const SUGGESTION_KEYS = ["hero.sug1", "hero.sug2", "hero.sug3"];

export function HeroSearch() {
  const { t } = useLocale();
  const [query, setQuery] = useState("");
  const [focused, setFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="fx-hero-search">
      <motion.form
        className={`fx-field ${focused ? "fx-field-focused" : ""}`}
        action="/recherche/"
        method="get"
        role="search"
        animate={focused ? { scale: 1.01 } : { scale: 1 }}
        transition={{ type: "spring", stiffness: 400, damping: 25 }}
      >
        <motion.svg
          viewBox="0 0 24 24"
          aria-hidden="true"
          width="19"
          height="19"
          className="fx-field-icon"
          animate={focused ? { scale: 1.1, rotate: -8 } : { scale: 1, rotate: 0 }}
          transition={{ type: "spring", stiffness: 300, damping: 20 }}
        >
          <circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" strokeWidth="1.8" />
          <path d="m21 21-4.2-4.2" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </motion.svg>
        <input
          ref={inputRef}
          type="search"
          name="q"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder={t("hero.ask")}
          aria-label={t("hero.ask")}
          autoComplete="off"
        />
        <motion.button
          className="fx-btn primary"
          type="submit"
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          transition={{ type: "spring", stiffness: 400, damping: 20 }}
        >
          {t("hero.askBtn")}
        </motion.button>
      </motion.form>


    </div>
  );
}
