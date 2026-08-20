export type IntentDecisionKind = "intent-defined" | "intent-revised" | "catalogue-explored" | "assistant-opened" | "offer-linked" | "offer-unlinked" | "alert-created";

export type IntentDecisionEvent = { id: string; intentId: string; kind: IntentDecisionKind; label: string; occurredAt: string };

export function makeIntentDecisionEvent(intentId: string, kind: IntentDecisionKind, label: string, occurredAt: string): IntentDecisionEvent {
  return { id: `${intentId}:${kind}:${occurredAt}:${label}`, intentId, kind, label, occurredAt };
}

export function appendIntentDecisionEvent(current: IntentDecisionEvent[], event: IntentDecisionEvent, limit = 40): IntentDecisionEvent[] {
  return [event, ...current.filter((item) => item.id !== event.id)].slice(0, limit);
}

export function forPurchaseIntent(current: IntentDecisionEvent[], intentId: string, limit = 8) {
  return current.filter((item) => item.intentId === intentId).slice(0, limit);
}
