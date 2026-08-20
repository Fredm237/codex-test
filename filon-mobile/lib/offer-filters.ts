import type { FilonOffer } from "@/lib/filon-api";

export type OfferFilters = { minPrice: number | null; maxPrice: number | null; inStockOnly: boolean; merchant: string | null; brand: string | null };

export const defaultOfferFilters: OfferFilters = { minPrice: null, maxPrice: null, inStockOnly: false, merchant: null, brand: null };

export function filterOffers(offers: FilonOffer[], filters: OfferFilters) {
  return offers.filter((offer) => {
    if (filters.minPrice !== null && offer.price < filters.minPrice) return false;
    if (filters.maxPrice !== null && offer.price > filters.maxPrice) return false;
    if (filters.inStockOnly && !offer.inStock) return false;
    if (filters.merchant && offer.merchantSlug !== filters.merchant) return false;
    if (filters.brand && offer.brand?.localeCompare(filters.brand, undefined, { sensitivity: "accent" }) !== 0) return false;
    return true;
  });
}
