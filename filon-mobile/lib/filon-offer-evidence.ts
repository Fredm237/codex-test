import {
  isFilonOfferPriceCurrent,
  normalizeFilonCurrency,
  normalizeFilonObservedAt,
  type FilonOffer,
} from "./filon-api";
import { isSafePartnerOfferUrl } from "./partner-offer";

/**
 * Les paramètres Expo Router sont des indices d'affichage, jamais une preuve.
 * Ils peuvent provenir d'un lien profond externe et doivent donc être
 * rapprochés d'une réponse catalogue avant d'autoriser une action.
 */
export type RoutedOfferFacts = {
  id?: unknown;
  name?: unknown;
  price?: unknown;
  currency?: unknown;
  merchant?: unknown;
  link?: unknown;
  stock?: unknown;
  observedAt?: unknown;
  observed_at?: unknown;
  evidenceCurrent?: unknown;
};

function optionalText(value: unknown) {
  if (value === undefined || value === null || value === "") return null;
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : false;
}

function positiveInteger(value: unknown) {
  if (typeof value !== "string" && typeof value !== "number") return null;
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

function positivePrice(value: unknown) {
  if (typeof value !== "string" && typeof value !== "number") return null;
  if (typeof value === "string" && value.trim().length === 0) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

function matchesOptionalText(value: unknown, expected: string) {
  const text = optionalText(value);
  return text === null || (text !== false && text === expected);
}

/**
 * Compare uniquement les faits critiques fournis par la navigation. Un champ
 * absent ne reçoit aucune valeur inventée; un champ présent mais malformé ou
 * contradictoire ferme l'action.
 */
export function routedOfferFactsMatch(facts: RoutedOfferFacts, detailed: FilonOffer) {
  const id = positiveInteger(facts.id);
  if (id === null || id !== detailed.id) return false;
  if (!matchesOptionalText(facts.name, detailed.name)) return false;
  if (!matchesOptionalText(facts.merchant, detailed.merchantName)) return false;
  if (!matchesOptionalText(facts.link, detailed.link)) return false;

  const routedPriceText = optionalText(facts.price);
  if (routedPriceText !== null) {
    const price = positivePrice(facts.price);
    if (routedPriceText === false || price === null || price !== detailed.price) return false;
  }

  const routedCurrencyText = optionalText(facts.currency);
  if (routedCurrencyText !== null) {
    const currency = normalizeFilonCurrency(facts.currency);
    if (routedCurrencyText === false || currency === null || currency !== detailed.currency) return false;
  }

  const routedObservedAtValue = facts.observedAt ?? facts.observed_at;
  const routedObservedAtText = optionalText(routedObservedAtValue);
  if (routedObservedAtText !== null) {
    const observedAt = normalizeFilonObservedAt(routedObservedAtValue);
    const detailedObservedAt = normalizeFilonObservedAt(detailed.observedAt);
    if (routedObservedAtText === false || observedAt === null || observedAt !== detailedObservedAt) return false;
  }

  const evidenceCurrent = optionalText(facts.evidenceCurrent);
  if (evidenceCurrent !== null) {
    if (evidenceCurrent === false || (evidenceCurrent !== "1" && evidenceCurrent !== "0")) return false;
    if ((evidenceCurrent === "1") !== (detailed.evidenceCurrent === true)) return false;
  }

  const stock = optionalText(facts.stock);
  if (stock !== null && stock !== "unknown") {
    if (stock === false || (stock !== "1" && stock !== "0")) return false;
    const expectedStock = stock === "1";
    if (detailed.inStock !== expectedStock) return false;
  }
  return true;
}

/**
 * Seule la réponse de détail peut autoriser une action. Le snapshot routé
 * n'est jamais retourné, même s'il paraît plus récent ou si le réseau tombe.
 */
export function selectVerifiedDetailOffer(
  facts: RoutedOfferFacts,
  detailed: FilonOffer | null,
  now: number | Date = Date.now(),
) {
  if (
    detailed === null
    || !routedOfferFactsMatch(facts, detailed)
    || !isFilonOfferPriceCurrent(detailed, now)
    || !isSafePartnerOfferUrl(detailed.link)
  ) return null;
  return detailed;
}

/**
 * La création d'alerte exige en plus que l'identité, le prix, la devise et
 * le snapshot aient tous été transportés explicitement puis retrouvés à
 * l'identique dans le détail catalogue.
 */
export function selectVerifiedAlertOffer(
  facts: RoutedOfferFacts,
  detailed: FilonOffer | null,
  now: number | Date = Date.now(),
) {
  const name = optionalText(facts.name);
  if (
    positiveInteger(facts.id) === null
    || name === null
    || name === false
    || positivePrice(facts.price) === null
    || normalizeFilonCurrency(facts.currency) === null
    || normalizeFilonObservedAt(facts.observedAt) === null
    || facts.evidenceCurrent !== "1"
  ) return null;
  return selectVerifiedDetailOffer(facts, detailed, now);
}
