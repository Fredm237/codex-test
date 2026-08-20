import AsyncStorage from "@react-native-async-storage/async-storage";

import { appendFollowUpEvent, makeFollowUpEvent, type FollowUpEvent, type FollowUpEventKind } from "./follow-up-timeline-rules";

const KEY = "filon.follow-up-timeline.v1";

export type { FollowUpEvent, FollowUpEventKind } from "./follow-up-timeline-rules";

export async function readFollowUpTimeline(): Promise<FollowUpEvent[]> {
  const raw = await AsyncStorage.getItem(KEY);
  if (!raw) return [];
  try { const parsed = JSON.parse(raw); return Array.isArray(parsed) ? parsed as FollowUpEvent[] : []; } catch { return []; }
}

export async function recordFollowUpEvent(kind: FollowUpEventKind, label: string) {
  const next = appendFollowUpEvent(await readFollowUpTimeline(), makeFollowUpEvent(kind, label, new Date().toISOString()));
  await AsyncStorage.setItem(KEY, JSON.stringify(next));
  return next;
}

export async function clearFollowUpTimeline() { await AsyncStorage.removeItem(KEY); }
