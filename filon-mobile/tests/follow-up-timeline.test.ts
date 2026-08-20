import { describe, expect, it } from "vitest";

import { appendFollowUpEvent, makeFollowUpEvent } from "../lib/follow-up-timeline-rules";

describe("follow-up timeline", () => {
  it("places newest events first and keeps a bounded history", () => {
    const first = makeFollowUpEvent("favorite-added", "Casque", "2026-08-14T08:00:00.000Z");
    const next = makeFollowUpEvent("alert-created", "Téléphone", "2026-08-14T08:01:00.000Z");
    const result = appendFollowUpEvent([first], next, 1);
    expect(result).toEqual([next]);
  });

  it("replaces an event with the same identifier instead of duplicating it", () => {
    const event = makeFollowUpEvent("sync-succeeded", "FILON", "2026-08-14T08:00:00.000Z");
    expect(appendFollowUpEvent([event], event)).toEqual([event]);
  });
});
