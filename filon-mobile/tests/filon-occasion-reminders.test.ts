import { describe, expect, it } from "vitest";

import { buildOccasionReminder } from "../lib/filon-occasion-reminders";

describe("Rappels d’occasions FILON", () => {
  it("planifie un rappel la veille pour une occasion future", () => {
    const reminder = buildOccasionReminder({ id: "p1", title: "Dîner", date: "2026-08-20" }, new Date("2026-08-16T10:00:00"));
    expect(reminder?.triggerAt.toISOString()).toContain("2026-08-19T18:00:00");
  });

  it("refuse de programmer un rappel passé ou une date invalide", () => {
    expect(buildOccasionReminder({ id: "p1", title: "Dîner", date: "2026-08-10" }, new Date("2026-08-16T10:00:00"))).toBeNull();
    expect(buildOccasionReminder({ id: "p1", title: "Dîner", date: "invalid" })).toBeNull();
  });
});
