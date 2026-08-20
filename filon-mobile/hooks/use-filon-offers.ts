import { useQuery } from "@tanstack/react-query";

import { searchFilonOffers } from "@/lib/filon-api";

export function useFilonOffers(query: string, isInternetReachable = true) {
  const normalized = query.trim();
  return useQuery({
    queryKey: ["filon-offers", normalized],
    queryFn: () => searchFilonOffers(normalized),
    enabled: normalized.length >= 2 && isInternetReachable,
    staleTime: 45_000,
  });
}
