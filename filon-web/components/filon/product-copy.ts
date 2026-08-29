// Libellés et formatage de la carte produit.
//
// Séparés de ProductCard.tsx à dessein : ce dernier porte « use client », et
// une valeur exportée depuis un module client devient une *référence* client
// quand un composant serveur l'importe — pas l'objet lui-même. La page
// catalogue recevait donc `copy` indéfini et rendait une 500.
//
// Un module neutre s'importe correctement des deux côtés.

import { normalizeSupportedCurrency } from "@/lib/currency";

export type CardLocale = "fr" | "nl" | "en";

export type CardCopy = {
  see: string;
  at: string;
  lowest: string;
  noImage: string;
  available: string;
  unavailable: string;
  availabilityUnknown: string;
  observedToday: string;
  observedYesterday: string;
  observedDays: (days: number) => string;
  observedOn: (date: string) => string;
  observationUnavailable: string;
};

export const CARD_COPY: Record<CardLocale, CardCopy> = {
  fr: {
    see: "Voir l'offre", at: "chez", lowest: "Prix le plus bas relevé", noImage: "Visuel indisponible",
    available: "En stock dans le dernier flux", unavailable: "Indisponible dans le dernier flux", availabilityUnknown: "Disponibilité non renseignée",
    observedToday: "Prix relevé il y a moins de 24 h", observedYesterday: "Prix relevé il y a 1 j", observedDays: (days) => `Prix relevé il y a ${days} j`, observedOn: (date) => `Prix relevé le ${date}`, observationUnavailable: "Date de relevé non disponible",
  },
  nl: {
    see: "Bekijk aanbod", at: "bij", lowest: "Laagste gemeten prijs", noImage: "Geen afbeelding",
    available: "Op voorraad in de laatste feed", unavailable: "Niet beschikbaar in de laatste feed", availabilityUnknown: "Beschikbaarheid niet vermeld",
    observedToday: "Prijs minder dan 24 uur geleden gemeten", observedYesterday: "Prijs 1 dag geleden gemeten", observedDays: (days) => `Prijs ${days} d geleden gemeten`, observedOn: (date) => `Prijs gemeten op ${date}`, observationUnavailable: "Meetdatum niet beschikbaar",
  },
  en: {
    see: "See offer", at: "at", lowest: "Lowest observed price", noImage: "No image",
    available: "In stock in the latest feed", unavailable: "Unavailable in the latest feed", availabilityUnknown: "Availability not provided",
    observedToday: "Price checked less than 24h ago", observedYesterday: "Price checked 1 day ago", observedDays: (days) => `Price checked ${days} days ago`, observedOn: (date) => `Price checked on ${date}`, observationUnavailable: "Check date unavailable",
  },
};

export const OFFER_MAX_AGE_HOURS = 72;
const OFFER_MAX_AGE_MS = OFFER_MAX_AGE_HOURS * 60 * 60 * 1000;
const ISO_DATE_TIME = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?(Z|[+-]\d{2}:?\d{2})?$/i;

export type PurchasableOfferEvidence = {
  price?: unknown;
  currency?: unknown;
  in_stock?: unknown;
  observed_at?: unknown;
  /** Le serveur a rapproché le relevé du prix, de la devise et du stock actuels. */
  evidence_current?: unknown;
  link?: unknown;
};

export type ComparableHistoryPoint = {
  price: number;
  currency: string;
  at: string;
  in_stock: true;
};

export function positiveFinitePrice(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value) && value > 0;
}

/**
 * Lit uniquement les dates ISO transmises par le catalogue. Les anciennes
 * dates SQL sans suffixe sont en UTC : les traiter comme une heure locale
 * ferait varier l'éligibilité d'une offre selon le fuseau du visiteur.
 */
export function observationTimestamp(value: unknown): number | null {
  if (typeof value !== "string") return null;
  const raw = value.trim();
  const parts = raw.match(ISO_DATE_TIME);
  if (!parts) return null;
  const [, yearText, monthText, dayText, hourText, minuteText, secondText, fraction = ""] = parts;
  const [year, month, day, hour, minute, second] = [
    yearText, monthText, dayText, hourText, minuteText, secondText,
  ].map(Number);
  const millisecond = Number(`${fraction}000`.slice(0, 3));
  const calendar = new Date(0);
  calendar.setUTCFullYear(year, month - 1, day);
  calendar.setUTCHours(hour, minute, second, millisecond);
  if (
    calendar.getUTCFullYear() !== year
    || calendar.getUTCMonth() !== month - 1
    || calendar.getUTCDate() !== day
    || calendar.getUTCHours() !== hour
    || calendar.getUTCMinutes() !== minute
    || calendar.getUTCSeconds() !== second
  ) return null;
  const zoned = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(raw) ? raw : `${raw}Z`;
  const timestamp = Date.parse(zoned);
  return Number.isFinite(timestamp) ? timestamp : null;
}

