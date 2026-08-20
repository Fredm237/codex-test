export type OccasionReminder = { occasionId: string; title: string; triggerAt: Date };

/** Propose un rappel la veille à 18 h locale. Les dates passées ou invalides ne sont jamais planifiées. */
export function buildOccasionReminder(occasion: { id: string; title: string; date: string }, now = new Date()): OccasionReminder | null {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(occasion.date)) return null;
  const triggerAt = new Date(`${occasion.date}T18:00:00`);
  triggerAt.setDate(triggerAt.getDate() - 1);
  if (Number.isNaN(triggerAt.getTime()) || triggerAt.getTime() <= now.getTime()) return null;
  return { occasionId: occasion.id, title: occasion.title.trim().slice(0, 80), triggerAt };
}
