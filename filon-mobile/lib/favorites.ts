import AsyncStorage from "@react-native-async-storage/async-storage";

import type { FilonOffer } from "@/lib/filon-api";

const KEY = "filon.favorites.v1";

export type FavoriteOffer = Pick<FilonOffer, "id" | "name" | "price" | "currency" | "imageUrl" | "merchantName" | "link" | "inStock" | "category">;

export function applyFavoriteToggle(current: FavoriteOffer[], offer: FavoriteOffer) {
  return current.some((item) => item.id === offer.id) ? current.filter((item) => item.id !== offer.id) : [offer, ...current];
}

export async function readFavorites(): Promise<FavoriteOffer[]> {
  const raw = await AsyncStorage.getItem(KEY);
  if (!raw) return [];
  try { return JSON.parse(raw) as FavoriteOffer[]; } catch { return []; }
}

export async function toggleFavorite(offer: FavoriteOffer) {
  const current = await readFavorites();
  const next = applyFavoriteToggle(current, offer);
  await AsyncStorage.setItem(KEY, JSON.stringify(next));
  return next;
}
