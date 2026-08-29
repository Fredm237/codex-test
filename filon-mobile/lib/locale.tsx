import AsyncStorage from "@react-native-async-storage/async-storage";
import { createContext, useContext, useEffect, useMemo, useState, type PropsWithChildren } from "react";

export type FilonLocale = "fr" | "nl" | "en";

type Copy = {
  home: string;
  catalogue: string;
  assistant: string;
  saved: string;
  profile: string;
  greeting: string;
  headline: string;
  searchPlaceholder: string;
  startSearch: string;
  exploreCatalogue: string;
  verified: string;
  liveData: string;
  noSavedTitle: string;
  noSavedBody: string;
  configure: string;
  language: string;
  assistantTitle: string;
  assistantBody: string;
  askPlaceholder: string;
  promptOne: string;
  promptTwo: string;
  promptThree: string;
  categoriesTitle: string;
  defineIntent: string;
  intentHint: string;
};

export const copy: Record<FilonLocale, Copy> = {
  fr: {
    home: "Accueil", catalogue: "Catalogue", assistant: "Assistant", saved: "Suivis", profile: "Réglages",
    greeting: "FILON", headline: "Le bon prix commence par une bonne question.", searchPlaceholder: "Que cherchez-vous aujourd’hui ?",
    startSearch: "Rechercher", exploreCatalogue: "Explorer le catalogue", verified: "Offres du catalogue FILON", liveData: "Données indexées du catalogue",
    noSavedTitle: "Rien à suivre, pour le moment.", noSavedBody: "Enregistrez un produit pour garder son prix à l’œil.", configure: "Configurer",
    language: "Langue", assistantTitle: "Parlez à FILON", assistantBody: "Décrivez un besoin. FILON cherchera uniquement parmi les offres indexées dans son catalogue.",
    askPlaceholder: "Ex. un casque confortable pour le train", promptOne: "Un ordinateur pour étudier", promptTwo: "Un casque avec réduction de bruit", promptThree: "Quand acheter moins cher ?",
    categoriesTitle: "Choisir un rayon", defineIntent: "Définir une intention", intentHint: "Budget · délai · préférences",
  },
  nl: {
    home: "Start", catalogue: "Catalogus", assistant: "Assistent", saved: "Volgen", profile: "Instellingen",
    greeting: "FILON", headline: "Een goede prijs begint met een goede vraag.", searchPlaceholder: "Waar ben je vandaag naar op zoek?",
    startSearch: "Zoeken", exploreCatalogue: "Catalogus ontdekken", verified: "Aanbiedingen in de FILON-catalogus", liveData: "Geïndexeerde catalogusgegevens",
    noSavedTitle: "Nog niets om te volgen.", noSavedBody: "Bewaar een product om de prijs in de gaten te houden.", configure: "Instellen",
    language: "Taal", assistantTitle: "Praat met FILON", assistantBody: "Beschrijf je behoefte. FILON zoekt alleen in aanbiedingen die in de catalogus zijn geïndexeerd.",
    askPlaceholder: "Bijv. een comfortabele koptelefoon voor de trein", promptOne: "Een laptop om te studeren", promptTwo: "Een koptelefoon met ruisonderdrukking", promptThree: "Wanneer is kopen voordeliger?",
    categoriesTitle: "Kies een afdeling", defineIntent: "Een intentie bepalen", intentHint: "Budget · deadline · voorkeuren",
  },
  en: {
    home: "Home", catalogue: "Catalogue", assistant: "Assistant", saved: "Watching", profile: "Settings",
    greeting: "FILON", headline: "A fair price starts with a better question.", searchPlaceholder: "What are you looking for today?",
    startSearch: "Search", exploreCatalogue: "Explore catalogue", verified: "Offers in the FILON catalogue", liveData: "Indexed catalogue data",
    noSavedTitle: "Nothing to watch yet.", noSavedBody: "Save a product to keep an eye on its price.", configure: "Set up",
    language: "Language", assistantTitle: "Talk to FILON", assistantBody: "Describe what you need. FILON searches only offers indexed in its catalogue.",
    askPlaceholder: "E.g. comfortable headphones for the train", promptOne: "A laptop for studying", promptTwo: "Noise-cancelling headphones", promptThree: "When is it cheaper to buy?",
    categoriesTitle: "Choose a department", defineIntent: "Set an intent", intentHint: "Budget · deadline · preferences",
  },
};

type LocaleContextValue = { locale: FilonLocale; setLocale: (locale: FilonLocale) => void; t: Copy; ready: boolean };
const LocaleContext = createContext<LocaleContextValue | null>(null);
const STORAGE_KEY = "filon.locale";

export function LocaleProvider({ children }: PropsWithChildren) {
  const [locale, setLocaleState] = useState<FilonLocale>("fr");
  const [ready, setReady] = useState(false);

  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY).then((value) => {
      if (value === "fr" || value === "nl" || value === "en") setLocaleState(value);
      setReady(true);
    });
  }, []);

  const value = useMemo(() => ({
    locale,
    setLocale: (next: FilonLocale) => {
      setLocaleState(next);
      void AsyncStorage.setItem(STORAGE_KEY, next);
    },
    t: copy[locale],
    ready,
  }), [locale, ready]);

  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
}

export function useLocale() {
  const value = useContext(LocaleContext);
  if (!value) throw new Error("useLocale must be used within LocaleProvider");
  return value;
}
