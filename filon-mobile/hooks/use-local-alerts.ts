import { useCallback, useEffect, useState } from "react";

import { markPriceAlertsReconciled, readLocalPriceAlertState, removeLocalPriceAlert, saveLocalPriceAlertState, type LocalPriceAlert, type LocalPriceAlertState } from "@/lib/alerts";
import { haptic } from "@/lib/haptics";
import { recordFollowUpEvent } from "@/lib/follow-up-timeline";

export function useLocalAlerts() {
  const [state, setState] = useState<LocalPriceAlertState>({ items: [], pendingSync: false, lastSyncedAt: null });
  const [ready, setReady] = useState(false);
  const refresh = useCallback(async () => { setState(await readLocalPriceAlertState()); setReady(true); }, []);
  useEffect(() => { void refresh(); }, [refresh]);
  const remove = useCallback(async (offerId: number) => { const removed = state.items.find((item) => item.offerId === offerId); const next = await removeLocalPriceAlert(offerId); await refresh(); if (removed) await recordFollowUpEvent("alert-removed", removed.name); haptic.medium(); return next; }, [refresh, state.items]);
  const markReconciled = useCallback(async () => { const next = markPriceAlertsReconciled(state, new Date().toISOString()); await saveLocalPriceAlertState(next); setState(next); return next; }, [state]);
  return { ...state, ready, refresh, remove, markReconciled, findByOfferId: (offerId: number) => state.items.find((item) => item.offerId === offerId) };
}
