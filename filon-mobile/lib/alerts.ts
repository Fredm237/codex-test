import AsyncStorage from "@react-native-async-storage/async-storage";

export type LocalPriceAlert = { offerId: number; name: string; threshold: number; currency: string; createdAt: string };
export type AlertSyncPayload = { version: 1; kind: "price-alert"; alert: LocalPriceAlert };
export type LocalPriceAlertState = { items: LocalPriceAlert[]; pendingSync: boolean; lastSyncedAt: string | null };

const KEY = "filon.price-alerts.v1";
export const emptyLocalPriceAlertState: LocalPriceAlertState = { items: [], pendingSync: false, lastSyncedAt: null };

export function upsertLocalPriceAlert(current: LocalPriceAlert[], alert: LocalPriceAlert) {
  return [alert, ...current.filter((item) => item.offerId !== alert.offerId)];
}

export function removeLocalPriceAlertFromList(current: LocalPriceAlert[], offerId: number) {
  return current.filter((item) => item.offerId !== offerId);
}

export function serializeAlertForSync(alert: LocalPriceAlert): AlertSyncPayload {
  return { version: 1, kind: "price-alert", alert };
}

export function markPriceAlertsPending(current: LocalPriceAlertState): LocalPriceAlertState {
  return { ...current, pendingSync: true };
}

export function markPriceAlertsReconciled(current: LocalPriceAlertState, at: string): LocalPriceAlertState {
  return { ...current, pendingSync: false, lastSyncedAt: at };
}

export async function readLocalPriceAlertState(): Promise<LocalPriceAlertState> {
  const raw = await AsyncStorage.getItem(KEY);
  if (!raw) return emptyLocalPriceAlertState;
  try {
    const parsed = JSON.parse(raw) as LocalPriceAlert[] | Partial<LocalPriceAlertState>;
    if (Array.isArray(parsed)) return { items: parsed, pendingSync: false, lastSyncedAt: null };
    return {
      items: Array.isArray(parsed.items) ? parsed.items : [],
      pendingSync: parsed.pendingSync === true,
      lastSyncedAt: typeof parsed.lastSyncedAt === "string" ? parsed.lastSyncedAt : null,
    };
  } catch {
    return emptyLocalPriceAlertState;
  }
}

export async function saveLocalPriceAlertState(state: LocalPriceAlertState) {
  await AsyncStorage.setItem(KEY, JSON.stringify(state));
  return state;
}

export async function saveLocalPriceAlert(alert: LocalPriceAlert) {
  const current = await readLocalPriceAlertState();
  const next = markPriceAlertsPending({ ...current, items: upsertLocalPriceAlert(current.items, alert) });
  await saveLocalPriceAlertState(next);
  return next.items;
}

export async function readLocalPriceAlerts(): Promise<LocalPriceAlert[]> {
  return (await readLocalPriceAlertState()).items;
}

export async function removeLocalPriceAlert(offerId: number) {
  const current = await readLocalPriceAlertState();
  const next = markPriceAlertsPending({ ...current, items: removeLocalPriceAlertFromList(current.items, offerId) });
  await saveLocalPriceAlertState(next);
  return next.items;
}
