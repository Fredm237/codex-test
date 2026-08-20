import { useCallback, useEffect, useState } from "react";
import { useFocusEffect } from "expo-router";

import { readIntentOfferEvidence, removeIntentOfferEvidence, saveIntentOfferEvidence, type IntentOfferEvidence } from "@/lib/intent-offer-evidence";

export function useIntentOfferEvidence() {
  const [items, setItems] = useState<IntentOfferEvidence[]>([]);
  const [ready, setReady] = useState(false);
  const refresh = useCallback(async () => { const next = await readIntentOfferEvidence(); setItems(next); setReady(true); return next; }, []);
  useEffect(() => { void refresh(); }, [refresh]);
  useFocusEffect(useCallback(() => { void refresh(); }, [refresh]));
  const link = useCallback(async (evidence: IntentOfferEvidence) => { const next = await saveIntentOfferEvidence(evidence); setItems(next); return next; }, []);
  const unlink = useCallback(async (intentId: string) => { const next = await removeIntentOfferEvidence(intentId); setItems(next); return next; }, []);
  const forIntent = useCallback((intentId: string) => items.find((item) => item.intentId === intentId) ?? null, [items]);
  return { items, ready, refresh, link, unlink, forIntent };
}
