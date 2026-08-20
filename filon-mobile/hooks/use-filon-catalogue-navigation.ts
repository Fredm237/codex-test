import { useQuery } from "@tanstack/react-query";

import { getFilonCatalogueNavigation } from "@/lib/filon-api";

export function useFilonCatalogueNavigation(isInternetReachable = true) {
  return useQuery({ queryKey: ["filon-catalogue-navigation"], queryFn: getFilonCatalogueNavigation, enabled: isInternetReachable, staleTime: 5 * 60_000 });
}
