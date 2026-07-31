"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export type Locale = "fr" | "nl" | "en";

/** Dictionnaire FR/NL/EN. Clés courtes, regroupées par zone. */
const DICT: Record<string, { fr: string; nl: string; en: string }> = {
  // Navigation
  "nav.catalogue": { fr: "Catalogue", nl: "Catalogus", en: "Catalogue" },
  "nav.assistant": { fr: "Assistant", nl: "Assistent", en: "Assistant" },
  "nav.how": { fr: "Comment ça marche", nl: "Hoe het werkt", en: "How it works" },
  "nav.pricing": { fr: "Tarifs", nl: "Tarieven", en: "Pricing" },
  "nav.cashback": { fr: "Cashback", nl: "Cashback", en: "Cashback" },
  "nav.refurb": { fr: "Reconditionné", nl: "Refurbished", en: "Refurbished" },
  "nav.score": { fr: "Le Score", nl: "De Score", en: "The Score" },
  "nav.promos": { fr: "Codes promo", nl: "Kortingscodes", en: "Promo codes" },
  // CTA globales
  "cta.try": { fr: "Essayer le copilote", nl: "Probeer de copiloot", en: "Try the copilot" },
  "cta.chrome": { fr: "Ajouter à Chrome", nl: "Toevoegen aan Chrome", en: "Add to Chrome" },
  "cta.discover": { fr: "Découvrir", nl: "Ontdekken", en: "Discover" },
  "cta.catalogue": { fr: "Explorer le catalogue", nl: "Verken de catalogus", en: "Explore the catalogue" },
  // Hero (accueil)
  "hero.eyebrow": { fr: "Copilote d'achat", nl: "Koopcopiloot", en: "Shopping copilot" },
  "hero.h1a": { fr: "Est-ce", nl: "Is dit", en: "Is this" },
  "hero.h1b": { fr: "vraiment", nl: "echt", en: "really" },
  "hero.h1c": { fr: "le bon prix ?", nl: "de juiste prijs?", en: "the right price?" },
  "hero.h1aria": { fr: "Est-ce vraiment le bon prix ?", nl: "Is dit echt de juiste prijs?", en: "Is this really the right price?" },
  "hero.sub": {
    fr: "Décrivez ce que vous cherchez. FILON vous dit quoi acheter, et quand.",
    nl: "Beschrijf wat je zoekt. FILON zegt je wat te kopen, en wanneer.",
    en: "Describe what you're looking for. FILON tells you what to buy, and when.",
  },
  // Scène finale / CTA de clôture
  "final.eyebrow": { fr: "Ne payez plus jamais trop cher", nl: "Betaal nooit meer te veel", en: "Never overpay again" },
  "final.title_a": { fr: "Demandez à FILON", nl: "Vraag het aan FILON", en: "Ask FILON" },
  "final.title_b": { fr: "avant d'acheter", nl: "voordat je koopt", en: "before you buy" },
  "final.note": {
    fr: "Gratuit, pour toujours. Sans carte bancaire. Vos données restent chez vous.",
    nl: "Gratis, voor altijd. Geen bankkaart. Je gegevens blijven van jou.",
    en: "Free, forever. No credit card. Your data stays yours.",
  },
  // Langue
  "lang.fr": { fr: "FR", nl: "FR", en: "FR" },
  "lang.nl": { fr: "NL", nl: "NL", en: "NL" },
  "lang.en": { fr: "EN", nl: "EN", en: "EN" },
  "lang.aria": { fr: "Choisir la langue", nl: "Taal kiezen", en: "Choose language" },
};

/** Éléments de navigation localisés. */
export const NAV_KEYS: Array<{ key: string; href: string }> = [
  { key: "nav.catalogue", href: "/catalogue" },
  { key: "nav.assistant", href: "/recherche" },
  { key: "nav.how", href: "/comment-ca-marche" },
  { key: "nav.pricing", href: "/tarifs" },
  { key: "nav.cashback", href: "/cashback" },
  { key: "nav.refurb", href: "/reconditionne" },
  { key: "nav.score", href: "/score" },
  { key: "nav.promos", href: "/codes-promo" },
];

const LOCALES: Locale[] = ["fr", "nl", "en"];

type Ctx = { locale: Locale; setLocale: (l: Locale) => void; t: (k: string) => string };
const LocaleCtx = createContext<Ctx>({ locale: "fr", setLocale: () => {}, t: (k) => k });

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("fr");

  useEffect(() => {
    const saved = (typeof localStorage !== "undefined" && localStorage.getItem("filon-locale")) as Locale | null;
    if (saved && LOCALES.includes(saved)) {
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
