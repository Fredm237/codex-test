import AsyncStorage from "@react-native-async-storage/async-storage";

import { normalizeFashionErrorCode, type FashionErrorCode } from "./filon-fashion-quality";

export type FashionCorrectionCandidate = { id: string; recommendationKey: string; code: FashionErrorCode; note: string; createdAt: string };
const STORAGE_KEY = "filon.intelligence.fashion-corrections.v1";
const LIMIT = 60;

export function sanitizeFashionCorrections(raw: unknown): FashionCorrectionCandidate[] {
  if (!Array.isArray(raw)) return [];
  return raw.filter((item): item is FashionCorrectionCandidate => typeof item === "object" && item !== null && typeof (item as FashionCorrectionCandidate).id === "string" && typeof (item as FashionCorrectionCandidate).recommendationKey === "string" && normalizeFashionErrorCode((item as FashionCorrectionCandidate).code) !== null && typeof (item as FashionCorrectionCandidate).note === "string" && typeof (item as FashionCorrectionCandidate).createdAt === "string").slice(0, LIMIT);
}

export function mergeFashionCorrection(items: FashionCorrectionCandidate[], next: FashionCorrectionCandidate): FashionCorrectionCandidate[] {
  return [next, ...items.filter((item) => !(item.recommendationKey === next.recommendationKey && item.code === next.code && item.note === next.note))].slice(0, LIMIT);
}

export async function readFashionCorrections(): Promise<FashionCorrectionCandidate[]> {
  try { return sanitizeFashionCorrections(JSON.parse((await AsyncStorage.getItem(STORAGE_KEY)) ?? "[]")); } catch { return []; }
}

export async function saveFashionCorrection(input: Pick<FashionCorrectionCandidate, "recommendationKey" | "code" | "note">): Promise<FashionCorrectionCandidate[]> {
  const code = normalizeFashionErrorCode(input.code);
  if (!code || !input.recommendationKey.trim()) return readFashionCorrections();
  const next: FashionCorrectionCandidate = { id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`, recommendationKey: input.recommendationKey.trim().slice(0, 160), code, note: input.note.trim().slice(0, 280), createdAt: new Date().toISOString() };
  const items = mergeFashionCorrection(await readFashionCorrections(), next);
  await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  return items;
}

export async function removeFashionCorrection(id: string): Promise<FashionCorrectionCandidate[]> {
  const items = (await readFashionCorrections()).filter((item) => item.id !== id);
  await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  return items;
}
