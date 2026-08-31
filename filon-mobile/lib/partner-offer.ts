import { currentFilonStock, isFilonOfferActionable, normalizeFilonCurrency, type FilonOffer } from "./filon-api";

export type ComparedPartnerOffer = { offer: FilonOffer; differenceFromLowest: number; isLowestObserved: boolean };

export function isSafePartnerOfferUrl(value: string): boolean {
  try {
    const url = new URL(value);
    const host = url.hostname.toLowerCase().replace(/^\[|\]$/g, "").replace(/\.+$/, "");
    if (url.protocol !== "https:" || !host || url.username || url.password) return false;
    if (host.includes(":") || host.length > 253) return false;
    const ipv4 = host.match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/)?.slice(1).map(Number);
    if (ipv4) return false;
    const labels = host.split(".");
    const blockedSuffixes = new Set(["localhost", "local", "localdomain", "internal", "lan", "home", "corp", "test", "invalid", "example", "onion"]);
    if (labels.length < 2 || blockedSuffixes.has(labels.at(-1) ?? "")) return false;
    if (host === "home.arpa" || host.endsWith(".home.arpa")) return false;
    const dnsLabel = /^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/;
    return labels.every((label) => dnsLabel.test(label));
  } catch { return false; }
}

export function comparePartnerOffers(offers: FilonOffer[], now: number | Date = Date.now()): ComparedPartnerOffer[] {
  // On détermine d'abord les candidats dont prix/stock/snapshot/lien sont
  // actuels, puis on valide leur devise. Une devise inconnue actuelle interdit
  // la comparaison; une ligne legacy déjà fermée ne peut pas l'empoisonner.
  const candidates = offers.filter((offer) => Number.isFinite(offer.price) && offer.price > 0 && currentFilonStock(offer, now) === true && isSafePartnerOfferUrl(offer.link));
  const currencies = new Set(candidates.map((offer) => normalizeFilonCurrency(offer.currency)).filter((currency): currency is NonNullable<typeof currency> => currency !== null));
  if (currencies.size !== 1 || candidates.some((offer) => normalizeFilonCurrency(offer.currency) === null)) return [];
  const sorted = candidates
    .filter((offer) => isFilonOfferActionable(offer, now))
    .sort((a, b) => a.price - b.price || a.id - b.id);
  const lowest = sorted[0]?.price;
  return sorted.map((offer, index) => ({ offer, differenceFromLowest: lowest === undefined ? 0 : Math.max(0, offer.price - lowest), isLowestObserved: index === 0 }));
}
