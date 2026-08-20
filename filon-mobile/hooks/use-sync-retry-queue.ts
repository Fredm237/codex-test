import { useCallback, useEffect, useState } from "react";

import { clearSyncRetry, emptySyncRetryQueue, readSyncRetryQueue, saveSyncRetryQueue, scheduleSyncRetry, type SyncRetryQueue } from "@/lib/sync-retry-queue";

export function useSyncRetryQueue() {
  const [queue, setQueue] = useState<SyncRetryQueue>(emptySyncRetryQueue);
  const [ready, setReady] = useState(false);
  const refresh = useCallback(async () => { setQueue(await readSyncRetryQueue()); setReady(true); }, []);
  useEffect(() => { void refresh(); }, [refresh]);
  const recordFailure = useCallback(async () => { const next = scheduleSyncRetry(queue, new Date().toISOString()); await saveSyncRetryQueue(next); setQueue(next); return next; }, [queue]);
  const clear = useCallback(async () => { const next = clearSyncRetry(); await saveSyncRetryQueue(next); setQueue(next); return next; }, []);
  return { ...queue, ready, recordFailure, clear };
}
