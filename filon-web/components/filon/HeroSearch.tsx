"use client";

// Champ de recherche du hero.
//
// Formulaire GET vers /recherche : la question part dans l'URL, donc elle
// survit au changement de page, se partage et se met en favori. Un champ qui
// perd la question de l'utilisateur au premier clic est un défaut, pas un
// détail — l'assistant la relit et lance l'analyse tout seul.

import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";

const SUGGESTIONS = [
  "Un aspirateur robot fiable sous 300 €",
  "Chemise en lin homme",
  "Casque à réduction de bruit",
];

export function HeroSearch() {
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
          placeholder="Que voulez-vous acheter ?"
          aria-label="Que voulez-vous acheter ?"
          autoComplete="off"
        />
        <motion.button
          className="fx-btn primary"
          type="submit"
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          transition={{ type: "spring", stiffness: 400, damping: 20 }}
        >
          Demander
        </motion.button>
      </motion.form>

      <motion.div
        className="fx-hero-suggestions"
        initial="hidden"
        animate="show"
        variants={{
          hidden: { opacity: 0 },
          show: { opacity: 1, transition: { staggerChildren: 0.08, delayChildren: 0.3 } },
        }}
      >
        {SUGGESTIONS.map((s) => (
          <motion.a
            key={s}
            className="fx-chip"
            href={`/recherche/?q=${encodeURIComponent(s)}`}
            variants={{
              hidden: { opacity: 0, y: 8 },
              show: { opacity: 1, y: 0 },
            }}
            whileHover={{ y: -2, boxShadow: "var(--fx-elevation-1)" }}
            transition={{ type: "spring", stiffness: 300, damping: 20 }}
          >
            {s}
          </motion.a>
        ))}
      </motion.div>
    </div>
  );
}