function referenceTimestamp(now: number | Date): number | null {
  const timestamp = now instanceof Date ? now.getTime() : now;
  return Number.isFinite(timestamp) ? timestamp : null;
}

/** Une observation absente, illisible, future ou âgée de plus de 72 h
 * reste inconnue et ne peut jamais ouvrir une action d'achat. */
export function isFreshObservation(
  value: unknown,
  now: number | Date = Date.now(),
): boolean {
  const observed = observationTimestamp(value);
  const reference = referenceTimestamp(now);
  if (observed == null || reference == null) return false;
  const age = reference - observed;
  return age >= 0 && age <= OFFER_MAX_AGE_MS;
}

/** Âge entier d'un relevé valide. `null` couvre aussi bien une date absente
 * qu'une date future, afin qu'aucun libellé de fraîcheur ne puisse être
 * fabriqué à partir d'une preuve temporelle invalide. */
export function observationAgeHours(
  value: unknown,
  now: number | Date = Date.now(),
): number | null {
  const observed = observationTimestamp(value);
  const reference = referenceTimestamp(now);
  if (observed === null || reference === null || observed > reference) return null;
  return Math.floor((reference - observed) / (60 * 60 * 1000));
}

/** Même convention que le Core : nombre de jours entiers entre le premier et
 * le dernier relevé comparable effectivement conservé par le client. */
export function comparableHistoryTrackedDays(
  history: readonly Pick<ComparableHistoryPoint, "at">[],
): number {
  if (history.length < 2) return 0;
  const first = observationTimestamp(history[0]?.at);
  const last = observationTimestamp(history[history.length - 1]?.at);
  if (first === null || last === null || last < first) return 0;
  return Math.floor((last - first) / (24 * 60 * 60 * 1000));
}

export function isSafeExternalOfferUrl(value: unknown): boolean {
  if (typeof value !== "string" || value.trim().length === 0) return false;
  try {
    const url = new URL(value);
    const host = url.hostname.toLowerCase().replace(/^\[|\]$/g, "").replace(/\.+$/, "");
    if (url.protocol !== "https:" || !host || url.username || url.password) return false;
    // Un lien marchand doit porter un domaine attestable. Rejeter tous les
    // littéraux IP ferme aussi les plages spéciales, de test et partagées que
    // les listes partielles de réseaux privés oublient facilement.
    if (host.includes(":") || host.length > 253) return false;
    const ipv4 = host.match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/)?.slice(1).map(Number);
    if (ipv4) return false;
    const labels = host.split(".");
    const blockedSuffixes = new Set([
      "localhost", "local", "localdomain", "internal", "lan", "home",
      "corp", "test", "invalid", "example", "onion",
    ]);
    if (labels.length < 2 || blockedSuffixes.has(labels.at(-1) ?? "")) return false;
    if (host === "home.arpa" || host.endsWith(".home.arpa")) return false;
    const dnsLabel = /^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/;
    return labels.every((label) => dnsLabel.test(label));
  } catch {
    return false;
  }
}

export function currentStockState(
  offer: Pick<PurchasableOfferEvidence, "in_stock" | "observed_at" | "evidence_current">,
  now: number | Date = Date.now(),
): boolean | null {
  if (offer.evidence_current !== true || !isFreshObservation(offer.observed_at, now)) return null;
  return offer.in_stock === true ? true : offer.in_stock === false ? false : null;
}

/** Un prix ne devient publiable que si le serveur l'a rapproché d'un relevé
 * récent portant aussi une devise reconnue et un état de stock explicite.
 * L'offre peut être indisponible : son dernier prix reste alors informatif,
 * mais ne doit jamais ouvrir une action d'achat. */
export function hasCurrentOfferEvidence(
  offer: Pick<
    PurchasableOfferEvidence,
    "price" | "currency" | "in_stock" | "observed_at" | "evidence_current"
  >,
  now: number | Date = Date.now(),
): boolean {
  return positiveFinitePrice(offer.price)
    && normalizeSupportedCurrency(offer.currency) !== null
    && (offer.in_stock === true || offer.in_stock === false)
    && offer.evidence_current === true
    && isFreshObservation(offer.observed_at, now);
}

