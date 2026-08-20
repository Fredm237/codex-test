import { useQuery } from "@tanstack/react-query";

import { getFilonOfferDetail } from "@/lib/filon-api";

export function useFilonOfferDetail(offerId: number | undefined) {
  return useQuery({ queryKey: ["filon", "offer-detail", offerId], queryFn: () => getFilonOfferDetail(offerId!), enabled: typeof offerId === "number" && offerId > 0, staleTime: 60_000 });
}
