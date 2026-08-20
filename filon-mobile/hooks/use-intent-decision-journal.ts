import { useCallback, useEffect, useState } from "react";
import { useFocusEffect } from "expo-router";

import { clearIntentDecisionJournal, readIntentDecisionJournal, recordIntentDecision, type IntentDecisionEvent, type IntentDecisionKind } from "@/lib/intent-decision-journal";
import { forPurchaseIntent } from "@/lib/intent-decision-journal-rules";

export function useIntentDecisionJournal() {
  const [events, setEvents] = useState<IntentDecisionEvent[]>([]);
  const [ready, setReady] = useState(false);
  const refresh = useCallback(async () => { const next = await readIntentDecisionJournal(); setEvents(next); setReady(true); return next; }, []);
  useEffect(() => { void refresh(); }, [refresh]);
  useFocusEffect(useCallback(() => { void refresh(); }, [refresh]));
  const record = useCallback(async (intentId: string, kind: IntentDecisionKind, label: string) => { const next = await recordIntentDecision(intentId, kind, label); setEvents(next); return next; }, []);
  const clear = useCallback(async (intentId?: string) => { const next = await clearIntentDecisionJournal(intentId); setEvents(next); return next; }, []);
  const forIntent = useCallback((intentId: string) => forPurchaseIntent(events, intentId), [events]);
  return { events, ready, refresh, record, clear, forIntent };
}
