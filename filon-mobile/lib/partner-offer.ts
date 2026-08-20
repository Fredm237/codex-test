import type { FilonOffer } from "@/lib/filon-api";

export type ComparedPartnerOffer = { offer: FilonOffer; differenceFromLowest: number; isLowestObserved: boolean };

export function isSafePartnerOfferUrl(value: string): boolean {
  try {
    const url = new URL(value);
    const host = url.hostname.toLowerCase();
    return url.protocol === "https:" && host.length > 0 && host !== "localhost" && host !== "127.0.0.1" && host !== "::1";
  } catch { return false; }
}

export function comparePartnerOffers(offers: FilonOffer[]): ComparedPartnerOffer[] {
  const sorted = [...offers].filter((offer) => Number.isFinite(offer.price) && offer.price >= 0).sort((a, b) => a.price - b.price || Number(b.inStock) - Number(a.inStock));
  const lowest = sorted[0]?.price;
  return sorted.map((offer, index) => ({ offer, differenceFromLowest: lowest === undefined ? 0 : Math.max(0, offer.price - lowest), isLowestObserved: index === 0 }));
}
