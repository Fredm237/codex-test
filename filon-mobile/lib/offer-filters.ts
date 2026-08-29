import { currentFilonStock, type FilonOffer } from "./filon-api";

export type OfferFilters = { inStockOnly: boolean; merchant: string | null; brand: string | null };

export const defaultOfferFilters: OfferFilters = { inStockOnly: false, merchant: null, brand: null };

export function filterOffers(offers: FilonOffer[], filters: OfferFilters, now: number | Date = Date.now()) {
  return offers.filter((offer) => {
    if (filters.inStockOnly && currentFilonStock(offer, now) !== true) return false;
    if (filters.merchant && offer.merchantSlug !== filters.merchant) return false;
    if (filters.brand && offer.brand?.localeCompare(filters.brand, undefined, { sensitivity: "accent" }) !== 0) return false;
    return true;
  });
}
