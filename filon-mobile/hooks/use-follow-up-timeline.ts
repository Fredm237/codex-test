import { useCallback, useEffect, useState } from "react";

import { clearFollowUpTimeline, readFollowUpTimeline, type FollowUpEvent } from "@/lib/follow-up-timeline";

export function useFollowUpTimeline() {
  const [events, setEvents] = useState<FollowUpEvent[]>([]);
  const [ready, setReady] = useState(false);
  const refresh = useCallback(async () => { setEvents(await readFollowUpTimeline()); setReady(true); }, []);
  useEffect(() => { void refresh(); }, [refresh]);
  const clear = useCallback(async () => { await clearFollowUpTimeline(); setEvents([]); }, []);
  return { events, ready, refresh, clear };
}
