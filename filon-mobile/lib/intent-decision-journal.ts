import AsyncStorage from "@react-native-async-storage/async-storage";

import { appendIntentDecisionEvent, makeIntentDecisionEvent, type IntentDecisionEvent, type IntentDecisionKind } from "./intent-decision-journal-rules";

const KEY = "filon.intent-decision-journal.v1";

export type { IntentDecisionEvent, IntentDecisionKind } from "./intent-decision-journal-rules";

function isIntentDecisionEvent(value: unknown): value is IntentDecisionEvent {
  if (!value || typeof value !== "object") return false;
  const event = value as IntentDecisionEvent;
  return typeof event.id === "string" && typeof event.intentId === "string" && typeof event.kind === "string" && typeof event.label === "string" && typeof event.occurredAt === "string";
}

export async function readIntentDecisionJournal(): Promise<IntentDecisionEvent[]> {
  const raw = await AsyncStorage.getItem(KEY);
  if (!raw) return [];
  try { const parsed = JSON.parse(raw) as unknown; return Array.isArray(parsed) ? parsed.filter(isIntentDecisionEvent).slice(0, 40) : []; } catch { return []; }
}

export async function recordIntentDecision(intentId: string, kind: IntentDecisionKind, label: string) {
  const next = appendIntentDecisionEvent(await readIntentDecisionJournal(), makeIntentDecisionEvent(intentId, kind, label, new Date().toISOString()));
  await AsyncStorage.setItem(KEY, JSON.stringify(next));
  return next;
}

export async function clearIntentDecisionJournal(intentId?: string) {
  if (!intentId) { await AsyncStorage.removeItem(KEY); return []; }
  const next = (await readIntentDecisionJournal()).filter((item) => item.intentId !== intentId);
  await AsyncStorage.setItem(KEY, JSON.stringify(next));
  return next;
}
