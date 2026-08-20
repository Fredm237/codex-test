import { useQuery } from "@tanstack/react-query";

import { getFilonCatalogueFacets, getFilonCataloguePulse, getFilonCatalogueRelief, getFilonMerchants } from "@/lib/filon-api";

export function useFilonCatalogueFacets(enabled = true) {
  return useQuery({ queryKey: ["filon", "catalogue-facets"], queryFn: () => getFilonCatalogueFacets(), enabled, staleTime: 5 * 60_000 });
}

export function useFilonCatalogueMerchants(enabled = true) {
  return useQuery({ queryKey: ["filon", "catalogue-merchants"], queryFn: () => getFilonMerchants(), enabled, staleTime: 15 * 60_000 });
}

export function useFilonCataloguePulse(enabled = true) {
  return useQuery({ queryKey: ["filon-catalogue-pulse"], queryFn: getFilonCataloguePulse, enabled, staleTime: 60_000 });
}

export function useFilonCatalogueRelief(enabled = true) {
  return useQuery({ queryKey: ["filon-catalogue-relief"], queryFn: getFilonCatalogueRelief, enabled, staleTime: 5 * 60_000 });
}
