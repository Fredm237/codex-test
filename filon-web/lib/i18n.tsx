"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export type Locale = "fr" | "nl" | "en";

/** Dictionnaire FR/NL/EN. Clés courtes, regroupées par zone. */
const DICT: Record<string, { fr: string; nl: string; en: string }> = {
  // Démonstrations — promesse + objet réel, sur une scène de vie.
  "show.badge1": { fr: "Le prix observé", nl: "De waargenomen prijs", en: "The observed price" },
  "show.t1": { fr: "Le même article, vendu", nl: "Hetzelfde artikel, verkocht", en: "The same item, sold" },
  "show.e1": { fr: "à deux prix.", nl: "voor twee prijzen.", en: "at two prices." },
  "show.b1": { fr: "Lorsque plusieurs offres partagent un identifiant produit, FILON montre l'écart entre les prix observés dans le catalogue indexé.", nl: "Wanneer meerdere aanbiedingen dezelfde productidentificatie delen, toont FILON het verschil tussen de waargenomen prijzen in de geïndexeerde catalogus.", en: "When several offers share a product identifier, FILON shows the gap between observed prices in the indexed catalogue." },

  "show.badge2": { fr: "L'historique disponible", nl: "De beschikbare historiek", en: "Available history" },
  "show.t2": { fr: "Une variation remise", nl: "Een verandering geplaatst", en: "A change placed" },
  "show.e2": { fr: "dans son contexte.", nl: "in haar context.", en: "in context." },
  "show.b2": { fr: "Quand l'historique contient assez de relevés, le Verdict compare le prix courant aux observations disponibles. Sinon, il s'abstient.", nl: "Wanneer de historiek genoeg metingen bevat, vergelijkt het Verdict de huidige prijs met de beschikbare waarnemingen. Anders onthoudt het zich.", en: "When history contains enough readings, the Verdict compares the current price with available observations. Otherwise, it abstains." },

  "show.badge3": { fr: "Conditions à confirmer", nl: "Voorwaarden te bevestigen", en: "Terms to confirm" },
  "show.t3": { fr: "Les données de l'offre, visibles", nl: "De aanbiedingsgegevens, zichtbaar", en: "Offer data, visible" },
  "show.e3": { fr: "avant de payer.", nl: "voor je betaalt.", en: "before you pay." },
  "show.b3": { fr: "FILON restitue le marchand, le prix et la disponibilité lorsqu'ils sont fournis. Le total, le stock et les conditions restent à confirmer chez le vendeur.", nl: "FILON toont winkel, prijs en beschikbaarheid wanneer die zijn verstrekt. Bevestig totaal, voorraad en voorwaarden bij de verkoper.", en: "FILON shows the merchant, price and availability when supplied. Confirm the total, stock and terms with the seller." },

  // Vivant — pouls du catalogue et rangées.
  "pulse.last": { fr: "Dernier relevé", nl: "Laatste meting", en: "Last reading" },
  "pulse.ago": { fr: "il y a", nl: "", en: "" },
  "pulse.now": { fr: "à l'instant", nl: "zojuist", en: "just now" },
  "pulse.yesterday": { fr: "hier", nl: "gisteren", en: "yesterday" },
  "pulse.days": { fr: "jours", nl: "dagen geleden", en: "days ago" },
  "pulse.readings": { fr: "prix relevés sur les dernières 24 h", nl: "prijzen gemeten in de voorbije 24 uur", en: "prices read in the last 24 hours" },
  "pulse.drops": { fr: "ont baissé sur les dernières 24 h", nl: "daalden in de voorbije 24 uur", en: "dropped in the last 24 hours" },

  "rail.dropsT": { fr: "Baisses dans les relevés comparables", nl: "Dalingen in vergelijkbare metingen", en: "Drops in comparable readings" },
  "rail.dropsS": { fr: "Prix, devise, stock et relevé actuel rapprochés.", nl: "Prijs, valuta, voorraad en huidige meting gekoppeld.", en: "Price, currency, stock and current reading reconciled." },
  "rail.lowestT": { fr: "Plus bas parmi les relevés suivis", nl: "Laagste binnen de gevolgde metingen", en: "Lowest among tracked readings" },
  "rail.lowestS": { fr: "Périmètre limité aux observations comparables conservées par FILON.", nl: "Beperkt tot vergelijkbare metingen die FILON bewaart.", en: "Limited to comparable observations retained by FILON." },
  "rail.budgetT": { fr: "Prix catalogue sous 100 €", nl: "Catalogusprijzen onder €100", en: "Catalogue prices under €100" },
  "rail.budgetS": { fr: "Prix et disponibilité à confirmer chez le marchand.", nl: "Bevestig prijs en beschikbaarheid bij de winkel.", en: "Confirm price and availability with the merchant." },
  "rail.freshT": { fr: "Sélection du catalogue", nl: "Selectie uit de catalogus", en: "Catalogue selection" },
  "rail.freshS": { fr: "Prix et disponibilité à confirmer chez le marchand.", nl: "Bevestig prijs en beschikbaarheid bij de winkel.", en: "Confirm price and availability with the merchant." },

  // Refonte 2026 — hero, méthode, clôture, catalogue.
  "hero.eyebrowNew": { fr: "Copilote d'achat · Belgique", nl: "Aankoopcopiloot · België", en: "Shopping copilot · Belgium" },
  "hero.l1": { fr: "Est-ce vraiment", nl: "Is dit echt", en: "Is this really" },
  "hero.l2": { fr: "le bon", nl: "de juiste", en: "the right" },
  "hero.l3": { fr: "prix ?", nl: "prijs?", en: "price?" },
  "hero.subtitle": { fr: "FILON compare les offres réellement comparables et vous montre ce que le prix d’aujourd’hui vaut.", nl: "FILON vergelijkt echt vergelijkbare aanbiedingen en toont wat de prijs van vandaag waard is.", en: "FILON compares genuinely comparable offers and shows what today’s price is worth." },
  "hero.ledeA": { fr: "FILON réunit les offres de", nl: "FILON bundelt de aanbiedingen van", en: "FILON gathers the offers of" },
  "hero.ledeB": { fr: "marchands indexés et montre l'historique disponible, sa durée et sa fraîcheur.", nl: "geïndexeerde winkels en toont de beschikbare prijshistoriek, de duur en actualiteit ervan.", en: "indexed merchants and shows available price history, its duration and freshness." },
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
  "method.s1b": { fr: "FILON regroupe les offres lorsqu'un identifiant produit commun et exploitable est disponible. Sans preuve d'identité suffisante, elles restent séparées.", nl: "FILON groepeert aanbiedingen wanneer een bruikbare gedeelde productidentificatie beschikbaar is. Zonder voldoende identiteitsbewijs blijven ze gescheiden.", en: "FILON groups offers when a usable shared product identifier is available. Without sufficient identity evidence, they remain separate." },
  "method.s2t": { fr: "On garde l'historique", nl: "We bewaren de geschiedenis", en: "We keep the history" },
  "method.s2b": { fr: "Les relevés disponibles sont horodatés. Leur nombre, leur durée et leur fraîcheur déterminent si un contexte historique peut être affiché.", nl: "Beschikbare metingen krijgen een tijdstempel. Aantal, duur en actualiteit bepalen of prijscontext kan worden getoond.", en: "Available readings are timestamped. Their count, duration and freshness determine whether historical context can be shown." },
  "method.s3t": { fr: "On tranche", nl: "We hakken de knoop door", en: "We decide" },
  "method.s3b": { fr: "Le Verdict expose les signaux documentés, les inconnues et le périmètre comparé. Si les preuves ne suffisent pas, il s'abstient.", nl: "Het Verdict toont gedocumenteerde signalen, onbekenden en de vergelijkingsomvang. Bij onvoldoende bewijs onthoudt het zich.", en: "The Verdict exposes documented signals, unknowns and the comparison scope. If evidence is insufficient, it abstains." },

  "closing.eyebrow": { fr: "Avant de payer", nl: "Voor je betaalt", en: "Before you pay" },
  "closing.t1": { fr: "Posez la question à FILON.", nl: "Stel de vraag aan FILON.", en: "Ask FILON." },
  "closing.t2": { fr: "C'est gratuit, et c'est rapide.", nl: "Het is gratis, en het gaat snel.", en: "It's free, and it's fast." },
  "closing.factsA": { fr: "offres suivies chez", nl: "gevolgde aanbiedingen bij", en: "offers tracked across" },
  "closing.factsB": { fr: "marchands indexés.", nl: "geïndexeerde winkels.", en: "indexed merchants." },
  "closing.fallback": { fr: "Les offres indexées, avec leur source et leur fraîcheur lorsqu'elles sont connues.", nl: "Geïndexeerde aanbiedingen, met bron en actualiteit wanneer bekend.", en: "Indexed offers, with their source and freshness when known." },

  "cat.title1": { fr: "Le catalogue,", nl: "De catalogus,", en: "The catalogue," },
  "cat.title2": { fr: "pour choisir sans deviner.", nl: "om te kiezen zonder giswerk.", en: "to choose without guessing." },
  "cat.count": { fr: "offres indexées dans le catalogue.", nl: "aanbiedingen in de catalogus geïndexeerd.", en: "offers indexed in the catalogue." },
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
  "cat.askAssistant": { fr: "Décrire mon besoin à l’assistant", nl: "Mijn behoefte aan de assistent beschrijven", en: "Describe my need to the assistant" },
  "cat.reset": { fr: "Repartir de tout le catalogue", nl: "Opnieuw beginnen met de hele catalogus", en: "Start again from the whole catalogue" },
  "cat.from": { fr: "à partir de", nl: "vanaf", en: "from" },
  "cat.upTo": { fr: "jusqu'à", nl: "tot", en: "up to" },
  "cat.crumb": { fr: "Fil d'Ariane", nl: "Kruimelpad", en: "Breadcrumb" },

  // Navigation
  "nav.catalogue": { fr: "Catalogue", nl: "Catalogus", en: "Catalogue" },
  "nav.assistant": { fr: "Assistant", nl: "Assistent", en: "Assistant" },
  "nav.create": { fr: "Créer", nl: "Creëren", en: "Create" },
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
    fr: "Décrivez ce que vous cherchez. FILON classe les offres indexées et s'abstient si les preuves manquent.",
    nl: "Beschrijf wat je zoekt. FILON rangschikt geïndexeerde aanbiedingen en onthoudt zich bij onvoldoende bewijs.",
    en: "Describe what you're looking for. FILON ranks indexed offers and abstains when evidence is insufficient.",
  },
  // Scène finale / CTA de clôture
  "final.eyebrow": { fr: "Avant de choisir", nl: "Voor je kiest", en: "Before you choose" },
  "final.title_a": { fr: "Demandez à FILON", nl: "Vraag het aan FILON", en: "Ask FILON" },
  "final.title_b": { fr: "avant d'acheter", nl: "voordat je koopt", en: "before you buy" },
  "final.note": {
    fr: "Accès actuel sans carte bancaire. Consultez nos conditions et notre politique de confidentialité.",
    nl: "Huidige toegang zonder bankkaart. Raadpleeg onze voorwaarden en ons privacybeleid.",
    en: "Current access requires no payment card. See our terms and privacy policy.",
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
  { key: "nav.create", href: "/creer/outfit-studio" },
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
