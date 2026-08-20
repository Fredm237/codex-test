import AsyncStorage from "@react-native-async-storage/async-storage";

const KEY = "filon.sync-retry.v1";
const BASE_DELAY_MS = 5_000;
const MAX_DELAY_MS = 300_000;
const MAX_ATTEMPTS = 6;

export type SyncRetryQueue = { attempts: number; lastFailureAt: string | null; nextRetryAt: string | null };
export const emptySyncRetryQueue: SyncRetryQueue = { attempts: 0, lastFailureAt: null, nextRetryAt: null };

export function delayForSyncAttempt(attempt: number) { return Math.min(MAX_DELAY_MS, BASE_DELAY_MS * 2 ** Math.max(0, attempt - 1)); }
export function scheduleSyncRetry(current: SyncRetryQueue, at: string): SyncRetryQueue {
  const attempts = Math.min(MAX_ATTEMPTS, current.attempts + 1);
  return { attempts, lastFailureAt: at, nextRetryAt: new Date(Date.parse(at) + delayForSyncAttempt(attempts)).toISOString() };
}
export function isSyncRetryDue(current: SyncRetryQueue, at: string) { return Boolean(current.nextRetryAt && Date.parse(current.nextRetryAt) <= Date.parse(at)); }
export function clearSyncRetry(): SyncRetryQueue { return emptySyncRetryQueue; }

export async function readSyncRetryQueue(): Promise<SyncRetryQueue> {
  const raw = await AsyncStorage.getItem(KEY);
  if (!raw) return emptySyncRetryQueue;
  try {
    const parsed = JSON.parse(raw) as Partial<SyncRetryQueue>;
    return { attempts: typeof parsed.attempts === "number" && Number.isInteger(parsed.attempts) ? Math.max(0, Math.min(MAX_ATTEMPTS, parsed.attempts)) : 0, lastFailureAt: typeof parsed.lastFailureAt === "string" ? parsed.lastFailureAt : null, nextRetryAt: typeof parsed.nextRetryAt === "string" ? parsed.nextRetryAt : null };
  } catch { return emptySyncRetryQueue; }
}
export async function saveSyncRetryQueue(queue: SyncRetryQueue) { await AsyncStorage.setItem(KEY, JSON.stringify(queue)); return queue; }
