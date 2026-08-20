import { useCallback, useEffect, useState } from "react";

import { clearRecentSearches, readRecentSearches, saveRecentSearch, type RecentSearch } from "@/lib/search-history";

export function useRecentSearches() {
  const [items, setItems] = useState<RecentSearch[]>([]);
  useEffect(() => { void readRecentSearches().then(setItems); }, []);
  const add = useCallback(async (query: string) => { const next = await saveRecentSearch(query); setItems(next); return next; }, []);
  const clear = useCallback(async () => { await clearRecentSearches(); setItems([]); }, []);
  return { items, add, clear };
}
