import AsyncStorage from "@react-native-async-storage/async-storage";

export type OutfitFeedbackValue = "helpful" | "needs_review";
export type OutfitFeedback = {
  solutionKey: string;
  value: OutfitFeedbackValue;
  updatedAt: string;
};

const STORAGE_KEY = "filon.intelligence.outfit-feedback.v1";

export function buildOutfitFeedbackKey(request: string, offerIds: number[]) {
  return `${request.trim().toLocaleLowerCase()}::${offerIds.slice().sort((left, right) => left - right).join(",")}`;
}

export function mergeOutfitFeedback(items: OutfitFeedback[], next: OutfitFeedback): OutfitFeedback[] {
  return [next, ...items.filter((item) => item.solutionKey !== next.solutionKey)].slice(0, 80);
}

export async function readOutfitFeedback(solutionKey: string): Promise<OutfitFeedbackValue | null> {
  try {
    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const items = JSON.parse(raw) as unknown;
    if (!Array.isArray(items)) return null;
    const matched = items.find((item): item is OutfitFeedback => typeof item === "object" && item !== null && "solutionKey" in item && "value" in item && (item as OutfitFeedback).solutionKey === solutionKey && ((item as OutfitFeedback).value === "helpful" || (item as OutfitFeedback).value === "needs_review"));
    return matched?.value ?? null;
  } catch {
    return null;
  }
}

export async function saveOutfitFeedback(solutionKey: string, value: OutfitFeedbackValue): Promise<OutfitFeedbackValue> {
  const next: OutfitFeedback = { solutionKey, value, updatedAt: new Date().toISOString() };
  let existing: OutfitFeedback[] = [];
  try {
    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    if (Array.isArray(parsed)) existing = parsed.filter((item): item is OutfitFeedback => typeof item === "object" && item !== null && "solutionKey" in item && "value" in item && typeof (item as OutfitFeedback).solutionKey === "string" && ((item as OutfitFeedback).value === "helpful" || (item as OutfitFeedback).value === "needs_review"));
  } catch {
    existing = [];
  }
  await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(mergeOutfitFeedback(existing, next)));
  return value;
}