export function isPurchasableOffer(
  offer: PurchasableOfferEvidence,
  now: number | Date = Date.now(),
): boolean {
  return hasCurrentOfferEvidence(offer, now)
    && offer.in_stock === true
    && isSafeExternalOfferUrl(offer.link);
}

/** Retourne une devise seulement si chaque valeur appartient au registre et si
 * elles sont toutes identiques. Sans moteur FX, deux devises ne sont jamais
 * ordonnées ni agrégées. */
export function commonSupportedCurrency(values: readonly unknown[]): string | null {
  if (values.length === 0) return null;
  const currencies = values.map(normalizeSupportedCurrency);
  if (currencies.some((currency) => currency === null)) return null;
  const unique = new Set(currencies as string[]);
  return unique.size === 1 ? [...unique][0] : null;
}

export function orderOffersForDisplay<T extends { id: number; price?: unknown; currency?: unknown }>(
  offers: readonly T[],
): T[] {
  const canSortByPrice = offers.length > 0
    && offers.every((offer) => positiveFinitePrice(offer.price))
    && commonSupportedCurrency(offers.map((offer) => offer.currency)) !== null;
  return [...offers].sort((left, right) => {
    if (canSortByPrice) {
      const priceDifference = Number(left.price) - Number(right.price);
      if (priceDifference !== 0) return priceDifference;
    }
    // En multidevise (ou avec une devise inconnue), l'identifiant stable casse
    // tout ordre de prix potentiellement trompeur reçu de l'API legacy.
    return left.id - right.id;
  });
}

export type ProductComparison<T> = {
  currency: string;
  offers: T[];
  best: T;
  priceMin: number;
  priceMax: number;
};

export function deriveProductComparison<T extends PurchasableOfferEvidence & { id: number }>(
  offers: readonly T[],
  now: number | Date = Date.now(),
): ProductComparison<T> | null {
  const eligible = offers.filter((offer) => isPurchasableOffer(offer, now));
  const currency = commonSupportedCurrency(eligible.map((offer) => offer.currency));
  if (currency === null) return null;
  const ordered = orderOffersForDisplay(eligible);
  const first = ordered[0];
  const last = ordered[ordered.length - 1];
  if (!first || !last || !positiveFinitePrice(first.price) || !positiveFinitePrice(last.price)) return null;
  return {
    currency,
    offers: ordered,
    best: first,
    priceMin: first.price,
    priceMax: last.price,
  };
}

/**
 * L'historique ne hérite jamais de la devise du prix courant. Chaque point
 * doit la porter explicitement, avec un montant positif, une date réelle et
 * une disponibilité attestée. Un prix indisponible n'est pas comparable à une
 * offre que l'utilisateur pouvait effectivement acheter.
 */
export function comparablePriceHistory(
  history: readonly { price?: unknown; currency?: unknown; at?: unknown; in_stock?: unknown }[],
  offerCurrency: unknown,
  now: number | Date = Date.now(),
): ComparableHistoryPoint[] {
  const currency = normalizeSupportedCurrency(offerCurrency);
  const reference = referenceTimestamp(now);
  if (currency === null || reference === null) return [];
  return history.reduce<ComparableHistoryPoint[]>((points, entry) => {
    const pointCurrency = normalizeSupportedCurrency(entry.currency);
    const timestamp = observationTimestamp(entry.at);
    if (
      !positiveFinitePrice(entry.price)
      || pointCurrency !== currency
      || entry.in_stock !== true
      || timestamp === null
      || timestamp > reference
    ) return points;
    points.push({ price: entry.price, currency, at: new Date(timestamp).toISOString(), in_stock: true });
    return points;
  }, []).sort((left, right) => Date.parse(left.at) - Date.parse(right.at));
}

export function money(
  price: number | null | undefined,
  currency: string | null | undefined,
  locale: CardLocale = "fr"
): string {
  const normalizedCurrency = normalizeSupportedCurrency(currency);
  if (!positiveFinitePrice(price) || normalizedCurrency === null) return "—";
  const numberLocale = locale === "nl" ? "nl-BE" : locale === "en" ? "en-GB" : "fr-BE";
  return new Intl.NumberFormat(numberLocale, {
    style: "currency",
    currency: normalizedCurrency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(price);
}
