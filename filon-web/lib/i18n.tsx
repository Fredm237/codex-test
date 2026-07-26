"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export type Locale = "fr" | "nl";

/** Dictionnaire FR/NL. Clés courtes, regroupées par zone. */
const DICT: Record<string, { fr: string; nl: string }> = {
  // Navigation
  "nav.assistant": { fr: "Assistant", nl: "Assistent" },
  "nav.how": { fr: "Comment ça marche", nl: "Hoe het werkt" },
  "nav.pricing": { fr: "Tarifs", nl: "Tarieven" },
  "nav.cashback": { fr: "Cashback", nl: "Cashback" },
  "nav.refurb": { fr: "Reconditionné", nl: "Refurbished" },
  "nav.score": { fr: "Le Score", nl: "De Score" },
  "nav.promos": { fr: "Codes promo", nl: "Kortingscodes" },
  // CTA globales
  "cta.try": { fr: "Essayer le copilote", nl: "Probeer de copiloot" },
  "cta.chrome": { fr: "Ajouter à Chrome", nl: "Toevoegen aan Chrome" },
  "cta.discover": { fr: "Découvrir", nl: "Ontdekken" },
  // Hero (accueil)
  "hero.eyebrow": { fr: "Copilote d'achat", nl: "Koopcopiloot" },
  "hero.h1a": { fr: "Est-ce", nl: "Is dit" },
  "hero.h1b": { fr: "vraiment", nl: "echt" },
  "hero.h1c": { fr: "le bon prix ?", nl: "de juiste prijs?" },
  "hero.h1aria": { fr: "Est-ce vraiment le bon prix ?", nl: "Is dit echt de juiste prijs?" },
  "hero.sub": {
    fr: "Décrivez ce que vous cherchez. FILON vous dit quoi acheter, et quand.",
    nl: "Beschrijf wat je zoekt. FILON zegt je wat te kopen, en wanneer.",
  },
  // Scène finale / CTA de clôture
  "final.eyebrow": { fr: "Ne payez plus jamais trop cher", nl: "Betaal nooit meer te veel" },
  "final.title_a": { fr: "Demandez à FILON", nl: "Vraag het aan FILON" },
  "final.title_b": { fr: "avant d'acheter", nl: "voordat je koopt" },
  "final.note": {
    fr: "Gratuit, pour toujours. Sans carte bancaire. Vos données restent chez vous.",
    nl: "Gratis, voor altijd. Geen bankkaart. Je gegevens blijven van jou.",
  },
  // Langue
  "lang.fr": { fr: "FR", nl: "FR" },
  "lang.nl": { fr: "NL", nl: "NL" },
  "lang.aria": { fr: "Choisir la langue", nl: "Taal kiezen" },
};

/** Éléments de navigation localisés. */
export const NAV_KEYS: Array<{ key: string; href: string }> = [
  { key: "nav.assistant", href: "/recherche" },
  { key: "nav.how", href: "/comment-ca-marche" },
  { key: "nav.pricing", href: "/tarifs" },
  { key: "nav.cashback", href: "/cashback" },
  { key: "nav.refurb", href: "/reconditionne" },
  { key: "nav.score", href: "/score" },
  { key: "nav.promos", href: "/codes-promo" },
];

type Ctx = { locale: Locale; setLocale: (l: Locale) => void; t: (k: string) => string };
const LocaleCtx = createContext<Ctx>({ locale: "fr", setLocale: () => {}, t: (k) => k });

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("fr");

  useEffect(() => {
    const saved = (typeof localStorage !== "undefined" && localStorage.getItem("filon-locale")) as Locale | null;
    if (saved === "nl" || saved === "fr") {
      setLocaleState(saved);
      document.documentElement.lang = saved;
    }
  }, []);

  const setLocale = useCallback((l: Locale) => {
    setLocaleState(l);
    try {
      localStorage.setItem("filon-locale", l);
    } catch {}
    document.documentElement.lang = l;
  }, []);

  const t = useCallback((k: string) => DICT[k]?.[locale] ?? DICT[k]?.fr ?? k, [locale]);
  const value = useMemo(() => ({ locale, setLocale, t }), [locale, setLocale, t]);
  return <LocaleCtx.Provider value={value}>{children}</LocaleCtx.Provider>;
}

export const useLocale = () => useContext(LocaleCtx);
