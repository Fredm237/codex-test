export type FollowUpEventKind = "favorite-added" | "favorite-removed" | "alert-created" | "alert-removed" | "sync-succeeded";

export type FollowUpEvent = { id: string; kind: FollowUpEventKind; label: string; occurredAt: string };

export function appendFollowUpEvent(current: FollowUpEvent[], event: FollowUpEvent, limit = 14): FollowUpEvent[] {
  return [event, ...current.filter((item) => item.id !== event.id)].slice(0, limit);
}

export function makeFollowUpEvent(kind: FollowUpEventKind, label: string, occurredAt: string): FollowUpEvent {
  return { id: `${kind}:${occurredAt}:${label}`, kind, label, occurredAt };
}
