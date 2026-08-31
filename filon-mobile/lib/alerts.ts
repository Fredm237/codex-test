import AsyncStorage from "@react-native-async-storage/async-storage";

import { isFilonOfferPriceCurrent, normalizeFilonCurrency, normalizeFilonObservedAt, type FilonCurrency } from "./filon-api";

export type LocalPriceAlert = { offerId: number; name: string; threshold: number; currency: FilonCurrency; createdAt: string };
export type AlertSyncPayload = { version: 1; kind: "price-alert"; alert: LocalPriceAlert };
export type LocalPriceAlertState = { items: LocalPriceAlert[]; pendingSync: boolean; lastSyncedAt: string | null };

const KEY = "filon.price-alerts.v1";
let localPriceAlertMutationTail: Promise<void> = Promise.resolve();
export const emptyLocalPriceAlertState: LocalPriceAlertState = { items: [], pendingSync: false, lastSyncedAt: null };

export function isAlertReferenceCurrent(value: { price: unknown; currency: unknown; observedAt: unknown; evidenceCurrent: unknown }, now: number | Date = Date.now()) {
  const price = typeof value.price === "number" && Number.isFinite(value.price) && value.price > 0 ? value.price : null;
  const currency = normalizeFilonCurrency(value.currency);
  const observedAt = normalizeFilonObservedAt(value.observedAt);
  return price !== null && currency !== null && isFilonOfferPriceCurrent({ price, currency, observedAt, evidenceCurrent: value.evidenceCurrent === true }, now);
}

export function normalizeLocalPriceAlert(value: unknown): LocalPriceAlert | null {
  if (!value || typeof value !== "object") return null;
  const candidate = value as Record<string, unknown>;
  const name = typeof candidate.name === "string" ? candidate.name.trim() : "";
  const currency = normalizeFilonCurrency(candidate.currency);
  const createdAt = normalizeFilonObservedAt(candidate.createdAt);
  if (
    typeof candidate.offerId !== "number"
    || !Number.isInteger(candidate.offerId)
    || candidate.offerId <= 0
    || name.length === 0
    || typeof candidate.threshold !== "number"
    || !Number.isFinite(candidate.threshold)
    || candidate.threshold <= 0
    || currency === null
    || createdAt === null
  ) return null;
  return { offerId: candidate.offerId, name, threshold: candidate.threshold, currency, createdAt };
}

export function normalizeLocalPriceAlerts(value: unknown) {
  if (!Array.isArray(value)) return [];
  return value.reduce<LocalPriceAlert[]>((items, candidate) => {
    const normalized = normalizeLocalPriceAlert(candidate);
    if (normalized && !items.some((item) => item.offerId === normalized.offerId)) items.push(normalized);
    return items;
  }, []);
}

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

function alertSnapshot(items: LocalPriceAlert[]) {
  return [...items]
    .sort((left, right) => left.offerId - right.offerId)
    .map(({ offerId, name, threshold, currency, createdAt }) => ({ offerId, name, threshold, currency, createdAt }));
}

export function reconcilePriceAlertsAfterSync(current: LocalPriceAlertState, syncedItems: LocalPriceAlert[], at: string): LocalPriceAlertState {
  const unchanged = JSON.stringify(alertSnapshot(current.items)) === JSON.stringify(alertSnapshot(syncedItems));
  return unchanged ? markPriceAlertsReconciled(current, at) : { ...current, pendingSync: true };
}

export async function readLocalPriceAlertState(): Promise<LocalPriceAlertState> {
  const raw = await AsyncStorage.getItem(KEY);
  if (!raw) return emptyLocalPriceAlertState;
  try {
    const parsed = JSON.parse(raw) as LocalPriceAlert[] | Partial<LocalPriceAlertState>;
    if (Array.isArray(parsed)) return { items: normalizeLocalPriceAlerts(parsed), pendingSync: false, lastSyncedAt: null };
    return {
      items: normalizeLocalPriceAlerts(parsed.items),
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

export function updateLocalPriceAlertState(transition: (current: LocalPriceAlertState) => LocalPriceAlertState) {
  const operation = localPriceAlertMutationTail.then(async () => {
    const current = await readLocalPriceAlertState();
    const next = transition(current);
    if (next !== current) await saveLocalPriceAlertState(next);
    return next;
  });
  localPriceAlertMutationTail = operation.then(() => undefined, () => undefined);
  return operation;
}

export async function saveLocalPriceAlert(alert: LocalPriceAlert) {
  const normalized = normalizeLocalPriceAlert(alert);
  const next = await updateLocalPriceAlertState((current) => normalized ? markPriceAlertsPending({ ...current, items: upsertLocalPriceAlert(current.items, normalized) }) : current);
  return next.items;
}

export async function readLocalPriceAlerts(): Promise<LocalPriceAlert[]> {
  return (await readLocalPriceAlertState()).items;
}

export async function removeLocalPriceAlert(offerId: number) {
  const next = await updateLocalPriceAlertState((current) => markPriceAlertsPending({ ...current, items: removeLocalPriceAlertFromList(current.items, offerId) }));
  return next.items;
}
