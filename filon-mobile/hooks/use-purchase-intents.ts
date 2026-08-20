import { useCallback, useEffect, useState } from "react";

import { readPurchaseIntents, removePurchaseIntent, savePurchaseIntent, type PurchaseIntent, type PurchaseIntentDraft } from "@/lib/purchase-intents";

export function usePurchaseIntents() {
  const [items, setItems] = useState<PurchaseIntent[]>([]);
  const [ready, setReady] = useState(false);

  const refresh = useCallback(async () => {
    const next = await readPurchaseIntents();
    setItems(next);
    setReady(true);
    return next;
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);

  const save = useCallback(async (draft: PurchaseIntentDraft, existing?: PurchaseIntent) => {
    const next = await savePurchaseIntent(draft, existing);
    setItems((current) => [next, ...current.filter((item) => item.id !== next.id)].slice(0, 10));
    return next;
  }, []);

  const remove = useCallback(async (id: string) => {
    const next = await removePurchaseIntent(id);
    setItems(next);
    return next;
  }, []);

  return { items, ready, refresh, save, remove };
}
