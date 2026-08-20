import { useInfiniteQuery } from "@tanstack/react-query";

import { searchFilonOffers, type FilonOfferSearch } from "@/lib/filon-api";

const PAGE_SIZE = 24;

export function useFilonOfferFeed(criteria: FilonOfferSearch, enabled = true) {
  const key = { ...criteria, query: criteria.query?.trim() || "", limit: PAGE_SIZE, offset: undefined };
  return useInfiniteQuery({
    queryKey: ["filon-offer-feed", key],
    queryFn: ({ pageParam }) => searchFilonOffers({ ...criteria, limit: PAGE_SIZE, offset: pageParam }),
    initialPageParam: 0,
    enabled,
    staleTime: 45_000,
    getNextPageParam: (last) => last.offset + last.items.length < last.total ? last.offset + last.items.length : undefined,
  });
}
