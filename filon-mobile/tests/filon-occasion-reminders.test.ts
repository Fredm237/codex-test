import { describe, expect, it } from "vitest";

import { buildOccasionReminder } from "../lib/filon-occasion-reminders";

describe("Rappels d’occasions FILON", () => {
  it("planifie un rappel la veille pour une occasion future", () => {
    const reminder = buildOccasionReminder({ id: "p1", title: "Dîner", date: "2026-08-20" }, new Date("2026-08-16T10:00:00"));
    expect(reminder?.triggerAt.getFullYear()).toBe(2026);
    expect(reminder?.triggerAt.getMonth()).toBe(7);
    expect(reminder?.triggerAt.getDate()).toBe(19);
    expect(reminder?.triggerAt.getHours()).toBe(18);
  });

  it("refuse de programmer un rappel passé ou une date invalide", () => {
    expect(buildOccasionReminder({ id: "p1", title: "Dîner", date: "2026-08-10" }, new Date("2026-08-16T10:00:00"))).toBeNull();
    expect(buildOccasionReminder({ id: "p1", title: "Dîner", date: "invalid" })).toBeNull();
  });
});
