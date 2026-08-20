import AsyncStorage from "@react-native-async-storage/async-storage";

export type PlannedOccasion = { id: string; title: string; date: string; outfitId: string; createdAt: string; reminderId?: string };
const STORAGE_KEY = "filon.intelligence.planned-occasions.v1";
const LIMIT = 30;

function isDate(value: unknown): value is string {
  return typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value);
}

export function sanitizePlannedOccasions(raw: unknown): PlannedOccasion[] {
  if (!Array.isArray(raw)) return [];
  return raw.filter((item): item is PlannedOccasion => typeof item === "object" && item !== null && typeof (item as PlannedOccasion).id === "string" && typeof (item as PlannedOccasion).title === "string" && (item as PlannedOccasion).title.trim().length > 0 && isDate((item as PlannedOccasion).date) && typeof (item as PlannedOccasion).outfitId === "string" && typeof (item as PlannedOccasion).createdAt === "string" && (typeof (item as PlannedOccasion).reminderId === "undefined" || typeof (item as PlannedOccasion).reminderId === "string")).slice(0, LIMIT);
}

export function mergePlannedOccasions(items: PlannedOccasion[], next: PlannedOccasion): PlannedOccasion[] {
  return [next, ...items.filter((item) => !(item.outfitId === next.outfitId && item.date === next.date && item.title.trim().toLocaleLowerCase() === next.title.trim().toLocaleLowerCase()))].slice(0, LIMIT);
}

export async function readPlannedOccasions(): Promise<PlannedOccasion[]> {
  try { return sanitizePlannedOccasions(JSON.parse((await AsyncStorage.getItem(STORAGE_KEY)) ?? "[]")); } catch { return []; }
}

export async function savePlannedOccasion(input: Pick<PlannedOccasion, "title" | "date" | "outfitId">): Promise<PlannedOccasion[]> {
  const now = new Date().toISOString();
  const next: PlannedOccasion = { id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`, title: input.title.trim().slice(0, 80), date: input.date, outfitId: input.outfitId, createdAt: now };
  const items = mergePlannedOccasions(await readPlannedOccasions(), next);
  await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  return items;
}

export async function removePlannedOccasion(id: string): Promise<PlannedOccasion[]> {
  const items = (await readPlannedOccasions()).filter((item) => item.id !== id);
  await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  return items;
}

export async function updatePlannedOccasionReminder(id: string, reminderId: string | undefined): Promise<PlannedOccasion[]> {
  const items = (await readPlannedOccasions()).map((item) => item.id === id ? { ...item, reminderId } : item);
  await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  return items;
}
