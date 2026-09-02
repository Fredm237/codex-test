import { useQuery } from "@tanstack/react-query";

import { getFilonProductByEan } from "@/lib/filon-api";
import { normalizeProductCode } from "@/lib/barcode";

export function useFilonProduct(ean: string) {
  const canonicalEan = normalizeProductCode(ean);
  return useQuery({
    queryKey: ["filon", "product", canonicalEan],
    queryFn: () => getFilonProductByEan(canonicalEan!),
    enabled: canonicalEan !== null,
    staleTime: 60_000,
  });
}
