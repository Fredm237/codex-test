import AsyncStorage from "@react-native-async-storage/async-storage";

import { normalizeFilonCurrency } from "./filon-api";
import type { OutfitRole, OutfitSolution } from "./filon-intelligence";
import { isSafePartnerOfferUrl } from "./partner-offer";

export type SavedOutfitPiece = { offerId: number; name: string; price: number; currency: string; merchantName: string; link: string; imageUrl: string | null; role: OutfitRole };
export type SavedOutfit = { id: string; title: string; mode: "create" | "complete"; total: number; currency: string | null; confidenceScore: null; measurementStatus: "not_calibrated"; pieces: SavedOutfitPiece[]; createdAt: string };
const STORAGE_KEY = "filon.intelligence.outfit-journal.v1";
const LIMIT = 30;
const OUTFIT_ROLES: ReadonlySet<string> = new Set(["base", "structure", "footwear", "accessory"]);

function nonEmptyText(value: unknown): string | null {
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : null;
}

function normalizeSavedPiece(raw: unknown): SavedOutfitPiece | null {
  if (typeof raw !== "object" || raw === null) return null;
  const piece = raw as Partial<SavedOutfitPiece>;
  const name = nonEmptyText(piece.name);
  const currency = normalizeFilonCurrency(piece.currency);
  const merchantName = nonEmptyText(piece.merchantName);
  const link = nonEmptyText(piece.link);
  if (!Number.isInteger(piece.offerId) || piece.offerId! <= 0 || name === null || typeof piece.price !== "number" || !Number.isFinite(piece.price) || piece.price <= 0 || currency === null || merchantName === null || link === null || !isSafePartnerOfferUrl(link) || typeof piece.role !== "string" || !OUTFIT_ROLES.has(piece.role)) return null;
  if (piece.imageUrl !== null && piece.imageUrl !== undefined && typeof piece.imageUrl !== "string") return null;
  return { offerId: piece.offerId!, name, price: piece.price, currency, merchantName, link, imageUrl: piece.imageUrl ?? null, role: piece.role as OutfitRole };
}

export function makeSavedOutfit(title: string, mode: SavedOutfit["mode"], solution: OutfitSolution, now = new Date().toISOString()): SavedOutfit {
  const pieces = solution.pieces.map((piece) => ({ offerId: piece.offer.id, name: piece.offer.name, price: piece.offer.price, currency: piece.offer.currency, merchantName: piece.offer.merchantName, link: piece.offer.link, imageUrl: piece.offer.imageUrl, role: piece.role }));
  return { id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`, title: title.trim().slice(0, 120) || "Tenue FILON", mode, total: solution.total, currency: solution.currency, confidenceScore: null, measurementStatus: "not_calibrated", pieces, createdAt: now };
}

export function mergeSavedOutfits(items: SavedOutfit[], next: SavedOutfit): SavedOutfit[] {
  const signature = next.pieces.map((piece) => piece.offerId).sort((left, right) => left - right).join(",");
  const withoutDuplicate = items.filter((item) => item.pieces.map((piece) => piece.offerId).sort((left, right) => left - right).join(",") !== signature);
  return [next, ...withoutDuplicate].slice(0, LIMIT);
}

export function sanitizeSavedOutfits(raw: unknown): SavedOutfit[] {
  if (!Array.isArray(raw)) return [];
  return raw.reduce<SavedOutfit[]>((valid, item) => {
    if (typeof item !== "object" || item === null) return valid;
    const candidate = item as Partial<SavedOutfit>;
    if (typeof candidate.id !== "string" || typeof candidate.title !== "string" || (candidate.mode !== "create" && candidate.mode !== "complete") || typeof candidate.total !== "number" || !Number.isFinite(candidate.total) || candidate.total <= 0 || !Array.isArray(candidate.pieces) || candidate.pieces.length === 0 || typeof candidate.createdAt !== "string") return valid;
    const pieces = candidate.pieces.map(normalizeSavedPiece);
    if (pieces.some((piece) => piece === null)) return valid;
    const normalizedPieces = pieces as SavedOutfitPiece[];
    const offerIds = new Set(normalizedPieces.map((piece) => piece.offerId));
    const pieceCurrencies = new Set(normalizedPieces.map((piece) => piece.currency));
    const observedTotal = normalizedPieces.reduce((total, piece) => total + piece.price, 0);
    const currency = normalizeFilonCurrency(candidate.currency);
    if ((candidate.currency !== undefined && candidate.currency !== null && currency === null) || offerIds.size !== normalizedPieces.length || pieceCurrencies.size !== 1 || (currency !== null && !pieceCurrencies.has(currency)) || Math.abs(observedTotal - candidate.total) > 0.005) return valid;
    valid.push({
      id: candidate.id,
      title: candidate.title,
      mode: candidate.mode,
      total: candidate.total,
      // Les anciennes sauvegardes n’avaient aucune devise au niveau du total.
      // Elles restent lisibles, mais leur total ne reçoit aucune devise inventée.
      currency,
      // Tout ancien score heuristique est dégradé, jamais repris comme mesure.
      confidenceScore: null,
      measurementStatus: "not_calibrated",
      pieces: normalizedPieces,
      createdAt: candidate.createdAt,
    });
    return valid;
  }, []).slice(0, LIMIT);
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
