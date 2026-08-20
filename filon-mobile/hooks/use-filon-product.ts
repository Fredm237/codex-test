import { useQuery } from "@tanstack/react-query";

import { getFilonProductByEan } from "@/lib/filon-api";

export function useFilonProduct(ean: string) {
  return useQuery({ queryKey: ["filon", "product", ean], queryFn: () => getFilonProductByEan(ean), enabled: ean.length >= 8, staleTime: 60_000 });
}
