import { useCallback, useEffect, useState } from "react";

import { readFavorites, toggleFavorite, type FavoriteOffer } from "@/lib/favorites";
import { haptic } from "@/lib/haptics";
import { recordFollowUpEvent } from "@/lib/follow-up-timeline";

export function useFavorites() {
  const [items, setItems] = useState<FavoriteOffer[]>([]);
  const [ready, setReady] = useState(false);
  const refresh = useCallback(async () => { setItems(await readFavorites()); setReady(true); }, []);
  useEffect(() => { void refresh(); }, [refresh]);
  const toggle = useCallback(async (offer: FavoriteOffer) => { const wasSaved = items.some((item) => item.id === offer.id); const next = await toggleFavorite(offer); setItems(next); await recordFollowUpEvent(wasSaved ? "favorite-removed" : "favorite-added", offer.name); haptic.medium(); return next; }, [items]);
  return { items, ready, refresh, toggle, isSaved: (id: number) => items.some((item) => item.id === id) };
}
