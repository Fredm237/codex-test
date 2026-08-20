import AsyncStorage from "@react-native-async-storage/async-storage";

import type { OutfitRole } from "./filon-intelligence";

export type WardrobeItem = { id: string; label: string; role: OutfitRole; createdAt: string; updatedAt: string };
const STORAGE_KEY = "filon.intelligence.wardrobe.v1";
const LIMIT = 40;

function isRole(value: unknown): value is OutfitRole {
  return value === "base" || value === "structure" || value === "footwear" || value === "accessory";
}

function canonical(value: string) {
  return value.trim().toLocaleLowerCase().replace(/\s+/g, " ");
}

export function mergeWardrobeItems(items: WardrobeItem[], next: WardrobeItem): WardrobeItem[] {
  const duplicate = items.find((item) => item.role === next.role && canonical(item.label) === canonical(next.label));
  if (duplicate) return [{ ...duplicate, label: next.label, updatedAt: next.updatedAt }, ...items.filter((item) => item.id !== duplicate.id)].slice(0, LIMIT);
  return [next, ...items].slice(0, LIMIT);
}

export function sanitizeWardrobe(raw: unknown): WardrobeItem[] {
  if (!Array.isArray(raw)) return [];
  return raw.filter((item): item is WardrobeItem => typeof item === "object" && item !== null && typeof (item as WardrobeItem).id === "string" && typeof (item as WardrobeItem).label === "string" && (item as WardrobeItem).label.trim().length > 0 && isRole((item as WardrobeItem).role) && typeof (item as WardrobeItem).createdAt === "string" && typeof (item as WardrobeItem).updatedAt === "string").slice(0, LIMIT);
}

export async function readWardrobe(): Promise<WardrobeItem[]> {
  try { return sanitizeWardrobe(JSON.parse((await AsyncStorage.getItem(STORAGE_KEY)) ?? "[]")); } catch { return []; }
}

export async function saveWardrobeItem(input: Pick<WardrobeItem, "label" | "role">): Promise<WardrobeItem[]> {
  const now = new Date().toISOString();
  const item: WardrobeItem = { id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`, label: input.label.trim().slice(0, 120), role: input.role, createdAt: now, updatedAt: now };
  const items = mergeWardrobeItems(await readWardrobe(), item);
  await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  return items;
}

export async function removeWardrobeItem(id: string): Promise<WardrobeItem[]> {
  const items = (await readWardrobe()).filter((item) => item.id !== id);
  await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  return items;
}
