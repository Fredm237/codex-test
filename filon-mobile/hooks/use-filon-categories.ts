import { useQuery } from "@tanstack/react-query";

import { getFilonCatalogueNavigation } from "@/lib/filon-api";

export function useFilonCategories(isInternetReachable = true) {
  return useQuery({ queryKey: ["filon-category-coverage"], queryFn: async () => (await getFilonCatalogueNavigation()).categories, enabled: isInternetReachable, staleTime: 5 * 60_000 });
}
