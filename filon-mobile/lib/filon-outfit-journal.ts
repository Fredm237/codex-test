import AsyncStorage from "@react-native-async-storage/async-storage";

import type { OutfitRole, OutfitSolution } from "./filon-intelligence";

export type SavedOutfitPiece = { offerId: number; name: string; price: number; currency: string; merchantName: string; link: string; imageUrl: string | null; role: OutfitRole };
export type SavedOutfit = { id: string; title: string; mode: "create" | "complete"; total: number; confidenceScore: number; pieces: SavedOutfitPiece[]; createdAt: string };
const STORAGE_KEY = "filon.intelligence.outfit-journal.v1";
const LIMIT = 30;

export function makeSavedOutfit(title: string, mode: SavedOutfit["mode"], solution: OutfitSolution, now = new Date().toISOString()): SavedOutfit {
  const pieces = solution.pieces.map((piece) => ({ offerId: piece.offer.id, name: piece.offer.name, price: piece.offer.price, currency: piece.offer.currency, merchantName: piece.offer.merchantName, link: piece.offer.link, imageUrl: piece.offer.imageUrl, role: piece.role }));
  return { id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`, title: title.trim().slice(0, 120) || "Tenue FILON", mode, total: solution.total, confidenceScore: solution.confidenceScore, pieces, createdAt: now };
}

export function mergeSavedOutfits(items: SavedOutfit[], next: SavedOutfit): SavedOutfit[] {
  const signature = next.pieces.map((piece) => piece.offerId).sort((left, right) => left - right).join(",");
  const withoutDuplicate = items.filter((item) => item.pieces.map((piece) => piece.offerId).sort((left, right) => left - right).join(",") !== signature);
  return [next, ...withoutDuplicate].slice(0, LIMIT);
}

export function sanitizeSavedOutfits(raw: unknown): SavedOutfit[] {
  if (!Array.isArray(raw)) return [];
  return raw.filter((item): item is SavedOutfit => typeof item === "object" && item !== null && typeof (item as SavedOutfit).id === "string" && typeof (item as SavedOutfit).title === "string" && ((item as SavedOutfit).mode === "create" || (item as SavedOutfit).mode === "complete") && typeof (item as SavedOutfit).total === "number" && typeof (item as SavedOutfit).confidenceScore === "number" && Array.isArray((item as SavedOutfit).pieces) && typeof (item as SavedOutfit).createdAt === "string").slice(0, LIMIT);
}

export async function readSavedOutfits(): Promise<SavedOutfit[]> {
  try { return sanitizeSavedOutfits(JSON.parse((await AsyncStorage.getItem(STORAGE_KEY)) ?? "[]")); } catch { return []; }
}

export async function saveOutfit(outfit: SavedOutfit): Promise<SavedOutfit[]> {
  const next = mergeSavedOutfits(await readSavedOutfits(), outfit);
  await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  return next;
}

export async function removeSavedOutfit(id: string): Promise<SavedOutfit[]> {
  const next = (await readSavedOutfits()).filter((item) => item.id !== id);
  await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  return next;
}
