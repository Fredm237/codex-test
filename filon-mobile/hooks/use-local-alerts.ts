import { useFocusEffect } from "expo-router";
import { useCallback, useRef, useState } from "react";

import {
  emptyLocalPriceAlertState,
  markPriceAlertsPending,
  reconcilePriceAlertsAfterSync,
  removeLocalPriceAlertFromList,
  updateLocalPriceAlertState,
  type LocalPriceAlert,
  type LocalPriceAlertState,
} from "@/lib/alerts";
import { recordFollowUpEvent } from "@/lib/follow-up-timeline";
import { haptic } from "@/lib/haptics";

export function useLocalAlerts() {
  const [state, setState] = useState<LocalPriceAlertState>(emptyLocalPriceAlertState);
  const [ready, setReady] = useState(false);
  const stateRef = useRef<LocalPriceAlertState>(emptyLocalPriceAlertState);

  const enqueue = useCallback((transition: (current: LocalPriceAlertState) => LocalPriceAlertState) => {
    return updateLocalPriceAlertState(transition).then((next) => {
      stateRef.current = next;
      setState(next);
      return next;
    });
  }, []);

  const refresh = useCallback(() => {
    return updateLocalPriceAlertState((current) => current).then((next) => {
      stateRef.current = next;
      setState(next);
      setReady(true);
      return next;
    });
  }, []);

  useFocusEffect(useCallback(() => { void refresh(); }, [refresh]));

  const remove = useCallback(async (offerId: number) => {
    const removed = stateRef.current.items.find((item) => item.offerId === offerId);
    const next = await enqueue((current) => markPriceAlertsPending({ ...current, items: removeLocalPriceAlertFromList(current.items, offerId) }));
    if (removed) await recordFollowUpEvent("alert-removed", removed.name);
    haptic.medium();
    return next.items;
  }, [enqueue]);
  const markReconciled = useCallback(
    (syncedItems: LocalPriceAlert[]) => enqueue((current) => reconcilePriceAlertsAfterSync(current, syncedItems, new Date().toISOString())),
    [enqueue],
  );

  return {
    ...state,
    ready,
    refresh,
    remove,
    markReconciled,
    findByOfferId: (offerId: number) => state.items.find((item) => item.offerId === offerId),
  };
}
