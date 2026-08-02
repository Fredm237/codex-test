"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export type Locale = "fr" | "nl" | "en";

/** Dictionnaire FR/NL/EN. Clés courtes, regroupées par zone. */
const DICT: Record<string, { fr: string; nl: string; en: string }> = {
  // Refonte 2026 — hero, méthode, clôture, catalogue.
  "hero.eyebrowNew": { fr: "Copilote d'achat · Belgique", nl: "Aankoopcopiloot · België", en: "Shopping copilot · Belgium" },
  "hero.l1": { fr: "Est-ce vraiment", nl: "Is dit echt", en: "Is this really" },
  "hero.l2": { fr: "le bon moment", nl: "het juiste moment", en: "the right moment" },
  "hero.l3": { fr: "pour acheter ?", nl: "om te kopen?", en: "to buy?" },
  "hero.ledeA": { fr: "FILON réunit les offres de", nl: "FILON bundelt de aanbiedingen van", en: "FILON gathers the offers of" },
  "hero.ledeB": { fr: "marchands partenaires, conserve l'historique des prix, et vous dit ce que vaut celui d'aujourd'hui.", nl: "partnerwinkels, bewaart de prijsgeschiedenis en zegt je wat die van vandaag waard is.", en: "partner merchants, keeps the price history, and tells you what today's price is worth." },
  "hero.ledeOur": { fr: "nos", nl: "onze", en: "our" },
  "hero.ask": { fr: "Que voulez-vous acheter ?", nl: "Wat wil je kopen?", en: "What do you want to buy?" },
  "hero.askBtn": { fr: "Demander", nl: "Vragen", en: "Ask" },
  "hero.explore": { fr: "Explorer le catalogue", nl: "Verken de catalogus", en: "Explore the catalogue" },
  "hero.tracked": { fr: "Produit suivi", nl: "Gevolgd product", en: "Tracked product" },
  "hero.sellIt": { fr: "marchands le vendent", nl: "winkels verkopen het", en: "merchants sell it" },
  "hero.highest": { fr: "Le plus cher constaté", nl: "Duurst vastgesteld", en: "Highest observed" },
  "hero.lowest": { fr: "Le moins cher constaté", nl: "Goedkoopst vastgesteld", en: "Lowest observed" },
  "hero.gap": { fr: "d'écart", nl: "verschil", en: "spread" },
  "hero.dossier": { fr: "Voir le dossier", nl: "Bekijk de fiche", en: "See the product" },
  "hero.realData": { fr: "Données lues dans notre catalogue, pas un exemple illustratif.", nl: "Gegevens uit onze catalogus, geen illustratief voorbeeld.", en: "Data read from our catalogue, not an illustrative example." },
  "hero.offersTracked": { fr: "offres suivies", nl: "gevolgde aanbiedingen", en: "offers tracked" },
  "hero.multiMerchant": { fr: "produits comparés chez plusieurs marchands", nl: "producten bij meerdere winkels vergeleken", en: "products compared across several merchants" },
  "hero.snapshots": { fr: "relevés de prix", nl: "prijsmetingen", en: "price readings" },
  "hero.sug1": { fr: "Un aspirateur robot fiable sous 300 €", nl: "Een betrouwbare robotstofzuiger onder 300 €", en: "A reliable robot vacuum under €300" },
  "hero.sug2": { fr: "Chemise en lin homme", nl: "Linnen overhemd heren", en: "Men's linen shirt" },
  "hero.sug3": { fr: "Casque à réduction de bruit", nl: "Koptelefoon met ruisonderdrukking", en: "Noise-cancelling headphones" },

  "method.eyebrow": { fr: "La méthode", nl: "De methode", en: "The method" },
  "method.t1": { fr: "Un avis vaut ce que vaut", nl: "Een oordeel is waard wat", en: "A verdict is worth what" },
  "method.t2": { fr: "ce qu'on a mesuré.", nl: "de meting waard is.", en: "the measurement is worth." },
  "method.s1t": { fr: "On réunit les offres", nl: "We bundelen de aanbiedingen", en: "We gather the offers" },
  "method.s1b": { fr: "Le même produit est vendu par plusieurs marchands, sous des libellés différents. FILON les regroupe par code-barres pour qu'une comparaison porte bien sur un seul et même article.", nl: "Hetzelfde product wordt door meerdere winkels verkocht, onder verschillende benamingen. FILON groepeert ze per barcode zodat een vergelijking echt over één artikel gaat.", en: "The same product is sold by several merchants under different names. FILON groups them by barcode so a comparison really covers one and the same item." },
  "method.s2t": { fr: "On garde l'historique", nl: "We bewaren de geschiedenis", en: "We keep the history" },
  "method.s2b": { fr: "Chaque prix est relevé et conservé. C'est la seule façon de savoir si une promotion en est une, ou si le prix barré n'a jamais existé.", nl: "Elke prijs wordt gemeten en bewaard. Alleen zo weet je of een korting er echt een is, of dat de doorgestreepte prijs nooit heeft bestaan.", en: "Every price is recorded and kept. It is the only way to know whether a promotion is one, or whether the struck-through price never existed." },
  "method.s3t": { fr: "On tranche", nl: "We hakken de knoop door", en: "We decide" },
  "method.s3b": { fr: "Le Verdict compare le prix du jour à ce que nous avons réellement observé, et le dit franchement : bon moment, moment ordinaire, ou attendez. Sans historique suffisant, il le dit aussi.", nl: "Het Verdict vergelijkt de prijs van vandaag met wat we werkelijk hebben waargenomen, en zegt het eerlijk: goed moment, gewoon moment, of wacht. Bij te weinig geschiedenis zegt het dat ook.", en: "The Verdict compares today's price with what we actually observed, and says it plainly: good moment, ordinary moment, or wait. Without enough history, it says that too." },

  "closing.eyebrow": { fr: "Avant de payer", nl: "Voor je betaalt", en: "Before you pay" },
  "closing.t1": { fr: "Posez la question à FILON.", nl: "Stel de vraag aan FILON.", en: "Ask FILON." },
  "closing.t2": { fr: "C'est gratuit, et c'est rapide.", nl: "Het is gratis, en het gaat snel.", en: "It's free, and it's fast." },
  "closing.factsA": { fr: "offres suivies chez", nl: "gevolgde aanbiedingen bij", en: "offers tracked across" },
  "closing.factsB": { fr: "marchands partenaires.", nl: "partnerwinkels.", en: "partner merchants." },
  "closing.fallback": { fr: "Les offres de nos marchands partenaires, réunies et suivies dans le temps.", nl: "De aanbiedingen van onze partnerwinkels, gebundeld en door de tijd gevolgd.", en: "The offers of our partner merchants, gathered and tracked over time." },

  "cat.title1": { fr: "Le catalogue,", nl: "De catalogus,", en: "The catalogue," },
  "cat.title2": { fr: "rayon par rayon.", nl: "afdeling per afdeling.", en: "aisle by aisle." },
  "cat.count": { fr: "produits comparés chez nos marchands partenaires.", nl: "producten vergeleken bij onze partnerwinkels.", en: "products compared across our partner merchants." },
  "cat.down": { fr: "Le catalogue est momentanément indisponible. Réessayez dans un instant.", nl: "De catalogus is even niet beschikbaar. Probeer het zo opnieuw.", en: "The catalogue is momentarily unavailable. Try again in a moment." },
  "cat.search": { fr: "Rechercher dans le catalogue", nl: "Zoeken in de catalogus", en: "Search the catalogue" },
  "cat.searchBtn": { fr: "Chercher", nl: "Zoeken", en: "Search" },
  "cat.browse": { fr: "Parcourir les rayons", nl: "Blader door de afdelingen", en: "Browse the aisles" },
  "cat.aisles": { fr: "Rayons", nl: "Afdelingen", en: "Aisles" },
  "cat.all": { fr: "Tout le catalogue", nl: "De hele catalogus", en: "The whole catalogue" },
  "cat.allOf": { fr: "Tout", nl: "Alles", en: "All" },
  "cat.filters": { fr: "Filtrer et trier", nl: "Filteren en sorteren", en: "Filter and sort" },
  "cat.clear": { fr: "Effacer les filtres", nl: "Filters wissen", en: "Clear filters" },
  "cat.remove": { fr: "Retirer ce filtre", nl: "Filter verwijderen", en: "Remove this filter" },
  "cat.min": { fr: "Prix min", nl: "Min. prijs", en: "Min price" },
  "cat.max": { fr: "Prix max", nl: "Max. prijs", en: "Max price" },
  "cat.sort": { fr: "Trier par", nl: "Sorteren op", en: "Sort by" },
  "cat.per": { fr: "Par page", nl: "Per pagina", en: "Per page" },
  "cat.apply": { fr: "Appliquer", nl: "Toepassen", en: "Apply" },
  "cat.sortRelevance": { fr: "Pertinence", nl: "Relevantie", en: "Relevance" },
  "cat.sortPriceAsc": { fr: "Prix croissant", nl: "Prijs oplopend", en: "Price, low to high" },
  "cat.sortPriceDesc": { fr: "Prix décroissant", nl: "Prijs aflopend", en: "Price, high to low" },
  "cat.sortName": { fr: "Nom", nl: "Naam", en: "Name" },
  "cat.prev": { fr: "Précédent", nl: "Vorige", en: "Previous" },
  "cat.next": { fr: "Suivant", nl: "Volgende", en: "Next" },
  "cat.pageOf": { fr: "Page {p} sur {n}", nl: "Pagina {p} van {n}", en: "Page {p} of {n}" },
  "cat.empty": { fr: "Aucun produit ne correspond à cette sélection.", nl: "Geen enkel product komt overeen met deze selectie.", en: "No product matches this selection." },
  "cat.reset": { fr: "Repartir de tout le catalogue", nl: "Opnieuw beginnen met de hele catalogus", en: "Start again from the whole catalogue" },
  "cat.from": { fr: "à partir de", nl: "vanaf", en: "from" },
  "cat.upTo": { fr: "jusqu'à", nl: "tot", en: "up to" },
  "cat.crumb": { fr: "Fil d'Ariane", nl: "Kruimelpad", en: "Breadcrumb" },

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
// L'ordre porte le positionnement, et le bureau n'affiche que les cinq
// premiers. « Cashback » et « Codes promo » quittent cette tête de liste :
// deux annonceurs ont refusé le partenariat au motif qu'ils ne travaillent pas
// avec ce type d'éditeurs, et la navigation est le premier endroit où un
// responsable d'affiliation lit à quelle catégorie appartient un site. Les
// pages restent en ligne — elles gardent leur valeur de référencement — mais
// elles ne définissent plus la marque.
export const NAV_KEYS: Array<{ key: string; href: string }> = [
  { key: "nav.catalogue", href: "/catalogue" },
  { key: "nav.assistant", href: "/recherche" },
  { key: "nav.how", href: "/comment-ca-marche" },
  { key: "nav.score", href: "/score" },
  { key: "nav.refurb", href: "/reconditionne" },
  { key: "nav.pricing", href: "/tarifs" },
  { key: "nav.cashback", href: "/cashback" },
  { key: "nav.promos", href: "/codes-promo" },
];

const LOCALES: Locale[] = ["fr", "nl", "en"];

type Ctx = {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (k: string) => string;
  /** Pays deviné par géolocalisation (« BE », « NL », …), sinon null. */
  country: string | null;
};
const LocaleCtx = createContext<Ctx>({
  locale: "fr", setLocale: () => {}, t: (k) => k, country: null,
});

/** Valeur d'un cookie, ou null. Lu à la volée : aucune dépendance ajoutée. */
function cookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const found = document.cookie
    .split("; ")
    .find((c) => c.startsWith(name + "="));
  return found ? decodeURIComponent(found.slice(name.length + 1)) : null;
}

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("fr");
  const [country, setCountry] = useState<string | null>(null);

  useEffect(() => {
    setCountry(cookie("filon-country"));

    // Ordre de priorité, du plus explicite au plus supposé :
    //   1. le choix déjà fait par la personne — il ne se rediscute pas ;
    //   2. la langue du navigateur, devinée côté serveur (middleware) ;
    //   3. la langue du navigateur, lue ici si le middleware n'a rien posé ;
    //   4. le français, langue de départ de FILON.
    // La géolocalisation n'intervient qu'à l'étape 2, et jamais seule : la
    // Belgique est bilingue, l'IP ne dit pas ce qu'on lit.
    const chosen = (typeof localStorage !== "undefined"
      && localStorage.getItem("filon-locale")) as Locale | null;
    if (chosen && LOCALES.includes(chosen)) {
      setLocaleState(chosen);
      document.documentElement.lang = chosen;
      return;
    }

    const guessed = (cookie("filon-locale-guess")
      || navigator.language?.split("-")[0]) as Locale | null;
    if (guessed && LOCALES.includes(guessed)) {
      setLocaleState(guessed);
      document.documentElement.lang = guessed;
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
  const value = useMemo(
    () => ({ locale, setLocale, t, country }),
    [locale, setLocale, t, country]
  );
  return <LocaleCtx.Provider value={value}>{children}</LocaleCtx.Provider>;
}

export const useLocale = () => useContext(LocaleCtx);
