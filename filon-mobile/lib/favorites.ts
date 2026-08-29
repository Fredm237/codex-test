import AsyncStorage from "@react-native-async-storage/async-storage";

import { isFilonObservationFresh, normalizeFilonCurrency, normalizeFilonObservedAt, type FilonOffer } from "./filon-api";

const KEY = "filon.favorites.v1";

export type FavoriteOffer = Pick<FilonOffer, "id" | "name" | "price" | "currency" | "imageUrl" | "merchantName" | "link" | "inStock" | "category"> & { observedAt: string | null; evidenceCurrent: boolean };

function nonEmptyText(value: unknown) {
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : null;
}

export function normalizeFavoriteOffer(value: unknown, now: number | Date = Date.now()): FavoriteOffer | null {
  if (!value || typeof value !== "object") return null;
  const candidate = value as Record<string, unknown>;
  const id = candidate.id;
  const price = candidate.price;
  const name = nonEmptyText(candidate.name);
  const currency = normalizeFilonCurrency(candidate.currency);
  const merchantName = nonEmptyText(candidate.merchantName);
  const link = nonEmptyText(candidate.link);
  if (
    typeof id !== "number"
    || !Number.isInteger(id)
    || id <= 0
    || typeof price !== "number"
    || !Number.isFinite(price)
    || price <= 0
    || name === null
    || currency === null
    || merchantName === null
    || link === null
    || !/^https?:\/\//i.test(link)
  ) return null;

  const observedAt = normalizeFilonObservedAt(candidate.observedAt);
  const evidenceCurrent = candidate.evidenceCurrent === true;
  const observationIsFresh = evidenceCurrent && isFilonObservationFresh(observedAt, now);
  return {
    id,
    name,
    price,
    currency,
    imageUrl: nonEmptyText(candidate.imageUrl),
    merchantName,
    link,
    // Une disponibilité enregistrée n'est plus un fait actuel dès que son
    // relevé manque, vient du futur ou dépasse la fenêtre de 72 heures.
    inStock: observationIsFresh && candidate.inStock === true ? true : observationIsFresh && candidate.inStock === false ? false : null,
    observedAt,
    evidenceCurrent,
    category: nonEmptyText(candidate.category),
  };
}

export function normalizeFavoriteOffers(value: unknown, now: number | Date = Date.now()) {
  if (!Array.isArray(value)) return [];
  return value.reduce<FavoriteOffer[]>((items, candidate) => {
    const normalized = normalizeFavoriteOffer(candidate, now);
    if (normalized && !items.some((item) => item.id === normalized.id)) items.push(normalized);
    return items;
  }, []);
}

export function applyFavoriteToggle(current: FavoriteOffer[], offer: FavoriteOffer) {
  return current.some((item) => item.id === offer.id) ? current.filter((item) => item.id !== offer.id) : [offer, ...current];
}

export async function readFavorites(): Promise<FavoriteOffer[]> {
  const raw = await AsyncStorage.getItem(KEY);
  if (!raw) return [];
  try { return normalizeFavoriteOffers(JSON.parse(raw)); } catch { return []; }
}

export async function toggleFavorite(offer: FavoriteOffer) {
  const current = await readFavorites();
  const normalized = normalizeFavoriteOffer(offer);
  if (!normalized) return current;
  const next = applyFavoriteToggle(current, normalized);
  await AsyncStorage.setItem(KEY, JSON.stringify(next));
  return next;
}
